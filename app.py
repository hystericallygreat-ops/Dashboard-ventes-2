import streamlit as st
import pandas as pd
import os
import math

st.set_page_config(page_title="HelloWatt Dashboard", layout="wide")

SAVE_PATH = "last_uploaded.xlsx"

# ---------------- STYLE GLOBAL ----------------
st.markdown("""
<style>
html, body {
    background-color: #F5FAFD;
}

/* Header */
.header {
    font-size: 28px;
    font-weight: 700;
    color: #0F8BC6;
}
.subheader {
    color: #64748B;
    font-size: 14px;
}

/* Cards */
.card {
    background: white;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #E2E8F0;
}

/* Progress */
.stProgress > div > div > div > div {
    background-color: #0F8BC6;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #EDF7FA;
}

/* Texte sidebar */
section[data-testid="stSidebar"] * {
    color: #0F172A !important;
}

/* -------- TAGS MULTISELECT (VERSION DOUCE) -------- */
[data-baseweb="tag"] {
    background-color: #E0F2FE !important;
    color: #0369A1 !important;
    border-radius: 8px;
    border: none;
    font-weight: 500;
}

/* Croix X */
[data-baseweb="tag"] span {
    color: #0369A1 !important;
}

/* Hover */
[data-baseweb="tag"]:hover {
    background-color: #BAE6FD !important;
}

/* Boutons */
.stButton > button {
    background-color: #0F8BC6;
    color: white;
    border-radius: 8px;
    border: none;
}
.stButton > button:hover {
    background-color: #0B6FA4;
}
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.markdown('<div class="header">HelloWatt</div>', unsafe_allow_html=True)
st.markdown('<div class="subheader">Dashboard de performance commerciale</div>', unsafe_allow_html=True)
st.markdown("---")

# ---------------- AUTH ----------------
password = st.sidebar.text_input("🔐 Admin", type="password")
is_admin = password == "hello123"

# ---------------- UPLOAD ----------------
uploaded_file = None

if is_admin:
    st.sidebar.success("Mode Admin")

    uploaded_file = st.sidebar.file_uploader("Uploader fichier Excel", type=["xlsx"])

    if uploaded_file is not None:
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
    "🏢 Objectifs"
])

# ---------------- APP ----------------
if uploaded_file:

    xls = pd.ExcelFile(uploaded_file)

    df = pd.read_excel(xls, "Extraction")
    code = pd.read_excel(xls, "Code")
    objectifs = pd.read_excel(xls, "Objectifs")

    # CLEAN
    df["responder"] = df["responder"].astype(str).str.upper().str.strip()
    code.iloc[:,0] = code.iloc[:,0].astype(str).str.upper().str.strip()

    df = df.merge(
        code.rename(columns={code.columns[0]: "responder", code.columns[1]: "agent"}),
        on="responder",
        how="left"
    )

    df["agent"] = df["agent"].fillna("Inconnu")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # ---------------- FILTRES ----------------
    st.sidebar.markdown("### 🔎 Filtres")

    agents = st.sidebar.multiselect(
        "Agents",
        df["agent"].unique(),
        default=df["agent"].unique()
    )

    fournisseurs = st.sidebar.multiselect(
        "Fournisseurs",
        df["get_provider"].unique(),
        default=df["get_provider"].unique()
    )

    energie = st.sidebar.multiselect(
        "Énergie",
        df["energie"].unique(),
        default=df["energie"].unique()
    )

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

    def emoji(p):
        return "🟢" if p >= 1 else "🟠" if p >= 0.7 else "🔴"

    # ---------------- DASHBOARD ----------------
    if page == "📊 Dashboard":

        total = len(df_filtered)
        taux = total / objectif_total if objectif_total else 0

        c1, c2 = st.columns(2)

        with c1:
            st.markdown(f"""
            <div class="card">
                <div>Ventes</div>
                <h2>{total}</h2>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown(f"""
            <div class="card">
                <div>Progression</div>
                <h2>{taux:.0%}</h2>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("## 🎯 Performance détaillée")

        heures = st.number_input("Heures", value=185.0)
        agent = st.selectbox("Agent", df_filtered["agent"].unique())

        df_agent = df_filtered[df_filtered["agent"] == agent]

        col1, col2, col3 = st.columns([2,4,4])
        col1.markdown("**Fournisseur**")
        col2.markdown("**⚡ Elec**")
        col3.markdown("**🔥 Gaz**")

        for fournisseur in objectifs["Fournisseur"].dropna().unique():

            df_f = df_agent[df_agent["get_provider"].str.lower() == fournisseur.lower()]
            obj_row = objectifs[objectifs["Fournisseur"].str.lower() == fournisseur.lower()]

            ventes_elec = len(df_f[df_f["energie"].str.lower() == "elec"])
            ventes_gaz = len(df_f[df_f["energie"].str.lower().isin(["gaz","gas"])])

            obj_elec = math.ceil(heures * 0.75 * (obj_row["Objectif Elec"].sum() / objectif_total))
            obj_gaz = math.ceil(heures * 0.75 * (obj_row["Objectif Gaz"].sum() / objectif_total))

            p_elec = ventes_elec / obj_elec if obj_elec else 0
            p_gaz = ventes_gaz / obj_gaz if obj_gaz else 0

            col1, col2, col3 = st.columns([2,4,4])

            col1.write(f"**{fournisseur}**")

            with col2:
                st.caption(f"{emoji(p_elec)} {ventes_elec}/{obj_elec} ({p_elec:.0%})")
                st.progress(min(p_elec,1.0))

            with col3:
                st.caption(f"{emoji(p_gaz)} {ventes_gaz}/{obj_gaz} ({p_gaz:.0%})")
                st.progress(min(p_gaz,1.0))

    # ---------------- AGENTS ----------------
    elif page == "👤 Agents":

        ventes_agent = df_filtered.groupby("agent").size().reset_index(name="ventes")

        objectif_agent = math.ceil(185 * 0.75)

        ventes_agent["taux"] = ventes_agent["ventes"] / objectif_agent
        ventes_agent = ventes_agent.sort_values("taux", ascending=False)

        for _, r in ventes_agent.iterrows():
            col1, col2 = st.columns([3,5])

            with col1:
                st.markdown(f"**{r['agent']}**")
                st.caption(f"{emoji(r['taux'])} {r['ventes']}/{objectif_agent}")

            with col2:
                st.progress(min(r["taux"],1.0))

    # ---------------- OBJECTIFS ----------------
    elif page == "🏢 Objectifs":

        ventes_fournisseur = df_filtered.groupby("get_provider").size().reset_index(name="ventes")

        for _, r in ventes_fournisseur.iterrows():

            obj_row = objectifs[objectifs["Fournisseur"].str.lower() == r["get_provider"].lower()]
            obj = obj_row["Objectifs Total"].sum()

            p = r["ventes"] / obj if obj else 0

            st.markdown(f"**{r['get_provider']}**")
            st.caption(f"{emoji(p)} {r['ventes']}/{int(obj)}")
            st.progress(min(p,1.0))

else:
    st.info("🔒 Ajoute un fichier (admin uniquement)")
