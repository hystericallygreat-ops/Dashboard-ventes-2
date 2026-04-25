import streamlit as st
import pandas as pd
import os
import math
from datetime import datetime
import holidays

st.set_page_config(page_title="HelloWatt Dashboard", layout="wide")

# ---------------- CSS SAFE (INCHANGÉ) ----------------
st.markdown("""
<style>

section[data-testid="stSidebar"] {
    background-color: #E2E8F0;
}

[data-baseweb="tag"] {
    background-color: #BFDBFE !important;
    color: #1E3A8A !important;
}

.stProgress > div > div > div > div {
    background-color:#0F8BC6;
}

.block {
    padding: 12px;
    border-radius: 10px;
    background-color: #F8FAFC;
    border: 1px solid #CBD5E1;
    margin-bottom: 12px;
}

h1, h2, h3 {
    margin-top: 10px !important;
    margin-bottom: 10px !important;
}

</style>
""", unsafe_allow_html=True)

SAVE_PATH = "last_uploaded.xlsx"

st.title("HelloWatt - Dashboard")

page = st.sidebar.radio("Navigation", ["📊 Dashboard","👤 Agents","🎯 Objectifs"])

uploaded_file = None

# ---------------- UTILS ----------------
def clean_text(col):
    return col.astype(str).str.strip().str.replace('"','').str.replace("'","").str.upper()

def emoji(p):
    return "🟢" if p>=1 else "🟠" if p>=0.7 else "🔴"

def round_excel(x):
    return int(x+0.5+1e-9)

def get_working_days():
    today = datetime.today()
    start = today.replace(day=1)
    fr = holidays.FR()
    days = pd.date_range(start, today)
    return len([d for d in days if d.weekday()<5 and d.date() not in fr])

# ---------------- DATA ----------------
if os.path.exists(SAVE_PATH):
    uploaded_file = SAVE_PATH

