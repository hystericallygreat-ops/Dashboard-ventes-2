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

/* SIDEBAR */
section[data-testid="stSidebar"] {
    background-color: #E2E8F0;
}

/* TAGS */
[data-baseweb="tag"] {
    background-color: #BFDBFE !important;
    color: #1E3A8A !important;
}

/* PROGRESS */
.stProgress > div > div > div > div {
    background-color:#0F8BC6;
}

/* BLOCS */
.block {
    padding: 12px;
    border-radius: 10px;
    background-color: #F8FAFC;
    border: 1px solid #CBD5E1;
    margin-bottom: 12px;
}

/* ESPACE GLOBAL */
h1, h2, h3 {
    margin-top: 10px !important;
    margin-bottom: 10px !important;
}

</style>
""", unsafe_allow_html=True)

SAVE_PATH = "last_uploaded.xlsx"

# ---------------- HEADER ----------------
st.title("HelloWatt - Dashboard")
st.markdown("<br>", unsafe_allow_html=True)  # espace léger

# ---------------- NAV (RESTE EN HAUT) ----------------
page = st.sidebar.radio("Navigation", ["📊 Dashboard","👤 Agents","🎯 Objectifs"])

uploaded_file = None
is_admin = False

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

# ---------------- APP ----------------
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

    # ---------------- ADMIN (DÉPLACÉ EN BAS) ----------------
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

    # ---------------- FILTRAGE ----------------
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
        st.markdown("<br>", unsafe_allow_html=True)  # espace ajouté

        ventes = df_filtered.groupby("get_provider").size().reset_index(name="ventes")

        df_obj = objectifs.merge(
            ventes,left_on="Fournisseur",right_on="get_provider",how="left"
        ).fillna(0)

        df_obj = df_obj.sort_values("Objectifs Total",ascending=False)

        for _,r in df_obj.iterrows():

            p = r["ventes"]/r["Objectifs Total"] if r["Objectifs Total"] else 0

            with st.container():
                c1,c2,c3 = st.columns([3,6,2])
                c1.write(r["Fournisseur"])
                c2.progress(min(p,1.0))
                c3.write(f"{emoji(p)} {int(r['ventes'])}/{int(r['Objectifs Total'])} ({p:.0%})")

            st.markdown("<br>", unsafe_allow_html=True)  # petit espace entre lignes

    # ================= AGENTS =================
    elif page=="👤 Agents":

        st.header("👤 Performance Agents")
        st.markdown("<br>", unsafe_allow_html=True)

        jours = get_working_days()
        obj_agent = math.ceil(185*0.75)

        ventes_agent = df_filtered.groupby("agent").size().reset_index(name="ventes")
        ventes_agent["taux"]=ventes_agent["ventes"]/obj_agent
        ventes_agent["kpi"]=ventes_agent["ventes"]/jours if jours else 0

        ventes_agent = ventes_agent.sort_values("taux",ascending=False)

        for _,r in ventes_agent.iterrows():

            with st.container():
                c1,c2,c3,c4 = st.columns([3,5,2,2])
                c1.write(r["agent"])
                c2.progress(min(r["taux"],1.0))
                c3.write(f"{emoji(r['taux'])} {r['ventes']}/{obj_agent} ({r['taux']:.0%})")
                c4.write(f"📅 {round(r['kpi'],1)}/J")

            st.markdown("<br>", unsafe_allow_html=True)

    # ================= OBJECTIFS =================
    elif page=="🎯 Objectifs":

        st.header("🎯 Performance détaillée")
        st.markdown("<br>", unsafe_allow_html=True)

        # -------- BLOC 1 --------
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

        st.markdown("<br>", unsafe_allow_html=True)

        # -------- BLOC 2 --------
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

        st.markdown("<br>", unsafe_allow_html=True)

        # -------- BLOC 3 --------
        st.markdown("### ⭐ Ventes Additionnelles")

        total_unique = df_agent[USER_COL].nunique()

        for sp in special:

            df_sp = df_agent[df_agent["get_provider"]==sp]
            ventes_sp = df_sp[USER_COL].nunique()

            obj_sp = max(1, round_excel(total_unique*0.05))
            p_sp = ventes_sp/obj_sp if obj_sp else 0

            c1,c2,c3 = st.columns([3,6,2])
            c1.write(sp)
            c2.progress(min(p_sp,1.0))
            c3.write(f"{emoji(p_sp)} {ventes_sp}/{obj_sp} ({p_sp:.0%})")

else:
    st.info("🔒 Ajoute un fichier (admin)")
