import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Dashboard SaaS Ventes", layout="wide")

# ---------------- CONFIG FICHIER ----------------
SAVE_PATH = "last_uploaded.xlsx"

uploaded_file = st.file_uploader("Uploader votre fichier Excel", type=["xlsx"])

if uploaded_file is not None:
    with open(SAVE_PATH, "wb") as f:
        f.write(uploaded_file.getbuffer())

if uploaded_file is None and os.path.exists(SAVE_PATH):
    uploaded_file = SAVE_PATH

if os.path.exists(SAVE_PATH):
    if st.sidebar.button("🗑 Supprimer le fichier chargé"):
        os.remove(SAVE_PATH)
        st.rerun()

# ---------------- STYLE ----------------
st.markdown("""
<style>
body {background-color: #F7F9FB;}

h1, h2, h3 {color:#0F172A;}

.card {
    background: white;
    padding: 20px;
    border-radius: 16px;
    box-shadow: 0 6px 20px rgba(0,0,0,0.05);
}

.kpi-title {font-size:13px;color:#64748B;}
.kpi-value {font-size:30px;font-weight:bold;}
.kpi-sub {font-size:14px;color:#22C55E;}

.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #3B82F6, #06B6D4);
}
</style>
""", unsafe_allow_html=True)

st.title("📊 Dashboard Ventes")

# ---------------- SI FICHIER ----------------
if uploaded_file:

    xls = pd.ExcelFile(uploaded_file)

    df = pd.read_excel(xls, "Extraction")
    code = pd.read_excel(xls, "Code")
    objectifs = pd.read_excel(xls, "Objectifs")

    # CLEAN
    df["responder"] = df["responder"].astype(str).str.strip().str.upper()
    code.iloc[:, 0] = code.iloc[:, 0].astype(str).str.strip().str.upper()

    df = df.merge(
        code.rename(columns={code.columns[0]: "responder", code.columns[1]: "agent"}),
        on="responder",
        how="left"
    )

    df["agent"] = df["agent"].fillna("Inconnu")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # ---------------- FILTRES ----------------
    st.sidebar.header("🔎 Filtres")

    agents = st.sidebar.multiselect("Agent", df["agent"].unique(), default=df["agent"].unique())
    fournisseurs = st.sidebar.multiselect("Fournisseur", df["get_provider"].unique(), default=df["get_provider"].unique())

    df_filtered = df[
        (df["agent"].isin(agents)) &
        (df["get_provider"].isin(fournisseurs))
    ]

    # ---------------- KPI ----------------
    total_sales = len(df_filtered)
    objectif_total = objectifs["Objectifs Total"].sum()
    taux_global = total_sales / objectif_total if objectif_total else 0

    col1, col2, col3 = st.columns(3)

    def kpi(col, title, value, taux):
        col.markdown(f"""
        <div class="card">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-sub">{taux:.0%}</div>
        </div>
        """, unsafe_allow_html=True)

    kpi(col1, "Ventes", total_sales, taux_global)
    kpi(col2, "Objectif", int(objectif_total), 1)
    kpi(col3, "Progression", "", taux_global)

    st.markdown("---")

    # ---------------- EMOJI ----------------
    def emoji(p):
        return "🟢" if p >= 1 else "🟠" if p >= 0.7 else "🔴"

    # ---------------- FOURNISSEURS ----------------
    st.subheader("🏢 Performance Fournisseurs")

    objectif_global_185h = 185 * 0.75

    ventes_fournisseur = (
        df_filtered.groupby("get_provider")
        .size()
        .reset_index(name="ventes")
    )

    rows = []

    for _, row in ventes_fournisseur.iterrows():
        fournisseur = row["get_provider"]
        ventes = row["ventes"]

        obj_row = objectifs[objectifs["Fournisseur"].str.lower() == fournisseur.lower()]

        objectif_fournisseur = 0
        if not obj_row.empty and objectif_total:
            part = obj_row["Objectifs Total"].sum() / objectif_total
            objectif_fournisseur = objectif_global_185h * part

        taux = ventes / objectif_fournisseur if objectif_fournisseur else 0

        rows.append((fournisseur, ventes, objectif_fournisseur, taux))

    rows = sorted(rows, key=lambda x: x[3], reverse=True)

    for f, v, obj, t in rows:

        col1, col2 = st.columns([6, 1])

        with col1:
            st.markdown(f"""
            <div style="display:flex; align-items:center;">
                <div style="flex-grow:1;">
                    <b>{f}</b><br>
                    <span style="font-size:12px;color:gray;">
                    {v} / {int(obj)} ({t:.0%})
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.progress(min(t, 1.0))

        with col2:
            st.write(emoji(t))

    st.markdown("---")

    # ---------------- AGENTS COMPACT ----------------
    st.subheader("👤 Performance Agents")

    ventes_agent = (
        df_filtered.groupby("agent")
        .size()
        .reset_index(name="ventes")
    )

    objectif_agent = 185 * 0.75

    rows = []

    for _, row in ventes_agent.iterrows():
        agent = row["agent"]
        ventes = row["ventes"]
        taux = ventes / objectif_agent if objectif_agent else 0
        rows.append((agent, ventes, objectif_agent, taux))

    rows = sorted(rows, key=lambda x: x[3], reverse=True)

    for a, v, obj, t in rows:

        st.markdown(f"""
        <div style="
            display:flex;
            align-items:center;
            margin-bottom:6px;
            gap:10px;
        ">
            <div style="width:140px;">
                <b>{a}</b>
            </div>

            <div style="flex-grow:1;">
        """, unsafe_allow_html=True)

        st.progress(min(t, 1.0))

        st.markdown(f"""
            </div>

            <div style="width:140px; text-align:right; font-size:12px;">
                {emoji(t)} {v}/{int(obj)} ({t:.0%})
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ---------------- DETAIL ----------------
    st.subheader("🎯 Détail Agent")

    heures = st.number_input("Heures travaillées", value=185.0)
    agent_select = st.selectbox("Agent", df_filtered["agent"].unique())

    df_agent = df_filtered[df_filtered["agent"] == agent_select]

    for fournisseur in objectifs["Fournisseur"].dropna().unique():

        df_f = df_agent[df_agent["get_provider"].str.lower() == fournisseur.lower()]
        ventes = len(df_f)

        obj_row = objectifs[objectifs["Fournisseur"].str.lower() == fournisseur.lower()]

        objectif = 0
        if not obj_row.empty and objectif_total:
            part = obj_row["Objectifs Total"].sum() / objectif_total
            objectif = heures * 0.75 * part

        taux = ventes / objectif if objectif else 0

        st.markdown(f"**{fournisseur}**")
        st.caption(f"{emoji(taux)} {ventes} / {int(objectif)} ({taux:.0%})")
        st.progress(min(taux, 1.0))

else:
    st.info("Veuillez uploader un fichier Excel")
