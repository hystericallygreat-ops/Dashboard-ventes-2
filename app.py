import streamlit as st
import pandas as pd
import os
import math

st.set_page_config(page_title="HelloWatt Dashboard", layout="wide")

SAVE_PATH = "last_uploaded.xlsx"

# ---------------- STYLE PREMIUM ----------------
st.markdown("""
<style>

/* GLOBAL */
.block-container {
    max-width: 1100px;
    padding-top: 1rem;
}

/* HEADER */
.header {
    font-size:32px;
    font-weight:700;
    color:#0F8BC6;
    margin-bottom:0;
}
.subheader {
    color:#64748B;
    font-size:14px;
    margin-top:-5px;
}

/* KPI CARDS */
.card {
    background: white;
    padding:16px;
    border-radius:12px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.04);
    text-align:center;
}
.card-title {
    font-size:13px;
    color:#64748B;
}
.card-value {
    font-size:22px;
    font-weight:700;
}
.card-sub {
    font-size:13px;
    color:#0F8BC6;
}

/* SIDEBAR */
section[data-testid="stSidebar"] {
    background-color:#EDF7FA;
}
section[data-testid="stSidebar"] * {
    color:#0F172A !important;
}

/* TAGS */
[data-baseweb="tag"] {
    background-color:#E0F2FE !important;
    color:#0369A1 !important;
}

/* BUTTON */
.stButton > button {
    background-color:#0F8BC6 !important;
    color:white !important;
    border-radius:8px;
}

/* PROGRESS */
.stProgress > div > div > div > div {
    background-color:#0F8BC6;
}

/* LIGNES COMPACTES */
.row {
    padding:6px 0;
    border-bottom:1px solid #E2E8F0;
}

</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.markdown('<div class="header">HelloWatt</div>', unsafe_allow_html=True)
st.markdown('<div class="subheader">Dashboard de performance commerciale</div>', unsafe_allow_html=True)

st.markdown("")

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

# ---------------- APP ----------------
if uploaded_file:

    xls = pd.ExcelFile(uploaded_file)

    df = pd.read_excel(xls, "Extraction")
    code = pd.read_excel(xls, "Code")
    objectifs = pd.read_excel(xls, "Objectifs")

    def clean_text(col):
        return (
            col.astype(str)
            .str.strip()
            .str.replace('"', '', regex=False)
            .str.replace("'", "", regex=False)
            .str.replace("\xa0", "", regex=False)
            .str.upper()
        )

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

    # -------- FILTRES --------
    st.sidebar.markdown("### 🔎 Filtres")

    agents = st.sidebar.multiselect("Agents", df["agent"].unique(), default=df["agent"].unique())
    fournisseurs = st.sidebar.multiselect("Fournisseurs", df["get_provider"].unique(), default=df["get_provider"].unique())
    energie = st.sidebar.multiselect("Énergie", df["energie"].unique(), default=df["energie"].unique())

    df_filtered = df[
        (df["agent"].isin(agents)) &
        (df["get_provider"].isin(fournisseurs)) &
        (df["energie"].isin(energie))
    ]

    objectif_total = objectifs["Objectifs Total"].sum()
    objectif_elec_total = objectifs["Objectif Elec"].sum()
    objectif_gaz_total = objectifs["Objectif Gaz"].sum()

    def emoji(p):
        return "🟢" if p >= 1 else "🟠" if p >= 0.7 else "🔴"

    def round_excel(x):
        return int(x + 0.5 + 1e-9)

    # ---------------- DASHBOARD ----------------
    if page == "📊 Dashboard":

        st.title("🏢 Objectifs Globaux")

        ventes_elec = len(df_filtered[df_filtered["energie"] == "ELEC"])
        ventes_gaz = len(df_filtered[df_filtered["energie"].isin(["GAZ","GAS"])])
        ventes_total = ventes_elec + ventes_gaz

        # KPI CARDS
        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown(f"""
            <div class="card">
                <div class="card-title">⚡ Elec</div>
                <div class="card-value">{ventes_elec}/{objectif_elec_total}</div>
                <div class="card-sub">{ventes_elec/objectif_elec_total:.0%}</div>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown(f"""
            <div class="card">
                <div class="card-title">🔥 Gaz</div>
                <div class="card-value">{ventes_gaz}/{objectif_gaz_total}</div>
                <div class="card-sub">{ventes_gaz/objectif_gaz_total:.0%}</div>
            </div>
            """, unsafe_allow_html=True)

        with c3:
            st.markdown(f"""
            <div class="card">
                <div class="card-title">🏆 Total</div>
                <div class="card-value">{ventes_total}/{objectif_total}</div>
                <div class="card-sub">{ventes_total/objectif_total:.0%}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("")

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

        ventes_agent["taux"] = ventes_agent["ventes"] / objectif_agent
        ventes_agent = ventes_agent.sort_values("taux", ascending=False)

        for _, r in ventes_agent.iterrows():

            col1, col2, col3 = st.columns([3,6,2])

            col1.markdown(f"**{r['agent']}**")
            col2.progress(min(r["taux"],1.0))
            col3.markdown(f"{emoji(r['taux'])} {r['ventes']}/{objectif_agent} ({r['taux']:.0%})")

    # ---------------- OBJECTIFS ----------------
    elif page == "🎯 Objectifs":

        st.title("🎯 Performance détaillée")

        heures = st.number_input("Heures", value=185.0)
        agent = st.selectbox("Agent", df_filtered["agent"].unique())

        df_agent = df_filtered[df_filtered["agent"] == agent]

        objectif_agent = round_excel(heures * 0.75)
        ventes_total_agent = len(df_agent)
        taux_agent = ventes_total_agent / objectif_agent if objectif_agent else 0

        col1, col2, col3 = st.columns([3,6,2])

        col1.markdown(f"**{agent}**")
        col2.progress(min(taux_agent,1.0))
        col3.markdown(f"{emoji(taux_agent)} {ventes_total_agent}/{objectif_agent} ({taux_agent:.0%})")

        st.markdown("")

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
