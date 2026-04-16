import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard Ventes", layout="wide")

# ---------------- STYLE ----------------
st.markdown("""
<style>
body {
    background-color: #EDF7FA;
}

/* KPI */
.metric-card {
    background: white;
    padding: 20px;
    border-radius: 14px;
    box-shadow: 0 6px 20px rgba(0,0,0,0.06);
    border-left: 5px solid #0F8BC6;
}

.metric-title {
    font-size: 13px;
    color: #8C5C29;
}

.metric-value {
    font-size: 28px;
    font-weight: bold;
    color: #0F8BC6;
}

.metric-sub {
    font-size: 14px;
    color: #EEB055;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #9BC9DD;
}

/* Headers */
h1, h2, h3 {
    color: #0F8BC6;
}
</style>
""", unsafe_allow_html=True)

st.title("📊 Dashboard - Ventes")

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

    # 👉 IMPORTANT : adapte ici le nom de ta colonne date
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # ---------------- FILTRES ----------------
    st.sidebar.header("🔎 Filtres")

    agents = st.sidebar.multiselect("Agent", df["agent"].unique(), default=df["agent"].unique())
    fournisseurs = st.sidebar.multiselect("Fournisseur", df["get_provider"].unique(), default=df["get_provider"].unique())
    energie = st.sidebar.multiselect("Énergie", df["energie"].unique(), default=df["energie"].unique())

    # 📅 FILTRE DATE
    min_date = df["date"].min()
    max_date = df["date"].max()

    date_range = st.sidebar.date_input("Période", [min_date, max_date])

    df_filtered = df[
        (df["agent"].isin(agents)) &
        (df["get_provider"].isin(fournisseurs)) &
        (df["energie"].isin(energie))
    ]

    # appliquer filtre date
    if len(date_range) == 2:
        df_filtered = df_filtered[
            (df_filtered["date"] >= pd.to_datetime(date_range[0])) &
            (df_filtered["date"] <= pd.to_datetime(date_range[1]))
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

    # ---------------- GRAPHIQUES ----------------
# ---------------- GRAPHIQUES AMÉLIORÉS ----------------
colg1, colg2 = st.columns(2)

# 📦 VENTES PAR FOURNISSEUR (style Power BI)
ventes_fournisseur = df_filtered.groupby("get_provider").size().reset_index(name="ventes")
ventes_fournisseur = ventes_fournisseur.sort_values(by="ventes", ascending=True)

fig1 = px.bar(
    ventes_fournisseur,
    x="ventes",
    y="get_provider",
    orientation="h",
    text="ventes",
    color="ventes",
    color_continuous_scale=["#9BC9DD", "#0F8BC6"]
)

fig1.update_traces(textposition="outside")

fig1.update_layout(
    title="Ventes par fournisseur",
    plot_bgcolor="#EDF7FA",
    paper_bgcolor="#EDF7FA",
    xaxis_title="",
    yaxis_title="",
    coloraxis_showscale=False,
    margin=dict(l=10, r=10, t=40, b=10)
)

colg1.plotly_chart(fig1, use_container_width=True)


# 👥 CLASSEMENT AGENTS (plus clean)
ventes_agent = df_filtered.groupby("agent").size().reset_index(name="ventes")
ventes_agent = ventes_agent.sort_values(by="ventes", ascending=True)

fig2 = px.bar(
    ventes_agent,
    x="ventes",
    y="agent",
    orientation="h",
    text="ventes",
    color="ventes",
    color_continuous_scale=["#EEB055", "#8C5C29"]
)

fig2.update_traces(textposition="outside")

fig2.update_layout(
    title="Classement agents",
    plot_bgcolor="#EDF7FA",
    paper_bgcolor="#EDF7FA",
    xaxis_title="",
    yaxis_title="",
    coloraxis_showscale=False,
    margin=dict(l=10, r=10, t=40, b=10)
)

colg2.plotly_chart(fig2, use_container_width=True)

    # ---------------- PERFORMANCE COMPACT ----------------
    st.subheader("🎯 Performance détaillée")

    heures = st.number_input("Heures planifiées", min_value=0.0, step=1.0)
    agent_select = st.selectbox("Agent", df_filtered["agent"].unique())

    df_agent = df_filtered[df_filtered["agent"] == agent_select]

    rows = []

    for fournisseur in objectifs["Fournisseur"].dropna().unique():

        df_f = df_agent[df_agent["get_provider"].str.lower() == fournisseur.lower()]
        obj_row = objectifs[objectifs["Fournisseur"].str.lower() == fournisseur.lower()]

        ventes_elec = len(df_f[df_f["energie"].str.lower() == "elec"])
        ventes_gaz = len(df_f[df_f["energie"].str.lower().isin(["gaz", "gas"])])

        obj_elec = heures * 0.75 * (obj_row["Objectif Elec"].sum() / objectif_total) if objectif_total else 0
        obj_gaz = heures * 0.75 * (obj_row["Objectif Gaz"].sum() / objectif_total) if objectif_total else 0

        p_elec = ventes_elec / obj_elec if obj_elec else 0
        p_gaz = ventes_gaz / obj_gaz if obj_gaz else 0

        rows.append({
            "fournisseur": fournisseur,
            "p_total": p_elec + p_gaz,
            "p_elec": p_elec,
            "p_gaz": p_gaz,
            "ventes_elec": ventes_elec,
            "ventes_gaz": ventes_gaz,
            "obj_elec": int(obj_elec) if obj_elec > 0 else 0,
            "obj_gaz": int(obj_gaz) if obj_gaz > 0 else 0
        })

    # tri
    rows = sorted(rows, key=lambda x: x["p_total"], reverse=True)

    def emoji(p):
        return "🟢" if p >= 1 else "🟠" if p >= 0.7 else "🔴"

    # 👉 AFFICHAGE ULTRA COMPACT EN LIGNE
    for r in rows:
        col1, col2, col3 = st.columns([2, 4, 4])

        col1.write(f"**{r['fournisseur']}**")

        with col2:
            st.caption(f"{emoji(r['p_elec'])} ⚡ {r['p_elec']:.0%} ({r['ventes_elec']}/{r['obj_elec']})")
            st.progress(min(r["p_elec"], 1.0))

        with col3:
            st.caption(f"{emoji(r['p_gaz'])} 🔥 {r['p_gaz']:.0%} ({r['ventes_gaz']}/{r['obj_gaz']})")
            st.progress(min(r["p_gaz"], 1.0))

else:
    st.info("Veuillez uploader un fichier Excel")
