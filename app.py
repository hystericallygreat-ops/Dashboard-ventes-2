import streamlit as st
import pandas as pd
import os
import math
from datetime import datetime
import holidays

st.set_page_config(page_title="HelloWatt Dashboard", layout="wide")

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

div[data-testid="column"] {
    min-width: 120px;
}

</style>
""", unsafe_allow_html=True)

SAVE_PATH = "last_uploaded.xlsx"

st.title("HelloWatt - Dashboard")

page = st.sidebar.radio("Navigation", ["📊 Dashboard","👤 Agents","🎯 Objectifs"])

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
else:
    uploaded_file = None

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

    agents = st.sidebar.multiselect("Agents", df["agent"].unique(), df["agent"].unique())
    fournisseurs = st.sidebar.multiselect("Fournisseurs", df["get_provider"].unique(), df["get_provider"].unique())
    energie = st.sidebar.multiselect("Énergie", df["energie"].unique(), df["energie"].unique())

    min_d,max_d=df["date"].min(),df["date"].max()
    dates = st.sidebar.date_input("Période",[min_d,max_d])

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
            ventes,
            left_on="Fournisseur",
            right_on="get_provider",
            how="left"
        ).fillna({"ventes":0})

        for _,r in df_obj.iterrows():

            p = r["ventes"]/r["Objectifs Total"] if r["Objectifs Total"] else 0

            df_f = df_filtered[df_filtered["get_provider"]==r["Fournisseur"]]

            v_elec = len(df_f[df_f["energie"]=="ELEC"])
            v_gaz = len(df_f[df_f["energie"]=="GAZ"])
            v_total = len(df_f)

            obj_elec = objectifs[objectifs["Fournisseur"]==r["Fournisseur"]]["Objectif Elec"].sum()
            obj_gaz = objectifs[objectifs["Fournisseur"]==r["Fournisseur"]]["Objectif Gaz"].sum()

            c1,c2,c3 = st.columns([3,6,4])
            c1.write(r["Fournisseur"])
            c2.progress(min(p,1.0))
            c3.markdown(
                f"⚡ {v_elec}/{obj_elec} 🔥 {v_gaz}/{obj_gaz} 🎯 {int(v_total)}/{int(r['Objectifs Total'])} {emoji(p)} {p:.0%}",
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

        total_obj = objectifs["Objectifs Total"].sum()
        obj_elec_global = objectifs["Objectif Elec"].sum()
        obj_gaz_global = objectifs["Objectif Gaz"].sum()

        ratio_elec = obj_elec_global/total_obj if total_obj else 0
        ratio_gaz = obj_gaz_global/total_obj if total_obj else 0

        for _,r in ventes_agent.iterrows():

            agent_name = r["agent"]
            df_agent = df_filtered[df_filtered["agent"]==agent_name]

            v_elec = len(df_agent[df_agent["energie"]=="ELEC"])
            v_gaz = len(df_agent[df_agent["energie"]=="GAZ"])
            v_total = len(df_agent)

            obj_elec = round(obj_agent*ratio_elec)
            obj_gaz = round(obj_agent*ratio_gaz)
            obj_total = obj_elec + obj_gaz

            p = v_total/obj_total if obj_total else 0

            c1,c2,c3,c4 = st.columns([3,5,6,3])

            c1.write(agent_name)
            c2.progress(min(p,1.0))

            c3.markdown(
                f"""
                <div style="
                    display:flex;
                    gap:18px;
                    align-items:center;
                    white-space:nowrap;
                ">
                    <div>⚡ <b>{v_elec}</b>/<span>{obj_elec}</span></div>
                    <div>🔥 <b>{v_gaz}</b>/<span>{obj_gaz}</span></div>
                    <div>🎯 <b>{v_total}</b>/<span>{obj_total}</span></div>
                    <div>{emoji(p)} <b>{p:.0%}</b></div>
                </div>
                """,
                unsafe_allow_html=True
            )

            c4.write(f"📅 {round(r['kpi'],1)}/J")

    # ================= OBJECTIFS (RESTAURÉ COMPLET) =================
    elif page=="🎯 Objectifs":

        st.header("🎯 Performance détaillée")

        colA,colB = st.columns(2)
        heures = colA.number_input("Heures", value=185.0)
        agent = colB.selectbox("Agent", df_filtered["agent"].dropna().unique())

        df_agent = df_filtered[df_filtered["agent"]==agent]

        obj_agent = round_excel(heures*0.75)
        ventes_total = len(df_agent)
        taux = ventes_total/obj_agent if obj_agent else 0

        st.markdown("<div class='block'>", unsafe_allow_html=True)
        st.subheader(agent)
        st.progress(min(taux,1.0))
        st.write(f"{emoji(taux)} {ventes_total}/{obj_agent} ({taux:.0%})")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("### ⚡ Ventes Fournisseurs")

        special=["HOMESERVE","FREE"]

        for f in objectifs["Fournisseur"].dropna().unique():

            if f in special:
                continue

            df_f = df_agent[df_agent["get_provider"]==f]
            obj_row = objectifs[objectifs["Fournisseur"]==f]

            obj_total_f = round_excel(heures*0.75*(obj_row["Objectifs Total"].sum()/objectif_total))
            obj_elec_f = round_excel(heures*0.75*(obj_row["Objectif Elec"].sum()/objectif_total))
            obj_gaz_f = round_excel(heures*0.75*(obj_row["Objectif Gaz"].sum()/objectif_total))

            v_total = len(df_f)
            v_elec = len(df_f[df_f["energie"]=="ELEC"])
            v_gaz = len(df_f[df_f["energie"]=="GAZ"])

            p = v_total/obj_total_f if obj_total_f else 0

            c1,c2,c3 = st.columns([2,5,5])
            c1.write(f)
            c2.progress(min(p,1.0))
            c3.markdown(
                f"⚡ {v_elec}/{obj_elec_f} 🔥 {v_gaz}/{obj_gaz_f} 🎯 {v_total}/{obj_total_f} {emoji(p)} {p:.0%}",
                unsafe_allow_html=True
            )

else:
    st.info("🔒 Ajoute un fichier (admin)")
