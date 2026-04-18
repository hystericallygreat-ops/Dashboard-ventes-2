import streamlit as st
import pandas as pd
import os
import math
from datetime import datetime
import holidays

st.set_page_config(page_title="HelloWatt Dashboard", layout="wide")

SAVE_PATH = "last_uploaded.xlsx"

# ---------------- STYLE ----------------
st.markdown("""
<style>

/* Responsive largeur dynamique */
.block-container {
    max-width: 100% !important;
    padding-top: 3rem;
}

/* HERO */
.hero {
    background: linear-gradient(135deg, #E0F2FE 0%, #EDF7FA 100%);
    padding: 20px;
    border-radius: 14px;
    margin-bottom: 15px;
}

/* CARD */
.card {
    background: white;
    padding: 14px;
    border-radius: 10px;
    box-shadow: 0 3px 10px rgba(0,0,0,0.04);
}

/* AGENT CARD */
.agent-card {
    background: white;
    padding: 14px;
    border-radius: 10px;
    box-shadow: 0 3px 10px rgba(0,0,0,0.04);
    margin-bottom: 10px;
}

/* PROGRESS */
.stProgress > div > div > div > div {
    background-color:#0F8BC6;
}

/* TAG */
[data-baseweb="tag"] {
    background-color:#E0F2FE !important;
    color:#0369A1 !important;
}

</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.markdown("""
<div class="hero">
    <h2 style="color:#0F8BC6;margin:0;">HelloWatt</h2>
    <span style="color:#64748B;">Dashboard de performance commerciale</span>
</div>
""", unsafe_allow_html=True)

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
page = st.sidebar.radio("Navigation", [
    "📊 Dashboard",
    "👤 Agents",
    "🎯 Objectifs"
])

# ---------------- UTILS ----------------
def clean_text(col):
    return (
        col.astype(str)
        .str.strip()
        .str.replace('"', '', regex=False)
        .str.replace("'", "", regex=False)
        .str.replace("\xa0", "", regex=False)
        .str.upper()
    )

def emoji(p):
    return "🟢" if p >= 1 else "🟠" if p >= 0.7 else "🔴"

def round_excel(x):
    return int(x + 0.5 + 1e-9)

def get_working_days():
    today = datetime.today()
    start = today.replace(day=1)
    fr_holidays = holidays.FR()

    days = pd.date_range(start, today)
    working_days = [
        d for d in days
        if d.weekday() < 5 and d.date() not in fr_holidays
    ]
    return len(working_days)

# ---------------- APP ----------------
if uploaded_file:

    xls = pd.ExcelFile(uploaded_file)

    df = pd.read_excel(xls, "Extraction")
    code = pd.read_excel(xls, "Code")
    objectifs = pd.read_excel(xls, "Objectifs")

    df["responder"] = clean_text(df["responder"])
    code.iloc[:, 0] = clean_text(code.iloc[:, 0])

    df = df.merge(
        code.rename(columns={code.columns[0]: "responder", code.columns[1]: "agent"}),
        on="responder",
        how="left"
    )

    df["agent"] = clean_text(df["agent"]).fillna("INCONNU")
    df["get_provider"] = clean_text(df["get_provider"])
    df["energie"] = clean_text(df["energie"])
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    objectifs["Fournisseur"] = clean_text(objectifs["Fournisseur"])

    # ---------------- FILTRES ----------------
    st.sidebar.markdown("### 🔎 Filtres")

    agents = st.sidebar.multiselect("Agents", df["agent"].unique(), default=df["agent"].unique())
    fournisseurs = st.sidebar.multiselect("Fournisseurs", df["get_provider"].unique(), default=df["get_provider"].unique())
    energie = st.sidebar.multiselect("Énergie", df["energie"].unique(), default=df["energie"].unique())

    min_date = df["date"].min()
    max_date = df["date"].max()
    date_range = st.sidebar.date_input("Période", [min_date, max_date])

    df_filtered = df[
        (df["agent"].isin(agents)) &
        (df["get_provider"].isin(fournisseurs)) &
        (df["energie"].isin(energie))
    ]

    if len(date_range) == 2:
        df_filtered = df_filtered[
            (df_filtered["date"] >= pd.to_datetime(date_range[0])) &
            (df_filtered["date"] <= pd.to_datetime(date_range[1]))
        ]

    objectif_total = objectifs["Objectifs Total"].sum()
    objectif_elec_total = objectifs["Objectif Elec"].sum()
    objectif_gaz_total = objectifs["Objectif Gaz"].sum()

    # ---------------- DASHBOARD ----------------
    if page == "📊 Dashboard":

        st.title("🏢 Objectifs Globaux")

        ventes_elec = len(df_filtered[df_filtered["energie"] == "ELEC"])
        ventes_gaz = len(df_filtered[df_filtered["energie"].isin(["GAZ","GAS"])])
        ventes_total = ventes_elec + ventes_gaz

        c1, c2, c3 = st.columns(3)

        c1.metric("⚡ Elec", f"{ventes_elec}/{objectif_elec_total}", f"{ventes_elec/objectif_elec_total:.0%}")
        c2.metric("🔥 Gaz", f"{ventes_gaz}/{objectif_gaz_total}", f"{ventes_gaz/objectif_gaz_total:.0%}")
        c3.metric("🏆 Total", f"{ventes_total}/{objectif_total}", f"{ventes_total/objectif_total:.0%}")

        ventes_fournisseur = df_filtered.groupby("get_provider").size().reset_index(name="ventes")

        df_obj = objectifs.merge(
            ventes_fournisseur,
            left_on="Fournisseur",
            right_on="get_provider",
            how="left"
        )

        df_obj["ventes"] = df_obj["ventes"].fillna(0)
        df_obj = df_obj.sort_values("Objectifs Total", ascending=False)

        for _, r in df_obj.iterrows():
            p = r["ventes"] / r["Objectifs Total"] if r["Objectifs Total"] else 0

            col1, col2, col3 = st.columns([3,6,2])
            col1.markdown(f"**{r['Fournisseur']}**")
            col2.progress(min(p,1.0))
            col3.markdown(f"{emoji(p)} {int(r['ventes'])}/{int(r['Objectifs Total'])} ({p:.0%})")

    # ---------------- AGENTS ----------------
    elif page == "👤 Agents":

        st.title("👤 Performance Agents")

        ventes_agent = df_filtered.groupby("agent").size().reset_index(name="ventes")
        objectif_agent = math.ceil(185 * 0.75)
        jours_travailles = get_working_days()

        ventes_agent["taux"] = ventes_agent["ventes"] / objectif_agent
        ventes_agent["kpi_jour"] = ventes_agent["ventes"] / jours_travailles if jours_travailles else 0

        ventes_agent = ventes_agent.sort_values("taux", ascending=False)

        for _, r in ventes_agent.iterrows():

            ventes_jour = round(r["kpi_jour"], 1)

            col1, col2, col3, col4 = st.columns([3,5,2,2])

            col1.markdown(f"**{r['agent']}**")
            col2.progress(min(r["taux"],1.0))
            col3.markdown(f"{emoji(r['taux'])} {r['ventes']}/{objectif_agent} ({r['taux']:.0%})")
            col4.markdown(f"📅 {ventes_jour}/J")

    # ---------------- OBJECTIFS ----------------
    elif page == "🎯 Objectifs":

        st.title("🎯 Performance détaillée")

        heures = st.number_input("Heures", value=185.0)
        agent = st.selectbox("Agent", df_filtered["agent"].unique())

        df_agent = df_filtered[df_filtered["agent"] == agent]

        objectif_agent = round_excel(heures * 0.75)
        ventes_total_agent = len(df_agent)
        taux_agent = ventes_total_agent / objectif_agent if objectif_agent else 0

        st.markdown('<div class="agent-card">', unsafe_allow_html=True)

        col1, col2, col3 = st.columns([3,6,2])
        col1.markdown(f"**{agent}**")
        col2.progress(min(taux_agent,1.0))
        col3.markdown(f"{emoji(taux_agent)} {ventes_total_agent}/{objectif_agent} ({taux_agent:.0%})")

        st.markdown('</div>', unsafe_allow_html=True)

        for fournisseur in objectifs["Fournisseur"].dropna().unique():

            df_f = df_agent[df_agent["get_provider"] == fournisseur]
            obj_row = objectifs[objectifs["Fournisseur"] == fournisseur]

            ventes = len(df_f)

            obj = round_excel(
                heures * 0.75 *
                (obj_row["Objectifs Total"].sum() / objectif_total)
            )

            p = ventes / obj if obj else 0

            col1, col2, col3 = st.columns([3,6,2])

            col1.markdown(f"**{fournisseur}**")
            col2.progress(min(p,1.0))
            col3.markdown(f"{emoji(p)} {ventes}/{obj} ({p:.0%})")

else:
    st.info("🔒 Ajoute un fichier (admin uniquement)")
