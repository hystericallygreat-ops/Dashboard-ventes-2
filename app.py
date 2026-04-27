import streamlit as st
import pandas as pd
import os
import math
from datetime import datetime
import holidays

st.set_page_config(page_title="HelloWatt Dashboard", layout="wide")

# ---------------- CSS SAFE (INCHANGÉ) ----------------
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
.block {
    padding: 12px;
    border-radius: 10px;
    background-color: #F8FAFC;
    border: 1px solid #CBD5E1;
    margin-bottom: 12px;
}
h1, h2, h3 {
    margin-top: 10px !important;
    margin-bottom: 10px !important;
}
</style>
""", unsafe_allow_html=True)

SAVE_PATH = "last_uploaded.xlsx"

# ---------------- HEADER ----------------
st.title("HelloWatt - Dashboard")
st.markdown("<br>", unsafe_allow_html=True)

# ---------------- NAV ----------------
page = st.sidebar.radio("Navigation", ["📊 Dashboard","👤 Agents","🎯 Objectifs"])

# ✅ FIX ADMIN (AJOUT UNIQUEMENT ICI)
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔐 Admin")
password = st.sidebar.text_input("Mot de passe", type="password")
is_admin = password == "hello123"

if is_admin:
    uploaded_file_admin = st.sidebar.file_uploader("Uploader fichier Excel", type=["xlsx"])

    if uploaded_file_admin:
        with open(SAVE_PATH, "wb") as f:
            f.write(uploaded_file_admin.getbuffer())
        st.rerun()

    if os.path.exists(SAVE_PATH):
        if st.sidebar.button("🗑 Supprimer"):
            os.remove(SAVE_PATH)
            st.rerun()

uploaded_file = None

# ---------------- UTILS ----------------
def clean_text(col):
    return col.astype(str).str.strip().str.replace('"','').str.replace("'","").str.upper()

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

# ---------------- APP ----------------
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
        st.markdown("<br>", unsafe_allow_html=True)

        ventes = df_filtered.groupby("get_provider").size().reset_index(name="ventes")

        df_obj = objectifs.merge(
            ventes,left_on="Fournisseur",right_on="get_provider",how="left"
        ).fillna(0)

        df_obj = df_obj.sort_values("Objectifs Total",ascending=False)

        for _,r in df_obj.iterrows():

            p = r["ventes"]/r["Objectifs Total"] if r["Objectifs Total"] else 0

            df_f = df_filtered[df_filtered["get_provider"]==r["Fournisseur"]]

            v_elec = len(df_f[df_f["energie"]=="ELEC"])
            v_gaz = len(df_f[df_f["energie"]=="GAZ"])

            obj_elec = objectifs[objectifs["Fournisseur"]==r["Fournisseur"]]["Objectif Elec"].sum()
            obj_gaz = objectifs[objectifs["Fournisseur"]==r["Fournisseur"]]["Objectif Gaz"].sum()

            with st.container():
                c1,c2,c3 = st.columns([3,6,4])
                c1.write(r["Fournisseur"])
                c2.progress(min(p,1.0))
                c3.markdown(
                    f"⚡ {v_elec}/{obj_elec} &nbsp;&nbsp; "
                    f"🔥 {v_gaz}/{obj_gaz} &nbsp;&nbsp; "
                    f"🎯 {int(r['ventes'])}/{int(r['Objectifs Total'])} &nbsp;&nbsp; "
                    f"{emoji(p)} {p:.0%}",
                    unsafe_allow_html=True
                )

    # ================= AGENTS =================
    elif page == "👤 Agents":
    
        st.header("👤 Performance Agents")
        st.markdown("<br>", unsafe_allow_html=True)
    
        jours = get_working_days()
        obj_agent = math.ceil(185 * 0.75)
    
        # ---------------- DATA ----------------
        ventes_agent = df_filtered.groupby("agent").size().reset_index(name="ventes")
    
        ventes_energie = (
            df_filtered
            .groupby(["agent", "energie"])
            .size()
            .unstack(fill_value=0)
            .reset_index()
        )
    
        if "ELEC" not in ventes_energie.columns:
            ventes_energie["ELEC"] = 0
        if "GAZ" not in ventes_energie.columns:
            ventes_energie["GAZ"] = 0
    
        ventes_agent = ventes_agent.merge(ventes_energie, on="agent", how="left").fillna(0)
    
        ventes_agent["taux"] = ventes_agent["ventes"] / obj_agent
        ventes_agent["kpi"] = ventes_agent["ventes"] / jours if jours else 0
    
        ventes_agent = ventes_agent.sort_values("taux", ascending=False)
    
        # ---------------- CSS FIX ALIGNEMENT NUMÉRIQUE ----------------
        st.markdown("""
        <style>
    
        .row {
            display: flex;
            align-items: center;
            gap: 14px;
            padding: 6px 0;
        }
    
        .name {
            width: 260px;
            font-weight: 500;
            white-space: nowrap;
        }
    
        .bar {
            flex: 1;
            min-width: 180px;
        }
    
        .num {
            width: 85px;
            text-align: right;
    
            /* 🔥 FIX CRITIQUE ALIGNEMENT CHIFFRES */
            font-variant-numeric: tabular-nums;
            font-family: "Arial", sans-serif;
            white-space: nowrap;
        }
    
        .kpi {
            width: 70px;
            text-align: right;
            font-variant-numeric: tabular-nums;
            white-space: nowrap;
        }
    
        .bar-bg {
            background: #E5E7EB;
            height: 10px;
            border-radius: 6px;
            overflow: hidden;
        }
    
        .bar-fill {
            height: 10px;
            background: #0F8BC6;
            border-radius: 6px;
        }
    
        </style>
        """, unsafe_allow_html=True)
    
        # ---------------- HEADER ----------------
        st.markdown("**Agent | Progression | ⚡ | 🔥 | 🎯 Total | 📅 KPI**")
    
        # ---------------- LIGNES ----------------
        for _, r in ventes_agent.iterrows():
    
            agent = r["agent"]
            v_total = int(r["ventes"])
            v_elec = int(r["ELEC"])
            v_gaz = int(r["GAZ"])
            taux = r["taux"]
            kpi = r["kpi"]
    
            st.markdown(f"""
            <div class="row">
    
                <div class="name">{agent}</div>
    
                <div class="bar">
                    <div class="bar-bg">
                        <div class="bar-fill" style="width:{min(taux,1)*100}%"></div>
                    </div>
                </div>
    
                <div class="num">⚡ {v_elec}</div>
    
                <div class="num">🔥 {v_gaz}</div>
    
                <div class="num">🎯 {v_total}/{obj_agent}</div>
    
                <div class="kpi">📅 {round(kpi,1)}</div>
    
            </div>
            """, unsafe_allow_html=True)
    # ================= OBJECTIFS =================
    elif page=="🎯 Objectifs":

        st.header("🎯 Performance détaillée")

        colA,colB = st.columns(2)
        heures = colA.number_input("Heures", value=185.0)
        agent = colB.selectbox("Agent", df_filtered["agent"].unique())

        df_agent = df_filtered[df_filtered["agent"] == agent]

        obj_agent = round_excel(heures*0.75)
        ventes_total = len(df_agent)
        taux = ventes_total/obj_agent if obj_agent else 0

        st.markdown("<div class='block'>", unsafe_allow_html=True)
        st.subheader(agent)
        st.progress(min(taux,1.0))
        st.write(f"{emoji(taux)} {ventes_total}/{obj_agent} ({taux:.0%})")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("### ⚡ Ventes Fournisseurs")

        special=["HOMESERVE","FREE"]

        for f in objectifs["Fournisseur"].dropna().unique():

            if f in special:
                continue

            df_f = df_agent[df_agent["get_provider"]==f]
            obj_row = objectifs[objectifs["Fournisseur"]==f]

            obj_total_f = round_excel(
                heures*0.75*(obj_row["Objectifs Total"].sum()/objectif_total)
            )

            obj_elec_f = round_excel(
                heures*0.75*(obj_row["Objectif Elec"].sum()/objectif_total)
            )

            obj_gaz_f = round_excel(
                heures*0.75*(obj_row["Objectif Gaz"].sum()/objectif_total)
            )

            v_total = len(df_f)
            v_elec = len(df_f[df_f["energie"]=="ELEC"])
            v_gaz = len(df_f[df_f["energie"]=="GAZ"])

            p = v_total/obj_total_f if obj_total_f else 0

            c1,c2,c3 = st.columns([2,5,5])
            c1.write(f)
            c2.progress(min(p,1.0))
            c3.markdown(
                f"⚡ {v_elec}/{obj_elec_f} &nbsp;&nbsp; "
                f"🔥 {v_gaz}/{obj_gaz_f} &nbsp;&nbsp; "
                f"🎯 {v_total}/{obj_total_f} &nbsp;&nbsp; "
                f"{emoji(p)} {p:.0%}",
                unsafe_allow_html=True
            )

else:
    st.info("🔒 Ajoute un fichier (admin)")
