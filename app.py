import streamlit as st
import pandas as pd
import os
import math
from datetime import datetime
import holidays

st.set_page_config(page_title="HelloWatt Dashboard", layout="wide")

# ---------------- CSS FIX SAFE ----------------
st.markdown("""
<style>

/* SIDEBAR CLEAN */
section[data-testid="stSidebar"] {
    background-color: #EDF7FA;
    border-right: 1px solid #E2E8F0;
}

/* LABEL */
section[data-testid="stSidebar"] label {
    color: #475569;
    font-weight: 500;
}

/* TAGS FIX (IMPORTANT) */
[data-baseweb="tag"] {
    background-color: #E0F2FE !important;
    color: #0369A1 !important;
    border-radius: 6px !important;
    max-width: 100% !important;
}

/* Empêche le bloc gris cassé */
[data-baseweb="select"] {
    overflow: hidden !important;
}

/* PROGRESS */
.stProgress > div > div > div > div {
    background-color:#0F8BC6;
}

/* BLOCS VISUELS */
.block {
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 15px;
    margin-bottom: 15px;
    background: white;
}

</style>
""", unsafe_allow_html=True)

SAVE_PATH = "last_uploaded.xlsx"

st.title("HelloWatt - Dashboard")

# ---------------- AUTH ----------------
password = st.sidebar.text_input("🔐 Admin", type="password")
is_admin = password == "hello123"

uploaded_file = None

if is_admin:
    uploaded_file = st.sidebar.file_uploader("Uploader fichier Excel", type=["xlsx"])
    if uploaded_file:
        with open(SAVE_PATH, "wb") as f:
            f.write(uploaded_file.getbuffer())

    if os.path.exists(SAVE_PATH):
        if st.sidebar.button("🗑 Supprimer"):
            os.remove(SAVE_PATH)
            st.rerun()
else:
    if os.path.exists(SAVE_PATH):
        uploaded_file = SAVE_PATH

# ---------------- NAV ----------------
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

# ---------------- APP ----------------
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

    # ================= OBJECTIFS =================
    if page=="🎯 Objectifs":

        st.header("🎯 Performance détaillée")

        # -------- BLOCK 1 : AGENT --------
        st.markdown('<div class="block">', unsafe_allow_html=True)

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

        st.markdown('</div>', unsafe_allow_html=True)

        # -------- BLOCK 2 : FOURNISSEURS --------
        st.markdown('<div class="block">', unsafe_allow_html=True)

        st.subheader("⚡ Ventes Fournisseurs")

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

        st.markdown('</div>', unsafe_allow_html=True)

        # -------- BLOCK 3 : ADDITIONNEL --------
        st.markdown('<div class="block">', unsafe_allow_html=True)

        st.subheader("⭐ Ventes Additionnelles")

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

        st.markdown('</div>', unsafe_allow_html=True)

else:
    st.info("🔒 Ajoute un fichier (admin)")
