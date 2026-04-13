import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard Ventes", layout="wide")

# ---------------- STYLE (Power BI like) ----------------
st.markdown("""
<style>
body {background-color: #0E1117;}
.metric-card {
    background: linear-gradient(135deg, #1f2937, #111827);
    padding: 20px;
    border-radius: 14px;
    color: white;
    box-shadow: 0 4px 12px rgba(0,0,0,0.4);
}
.metric-title {font-size: 14px; opacity: 0.7;}
.metric-value {font-size: 28px; font-weight: bold;}
.section-title {
    font-size: 20px;
    font-weight: bold;
    margin-top: 20px;
}
</style>
""", unsafe_allow_html=True)

st.title("📊 Dashboard des ventes")

# ---------------- UPLOAD ----------------
uploaded_file = st.file_uploader("Uploader votre fichier Excel", type=["xlsx"])

if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)

    df = pd.read_excel(xls, "Extraction")
    code = pd.read_excel(xls, "Code")
    objectifs = pd.read_excel(xls, "Objectifs")

    # Mapping agents
    code_dict = dict(zip(code.iloc[:, 0], code.iloc[:, 1]))
    df["agent"] = df["responder"].map(code_dict)

    # Nettoyage
    df["energie"] = df["energie"].str.lower()

    # ---------------- KPI ----------------
    total_sales = len(df)
    objectif_total = objectifs["Objectifs Total"].sum()
    taux_global = total_sales / objectif_total if objectif_total else 0

    col1, col2, col3 = st.columns(3)

    col1.markdown(f"""
    <div class='metric-card'>
        <div class='metric-title'>Ventes totales</div>
        <div class='metric-value'>{total_sales}</div>
    </div>
    """, unsafe_allow_html=True)

    col2.markdown(f"""
    <div class='metric-card'>
        <div class='metric-title'>Objectif global</div>
        <div class='metric-value'>{objectif_total}</div>
    </div>
    """, unsafe_allow_html=True)

    col3.markdown(f"""
    <div class='metric-card'>
        <div class='metric-title'>Taux d’atteinte</div>
        <div class='metric-value'>{taux_global:.1%}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ---------------- FILTRES ----------------
    st.markdown("### 🎯 Filtres")

    colf1, colf2 = st.columns(2)

    fournisseurs = df["get_provider"].dropna().unique()
    agents = df["agent"].dropna().unique()

    selected_fournisseur = colf1.multiselect("Fournisseur", fournisseurs)
    selected_agent = colf2.multiselect("Agent", agents)

    df_filtered = df.copy()

    if selected_fournisseur:
        df_filtered = df_filtered[df_filtered["get_provider"].isin(selected_fournisseur)]

    if selected_agent:
        df_filtered = df_filtered[df_filtered["agent"].isin(selected_agent)]

    st.markdown("---")

    # ---------------- GRAPHIQUES ----------------
    colg1, colg2 = st.columns(2)

    ventes_fournisseur = df_filtered.groupby("get_provider").size().reset_index(name="ventes")
    fig_fournisseur = px.bar(
        ventes_fournisseur,
        x="get_provider",
        y="ventes",
        title="Ventes par fournisseur",
        template="plotly_dark"
    )

    colg1.plotly_chart(fig_fournisseur, use_container_width=True)

    ventes_agent = df_filtered.groupby("agent").size().reset_index(name="ventes")
    ventes_agent = ventes_agent.sort_values(by="ventes", ascending=False)

    fig_agent = px.bar(
        ventes_agent,
        x="agent",
        y="ventes",
        title="Classement des agents",
        template="plotly_dark"
    )

    colg2.plotly_chart(fig_agent, use_container_width=True)

    # ---------------- PODIUM ----------------
    st.markdown("### 🏆 Top 3 agents")

    top3 = ventes_agent.head(3)
    cols = st.columns(3)

    medals = ["🥇", "🥈", "🥉"]

    for i, row in enumerate(top3.itertuples()):
        cols[i].markdown(f"""
        <div class='metric-card'>
            <div style='font-size:30px'>{medals[i]}</div>
            <div class='metric-value'>{row.agent}</div>
            <div class='metric-title'>{row.ventes} ventes</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ---------------- TABLE DETAIL ----------------
    st.markdown("### 📋 Détail des performances")

    df_detail = ventes_agent.copy()
    df_detail["taux"] = df_detail["ventes"] / objectif_total

    st.dataframe(df_detail, use_container_width=True)

else:
    st.info("Veuillez uploader un fichier Excel pour commencer.")
