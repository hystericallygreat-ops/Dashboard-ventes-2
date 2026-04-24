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

[data-baseweb="tag"] {
    background-color: #BFDBFE !important;
    color: #1E3A8A !important;
}

/* KPI CARD ULTRA CLEAN */
.kpi-card {
    background-color: #F8FAFC;
    border: 1px solid #CBD5E1;
    border-radius: 14px;
    height: 120px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    padding: 10px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.kpi-card h4 {
    margin: 0;
    font-size: 14px;
    color: #334155;
}

.kpi-card h2 {
    margin: 5px 0 0 0;
    font-size: 22px;
}

/* PROGRESS */
.stProgress > div > div > div > div {
    background-color:#0F8BC6;
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

    df["responder"] = clean_text(df["responder"])
    code.iloc[:,0] = clean_text(code.iloc[:,0])

    df = df.merge(
        code.rename(columns={code.columns[0]:"responder",code.columns[1]:"agent"}),
        on="responder",how="left"
    )

    df["agent"] = clean_text(df["agent"]).fillna("INCONNU")
    df["get_provider"] = clean_text(df["get_provider"])

    # ---------------- FIX ÉNERGIE (IMPORTANT) ----------------
    df["energie"] = (
        df["energie"]
        .astype(str)
        .str.strip()
        .str.lower()
        .replace({"gas":"GAZ","elec":"ELEC"})
        .str.upper()
    )

    df["date"] = pd.to_datetime(df["date"],errors="coerce")
    objectifs["Fournisseur"] = clean_text(objectifs["Fournisseur"])

    USER_COL = "user id"

    # ---------------- FILTRES ----------------
    st.sidebar.markdown("### 🔎 Filtres")

    agents = st.sidebar.multiselect("Agents", df["agent"].unique(), df["agent"].unique())
    fournisseurs = st.sidebar.multiselect("Fournisseurs", df["get_provider"].unique(), df["get_provider"].unique())
    energie = st.sidebar.multiselect("Énergie", df["energie"].unique(), df["energie"].unique())

    min_d,max_d = df["date"].min(),df["date"].max()
    dates = st.sidebar.date_input("Période",[min_d,max_d])

    if len(energie) == 0:
        energie = df["energie"].unique()

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

    objectif_total = objectifs["Objectifs Total"].sum()

    # ================= DASHBOARD =================
    if page=="📊 Dashboard":

        st.header("🏢 Objectifs Globaux")

        ventes = df_filtered.groupby("get_provider").size().reset_index(name="ventes")

        df_obj = objectifs.merge(
            ventes,left_on="Fournisseur",right_on="get_provider",how="left"
        ).fillna(0)

        total_ventes = df_filtered.shape[0]

        # ---------------- KPI CENTRÉS ----------------
        total_elec = df_filtered[df_filtered["energie"]=="ELEC"].shape[0]
        total_gaz = df_filtered[df_filtered["energie"]=="GAZ"].shape[0]

        obj_elec = objectifs["Objectif Elec"].sum()
        obj_gaz = objectifs["Objectif Gaz"].sum()

        perf_global = total_ventes / objectif_total if objectif_total else 0

        kpi_cols = st.columns(5, gap="large")

        kpi_data = [
            ("🎯 Objectif", f"{int(objectif_total)}"),
            ("📈 Réalisé", f"{int(total_ventes)}"),
            ("🔥 Performance", f"{perf_global:.1%}"),
            ("⚡ Élec", f"{total_elec}/{int(obj_elec)}"),
            ("🔥 Gaz", f"{total_gaz}/{int(obj_gaz)}"),
        ]

        for col,(title,value) in zip(kpi_cols,kpi_data):
            with col:
                st.markdown(f"""
                <div class="kpi-card">
                    <h4>{title}</h4>
                    <h2>{value}</h2>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ---------------- FOURNISSEURS ----------------
        st.subheader("🏭 Performance par fournisseur")

        for f in objectifs["Fournisseur"].dropna().unique():

            df_f = df_filtered[df_filtered["get_provider"]==f]

            ventes_total_f = len(df_f)
            obj_row = objectifs[objectifs["Fournisseur"]==f]

            obj_total_f = obj_row["Objectifs Total"].sum()
            obj_elec_f = obj_row["Objectif Elec"].sum()
            obj_gaz_f = obj_row["Objectif Gaz"].sum()

            ventes_elec = len(df_f[df_f["energie"]=="ELEC"])
            ventes_gaz = len(df_f[df_f["energie"]=="GAZ"])

            p = ventes_total_f / obj_total_f if obj_total_f else 0

            c1,c2,c3 = st.columns([2,5,4])

            with c1:
                st.write(f)

            with c2:
                st.progress(min(p,1.0))

            with c3:
                st.markdown(f"""
                ⚡ {ventes_elec}/{int(obj_elec_f)} &nbsp;&nbsp;
                🔥 {ventes_gaz}/{int(obj_gaz_f)} &nbsp;&nbsp;
                🎯 {ventes_total_f}/{int(obj_total_f)} &nbsp;&nbsp;
                <b>{emoji(p)} {p:.0%}</b>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

else:
    st.info("🔒 Ajoute un fichier (admin)")
