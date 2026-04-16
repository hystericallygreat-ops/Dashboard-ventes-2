import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard Ventes", layout="wide")

# ---------------- THEME MODERNE ----------------
st.markdown("""
<style>
body {
    background-color: #f5f7fb;
}

/* KPI CARDS */
.metric-card {
    background: white;
    padding: 18px;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    border-left: 5px solid #4f46e5;
}

.metric-title {
    font-size: 13px;
    color: #6b7280;
}

.metric-value {
    font-size: 26px;
    font-weight: bold;
    color: #111827;
}

.metric-sub {
    font-size: 14px;
    color: #10b981;
}

/* TITRES */
h1, h2, h3 {
    color: #111827;
}

/* SECTION */
.section {
    background: white;
    padding: 15px;
    border-radius: 12px;
    box-shadow: 0 3px 15px rgba(0,0,0,0.05);
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

st.title("📊 Dashboard des ventes")

uploaded_file = st.file_uploader("Uploader votre fichier Excel", type=["xlsx"])

if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)

    df = pd.read_excel(xls, "Extraction")
    code = pd.read_excel(xls, "Code")
    objectifs = pd.read_excel(xls, "Objectifs")

    df["responder"] = df["responder"].astype(str).str.strip().str.upper()
    code.iloc[:, 0] = code.iloc[:, 0].astype(str).str.strip().str.upper()

    df = df.merge(
        code.rename(columns={code.columns[0]: "responder", code.columns[1]: "agent"}),
        on="responder",
        how="left"
    )

    df["agent"] = df["agent"].fillna("Inconnu")

    # ---------------- KPI ----------------
    total_sales = len(df)
    objectif_total = objectifs["Objectifs Total"].sum()
    objectif_elec = objectifs["Objectif Elec"].sum()
    objectif_gaz = objectifs["Objectif Gaz"].sum()

    ventes_elec = len(df[df["energie"].str.lower() == "elec"])
    ventes_gaz = len(df[df["energie"].str.lower().isin(["gaz", "gas"])])

    taux_global = total_sales / objectif_total if objectif_total else 0
    taux_elec = ventes_elec / objectif_elec if objectif_elec else 0
    taux_gaz = ventes_gaz / objectif_gaz if objectif_gaz else 0

    col1, col2, col3 = st.columns(3)

    def kpi_card(col, title, value, taux):
        col.markdown(f"""
        <div class='metric-card'>
            <div class='metric-title'>{title}</div>
            <div class='metric-value'>{value}</div>
            <div class='metric-sub'>{taux:.1%}</div>
        </div>
        """, unsafe_allow_html=True)

    kpi_card(col1, "Ventes Totales", f"{total_sales}/{objectif_total}", taux_global)
    kpi_card(col2, "Électricité", f"{ventes_elec}/{objectif_elec}", taux_elec)
    kpi_card(col3, "Gaz", f"{ventes_gaz}/{objectif_gaz}", taux_gaz)

    st.markdown("## 📊 Analyse")

    colg1, colg2 = st.columns(2)

    # ---------------- GRAPHIQUES ----------------
    ventes_fournisseur = df.groupby("get_provider").size().reset_index(name="ventes")

    fig_fournisseur = px.bar(
        ventes_fournisseur,
        x="get_provider",
        y="ventes",
        color="ventes",
        color_continuous_scale="Blues"
    )

    fig_fournisseur.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        title="Ventes par fournisseur",
        xaxis_title="",
        yaxis_title="",
        title_x=0.1
    )

    colg1.plotly_chart(fig_fournisseur, use_container_width=True)

    ventes_agent = df.groupby("agent").size().reset_index(name="ventes")
    ventes_agent = ventes_agent.sort_values(by="ventes", ascending=False)

    fig_agents = px.bar(
        ventes_agent,
        x="ventes",
        y="agent",
        orientation="h",
        color="ventes",
        color_continuous_scale="Viridis"
    )

    fig_agents.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        title="Classement agents",
        yaxis=dict(autorange="reversed")
    )

    colg2.plotly_chart(fig_agents, use_container_width=True)

    # ---------------- PODIUM ----------------
    st.markdown("## 🏆 Top 3 Agents")
    top3 = ventes_agent.head(3)
    cols = st.columns(3)

    colors = ["#FFD700", "#C0C0C0", "#CD7F32"]

    for i, row in enumerate(top3.itertuples()):
        cols[i].markdown(f"""
        <div class='metric-card' style='border-left:5px solid {colors[i]}'>
            <div class='metric-value'>{row.agent}</div>
            <div>{row.ventes} ventes</div>
        </div>
        """, unsafe_allow_html=True)

    # ---------------- DETAIL ----------------
    st.markdown("## 🔍 Analyse par agent")

    heures = st.number_input("Heures planifiées", min_value=0.0, step=1.0)
    agent_select = st.selectbox("Agent", ventes_agent["agent"].unique())

    df_agent = df[df["agent"] == agent_select]

    ventes_par_fournisseur = df_agent.groupby("get_provider").size().reset_index(name="ventes")

    fig_detail = px.pie(
        ventes_par_fournisseur,
        names="get_provider",
        values="ventes",
        hole=0.5
    )

    st.plotly_chart(fig_detail, use_container_width=True)

else:
    st.info("Veuillez uploader un fichier Excel")
