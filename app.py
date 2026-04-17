import streamlit as st
import pandas as pd
import os
import math

st.set_page_config(page_title="HelloWatt Dashboard", layout="wide")

SAVE_PATH = "last_uploaded.xlsx"

# ---------------- STYLE ----------------
st.markdown("""
<style>
html, body {background-color: #F5FAFD;}

.header {font-size:28px;font-weight:700;color:#0F8BC6;}
.subheader {color:#64748B;font-size:14px;}

.card {
    background:white;
    padding:18px;
    border-radius:12px;
    border:1px solid #E2E8F0;
}

.stProgress > div > div > div > div {
    background-color:#0F8BC6;
}

section[data-testid="stSidebar"] {
    background-color:#EDF7FA;
}

section[data-testid="stSidebar"] * {
    color:#0F172A !important;
}

/* TAGS DOUX */
[data-baseweb="tag"] {
    background-color:#E0F2FE !important;
    color:#0369A1 !important;
    border-radius:8px;
}

/* BUTTON */
.stButton > button {
    background-color:#0F8BC6;
    color:white;
    border:none;
    border-radius:8px;
}
.stButton > button:hover {
    background-color:#0B6FA4;
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

    # -------- CLEAN --------
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

    # -------- FILTRES --------
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

    def emoji(p):
        return "🟢" if p >= 1 else "🟠" if p >= 0.7 else "🔴"

    # ---------------- DASHBOARD (OBJECTIFS GLOBAUX) ----------------
    if page == "📊 Dashboard":

        st.title("🏢 Objectifs Globaux")

        ventes_fournisseur = df_filtered.groupby("get_provider").size().reset_index(name="ventes")

        for _, r in ventes_fournisseur.iterrows():

            obj_row = objectifs[objectifs["Fournisseur"].str.upper() == r["get_provider"]]
            obj = obj_row["Objectifs Total"].sum()

            p = r["ventes"] / obj if obj else 0

            st.markdown(f"**{r['get_provider']}**")
            st.caption(f"{emoji(p)} {r['ventes']}/{int(obj)} ({p:.0%})")
            st.progress(min(p,1.0))

    # ---------------- AGENTS ----------------
    elif page == "👤 Agents":

        st.title("👤 Performance Agents")

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

    # ---------------- OBJECTIFS (DETAILLE) ----------------
    elif page == "🎯 Objectifs":

        st.title("🎯 Performance détaillée")

        heures = st.number_input("Heures", value=185.0)
        agent = st.selectbox("Agent", df_filtered["agent"].unique())

        df_agent = df_filtered[df_filtered["agent"] == agent]

        col1, col2, col3 = st.columns([2,4,4])
        col1.markdown("**Fournisseur**")
        col2.markdown("**⚡ Elec**")
        col3.markdown("**🔥 Gaz**")

        for fournisseur in objectifs["Fournisseur"].dropna().unique():

            df_f = df_agent[df_agent["get_provider"] == fournisseur]

            obj_row = objectifs[objectifs["Fournisseur"] == fournisseur]

            ventes_elec = len(df_f[df_f["energie"] == "ELEC"])
            ventes_gaz = len(df_f[df_f["energie"].isin(["GAZ","GAS"])])

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

else:
    st.info("🔒 Ajoute un fichier (admin uniquement)")
