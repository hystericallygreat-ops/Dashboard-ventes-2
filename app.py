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

.card {
    background: white;
    padding: 20px;
    border-radius: 16px;
    box-shadow: 0 6px 20px rgba(0,0,0,0.05);
}

.kpi-title {font-size:13px;color:#64748B;}
.kpi-value {font-size:30px;font-weight:bold;}
.kpi-sub {font-size:14px;color:#22C55E;}
</style>
""", unsafe_allow_html=True)

st.title("📊 Dashboard Ventes")

# ---------------- SI FICHIER ----------------
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
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # ---------------- FILTRES ----------------
    st.sidebar.header("🔎 Filtres")

    agents = st.sidebar.multiselect("Agent", df["agent"].unique(), default=df["agent"].unique())
    fournisseurs = st.sidebar.multiselect("Fournisseur", df["get_provider"].unique(), default=df["get_provider"].unique())
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

    # ---------------- KPI ----------------
    total_sales = len(df_filtered)
    objectif_total = objectifs["Objectifs Total"].sum()

    ventes_elec = len(df_filtered[df_filtered["energie"].str.lower() == "elec"])
    ventes_gaz = len(df_filtered[df_filtered["energie"].str.lower().isin(["gaz", "gas"])])

    taux_global = total_sales / objectif_total if objectif_total else 0

    col1, col2, col3 = st.columns(3)

    def kpi(col, title, value, taux):
        col.markdown(f"""
        <div class='card'>
            <div class='kpi-title'>{title}</div>
            <div class='kpi-value'>{value}</div>
            <div class='kpi-sub'>{taux:.1%}</div>
        </div>
        """, unsafe_allow_html=True)

    kpi(col1, "Ventes", total_sales, taux_global)
    kpi(col2, "Élec", ventes_elec, ventes_elec / total_sales if total_sales else 0)
    kpi(col3, "Gaz", ventes_gaz, ventes_gaz / total_sales if total_sales else 0)

    st.markdown("---")

    # ---------------- FOURNISSEURS (INCHANGÉ) ----------------
    st.subheader("🏢 Performance Fournisseurs")

    ventes_fournisseur = df_filtered.groupby("get_provider").size().reset_index(name="ventes")

    rows = []

    for _, row in ventes_fournisseur.iterrows():
        fournisseur = row["get_provider"]
        ventes = row["ventes"]

        obj_row = objectifs[objectifs["Fournisseur"].str.lower() == fournisseur.lower()]
        objectif_fournisseur = obj_row["Objectifs Total"].sum() if not obj_row.empty else 0

        taux = ventes / objectif_fournisseur if objectif_fournisseur else 0

        rows.append((fournisseur, ventes, objectif_fournisseur, taux))

    rows = sorted(rows, key=lambda x: x[3], reverse=True)

    def emoji(p):
        return "🟢" if p >= 1 else "🟠" if p >= 0.7 else "🔴"

    for f, v, obj, t in rows:
        st.markdown(f"**{f}**")
        st.caption(f"{emoji(t)} {v}/{int(obj)} ({t:.0%})")
        st.progress(min(t, 1.0))

    st.markdown("---")

    # ---------------- AGENTS (SANS HTML) ----------------
    st.subheader("👤 Performance Agents")

    ventes_agent = df_filtered.groupby("agent").size().reset_index(name="ventes")

    objectif_agent = 185 * 0.75

    rows = []

    for _, row in ventes_agent.iterrows():
        agent = row["agent"]
        ventes = row["ventes"]
        taux = ventes / objectif_agent if objectif_agent else 0
        rows.append((agent, ventes, objectif_agent, taux))

    rows = sorted(rows, key=lambda x: x[3], reverse=True)

    for a, v, obj, t in rows:

        col1, col2 = st.columns([3, 5])

        with col1:
            st.markdown(f"**{a}**")
            st.caption(f"{emoji(t)} {v}/{int(obj)} ({t:.0%})")

        with col2:
            st.progress(min(t, 1.0))

    st.markdown("---")

    # ---------------- DÉTAIL AGENT (TON CODE) ----------------
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

    rows = sorted(rows, key=lambda x: x["p_total"], reverse=True)

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
