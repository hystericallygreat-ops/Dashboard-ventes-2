import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard Ventes", layout="wide")

# ---------------- STYLE ----------------
st.markdown("""
<style>
.metric-card {
    background: linear-gradient(135deg, #1f2937, #111827);
    padding: 20px;
    border-radius: 14px;
    color: white;
    text-align: center;
}
.metric-title {font-size: 14px; opacity: 0.7;}
.metric-value {font-size: 22px; font-weight: bold;}
.metric-sub {font-size: 14px; opacity: 0.8;}
</style>
""", unsafe_allow_html=True)

st.title("📊 Dashboard des ventes")

uploaded_file = st.file_uploader("Uploader votre fichier Excel", type=["xlsx"])

if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)

    df = pd.read_excel(xls, "Extraction")
    code = pd.read_excel(xls, "Code")
    objectifs = pd.read_excel(xls, "Objectifs")

    # Nettoyage des colonnes pour éviter les erreurs de mapping
    df["responder"] = df["responder"].astype(str).str.strip().str.upper()
    code.iloc[:, 0] = code.iloc[:, 0].astype(str).str.strip().str.upper()

    # Merge robuste pour mapping agents
    df = df.merge(
        code.rename(columns={code.columns[0]: "responder", code.columns[1]: "agent"}),
        on="responder",
        how="left"
    )

    # Remplacer les NaN par "Inconnu"
    df["agent"] = df["agent"].fillna("Inconnu")

    # ---------------- KPI GLOBAL ----------------
    total_sales = len(df)
    objectif_total = objectifs["Objectifs Total"].sum()
    objectif_elec = objectifs["Objectif Elec"].sum()
    objectif_gaz = objectifs["Objectif Gaz"].sum()

    ventes_elec = len(df[df["energie"].str.lower() == "elec"])
    # accepter "gaz" ou "gas"
    ventes_gaz = len(df[df["energie"].str.lower().isin(["gaz", "gas"])])

    taux_global = total_sales / objectif_total if objectif_total else 0
    taux_elec = ventes_elec / objectif_elec if objectif_elec else 0
    taux_gaz = ventes_gaz / objectif_gaz if objectif_gaz else 0

    col1, col2, col3 = st.columns(3)

    col1.markdown(f"""
    <div class='metric-card'>
      <div class='metric-title'>Ventes Totales</div>
      <div class='metric-value'>{total_sales}/{objectif_total}</div>
      <div class='metric-sub'>{taux_global:.1%}</div>
    </div>
    """, unsafe_allow_html=True)

    col2.markdown(f"""
    <div class='metric-card'>
      <div class='metric-title'>Élec</div>
      <div class='metric-value'>{ventes_elec}/{objectif_elec}</div>
      <div class='metric-sub'>{taux_elec:.1%}</div>
    </div>
    """, unsafe_allow_html=True)

    col3.markdown(f"""
    <div class='metric-card'>
      <div class='metric-title'>Gaz</div>
      <div class='metric-value'>{ventes_gaz}/{objectif_gaz}</div>
      <div class='metric-sub'>{taux_gaz:.1%}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ---------------- GRAPHIQUES ----------------
    colg1, colg2 = st.columns(2)

    with colg1:
        st.subheader("📦 Ventes par fournisseur")
        ventes_fournisseur = df.groupby("get_provider").size().reset_index(name="ventes")
        fig_fournisseur = px.bar(ventes_fournisseur, x="get_provider", y="ventes", title="Ventes par fournisseur", template="plotly_dark")
        st.plotly_chart(fig_fournisseur, use_container_width=True)

    with colg2:
        st.subheader("👥 Classement agents")
        ventes_agent = df.groupby("agent").size().reset_index(name="ventes")
        ventes_agent = ventes_agent.sort_values(by="ventes", ascending=False)
        fig_agents = px.bar(ventes_agent, x="agent", y="ventes", title="Classement agents", template="plotly_dark")
        st.plotly_chart(fig_agents, use_container_width=True)

    st.markdown("---")

    # ---------------- PODIUM ----------------
    st.subheader("🏆 Top 3")
    top3 = ventes_agent.head(3)
    cols = st.columns(3)
    for i, row in enumerate(top3.itertuples()):
        cols[i].markdown(f"""<div class='metric-card'><div class='metric-value'>{row.agent}</div><div>{row.ventes} ventes</div></div>""", unsafe_allow_html=True)

    st.markdown("---")
      # ---------------- VUE DÉTAILLÉE PAR AGENT ----------------
    st.subheader("🔍 Vue détaillée par agent")
    heures = st.number_input("Heures planifiées du mois", min_value=0.0, step=1.0)
    agent_select = st.selectbox("Choisir un agent", ventes_agent["agent"].dropna().unique())
    df_agent = df[df["agent"] == agent_select]

    recap_rows = []
    for fournisseur in objectifs["Fournisseur"].dropna().unique():
        # Ventes de l’agent pour ce fournisseur
        df_f = df_agent[df_agent["get_provider"].str.lower() == fournisseur.lower()]
        ventes_elec = len(df_f[df_f["energie"].str.lower() == "elec"])
        ventes_gaz = len(df_f[df_f["energie"].str.lower().isin(["gaz", "gas"])])
        ventes_free = len(df_f[df_f["get_provider"].str.lower() == "free"])
        ventes_hs = len(df_f[df_f["get_provider"].str.lower() == "homeserve"])

        # Objectifs individuels par fournisseur
        obj_row = objectifs[objectifs["Fournisseur"].str.lower() == fournisseur.lower()]
        obj_total_f = obj_row["Objectifs Total"].sum() if not obj_row.empty else 0
        obj_elec_f = heures * 0.75 * (obj_row["Objectif Elec"].sum() / objectif_total) if objectif_total else 0
        obj_gaz_f = heures * 0.75 * (obj_row["Objectif Gaz"].sum() / objectif_total) if objectif_total else 0
        obj_free_f = heures * 0.75 * (obj_row["Objectif Free"].sum() / objectif_total) if "Objectif Free" in obj_row and objectif_total else 0
        obj_hs_f = heures * 0.75 * (obj_row["Objectif HomeServe"].sum() / objectif_total) if "Objectif HomeServe" in obj_row and objectif_total else 0

        recap_rows.append({
            "Fournisseur": fournisseur,
            "Elec": f"{ventes_elec}/{int(obj_elec_f)}",
            "Gaz": f"{ventes_gaz}/{int(obj_gaz_f)}",
            "Free": f"{ventes_free}/{int(obj_free_f)}",
            "HomeServe": f"{ventes_hs}/{int(obj_hs_f)}"
        })

    recap_df = pd.DataFrame(recap_rows)

    # Ligne TOTAL avec % de réalisation
    def parse_ratio(series):
        ventes = sum(int(x.split('/')[0]) for x in series if '/' in x)
        obj = sum(int(x.split('/')[1]) for x in series if '/' in x)
        return ventes, obj

    tot_elec, obj_elec_tot = parse_ratio(recap_df["Elec"])
    tot_gaz, obj_gaz_tot = parse_ratio(recap_df["Gaz"])
    tot_free, obj_free_tot = parse_ratio(recap_df["Free"])
    tot_hs, obj_hs_tot = parse_ratio(recap_df["HomeServe"])

    recap_df.loc["TOTAL"] = {
        "Fournisseur": "TOTAL",
        "Elec": f"{tot_elec}/{obj_elec_tot} ({tot_elec/obj_elec_tot:.1%})" if obj_elec_tot else "0/0",
        "Gaz": f"{tot_gaz}/{obj_gaz_tot} ({tot_gaz/obj_gaz_tot:.1%})" if obj_gaz_tot else "0/0",
        "Free": f"{tot_free}/{obj_free_tot} ({tot_free/obj_free_tot:.1%})" if obj_free_tot else "0/0",
        "HomeServe": f"{tot_hs}/{obj_hs_tot} ({tot_hs/obj_hs_tot:.1%})" if obj_hs_tot else "0/0"
    }

    st.write(f"Objectifs individuels pour {agent_select} (heures planifiées: {heures})")
    st.dataframe(recap_df, use_container_width=True)

else:
    st.info("Veuillez uploader un fichier Excel")
