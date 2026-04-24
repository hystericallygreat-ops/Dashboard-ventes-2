import streamlit as st
import pandas as pd
import os
import math
from datetime import datetime
import holidays

st.set_page_config(page_title="HelloWatt Dashboard", layout="wide")

# ---------------- CSS SAFE ----------------
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

.kpi-card {
    background-color: #F8FAFC;
    border: 1px solid #CBD5E1;
    border-radius: 12px;
    padding: 18px;
    text-align: center;
}

h1, h2, h3 {
    margin-top: 10px !important;
    margin-bottom: 10px !important;
}

</style>
""", unsafe_allow_html=True)

SAVE_PATH = "last_uploaded.xlsx"

st.title("HelloWatt - Dashboard")
st.markdown("<br>", unsafe_allow_html=True)

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

# ---------------- LOAD ----------------
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
    df["energie"]=clean_text(df["energie"])
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

    # FIX SAFE (GAZ / ELEC)
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
        st.markdown("<br>", unsafe_allow_html=True)

        ventes = df_filtered.groupby("get_provider").size().reset_index(name="ventes")
        df_obj = objectifs.merge(
            ventes,left_on="Fournisseur",right_on="get_provider",how="left"
        ).fillna(0)

        total_ventes = df_filtered.shape[0]

        # ---------------- KPI CENTRÉS ----------------
        col_space1, col1, col2, col3, col4, col5, col_space2 = st.columns([1,2,2,2,2,2,1])

        with col1:
            st.markdown(f"""
            <div class="kpi-card">
                <h4>🎯 Objectif Total</h4>
                <h2>{int(objectif_total)}</h2>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="kpi-card">
                <h4>📈 Réalisé</h4>
                <h2>{int(total_ventes)}</h2>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            perf_global = total_ventes / objectif_total if objectif_total else 0
            st.markdown(f"""
            <div class="kpi-card">
                <h4>🔥 Performance</h4>
                <h2>{perf_global:.1%}</h2>
            </div>
            """, unsafe_allow_html=True)

        total_elec = df_filtered[df_filtered["energie"]=="ELEC"].shape[0]
        total_gaz = df_filtered[df_filtered["energie"]=="GAZ"].shape[0]

        obj_elec = objectifs["Objectif Elec"].sum()
        obj_gaz = objectifs["Objectif Gaz"].sum()

        with col4:
            st.markdown(f"""
            <div class="kpi-card">
                <h4>⚡ Électricité</h4>
                <h2>{total_elec}/{int(obj_elec)}</h2>
            </div>
            """, unsafe_allow_html=True)

        with col5:
            st.markdown(f"""
            <div class="kpi-card">
                <h4>🔥 Gaz</h4>
                <h2>{total_gaz}/{int(obj_gaz)}</h2>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ================= FOURNISSEURS =================
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

    # ================= AGENTS (corrigé emoji KPI jour) =================
    elif page=="👤 Agents":

        st.header("👤 Performance Agents")

        jours = get_working_days()
        obj_agent = math.ceil(185*0.75)

        ventes_agent = df_filtered.groupby("agent").size().reset_index(name="ventes")
        ventes_agent["taux"]=ventes_agent["ventes"]/obj_agent
        ventes_agent["kpi"]=ventes_agent["ventes"]/jours if jours else 0

        ventes_agent = ventes_agent.sort_values("taux",ascending=False)

        for _,r in ventes_agent.iterrows():

            c1,c2,c3,c4 = st.columns([3,5,2,2])
            c1.write(r["agent"])
            c2.progress(min(r["taux"],1.0))
            c3.write(f"{emoji(r['taux'])} {r['ventes']}/{obj_agent} ({r['taux']:.0%})")
            c4.write(f"📅 {emoji(r['taux'])} {round(r['kpi'],1)}/J")

    # ================= OBJECTIFS (RESTE IDENTIQUE) =================
    elif page=="🎯 Objectifs":

        st.header("🎯 Performance détaillée")

        with st.container():
            st.markdown("### 👤 Agent")

            colA, colB = st.columns(2)
            heures = colA.number_input("Heures", value=185.0)
            agent = colB.selectbox("Agent", df_filtered["agent"].unique())

            df_agent = df_filtered[df_filtered["agent"]==agent]

            obj_agent = round_excel(heures*0.75)
            ventes_total = len(df_agent)
            taux = ventes_total/obj_agent if obj_agent else 0

            c1,c2,c3 = st.columns([3,6,2])
            c1.write(agent)
            c2.progress(min(taux,1.0))
            c3.write(f"{emoji(taux)} {ventes_total}/{obj_agent} ({taux:.0%})")

        st.markdown("### ⚡ Ventes Fournisseurs")

        special=["HOMESERVE","FREE"]

        for f in objectifs["Fournisseur"].dropna().unique():

            if f in special:
                continue

            df_f = df_agent[df_agent["get_provider"]==f]
            obj_row = objectifs[objectifs["Fournisseur"]==f]

            ventes=len(df_f)
            obj=round_excel(heures*0.75*(obj_row["Objectifs Total"].sum()/objectif_total))
            p=ventes/obj if obj else 0

            c1,c2,c3 = st.columns([3,6,2])
            c1.write(f)
            c2.progress(min(p,1.0))
            c3.write(f"{emoji(p)} {ventes}/{obj} ({p:.0%})")

else:
    st.info("🔒 Ajoute un fichier (admin)")
