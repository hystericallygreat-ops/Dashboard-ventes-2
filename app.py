import streamlit as st
import pandas as pd
import os
import math
from datetime import datetime
import holidays

st.set_page_config(page_title="HelloWatt Dashboard", layout="wide")

# ---------------- CSS ----------------
st.markdown("""
<style>

section[data-testid="stSidebar"] {
    background-color: #E2E8F0;
}

.stProgress > div > div > div > div {
    background-color:#0F8BC6;
}

.block {
    padding: 12px;
    border-radius: 10px;
    background-color: #F8FAFC;
    border: 1px solid #CBD5E1;
    margin-bottom: 10px;
}

</style>
""", unsafe_allow_html=True)

SAVE_PATH = "last_uploaded.xlsx"

st.title("HelloWatt - Dashboard")

# ---------------- NAVIGATION ----------------
page = st.sidebar.radio("Navigation", ["📊 Dashboard","👤 Agents","🎯 Objectifs"])

uploaded_file = None

# ---------------- UTILS ----------------
def clean_text(col):
    return col.astype(str).str.strip().str.upper()

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

# ---------------- LOAD ----------------
if os.path.exists(SAVE_PATH):
    uploaded_file = SAVE_PATH

if uploaded_file:

    xls = pd.ExcelFile(uploaded_file)
    df = pd.read_excel(xls,"Extraction")
    code = pd.read_excel(xls,"Code")
    objectifs = pd.read_excel(xls,"Objectifs")

    # ---------------- NORMALISATION ----------------
    objectifs.columns = (
        objectifs.columns
        .str.strip()
        .str.upper()
        .str.replace(" ", "_")
    )

    df["responder"] = clean_text(df["responder"])
    code.iloc[:,0] = clean_text(code.iloc[:,0])

    df = df.merge(
        code.rename(columns={code.columns[0]:"responder",code.columns[1]:"agent"}),
        on="responder",how="left"
    )

    df["agent"] = clean_text(df["agent"]).fillna("INCONNU")
    df["get_provider"] = clean_text(df["get_provider"])
    df["energie"] = clean_text(df["energie"])
    df["date"] = pd.to_datetime(df["date"],errors="coerce")

    USER_COL = "user id"

    # ---------------- FILTRES ----------------
    st.sidebar.markdown("### 🔎 Filtres")

    agents = st.sidebar.multiselect("Agents", df["agent"].unique(), df["agent"].unique())
    fournisseurs = st.sidebar.multiselect("Fournisseurs", df["get_provider"].unique(), df["get_provider"].unique())
    energie = st.sidebar.multiselect("Énergie", df["energie"].unique(), df["energie"].unique())

    min_d,max_d = df["date"].min(),df["date"].max()
    dates = st.sidebar.date_input("Période",[min_d,max_d])

    df_filtered = df[
        df["agent"].isin(agents) &
        df["get_provider"].isin(fournisseurs) &
        df["energie"].isin(energie)
    ]

    if len(dates)==2:
        df_filtered = df_filtered[
            (df_filtered["date"]>=pd.to_datetime(dates[0])) &
            (df_filtered["date"]<=pd.to_datetime(dates[1]))
        ]

    # ================= DASHBOARD =================
    if page=="📊 Dashboard":

        st.header("🏢 Objectifs Globaux")

        ventes = df_filtered.groupby("get_provider").size().reset_index(name="ventes")

        df_obj = objectifs.merge(
            ventes,left_on="FOURNISSEUR",right_on="get_provider",how="left"
        ).fillna(0)

        for _,r in df_obj.iterrows():

            df_f = df_filtered[df_filtered["get_provider"]==r["FOURNISSEUR"]]

            elec = len(df_f[df_f["energie"]=="ELEC"])
            gaz = len(df_f[df_f["energie"]=="GAZ"])
            total = elec + gaz

            obj_total = r["OBJECTIFS_TOTAL"]
            obj_elec = r["OBJECTIF_ELEC"]
            obj_gaz = r["OBJECTIF_GAZ"]

            p = total / obj_total if obj_total else 0

            c1,c2,c3 = st.columns([3,5,6])

            c1.write(r["FOURNISSEUR"])
            c2.progress(min(p,1.0))

            c3.write(
                f"{emoji(p)} "
                f"⚡ {elec}/{obj_elec} "
                f"🔥 {gaz}/{obj_gaz} "
                f"🎯 {total}/{obj_total} ({p:.0%})"
            )

    # ================= AGENTS =================
    elif page=="👤 Agents":

        st.header("👤 Performance Agents")

        jours = get_working_days()
        obj_agent = math.ceil(185*0.75)

        ventes_agent = df_filtered.groupby("agent").size().reset_index(name="ventes")
        ventes_agent["taux"] = ventes_agent["ventes"]/obj_agent
        ventes_agent["kpi"] = ventes_agent["ventes"]/jours if jours else 0

        ventes_agent = ventes_agent.sort_values("taux",ascending=False)

        for _,r in ventes_agent.iterrows():

            c1,c2,c3,c4 = st.columns([3,5,2,2])

            c1.write(r["agent"])
            c2.progress(min(r["taux"],1.0))
            c3.write(f"{emoji(r['taux'])} {r['ventes']}/{obj_agent} ({r['taux']:.0%})")
            c4.write(f"📅 {round(r['kpi'],1)}/J")

    # ================= OBJECTIFS =================
    elif page=="🎯 Objectifs":

        st.header("🎯 Performance détaillée")

        colA, colB = st.columns(2)
        heures = colA.number_input("Heures", value=185.0)
        agent = colB.selectbox("Agent", df_filtered["agent"].unique())

        df_agent = df_filtered[df_filtered["agent"]==agent]

        obj_total = round_excel(heures*0.75)

        elec = len(df_agent[df_agent["energie"]=="ELEC"])
        gaz = len(df_agent[df_agent["energie"]=="GAZ"])
        total = elec + gaz

        taux = total / obj_total if obj_total else 0

        st.markdown('<div class="block">', unsafe_allow_html=True)

        c1,c2,c3 = st.columns([3,5,6])

        c1.write(agent)
        c2.progress(min(taux,1.0))

        c3.write(
            f"{emoji(taux)} "
            f"⚡ {elec} "
            f"🔥 {gaz} "
            f"🎯 {total}/{obj_total} ({taux:.0%})"
        )

        st.markdown('</div>', unsafe_allow_html=True)

else:
    st.info("🔒 Ajoute un fichier (admin)")
