import streamlit as st
import pandas as pd
import os
import math
from datetime import datetime
import holidays

st.set_page_config(page_title="HelloWatt Dashboard", layout="wide")

# ---------------- CSS ----------------
st.markdown("""
<style>

section[data-testid="stSidebar"] {
    background-color: #E2E8F0;
}

[data-baseweb="tag"] {
    background-color: #BFDBFE !important;
    color: #1E3A8A !important;
}

.stProgress > div > div > div > div {
    background-color:#0F8BC6;
}

/* KPI STYLE */
.kpi-card {
    background-color: #F8FAFC;
    border: 1px solid #CBD5E1;
    border-radius: 14px;
    height: 110px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
}

.kpi-card h4 {
    margin: 0;
    font-size: 15px;
    font-weight: 600;
    color: #334155;
}

.kpi-card h2 {
    margin: 0;
    font-size: 22px;
    font-weight: 700;
}

</style>
""", unsafe_allow_html=True)

SAVE_PATH = "last_uploaded.xlsx"

st.title("HelloWatt - Dashboard")

page = st.sidebar.radio("Navigation", ["📊 Dashboard","👤 Agents","🎯 Objectifs"])

# ---------------- UTILS ----------------
def clean_text(col):
    return col.astype(str).str.strip().str.upper()

def emoji(p):
    return "🟢" if p>=1 else "🟠" if p>=0.7 else "🔴"

def round_excel(x):
    return int(x+0.5+1e-9)

def get_working_days():
    today = datetime.today()
    start = today.replace(day=1)
    fr = holidays.FR()
    days = pd.date_range(start, today)
    return len([d for d in days if d.weekday()<5 and d.date() not in fr])

# ---------------- LOAD ----------------
if os.path.exists(SAVE_PATH):
    uploaded_file = SAVE_PATH