if uploaded_file:

    xls = pd.ExcelFile(uploaded_file)
    df = pd.read_excel(xls,"Extraction")
    code = pd.read_excel(xls,"Code")
    objectifs = pd.read_excel(xls,"Objectifs")

    df["responder"]=clean_text(df["responder"])
    code.iloc[:,0]=clean_text(code.iloc[:,0])

    df = df.merge(
        code.rename(columns={code.columns[0]:"responder",code.columns[1]:"agent"}),
        on="responder",how="left"
    )

    df["agent"]=clean_text(df["agent"]).fillna("INCONNU")
    df["get_provider"]=clean_text(df["get_provider"])

    df["energie"]=(
        df["energie"]
        .astype(str)
        .str.strip()
        .str.lower()
        .replace({"gas":"GAZ","elec":"ELEC"})
        .str.upper()
    )

    df["date"]=pd.to_datetime(df["date"],errors="coerce")
    objectifs["Fournisseur"]=clean_text(objectifs["Fournisseur"])

    USER_COL="user id"

    # ---------------- FILTRES ----------------
    st.sidebar.markdown("### 🔎 Filtres")

    agents = st.sidebar.multiselect("Agents", df["agent"].unique(), df["agent"].unique())
    fournisseurs = st.sidebar.multiselect("Fournisseurs", df["get_provider"].unique(), df["get_provider"].unique())
    energie = st.sidebar.multiselect("Énergie", df["energie"].unique(), df["energie"].unique())

    min_d,max_d=df["date"].min(),df["date"].max()
    dates = st.sidebar.date_input("Période",[min_d,max_d])

    # ---------------- ADMIN ----------------
    st.sidebar.markdown("---")
    password = st.sidebar.text_input("🔐 Admin", type="password")
    is_admin = password == "hello123"

    if is_admin:
        uploaded_file_admin = st.sidebar.file_uploader("Uploader fichier Excel", type=["xlsx"])
        if uploaded_file_admin:
            with open(SAVE_PATH, "wb") as f:
                f.write(uploaded_file_admin.getbuffer())

        if os.path.exists(SAVE_PATH):
            if st.sidebar.button("🗑 Supprimer"):
                os.remove(SAVE_PATH)
                st.rerun()

    # ---------------- FILTRAGE SAFE ----------------
    df_filtered = df.copy()

    if len(agents)>0:
        df_filtered = df_filtered[df_filtered["agent"].isin(agents)]

    if len(fournisseurs)>0:
        df_filtered = df_filtered[df_filtered["get_provider"].isin(fournisseurs)]

    if len(energie)>0:
        df_filtered = df_filtered[df_filtered["energie"].isin(energie)]

    if len(dates)==2:
        df_filtered = df_filtered[
            (df_filtered["date"]>=pd.to_datetime(dates[0])) &
            (df_filtered["date"]<=pd.to_datetime(dates[1]))
        ]

    objectif_total = objectifs["Objectifs Total"].sum()

    # ================= DASHBOARD =================
    if page=="📊 Dashboard":

        st.header("🏢 Objectifs Globaux")

        ventes = df_filtered.groupby("get_provider").size().reset_index(name="ventes")

        df_obj = objectifs.merge(
            ventes,left_on="Fournisseur",right_on="get_provider",how="left"
        ).fillna(0)

        for _,r in df_obj.iterrows():

            p = r["ventes"]/r["Objectifs Total"] if r["Objectifs Total"] else 0

            df_f = df_filtered[df_filtered["get_provider"]==r["Fournisseur"]]

            v_elec = len(df_f[df_f["energie"]=="ELEC"])
            v_gaz = len(df_f[df_f["energie"]=="GAZ"])

            obj_elec = objectifs[objectifs["Fournisseur"]==r["Fournisseur"]]["Objectif Elec"].sum()
            obj_gaz = objectifs[objectifs["Fournisseur"]==r["Fournisseur"]]["Objectif Gaz"].sum()

            with st.container():
                c1,c2,c3 = st.columns([3,6,4])
                c1.write(r["Fournisseur"])
                c2.progress(min(p,1.0))
                c3.markdown(
                    f"⚡ {v_elec}/{obj_elec} 🔥 {v_gaz}/{obj_gaz} 🎯 {int(r['ventes'])}/{int(r['Objectifs Total'])} {emoji(p)} {p:.0%}",
                    unsafe_allow_html=True
                )

    # ================= AGENTS =================
    elif page=="👤 Agents":

        st.header("👤 Performance Agents")

        jours = get_working_days()
        obj_agent = math.ceil(185*0.75)

        ventes_agent = df_filtered.groupby("agent").size().reset_index(name="ventes")

        ventes_agent["taux"]=ventes_agent["ventes"]/obj_agent
        ventes_agent["kpi"]=ventes_agent["ventes"]/jours if jours else 0

        ventes_agent = ventes_agent.sort_values("taux",ascending=False)

        total_obj_global = objectifs["Objectifs Total"].sum()
        total_obj_elec = objectifs["Objectif Elec"].sum()
        total_obj_gaz = objectifs["Objectif Gaz"].sum()

        ratio_elec = total_obj_elec / total_obj_global if total_obj_global else 0
        ratio_gaz = total_obj_gaz / total_obj_global if total_obj_global else 0

        for _,r in ventes_agent.iterrows():

            agent_name = r["agent"]
            df_agent = df_filtered[df_filtered["agent"] == agent_name]

            v_elec = len(df_agent[df_agent["energie"]=="ELEC"])
            v_gaz = len(df_agent[df_agent["energie"]=="GAZ"])

            # 🔥 TOTAL = TOUT
            v_total = len(df_agent)

            obj_elec = round(obj_agent * ratio_elec)
            obj_gaz = round(obj_agent * ratio_gaz)
            obj_total = obj_elec + obj_gaz

            p = v_total / obj_total if obj_total else 0

            c1,c2,c3,c4 = st.columns([3,5,4,2])

            c1.write(agent_name)
            c2.progress(min(p,1.0))

            c3.markdown(
                f"⚡ {v_elec}/{obj_elec} 🔥 {v_gaz}/{obj_gaz} 🎯 {v_total}/{obj_total} {emoji(p)} {p:.0%}",
                unsafe_allow_html=True
            )

            c4.write(f"📅 {round(r['kpi'],1)}/J")

    # ================= OBJECTIFS =================
    elif page=="🎯 Objectifs":

        st.header("🎯 Performance détaillée")

        colA,colB = st.columns(2)
        heures = colA.number_input("Heures", value=185.0)
        agent = colB.selectbox("Agent", df_filtered["agent"].unique())

        df_agent = df_filtered[df_filtered["agent"] == agent]

        obj_agent = round_excel(heures*0.75)

        ventes_total = len(df_agent)

        taux = ventes_total/obj_agent if obj_agent else 0

        st.progress(min(taux,1.0))
        st.write(f"{emoji(taux)} {ventes_total}/{obj_agent} ({taux:.0%})")

else:
    st.info("🔒 Ajoute un fichier (admin)")
