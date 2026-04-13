import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard Ventes", layout="wide")

# ---------------- STYLE ----------------
st.markdown("""
<style>
.metric-card {
    background: linear-gradient(135deg, #1e3a8a, #3b82f6);
    padding: 20px;
    border-radius: 14px;
    color: white;
    text-align: center;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}
.metric-title {font-size: 14px; opacity: 0.9;}
.metric-value {font-size: 26px; font-weight: bold;}
.metric-sub {font-size: 14px; opacity: 0.8;}
</style>
""", unsafe_allow_html=True)

st.title("⚡ Dashboard des ventes")

# ---------------- UPLOAD ----------------
uploaded_file = st.file_uploader("Uploader votre fichier Excel", type=["xlsx"])

if uploaded_file is not None:

    # ---------------- LECTURE ----------------
    xls = pd.ExcelFile(uploaded_file)
    df = pd.read_excel(xls, "Extraction")
    code = pd.read_excel(xls, "Code")
    objectifs = pd.read_excel(xls, "Objectifs")

    # ---------------- NETTOYAGE ----------------
    df["responder"] = df["responder"].astype(str).str.strip().str.upper()
    code.iloc[:, 0] = code.iloc[:, 0].astype(str).str.strip().str.upper()
    df["energie"] = df["energie"].fillna("AUTRE").astype(str).str.lower()
    df["get_provider"] = df["get_provider"].astype(str).str.strip().str.lower()

    # Mapping agent
    df = df.merge(
        code.rename(columns={code.columns[0]: "responder", code.columns[1]: "agent"}),
        on="responder",
        how="left"
    )
    df["agent"] = df["agent"].fillna("Inconnu")

    # Date
    df["get_date_lead_date"] = pd.to_datetime(df["get_date_lead_date"], errors="coerce")

    # ---------------- FILTRE DATE ----------------
    st.sidebar.header("Filtres")
    date_range = st.sidebar.date_input("Filtrer par date", [])
    if len(date_range) == 2:
        df = df[
            (df["get_date_lead_date"] >= pd.to_datetime(date_range[0])) &
            (df["get_date_lead_date"] <= pd.to_datetime(date_range[1]))
        ]

    # ---------------- KPI ----------------
    total_sales = len(df)
    objectif_total = objectifs["Objectifs Total"].sum()
    objectif_elec = objectifs["Objectif Elec"].sum()
    objectif_gaz = objectifs["Objectif Gaz"].sum()

    ventes_elec = len(df[df["energie"] == "elec"])
    ventes_gaz = len(df[df["energie"].isin(["gaz", "gas"])])

    taux_global = total_sales / objectif_total if objectif_total else 0
    taux_elec = ventes_elec / objectif_elec if objectif_elec else 0
    taux_gaz = ventes_gaz / objectif_gaz if objectif_gaz else 0

    col1, col2, col3 = st.columns(3)
    col1.markdown(f"<div class='metric-card'><div class='metric-title'>Ventes Totales</div><div class='metric-value'>{total_sales}/{objectif_total}</div><div class='metric-sub'>{taux_global:.1%}</div></div>", unsafe_allow_html=True)
    col2.markdown(f"<div class='metric-card'><div class='metric-title'>Élec ⚡</div><div class='metric-value'>{ventes_elec}/{objectif_elec}</div><div class='metric-sub'>{taux_elec:.1%}</div></div>", unsafe_allow_html=True)
    col3.markdown(f"<div class='metric-card'><div class='metric-title'>Gaz 🔥</div><div class='metric-value'>{ventes_gaz}/{objectif_gaz}</div><div class='metric-sub'>{taux_gaz:.1%}</div></div>", unsafe_allow_html=True)

    st.markdown("---")

    # ---------------- GRAPHIQUES ----------------
    colg1, colg2 = st.columns(2)
    with colg1:
        st.subheader("📦 Ventes par fournisseur")
        ventes_fournisseur = df.groupby("get_provider").size().reset_index(name="ventes").sort_values(by="ventes", ascending=False)
        fig_fournisseur = px.bar(ventes_fournisseur, x="get_provider", y="ventes", color="ventes", color_continuous_scale="Blues")
        st.plotly_chart(fig_fournisseur, use_container_width=True)

    with colg2:
        st.subheader("👥 Classement agents")
        ventes_agent = df.groupby("agent").size().reset_index(name="ventes").sort_values(by="ventes", ascending=False)
        fig_agents = px.bar(ventes_agent, x="agent", y="ventes", color="ventes", color_continuous_scale="Blues")
        st.plotly_chart(fig_agents, use_container_width=True)

    st.markdown("---")

    # ---------------- TOP 3 ----------------
    st.subheader("🏆 Top 3 agents")
    top3 = ventes_agent.head(3)
    cols = st.columns(3)
    for i, row in enumerate(top3.itertuples()):
        cols[i].markdown(f"<div class='metric-card'><div class='metric-value'>{row.agent}</div><div>{row.ventes} ventes</div></div>", unsafe_allow_html=True)

    st.markdown("---")

    # ---------------- VUE AGENT ----------------
    st.subheader("🔍 Vue détaillée par agent")
    heures = st.number_input("Heures planifiées du mois", min_value=0.0, step=1.0)
    agent_select = st.selectbox("Choisir un agent", ventes_agent["agent"].dropna().unique())
    df_agent = df[df["agent"] == agent_select]

    recap_fournisseurs = []
    for fournisseur in objectifs["Fournisseur"].str.strip().str.lower().unique():
        df_f = df_agent[df_agent["get_provider"] == fournisseur]
        ventes_elec_f = len(df_f[df_f["energie"] == "elec"])
        ventes_gaz_f = len(df_f[df_f["energie"].isin(["gaz", "gas"])])
        ventes_free = len(df_f[df_f["get_provider"].str.contains("free", case=False)])
        ventes_hs = len(df_f[df_f["get_provider"].str.contains("homeserve", case=False)])
        obj_row = objectifs[objectifs["Fournisseur"].str.strip().str.lower() == fournisseur]
        obj_total_f = obj_row["Objectifs Total"].sum() if not obj_row.empty else 0
        obj_indiv = heures * 0.75 * (obj_total_f / objectif_total) if objectif_total else 0

        recap_fournisseurs.append({
            "Fournisseur": fournisseur,
            "Élec ⚡": ventes_elec_f,
            "Gaz 🔥": ventes_gaz_f,
            "Free 📱": ventes_free,
            "HomeServe 🏠": ventes_hs,
            "Total 🎯": ventes_elec_f + ventes_gaz_f + ventes_free + ventes_hs,
            "Objectif Individuel": int(obj_indiv)
        })

    recap_df = pd.DataFrame(recap_fournisseurs)
    recap_df.loc["TOTAL"] = recap_df.drop(columns="Fournisseur").sum(numeric_only=True)
    recap_df.loc["TOTAL", "Fournisseur"] = "TOTAL"
    st.dataframe(recap_df, use_container_width=True)

else:
    st.info("Veuillez uploader un fichier Excel pour afficher le dashboard.")