if uploaded_file:

    xls = pd.ExcelFile(uploaded_file)
    df = pd.read_excel(xls,"Extraction")
    code = pd.read_excel(xls,"Code")
    objectifs = pd.read_excel(xls,"Objectifs")

    df["responder"]=clean_text(df["responder"])
    code.iloc[:,0]=clean_text(code.iloc[:,0])

    df = df.merge(
        code.rename(columns={code.columns[0]:"responder",code.columns[1]:"agent"}),
        on="responder",how="left"
    )

    df["agent"]=clean_text(df["agent"]).fillna("INCONNU")
    df["get_provider"]=clean_text(df["get_provider"])

    # 🔥 FIX GAZ / ELEC STABLE
    df["energie"]=(
        df["energie"]
        .astype(str)
        .str.strip()
        .str.lower()
        .replace({"gas":"GAZ","elec":"ELEC"})
        .str.upper()
    )

    df["date"]=pd.to_datetime(df["date"],errors="coerce")
    objectifs["Fournisseur"]=clean_text(objectifs["Fournisseur"])

    USER_COL="user id"

    # ---------------- FILTRES ----------------
    st.sidebar.markdown("### 🔎 Filtres")

    agents = st.sidebar.multiselect("Agents", df["agent"].unique(), df["agent"].unique())
    fournisseurs = st.sidebar.multiselect("Fournisseurs", df["get_provider"].unique(), df["get_provider"].unique())
    energie = st.sidebar.multiselect("Énergie", df["energie"].unique(), df["energie"].unique())

    min_d,max_d=df["date"].min(),df["date"].max()
    dates = st.sidebar.date_input("Période",[min_d,max_d])

    df_filtered = df[
        df["agent"].isin(agents) &
        df["get_provider"].isin(fournisseurs) &
        df["energie"].isin(energie)
    ]

    if len(dates)==2:
        df_filtered = df_filtered[
            (df_filtered["date"]>=pd.to_datetime(dates[0])) &
            (df_filtered["date"]<=pd.to_datetime(dates[1]))
        ]

    objectif_total = objectifs["Objectifs Total"].sum()

    # ================= DASHBOARD =================
    if page=="📊 Dashboard":

        st.header("🏢 Objectifs Globaux")

        total = df_filtered.shape[0]
        elec = df_filtered[df_filtered["energie"]=="ELEC"].shape[0]
        gaz = df_filtered[df_filtered["energie"]=="GAZ"].shape[0]

        obj_elec = objectifs["Objectif Elec"].sum()
        obj_gaz = objectifs["Objectif Gaz"].sum()

        perf = total / objectif_total if objectif_total else 0

        cols = st.columns(5, gap="large")

        data = [
            ("🎯 Total", total),
            ("📊 Objectif", objectif_total),
            ("🔥 Perf", f"{perf:.0%}"),
            ("⚡ Élec", f"{elec}/{obj_elec}"),
            ("🔥 Gaz", f"{gaz}/{obj_gaz}")
        ]

        for c,(t,v) in zip(cols,data):
            with c:
                st.markdown(f"""
                <div class="kpi-card">
                    <h4>{t}</h4>
                    <h2>{v}</h2>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ================= FOURNISSEURS =================
        st.subheader("🏭 Performance par fournisseur")

        for f in objectifs["Fournisseur"].dropna().unique():

            df_f = df_filtered[df_filtered["get_provider"]==f]

            obj_row = objectifs[objectifs["Fournisseur"]==f]

            obj_total = obj_row["Objectifs Total"].sum()
            obj_elec = obj_row["Objectif Elec"].sum()
            obj_gaz = obj_row["Objectif Gaz"].sum()

            v_total = len(df_f)
            v_elec = len(df_f[df_f["energie"]=="ELEC"])
            v_gaz = len(df_f[df_f["energie"]=="GAZ"])

            p = v_total / obj_total if obj_total else 0

            c1,c2,c3 = st.columns([2,5,4])

            c1.write(f)
            c2.progress(min(p,1.0))

            c3.markdown(f"""
            ⚡ {v_elec}/{obj_elec}  
            🔥 {v_gaz}/{obj_gaz}  
            🎯 {v_total}/{obj_total}  
            {emoji(p)} {p:.0%}
            """, unsafe_allow_html=True)

    # ================= AGENTS =================
    elif page=="👤 Agents":

        st.header("👤 Performance Agents")

        jours = get_working_days()
        obj_agent = math.ceil(185*0.75)

        v = df_filtered.groupby("agent").size().reset_index(name="ventes")
        v["taux"] = v["ventes"]/obj_agent
        v["kpi"] = v["ventes"]/jours if jours else 0

        for _,r in v.iterrows():
            c1,c2,c3,c4 = st.columns([3,5,2,2])
            c1.write(r["agent"])
            c2.progress(min(r["taux"],1))
            c3.write(f"{emoji(r['taux'])} {r['ventes']}/{obj_agent}")
            c4.write(f"📅 {round(r['kpi'],1)}/J")

    # ================= OBJECTIFS (FIX CRITIQUE FINAL) =================
    elif page=="🎯 Objectifs":

        st.header("🎯 Performance détaillée")

        colA,colB = st.columns(2)
        heures = colA.number_input("Heures", value=185.0)
        agent = colB.selectbox("Agent", df_filtered["agent"].unique())

        # 🔥 FIX IMPORTANT : base filtrée + cohérente
        df_agent = df_filtered[df_filtered["agent"] == agent]

        obj_agent = round_excel(heures*0.75)
        ventes_total = len(df_agent)
        taux = ventes_total/obj_agent if obj_agent else 0

        c1,c2,c3 = st.columns([3,6,2])
        c1.write(agent)
        c2.progress(min(taux,1.0))
        c3.write(f"{emoji(taux)} {ventes_total}/{obj_agent}")

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("### ⚡ Ventes Fournisseurs")

        special=["HOMESERVE","FREE"]

        for f in objectifs["Fournisseur"].dropna().unique():

            if f in special:
                continue

            df_f = df_agent[df_agent["get_provider"]==f]
            obj_row = objectifs[objectifs["Fournisseur"]==f]

            obj = obj_row["Objectifs Total"].sum()
            v = len(df_f)
            p = v/obj if obj else 0

            c1,c2,c3 = st.columns([3,6,2])
            c1.write(f)
            c2.progress(min(p,1.0))
            c3.write(f"{emoji(p)} {v}/{obj}")

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("### ⭐ Ventes Additionnelles")

        total_unique = df_agent[USER_COL].nunique()

        for sp in special:

            df_sp = df_agent[df_agent["get_provider"]==sp]
            v = df_sp[USER_COL].nunique()

            obj_sp = max(1, round_excel(total_unique*0.05))
            p = v/obj_sp if obj_sp else 0

            c1,c2,c3 = st.columns([3,6,2])
            c1.write(sp)
            c2.progress(min(p,1))
            c3.write(f"{emoji(p)} {v}/{obj_sp}")

else:
    st.info("🔒 Ajoute un fichier (admin)")
