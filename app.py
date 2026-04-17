import streamlit as st
import pandas as pd
import os
import math

st.set_page_config(page_title="Dashboard Ventes", layout="wide")

SAVE_PATH = "last_uploaded.xlsx"

# ---------------- STYLE ----------------
st.markdown("""
<style>
body {background-color: #F5FAFD;}

h1, h2, h3 {color:#0F8BC6;}

.stProgress > div > div > div > div {
    background-color: #0F8BC6;
}
</style>
""", unsafe_allow_html=True)

# ---------------- LOGO (SOLUTION 3) ----------------
st.image(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5f/Hello_Watt_logo.png/320px-Hello_Watt_logo.png",
    width=180
)

# ---------------- AUTH ----------------
st.sidebar.header("🔐 Accès Admin")

password = st.sidebar.text_input("Mot de passe", type="password")

ADMIN_PASSWORD = "hello123"  # 🔥 change ici

is_admin = password == ADMIN_PASSWORD

# ---------------- UPLOAD ADMIN ----------------
uploaded_file = None

if is_admin:
    st.sidebar.success("Mode Admin activé")

    uploaded_file = st.sidebar.file_uploader("Uploader fichier Excel", type=["xlsx"])

    if uploaded_file is not None:
        with open(SAVE_PATH, "wb") as f:
            f.write(uploaded_file.getbuffer())

    if os.path.exists(SAVE_PATH):
        if st.sidebar.button("🗑 Supprimer fichier"):
            os.remove(SAVE_PATH)
            st.rerun()

else:
    if os.path.exists(SAVE_PATH):
        uploaded_file = SAVE_PATH

# ---------------- MENU ----------------
page = st.sidebar.radio("Navigation", [
    "📊 Dashboard",
    "👤 Performance Agents",
    "🏢 Objectifs Globaux"
])

# ---------------- APP ----------------
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

    # FILTRES
    agents = st.sidebar.multiselect("Agent", df["agent"].unique(), default=df["agent"].unique())
    fournisseurs = st.sidebar.multiselect("Fournisseur", df["get_provider"].unique(), default=df["get_provider"].unique())

    df_filtered = df[
        (df["agent"].isin(agents)) &
        (df["get_provider"].isin(fournisseurs))
    ]

    objectif_total = objectifs["Objectifs Total"].sum()

    def emoji(p):
        return "🟢" if p >= 1 else "🟠" if p >= 0.7 else "🔴"

    # ---------------- DASHBOARD ----------------
    if page == "📊 Dashboard":

        st.title("📊 Dashboard")

        total_sales = len(df_filtered)
        taux_global = total_sales / objectif_total if objectif_total else 0

        col1, col2 = st.columns(2)

        col1.metric("Ventes", total_sales)
        col2.metric("Progression", f"{taux_global:.0%}")

        st.markdown("---")

        st.subheader("🎯 Performance détaillée")

        heures = st.number_input("Heures planifiées", value=185.0)
        agent_select = st.selectbox("Agent", df_filtered["agent"].unique())

        df_agent = df_filtered[df_filtered["agent"] == agent_select]

        col1, col2, col3 = st.columns([2, 4, 4])
        col1.markdown("**Fournisseur**")
        col2.markdown("**⚡ Elec**")
        col3.markdown("**🔥 Gaz**")

        for fournisseur in objectifs["Fournisseur"].dropna().unique():

            df_f = df_agent[df_agent["get_provider"].str.lower() == fournisseur.lower()]
            obj_row = objectifs[objectifs["Fournisseur"].str.lower() == fournisseur.lower()]

            ventes_elec = len(df_f[df_f["energie"].str.lower() == "elec"])
            ventes_gaz = len(df_f[df_f["energie"].str.lower().isin(["gaz", "gas"])])

            obj_elec = math.ceil(
                heures * 0.75 * (obj_row["Objectif Elec"].sum() / objectif_total)
            ) if objectif_total else 0

            obj_gaz = math.ceil(
                heures * 0.75 * (obj_row["Objectif Gaz"].sum() / objectif_total)
            ) if objectif_total else 0

            p_elec = ventes_elec / obj_elec if obj_elec else 0
            p_gaz = ventes_gaz / obj_gaz if obj_gaz else 0

            col1, col2, col3 = st.columns([2, 4, 4])

            col1.write(f"**{fournisseur}**")

            with col2:
                st.caption(f"{emoji(p_elec)} {ventes_elec}/{obj_elec} ({p_elec:.0%})")
                st.progress(min(p_elec, 1.0))

            with col3:
                st.caption(f"{emoji(p_gaz)} {ventes_gaz}/{obj_gaz} ({p_gaz:.0%})")
                st.progress(min(p_gaz, 1.0))

    # ---------------- AGENTS ----------------
    elif page == "👤 Performance Agents":

        st.title("👤 Performance Agents")

        ventes_agent = df_filtered.groupby("agent").size().reset_index(name="ventes")

        objectif_agent = math.ceil(185 * 0.75)

        ventes_agent["taux"] = ventes_agent["ventes"] / objectif_agent
        ventes_agent = ventes_agent.sort_values("taux", ascending=False)

        for _, row in ventes_agent.iterrows():

            col1, col2 = st.columns([3, 5])

            with col1:
                st.markdown(f"**{row['agent']}**")
                st.caption(f"{emoji(row['taux'])} {row['ventes']}/{objectif_agent} ({row['taux']:.0%})")

            with col2:
                st.progress(min(row["taux"], 1.0))

    # ---------------- OBJECTIFS ----------------
    elif page == "🏢 Objectifs Globaux":

        st.title("🏢 Objectifs Globaux")

        ventes_fournisseur = df_filtered.groupby("get_provider").size().reset_index(name="ventes")

        for _, row in ventes_fournisseur.iterrows():

            fournisseur = row["get_provider"]
            ventes = row["ventes"]

            obj_row = objectifs[objectifs["Fournisseur"].str.lower() == fournisseur.lower()]
            objectif_fournisseur = obj_row["Objectifs Total"].sum() if not obj_row.empty else 0

            taux = ventes / objectif_fournisseur if objectif_fournisseur else 0

            st.markdown(f"**{fournisseur}**")
            st.caption(f"{emoji(taux)} {ventes}/{int(objectif_fournisseur)} ({taux:.0%})")
            st.progress(min(taux, 1.0))

else:
    st.info("Veuillez uploader un fichier Excel (admin uniquement)")
