import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard SaaS Ventes", layout="wide")

# ---------------- STYLE PREMIUM ----------------
st.markdown("""
<style>
body {background-color: #f5f7fb;}

.metric-card {
    background: white;
    padding: 20px;
    border-radius: 14px;
    box-shadow: 0 6px 25px rgba(0,0,0,0.08);
}

.metric-title {font-size: 13px; color: #6b7280;}
.metric-value {font-size: 28px; font-weight: bold;}
.metric-sub {font-size: 14px;}

.fournisseur-card {
    background: white;
    padding: 12px 15px;
    border-radius: 12px;
    margin-bottom: 12px;
    box-shadow: 0 3px 10px rgba(0,0,0,0.05);
}

.progress-label {
    font-size: 13px;
    display: flex;
    justify-content: space-between;
    margin-bottom: 3px;
}

.progress-bar-bg {
    background-color: #e5e7eb;
    border-radius: 8px;
    height: 10px;
    width: 100%;
}

.progress-bar-fill {
    height: 10px;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

st.title("📊 Dashboard SaaS - Ventes")

uploaded_file = st.file_uploader("Uploader votre fichier Excel", type=["xlsx"])

if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)

    df = pd.read_excel(xls, "Extraction")
    code = pd.read_excel(xls, "Code")
    objectifs = pd.read_excel(xls, "Objectifs")

    # ---------------- CLEAN ----------------
    df["responder"] = df["responder"].astype(str).str.strip().str.upper()
    code.iloc[:, 0] = code.iloc[:, 0].astype(str).str.strip().str.upper()

    df = df.merge(
        code.rename(columns={code.columns[0]: "responder", code.columns[1]: "agent"}),
        on="responder",
        how="left"
    )

    df["agent"] = df["agent"].fillna("Inconnu")

    # ---------------- SIDEBAR ----------------
    st.sidebar.header("🔎 Filtres")

    agents = st.sidebar.multiselect("Agent", df["agent"].unique(), default=df["agent"].unique())
    fournisseurs = st.sidebar.multiselect("Fournisseur", df["get_provider"].unique(), default=df["get_provider"].unique())
    energie = st.sidebar.multiselect("Énergie", df["energie"].unique(), default=df["energie"].unique())

    df_filtered = df[
        (df["agent"].isin(agents)) &
        (df["get_provider"].isin(fournisseurs)) &
        (df["energie"].isin(energie))
    ]

    # ---------------- KPI ----------------
    total_sales = len(df_filtered)
    objectif_total = objectifs["Objectifs Total"].sum()

    ventes_elec = len(df_filtered[df_filtered["energie"].str.lower() == "elec"])
    ventes_gaz = len(df_filtered[df_filtered["energie"].str.lower().isin(["gaz", "gas"])])

    taux_global = total_sales / objectif_total if objectif_total else 0

    col1, col2, col3 = st.columns(3)

    def kpi(col, title, value, taux):
        col.markdown(f"""
        <div class='metric-card'>
            <div class='metric-title'>{title}</div>
            <div class='metric-value'>{value}</div>
            <div class='metric-sub'>{taux:.1%}</div>
        </div>
        """, unsafe_allow_html=True)

    kpi(col1, "Ventes", total_sales, taux_global)
    kpi(col2, "Élec", ventes_elec, ventes_elec / total_sales if total_sales else 0)
    kpi(col3, "Gaz", ventes_gaz, ventes_gaz / total_sales if total_sales else 0)

    st.markdown("---")

    # ---------------- GRAPHIQUES ----------------
    colg1, colg2 = st.columns(2)

    ventes_fournisseur = df_filtered.groupby("get_provider").size().reset_index(name="ventes")

    fig1 = px.bar(ventes_fournisseur, x="get_provider", y="ventes", color="ventes")
    fig1.update_layout(plot_bgcolor="white")

    colg1.plotly_chart(fig1, use_container_width=True)

    ventes_agent = df_filtered.groupby("agent").size().reset_index(name="ventes").sort_values(by="ventes", ascending=False)

    fig2 = px.bar(ventes_agent, x="ventes", y="agent", orientation="h", color="ventes")
    fig2.update_layout(plot_bgcolor="white", yaxis=dict(autorange="reversed"))

    colg2.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")

    # ---------------- PERFORMANCE DETAILLEE ----------------
    st.subheader("🎯 Performance détaillée")

    heures = st.number_input("Heures planifiées", min_value=0.0, step=1.0)
    agent_select = st.selectbox("Agent", df_filtered["agent"].unique())

    df_agent = df_filtered[df_filtered["agent"] == agent_select]

    def get_color(p):
        if p < 0.7:
            return "#ef4444"
        elif p < 1:
            return "#f59e0b"
        else:
            return "#10b981"

    for fournisseur in objectifs["Fournisseur"].dropna().unique():

        df_f = df_agent[df_agent["get_provider"].str.lower() == fournisseur.lower()]

        ventes_elec = len(df_f[df_f["energie"].str.lower() == "elec"])
        ventes_gaz = len(df_f[df_f["energie"].str.lower().isin(["gaz", "gas"])])

        obj_row = objectifs[objectifs["Fournisseur"].str.lower() == fournisseur.lower()]

        # 🔥 FORMULE CONSERVÉE
        obj_elec = heures * 0.75 * (obj_row["Objectif Elec"].sum() / objectif_total) if objectif_total else 0
        obj_gaz = heures * 0.75 * (obj_row["Objectif Gaz"].sum() / objectif_total) if objectif_total else 0

        p_elec = ventes_elec / obj_elec if obj_elec else 0
        p_gaz = ventes_gaz / obj_gaz if obj_gaz else 0

        color_elec = get_color(p_elec)
        color_gaz = get_color(p_gaz)

        st.markdown(f"""
        <div class="fournisseur-card">

            <b>{fournisseur}</b>

            <div class="progress-label">
                <span>⚡ Elec</span>
                <span>{p_elec:.0%} ({ventes_elec} / {int(obj_elec)})</span>
            </div>
            <div class="progress-bar-bg">
                <div class="progress-bar-fill" style="
                    width:{min(p_elec*100,100)}%;
                    background:{color_elec};
                "></div>
            </div>

            <div class="progress-label" style="margin-top:8px;">
                <span>🔥 Gaz</span>
                <span>{p_gaz:.0%} ({ventes_gaz} / {int(obj_gaz)})</span>
            </div>
            <div class="progress-bar-bg">
                <div class="progress-bar-fill" style="
                    width:{min(p_gaz*100,100)}%;
                    background:{color_gaz};
                "></div>
            </div>

        </div>
        """, unsafe_allow_html=True)

else:
    st.info("Veuillez uploader un fichier Excel")
