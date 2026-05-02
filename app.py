import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import os
import math
import io
import base64
from datetime import datetime
import holidays
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

st.set_page_config(
    page_title="Suivi Commercial",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================================================================
# PALETTE — inspirée site énergie bleu/orange
# ================================================================
# Bleu principal : #00AEEF  Bleu foncé : #005F8E  Bleu clair : #E6F4FB
# Orange accent  : #00AEEF  Orange clair : #E6F4FB
# Vert succès    : #00C48C  Rouge danger : #FF4757  Jaune warning: #FFB300
# Gris texte     : #1A3A5C  Gris moyen : #64748B   Gris clair : #F4F6FA
# ================================================================

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* ---- RESET GLOBAL ---- */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}
.main .block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
    max-width: 1400px;
    background: #F0F6FA !important;
}

/* ---- SIDEBAR CONTRASTE HELLOWATT ---- */
section[data-testid="stSidebar"] {
    background: #C8E8F5 !important;
    border-right: 2px solid #6CC0E0 !important;
}
section[data-testid="stSidebar"] * {
    color: #1A3A5C !important;
}
section[data-testid="stSidebar"] .stRadio label {
    color: #1A3A5C !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    padding: 7px 10px !important;
    border-radius: 8px !important;
    transition: background 0.15s !important;
}
section[data-testid="stSidebar"] .stRadio label:hover {
    background: #E6F4FB !important;
    color: #00AEEF !important;
}
section[data-testid="stSidebar"] [data-baseweb="radio"] input:checked + div {
    background: #E6F4FB !important;
    border-radius: 8px !important;
}
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] .stMarkdown h3 {
    color: #94A3B8 !important;
    font-size: 0.68rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.12em !important;
    margin-top: 1rem !important;
}
section[data-testid="stSidebar"] .stMultiSelect > div,
section[data-testid="stSidebar"] .stDateInput > div,
section[data-testid="stSidebar"] .stTextInput > div {
    background: #FFFFFF !important;
    border: 1px solid #B8DFF0 !important;
    border-radius: 8px !important;
}
section[data-testid="stSidebar"] [data-baseweb="tag"] {
    background: #B8DFF0 !important;
    color: #1A3A5C !important;
    border-radius: 4px !important;
    font-weight: 600 !important;
}
section[data-testid="stSidebar"] hr {
    border-color: #DCEEF8 !important;
    margin: 12px 0 !important;
}
section[data-testid="stSidebar"] input[type="password"] {
    background: #F8FBFD !important;
    color: #1A3A5C !important;
    border: 1px solid #DCEEF8 !important;
}

/* ---- PAGE HEADER ---- */
.page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 2px solid #C8E6F5;
}
.page-header-left h1 {
    font-size: 1.6rem !important;
    font-weight: 800 !important;
    color: #1A3A5C !important;
    margin: 0 !important;
    letter-spacing: -0.02em;
}
.page-header-left p {
    color: #64748B;
    font-size: 0.85rem;
    margin: 2px 0 0 0;
}
.page-badge {
    background: #00AEEF;
    color: #1A3A5C !important;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.03em;
}

/* ---- METRIC CARDS ---- */
.kpi-grid {
    display: grid;
    gap: 1px;
}
.metric-card {
    background: #FFFFFF;
    border: 1px solid #C8E6F5;
    border-radius: 14px;
    padding: 18px 20px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(26,171,219,0.12), 0 6px 20px rgba(26,171,219,0.07);
    transition: transform 0.15s, box-shadow 0.15s;
    margin-bottom: 12px;
    text-align: center;
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #1AABDB, #3BBFE8);
    border-radius: 14px 14px 0 0;
}
.metric-card.orange::before {
    background: linear-gradient(90deg, #1AABDB, #3BBFE8);
}
.metric-card.green::before {
    background: linear-gradient(90deg, #00C48C, #00E0A3);
}
.metric-card.red::before {
    background: linear-gradient(90deg, #FF4757, #FF6B78);
}
.metric-card .mc-icon {
    font-size: 1.4rem;
    margin-bottom: 8px;
    display: block;
}
.metric-card .mc-value {
    font-size: 1.9rem;
    font-weight: 800;
    color: #1A3A5C;
    line-height: 1.1;
    letter-spacing: -0.02em;
}
.metric-card .mc-label {
    font-size: 0.72rem;
    font-weight: 600;
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 6px;
}
.metric-card .mc-sub {
    font-size: 0.78rem;
    color: #64748B;
    margin-top: 4px;
    font-weight: 500;
}

/* ---- PROGRESS BAR ---- */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #1AABDB, #3BBFE8) !important;
    border-radius: 4px !important;
}
.stProgress > div > div > div {
    background: #D6EEF8 !important;
    border-radius: 4px !important;
    height: 8px !important;
}

/* ---- SECTION LABEL ---- */
.section-label {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 20px 0 10px 0;
}
.section-label span.sl-line {
    flex: 1;
    height: 1px;
    background: #E6F4FB;
}
.section-label span.sl-text {
    font-size: 0.72rem;
    font-weight: 700;
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    white-space: nowrap;
}

/* ---- AGENT ROWS ---- */
.agent-card {
    background: #FFFFFF;
    border: 1px solid #E6F4FB;
    border-radius: 10px;
    padding: 10px 14px;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    box-shadow: 0 1px 3px rgba(14,74,203,0.04);
    transition: border-color 0.15s;
}
.agent-card:hover {
    border-color: #1AABDB;
}
.agent-rank {
    font-size: 1.2rem;
    min-width: 32px;
}
.agent-name {
    font-weight: 700;
    color: #1A3A5C;
    font-size: 0.9rem;
}

/* ---- PROVIDER ROWS ---- */
.provider-row {
    background: #FFFFFF;
    border: 1px solid #C8E6F5;
    border-radius: 10px;
    padding: 8px 14px;
    margin-bottom: 5px;
    box-shadow: 0 1px 4px rgba(26,171,219,0.08);
}
.provider-row:nth-child(even) {
    background: #F5FAFD;
}

/* ---- PERIOD BANNER ---- */
.period-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #E6F4FB;
    color: #00AEEF;
    padding: 5px 12px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
    margin-bottom: 16px;
}

/* ---- SIDEBAR PERIOD ---- */
.sb-period {
    background: #FFFFFF;
    border: 1px solid #B8DFF0;
    border-radius: 10px;
    padding: 10px 12px;
    font-size: 0.82rem;
    color: #1A3A5C !important;
    margin: 8px 0;
    text-align: center;
}
.sb-summary {
    background: #FFFFFF;
    border: 1px solid #B8DFF0;
    border-radius: 10px;
    padding: 10px 12px;
    font-size: 0.8rem;
    color: #1A3A5C !important;
    margin-top: 6px;
    line-height: 1.8;
}

/* ---- OBJECTIF AGENT BLOCK ---- */
.agent-recap {
    background: linear-gradient(135deg, #E6F4FB 0%, #F4F9FC 100%);
    border: 1px solid #DCEEF8;
    border-radius: 14px;
    padding: 20px 24px;
    margin-bottom: 16px;
}
.agent-recap h2 {
    font-size: 1.3rem !important;
    font-weight: 800 !important;
    color: #00AEEF !important;
    margin: 0 0 12px 0 !important;
}

/* ---- STATUS BADGE ---- */
.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 700;
}
.badge-green  { background: #DCFCE7; color: #16A34A; }
.badge-orange { background: #E6F4FB; color: #0099D6; }
.badge-red    { background: #FEE2E2; color: #DC2626; }

/* ---- MAIN TITLE ---- */
h1, h2, h3 { margin-top: 8px !important; margin-bottom: 8px !important; }
.stButton button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
}
</style>
"""

st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)

SAVE_PATH = "last_uploaded.xlsx"

# ================================================================
# UTILS — inchangés
# ================================================================
def clean_text(col):
    return col.astype(str).str.strip().str.replace('"','').str.replace("'","").str.upper()

def status_badge(p):
    if p >= 1:   return "<span class='status-badge badge-green'>● Objectif atteint</span>"
    if p >= 0.7: return "<span class='status-badge badge-orange'>● En cours</span>"
    return              "<span class='status-badge badge-red'>● Sous objectif</span>"

def emoji(p):
    return "🟢" if p >= 1 else "🟠" if p >= 0.7 else "🔴"

def color_pct(p):
    return "#00C48C" if p >= 1 else "#00AEEF" if p >= 0.7 else "#FF4757"

def round_excel(x):
    return int(x + 0.5 + 1e-9)

def get_working_days():
    today = datetime.today()
    start = today.replace(day=1)
    fr = holidays.FR()
    days = pd.date_range(start, today)
    return len([d for d in days if d.weekday() < 5 and d.date() not in fr])

def ensure_energie_cols(df_pivot):
    for col in ["ELEC", "GAZ"]:
        if col not in df_pivot.columns:
            df_pivot[col] = 0
    return df_pivot

def section_label(text):
    return (
        f"<div class='section-label'>"
        f"<span class='sl-line'></span>"
        f"<span class='sl-text'>{text}</span>"
        f"<span class='sl-line'></span>"
        f"</div>"
    )

def metric_card(icon, value, label, sub="", color="blue"):
    return (
        f"<div class='metric-card {color}'>"
        f"<span class='mc-icon'>{icon}</span>"
        f"<div class='mc-value'>{value}</div>"
        f"<div class='mc-label'>{label}</div>"
        f"{'<div class=mc-sub>' + sub + '</div>' if sub else ''}"
        f"</div>"
    )

@st.cache_data
def load_data(path):
    xls = pd.ExcelFile(path)
    df = pd.read_excel(xls, "Extraction")
    code = pd.read_excel(xls, "Code")
    objectifs = pd.read_excel(xls, "Objectifs")
    return df, code, objectifs

# ================================================================
# GÉNÉRATION PNG — matplotlib (inchangé, utilisé si besoin futur)
# ================================================================
def generate_rapport_png(df_obj_render, dates):
    fournisseurs_data = []
    for _, r in df_obj_render.iterrows():
        p = r["ventes"] / r["Objectifs Total"] if r["Objectifs Total"] else 0
        fournisseurs_data.append({
            "nom": r["Fournisseur"],
            "v_elec": int(r.get("v_elec", 0)),
            "v_gaz": int(r.get("v_gaz", 0)),
            "ventes": int(r["ventes"]),
            "obj": int(r["Objectifs Total"]),
            "obj_elec": int(r.get("obj_elec", 0)),
            "obj_gaz": int(r.get("obj_gaz", 0)),
            "pct": p,
        })
    n = len(fournisseurs_data)
    fig_height = 3.5 + n * 0.52 + 4.5
    fig, axes = plt.subplots(2, 1, figsize=(13, fig_height),
                             gridspec_kw={"height_ratios": [n * 0.52 + 3.5, 4.5]},
                             facecolor="#FFFFFF")
    ax_table = axes[0]
    ax_chart = axes[1]
    ax_table.set_facecolor("#FFFFFF")
    ax_table.set_xlim(0, 1); ax_table.set_ylim(0, 1); ax_table.axis("off")
    header_rect = FancyBboxPatch((0, 0.90), 1, 0.10, boxstyle="round,pad=0.005",
                                 facecolor="#00AEEF", edgecolor="none",
                                 transform=ax_table.transAxes, clip_on=False)
    ax_table.add_patch(header_rect)
    if len(dates) == 2:
        periode_str = f"Période : {dates[0].strftime('%d/%m/%Y')} → {dates[1].strftime('%d/%m/%Y')}"
    else:
        periode_str = f"Généré le {datetime.today().strftime('%d/%m/%Y')}"
    ax_table.text(0.02, 0.945, "Rapport Ventes", transform=ax_table.transAxes,
                  fontsize=13, fontweight="bold", color="white", va="center")
    ax_table.text(0.98, 0.945, periode_str, transform=ax_table.transAxes,
                  fontsize=9, color="rgba(255,255,255,0.8)", va="center", ha="right")
    col_x = [0.01, 0.22, 0.39, 0.54, 0.69, 0.79, 0.89]
    col_labels = ["Fournisseur", "⚡ Elec", "🔥 Gaz", "🎯 Total", "Obj.", "Taux", "Progression"]
    header_y = 0.86
    for cx, cl in zip(col_x, col_labels):
        ax_table.text(cx, header_y, cl, transform=ax_table.transAxes,
                      fontsize=8, fontweight="bold", color="#334155", va="center")
    ax_table.plot([0, 1], [header_y - 0.022, header_y - 0.022],
                  color="#CBD5E1", linewidth=1, transform=ax_table.transAxes, clip_on=False)
    row_h = (0.86 - 0.05) / max(n, 1)
    for i, d in enumerate(fournisseurs_data):
        y = header_y - 0.045 - i * row_h
        if i % 2 == 0:
            ax_table.add_patch(FancyBboxPatch((0, y - row_h * 0.45), 1, row_h * 0.90,
                                              boxstyle="square,pad=0", facecolor="#F8FAFF",
                                              edgecolor="none", transform=ax_table.transAxes, clip_on=True))
        pct = d["pct"]
        cp = "#00C48C" if pct >= 1 else "#00AEEF" if pct >= 0.7 else "#FF4757"
        ax_table.text(col_x[0], y, d["nom"], transform=ax_table.transAxes,
                      fontsize=8, color="#1A3A5C", va="center", fontweight="500")
        ax_table.text(col_x[1], y, f"{d['v_elec']}/{d['obj_elec']}",
                      transform=ax_table.transAxes, fontsize=8, color="#334155", va="center")
        ax_table.text(col_x[2], y, f"{d['v_gaz']}/{d['obj_gaz']}",
                      transform=ax_table.transAxes, fontsize=8, color="#334155", va="center")
        ax_table.text(col_x[3], y, str(d['ventes']),
                      transform=ax_table.transAxes, fontsize=9, fontweight="bold",
                      color="#00AEEF", va="center")
        ax_table.text(col_x[4], y, str(d['obj']),
                      transform=ax_table.transAxes, fontsize=8, color="#64748B", va="center")
        ax_table.text(col_x[5], y, f"{pct:.0%}",
                      transform=ax_table.transAxes, fontsize=9, fontweight="bold",
                      color=cp, va="center")
        bw = 0.10; bh = row_h * 0.35; bx = col_x[6]
        ax_table.add_patch(FancyBboxPatch((bx, y - bh/2), bw, bh, boxstyle="round,pad=0.002",
                                          facecolor="#E6F4FB", edgecolor="none",
                                          transform=ax_table.transAxes, clip_on=True))
        fw = bw * min(pct, 1.0)
        if fw > 0:
            ax_table.add_patch(FancyBboxPatch((bx, y - bh/2), fw, bh, boxstyle="round,pad=0.002",
                                              facecolor=cp, edgecolor="none",
                                              transform=ax_table.transAxes, clip_on=True))
    ax_chart.set_facecolor("#FAFBFF")
    for s in ["top", "right", "left"]: ax_chart.spines[s].set_visible(False)
    ax_chart.spines["bottom"].set_color("#E6F4FB")
    noms = [d["nom"] for d in fournisseurs_data]
    ventes_vals = [d["ventes"] for d in fournisseurs_data]
    obj_vals = [d["obj"] for d in fournisseurs_data]
    y_pos = range(len(noms))
    bh2 = 0.35
    ax_chart.barh([y + bh2/2 for y in y_pos], obj_vals, height=bh2, color="#E6F4FB", zorder=2)
    colors_bars = [("#00C48C" if d["pct"] >= 1 else "#00AEEF" if d["pct"] >= 0.7 else "#00AEEF")
                   for d in fournisseurs_data]
    ax_chart.barh([y - bh2/2 for y in y_pos], ventes_vals, height=bh2, color=colors_bars, zorder=3)
    ax_chart.set_yticks(list(y_pos)); ax_chart.set_yticklabels(noms, fontsize=8)
    ax_chart.set_xlabel("Nombre de ventes", fontsize=8, color="#64748B")
    ax_chart.tick_params(axis="x", labelsize=7, colors="#64748B")
    ax_chart.tick_params(axis="y", labelsize=8, colors="#334155")
    ax_chart.set_title("Ventes vs Objectif par fournisseur", fontsize=10,
                       fontweight="bold", color="#1A3A5C", pad=8)
    ax_chart.grid(axis="x", color="#E6F4FB", linewidth=0.8, zorder=1)
    legend_patches = [mpatches.Patch(color="#00AEEF", label="Ventes"),
                      mpatches.Patch(color="#E6F4FB", label="Objectif")]
    ax_chart.legend(handles=legend_patches, fontsize=8, loc="lower right",
                    framealpha=0.9, edgecolor="#CBD5E1")
    plt.tight_layout(pad=1.2)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="#FFFFFF")
    plt.close(fig); buf.seek(0)
    return buf.getvalue()


# ================================================================
# SIDEBAR
# ================================================================
with st.sidebar:
    # Logo texte stylisé
    st.markdown("""
    <div style="padding:16px 8px 8px 8px;text-align:center;border-bottom:1px solid #DCEEF8;">
      <div style="font-size:1.4rem;font-weight:800;color:#00AEEF;letter-spacing:-0.01em;">
        ⚡ Suivi Commercial
      </div>
      <div style="font-size:0.72rem;color:#94A3B8;margin-top:2px;text-transform:uppercase;letter-spacing:0.1em;">
        Tableau de bord
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    page = st.radio("", ["📊 Dashboard", "👤 Agents", "🎯 Objectifs"], label_visibility="collapsed")

    st.markdown("---")

uploaded_file = None
if os.path.exists(SAVE_PATH):
    uploaded_file = SAVE_PATH

if uploaded_file:

    df, code, objectifs = load_data(uploaded_file)

    df["responder"] = clean_text(df["responder"])
    code.iloc[:, 0] = clean_text(code.iloc[:, 0])
    df = df.merge(
        code.rename(columns={code.columns[0]: "responder", code.columns[1]: "agent"}),
        on="responder", how="left"
    )
    df["agent"] = clean_text(df["agent"]).fillna("INCONNU")
    df["get_provider"] = clean_text(df["get_provider"])
    df["energie"] = (
        df["energie"].astype(str).str.strip().str.lower()
        .replace({"gas": "GAZ", "elec": "ELEC"}).str.upper()
    )
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    objectifs["Fournisseur"] = clean_text(objectifs["Fournisseur"])

    USER_COL = "user id"

    with st.sidebar:
        st.markdown("### 🔎 Filtres")
        agents = st.multiselect("Agents", df["agent"].unique(), df["agent"].unique())
        fournisseurs = st.multiselect("Fournisseurs", df["get_provider"].unique(), df["get_provider"].unique())
        energie = st.multiselect("Énergie", df["energie"].unique(), df["energie"].unique())
        min_d, max_d = df["date"].min(), df["date"].max()
        dates = st.date_input("Période", [min_d, max_d])

        if len(dates) == 2:
            d_start = dates[0].strftime("%d/%m/%Y")
            d_end   = dates[1].strftime("%d/%m/%Y")
            st.markdown(
                f"<div class='sb-period' style='color:#1A3A5C!important;'>📅 {d_start} &nbsp;→&nbsp; {d_end}</div>",
                unsafe_allow_html=True
            )
            period_pill = (
                f"<div class='period-pill'>📅 {d_start} → {d_end}</div>"
            )
        else:
            d_start, d_end = "", ""
            period_pill = ""

        n_agents_actifs = len(agents)
        n_fournisseurs_actifs = len(fournisseurs)
        energie_label = " · ".join(energie) if energie else "—"
        st.markdown(
            f"<div class='sb-summary' style='color:#1A3A5C!important;'>"
            f"👤 <strong>{n_agents_actifs}</strong> agent(s)<br>"
            f"🏢 <strong>{n_fournisseurs_actifs}</strong> fournisseur(s)<br>"
            f"⚡ {energie_label}"
            f"</div>",
            unsafe_allow_html=True
        )

        st.markdown("---")
        st.markdown("### 🔐 Admin")
        password = st.text_input("Mot de passe", type="password")
        is_admin = password == "hello123"
        if is_admin:
            uploaded_file_admin = st.file_uploader("Uploader fichier Excel", type=["xlsx"])
            if uploaded_file_admin:
                with open(SAVE_PATH, "wb") as f:
                    f.write(uploaded_file_admin.getbuffer())
                load_data.clear()
                st.rerun()
            if os.path.exists(SAVE_PATH):
                if st.button("🗑 Supprimer le fichier"):
                    os.remove(SAVE_PATH)
                    load_data.clear()
                    st.rerun()

    # ---- FILTRE ----
    df_filtered = df[
        df["agent"].isin(agents) &
        df["get_provider"].isin(fournisseurs) &
        df["energie"].isin(energie)
    ]
    if len(dates) == 2:
        df_filtered = df_filtered[
            (df_filtered["date"] >= pd.to_datetime(dates[0])) &
            (df_filtered["date"] <= pd.to_datetime(dates[1]))
        ]

    objectif_total = objectifs["Objectifs Total"].sum()
    jours = get_working_days()

    # ================================================================
    # PAGE DASHBOARD
    # ================================================================
    if page == "📊 Dashboard":

        st.markdown("""
        <div class='page-header'>
          <div class='page-header-left'>
            <h1>Objectifs Globaux</h1>
            <p>Suivi en temps réel des performances commerciales</p>
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(period_pill, unsafe_allow_html=True)

        # ---- KPI GLOBAUX ----
        total_ventes    = len(df_filtered)
        total_obj       = int(objectifs["Objectifs Total"].sum())
        total_obj_elec  = int(objectifs["Objectif Elec"].sum())
        total_obj_gaz   = int(objectifs["Objectif Gaz"].sum())
        v_elec_global   = len(df_filtered[df_filtered["energie"] == "ELEC"])
        v_gaz_global    = len(df_filtered[df_filtered["energie"] == "GAZ"])
        v_elec_gaz_global = v_elec_global + v_gaz_global
        obj_elec_gaz    = total_obj_elec + total_obj_gaz
        taux_global     = total_ventes / total_obj if total_obj else 0
        taux_elec       = v_elec_global / total_obj_elec if total_obj_elec else 0
        taux_gaz        = v_gaz_global / total_obj_gaz if total_obj_gaz else 0
        kpi_jour        = round(total_ventes / jours, 1) if jours else 0

        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(metric_card(
            "🎯", f"{total_ventes}/{total_obj}",
            "Ventes totales / Objectif",
            sub=f"Taux global : {taux_global:.0%}",
            color="blue" if taux_global >= 0.7 else "red"
        ), unsafe_allow_html=True)
        c2.markdown(metric_card(
            "⚡", f"{v_elec_global}/{total_obj_elec}",
            "Électricité",
            sub=f"Taux : {taux_elec:.0%}",
            color="blue"
        ), unsafe_allow_html=True)
        c3.markdown(metric_card(
            "🔥", f"{v_gaz_global}/{total_obj_gaz}",
            "Gaz",
            sub=f"Taux : {taux_gaz:.0%}",
            color="orange"
        ), unsafe_allow_html=True)
        c4.markdown(metric_card(
            "📅", str(kpi_jour),
            "Ventes / Jour ouvré",
            sub=f"{jours} jours ouvrés ce mois",
            color="green" if kpi_jour > 0 else "red"
        ), unsafe_allow_html=True)

        c5, c6, c7, c8 = st.columns(4)
        c5.markdown(metric_card(
            "📊", f"{taux_global:.0%}",
            "% Atteinte globale",
            color="green" if taux_global >= 1 else ("orange" if taux_global >= 0.7 else "red")
        ), unsafe_allow_html=True)
        c6.markdown(metric_card(
            "⚡", f"{taux_elec:.0%}",
            "% Atteinte Elec",
            color="green" if taux_elec >= 1 else ("orange" if taux_elec >= 0.7 else "red")
        ), unsafe_allow_html=True)
        c7.markdown(metric_card(
            "🔥", f"{taux_gaz:.0%}",
            "% Atteinte Gaz",
            color="green" if taux_gaz >= 1 else ("orange" if taux_gaz >= 0.7 else "red")
        ), unsafe_allow_html=True)
        c8.markdown(metric_card(
            "🏢", str(n_fournisseurs_actifs),
            "Fournisseurs actifs",
            sub=f"{n_agents_actifs} agents suivis",
            color="blue"
        ), unsafe_allow_html=True)

        # ---- TABLEAU FOURNISSEURS ----
        st.markdown(section_label("Détail par fournisseur"), unsafe_allow_html=True)

        ventes = df_filtered.groupby("get_provider").size().reset_index(name="ventes")
        df_obj = objectifs.merge(
            ventes, left_on="Fournisseur", right_on="get_provider", how="left"
        ).fillna(0)
        df_obj = df_obj.sort_values("Objectifs Total", ascending=False)

        ventes_e = df_filtered.groupby(["get_provider", "energie"]).size().unstack(fill_value=0).reset_index()
        ventes_e = ensure_energie_cols(ventes_e)
        ventes_e = ventes_e.rename(columns={"get_provider": "Fournisseur", "ELEC": "v_elec", "GAZ": "v_gaz"})
        df_obj = df_obj.merge(ventes_e[["Fournisseur", "v_elec", "v_gaz"]], on="Fournisseur", how="left").fillna(0)

        df_obj_export = df_obj.copy()
        for idx, row in df_obj.iterrows():
            obj_row = objectifs[objectifs["Fournisseur"] == row["Fournisseur"]]
            df_obj_export.at[idx, "obj_elec"] = obj_row["Objectif Elec"].sum()
            df_obj_export.at[idx, "obj_gaz"]  = obj_row["Objectif Gaz"].sum()

        n_rows = len(df_obj)
        table_html_rows = ""
        for i, (_, r) in enumerate(df_obj.iterrows()):
            obj_row  = objectifs[objectifs["Fournisseur"] == r["Fournisseur"]]
            obj_elec = int(obj_row["Objectif Elec"].sum())
            obj_gaz  = int(obj_row["Objectif Gaz"].sum())
            v_elec   = int(r.get("v_elec", 0))
            v_gaz    = int(r.get("v_gaz", 0))
            p        = r["ventes"] / r["Objectifs Total"] if r["Objectifs Total"] else 0
            cp       = "#00C48C" if p >= 1 else "#00AEEF" if p >= 0.7 else "#FF4757"
            cp_bg    = "#DCFCE7" if p >= 1 else "#FFF7ED" if p >= 0.7 else "#FEE2E2"
            pct_fill = min(p * 100, 100)
            bg       = "#F8FAFF" if i % 2 == 0 else "#FFFFFF"

            table_html_rows += f"""
            <tr style="background:{bg};transition:background 0.15s;" onmouseover="this.style.background='#E6F4FB'" onmouseout="this.style.background='{bg}'">
              <td style="padding:7px 12px;font-weight:600;color:#1A3A5C;font-size:13px;">{r['Fournisseur']}</td>
              <td style="padding:7px 12px;text-align:center;color:#334155;font-size:13px;">⚡ <strong>{v_elec}</strong><span style='color:#94A3B8'>/{obj_elec}</span></td>
              <td style="padding:7px 12px;text-align:center;color:#334155;font-size:13px;">🔥 <strong>{v_gaz}</strong><span style='color:#94A3B8'>/{obj_gaz}</span></td>
              <td style="padding:7px 12px;text-align:center;font-size:14px;"><strong style='color:#00AEEF'>{int(r['ventes'])}</strong><span style='color:#94A3B8;font-size:12px'>/{int(r['Objectifs Total'])}</span></td>
              <td style="padding:7px 12px;text-align:center;">
                <span style="background:{cp_bg};color:{cp};padding:3px 10px;border-radius:12px;font-size:12px;font-weight:700;">{p:.0%}</span>
              </td>
              <td style="padding:7px 14px;width:140px;">
                <div style="background:#E6F4FB;border-radius:6px;height:8px;width:100%;overflow:hidden;">
                  <div style="background:linear-gradient(90deg,{cp},{cp}cc);border-radius:6px;height:8px;width:{pct_fill:.1f}%;transition:width 0.4s;"></div>
                </div>
              </td>
            </tr>"""

        fname = f"rapport_{datetime.today().strftime('%Y%m%d')}.png"
        show_buttons = "flex" if is_admin else "none"

        html2canvas_component = f"""
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
  * {{ box-sizing:border-box; }}
  body {{ margin:0; padding:0; background:#F4F6FA; font-family:'Inter',sans-serif; }}
  .btn-bar {{ display:{show_buttons}; gap:8px; justify-content:flex-end; margin-bottom:10px; }}
  .btn-x {{ padding:7px 16px; border:none; border-radius:8px; cursor:pointer; font-size:13px; font-weight:600; transition:opacity .15s; font-family:'Inter',sans-serif; }}
  .btn-x:hover {{ opacity:0.85; }}
  .btn-dl {{ background:linear-gradient(135deg,#00AEEF,#33C1F3); color:#fff; }}
  .btn-cp {{ background:#FFFFFF; color:#00AEEF; border:1.5px solid #00AEEF; }}
</style>

<div class="btn-bar">
  <button class="btn-x btn-cp" onclick="doCapture('copy')">📋 Copier</button>
  <button class="btn-x btn-dl" onclick="doCapture('download')">⬇️ Télécharger PNG</button>
</div>

<div id="rapport-table" style="background:#FFFFFF;border-radius:14px;overflow:hidden;border:1px solid #E6F4FB;box-shadow:0 4px 20px rgba(14,74,203,0.08);">
  <div style="background:linear-gradient(135deg,#005F8E,#00AEEF);padding:14px 18px;display:flex;justify-content:space-between;align-items:center;">
    <div>
      <div style="color:#fff;font-size:11px;opacity:0.7;text-transform:uppercase;letter-spacing:0.1em;font-weight:600;font-family:'Inter',sans-serif;">Rapport Ventes</div>
      <div style="color:#fff;font-size:14px;font-weight:700;margin-top:2px;font-family:'Inter',sans-serif;">Détail par fournisseur</div>
    </div>
    <div style="text-align:right;">
      <div style="color:rgba(255,255,255,0.7);font-size:11px;font-family:'Inter',sans-serif;">📅 {d_start} → {d_end}</div>
      <div style="color:rgba(255,255,255,0.5);font-size:10px;margin-top:2px;font-family:'Inter',sans-serif;">Généré le {datetime.today().strftime('%d/%m/%Y à %H:%M')}</div>
    </div>
  </div>
  <table style="width:100%;border-collapse:collapse;font-family:'Inter',sans-serif;">
    <thead>
      <tr style="background:#F4F6FA;border-bottom:2px solid #E6F4FB;">
        <th style="padding:9px 12px;text-align:left;color:#64748B;font-size:11px;text-transform:uppercase;letter-spacing:0.06em;font-weight:700;">Fournisseur</th>
        <th style="padding:9px 12px;text-align:center;color:#64748B;font-size:11px;text-transform:uppercase;font-weight:700;">Elec</th>
        <th style="padding:9px 12px;text-align:center;color:#64748B;font-size:11px;text-transform:uppercase;font-weight:700;">Gaz</th>
        <th style="padding:9px 12px;text-align:center;color:#64748B;font-size:11px;text-transform:uppercase;font-weight:700;">Total</th>
        <th style="padding:9px 12px;text-align:center;color:#64748B;font-size:11px;text-transform:uppercase;font-weight:700;">Taux</th>
        <th style="padding:9px 12px;text-align:center;color:#64748B;font-size:11px;text-transform:uppercase;font-weight:700;">Progression</th>
      </tr>
    </thead>
    <tbody>{table_html_rows}</tbody>
  </table>
</div>

<script>
function doCapture(action) {{
  const el = document.getElementById('rapport-table');
  html2canvas(el, {{ backgroundColor:'#FFFFFF', scale:2, useCORS:true, logging:false }})
    .then(canvas => {{
      if (action === 'download') {{
        const a = document.createElement('a');
        a.href = canvas.toDataURL('image/png');
        a.download = '{fname}';
        a.click();
      }} else {{
        canvas.toBlob(blob => {{
          navigator.clipboard.write([new ClipboardItem({{'image/png': blob}})])
            .then(() => {{
              const btn = document.querySelector('.btn-cp');
              const orig = btn.textContent;
              btn.textContent = '✅ Copié !';
              btn.style.background = '#DCFCE7';
              btn.style.color = '#16A34A';
              btn.style.borderColor = '#16A34A';
              setTimeout(() => {{
                btn.textContent = orig;
                btn.style.background = '';
                btn.style.color = '';
                btn.style.borderColor = '';
              }}, 2500);
            }})
            .catch(() => {{
              const url = URL.createObjectURL(blob);
              window.open(url, '_blank');
            }});
        }});
      }}
    }});
}}
</script>"""

        components.html(html2canvas_component, height=n_rows * 40 + 180, scrolling=False)

    # ================================================================
    # PAGE AGENTS
    # ================================================================
    elif page == "👤 Agents":

        st.markdown("""
        <div class='page-header'>
          <div class='page-header-left'>
            <h1>Performance Agents</h1>
            <p>Classement et suivi individuel de l'équipe</p>
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(period_pill, unsafe_allow_html=True)

        # Calculs — inchangés
        obj_agent = math.ceil(185 * 0.75)

        ventes_agent = df_filtered.groupby("agent").size().reset_index(name="ventes")
        ventes_energie = (
            df_filtered.groupby(["agent", "energie"]).size()
            .unstack(fill_value=0).reset_index()
        )
        ventes_energie = ensure_energie_cols(ventes_energie)
        ventes_agent = ventes_agent.merge(ventes_energie, on="agent", how="left").fillna(0)
        ventes_agent["taux"] = ventes_agent["ventes"] / obj_agent
        ventes_agent["kpi"]  = ventes_agent["ventes"] / jours if jours else 0
        ventes_agent = ventes_agent.sort_values("taux", ascending=False)

        total_ventes_agents = int(ventes_agent["ventes"].sum())
        meilleur = ventes_agent.iloc[0]["agent"] if not ventes_agent.empty else "—"
        meilleur_taux = ventes_agent.iloc[0]["taux"] if not ventes_agent.empty else 0
        n_vert = len(ventes_agent[ventes_agent["taux"] >= 1])
        n_orange = len(ventes_agent[(ventes_agent["taux"] >= 0.7) & (ventes_agent["taux"] < 1)])
        n_rouge = len(ventes_agent[ventes_agent["taux"] < 0.7])

        # KPI cards
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(metric_card("👥", str(total_ventes_agents), "Ventes équipe",
                                sub=f"Objectif : {obj_agent} / agent", color="blue"), unsafe_allow_html=True)
        c2.markdown(metric_card("🏆", meilleur, "Meilleur agent",
                                sub=f"Taux : {meilleur_taux:.0%}", color="green"), unsafe_allow_html=True)
        c3.markdown(metric_card("📅", str(jours), "Jours ouvrés",
                                sub=f"Mois en cours", color="blue"), unsafe_allow_html=True)
        c4.markdown(metric_card("📈", f"{round(total_ventes_agents/jours,1) if jours else 0}/J",
                                "Rythme équipe",
                                sub=f"🟢 {n_vert}  🟠 {n_orange}  🔴 {n_rouge}", color="orange"), unsafe_allow_html=True)

        st.markdown(section_label("Classement des agents"), unsafe_allow_html=True)

        BADGES = {0: "🥇", 1: "🥈", 2: "🥉"}

        for i, (_, r) in enumerate(ventes_agent.iterrows()):
            v_total = int(r["ventes"])
            v_elec  = int(r["ELEC"])
            v_gaz   = int(r["GAZ"])
            taux    = r["taux"]
            kpi_j   = round(r["kpi"], 1)
            badge   = BADGES.get(i, f"#{i+1}")
            cp      = color_pct(taux)
            sb      = status_badge(taux)

            with st.container():
                st.markdown(f"<div class='provider-row'>", unsafe_allow_html=True)
                c1, c2, c3, c4, c5 = st.columns([1, 3, 5, 4, 2])
                c1.markdown(f"<div style='font-size:1.2rem;text-align:center;padding-top:4px'>{badge}</div>",
                            unsafe_allow_html=True)
                c2.markdown(
                    f"<div style='font-weight:700;color:#1A3A5C;font-size:0.9rem;padding-top:6px'>{r['agent']}</div>",
                    unsafe_allow_html=True
                )
                c3.progress(min(taux, 1.0))
                c4.markdown(
                    f"<div style='font-size:0.85rem;color:#334155;padding-top:4px'>"
                    f"⚡ <strong>{v_elec}</strong> &nbsp; 🔥 <strong>{v_gaz}</strong>"
                    f" &nbsp;&nbsp; 🎯 <strong style='color:#1AABDB'>{v_total}</strong>"
                    f"<span style='color:#94A3B8'>/{obj_agent}</span>"
                    f" &nbsp; <strong style='color:{cp}'>{taux:.0%}</strong>"
                    f" &nbsp; {sb}"
                    f"</div>",
                    unsafe_allow_html=True
                )
                c5.markdown(
                    f"<div style='font-size:0.82rem;color:#64748B;text-align:center;padding-top:4px'>"
                    f"📅 <strong>{kpi_j}</strong>/J</div>",
                    unsafe_allow_html=True
                )
                st.markdown("</div>", unsafe_allow_html=True)

    # ================================================================
    # PAGE OBJECTIFS
    # ================================================================
    elif page == "🎯 Objectifs":

        st.markdown("""
        <div class='page-header'>
          <div class='page-header-left'>
            <h1>Performance Détaillée</h1>
            <p>Suivi individuel par agent et fournisseur</p>
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(period_pill, unsafe_allow_html=True)

        colA, colB = st.columns([1, 2])
        heures = colA.number_input("⏱ Heures travaillées", value=185.0, step=1.0)
        agent  = colB.selectbox("👤 Agent", df_filtered["agent"].unique())

        df_agent    = df_filtered[df_filtered["agent"] == agent]
        obj_agent   = round_excel(heures * 0.75)
        ventes_total = len(df_agent)
        taux         = ventes_total / obj_agent if obj_agent else 0
        v_elec_agent = len(df_agent[df_agent["energie"] == "ELEC"])
        v_gaz_agent  = len(df_agent[df_agent["energie"] == "GAZ"])
        kpi_j_agent  = round(ventes_total / jours, 1) if jours else 0
        cp           = color_pct(taux)

        # Cards agent
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(metric_card("🎯", f"{ventes_total}/{obj_agent}", "Ventes / Objectif",
                                sub=f"Taux : {taux:.0%}",
                                color="green" if taux >= 1 else ("orange" if taux >= 0.7 else "red")),
                    unsafe_allow_html=True)
        c2.markdown(metric_card("⚡", str(v_elec_agent), "Électricité",
                                sub=f"sur {ventes_total} ventes", color="blue"), unsafe_allow_html=True)
        c3.markdown(metric_card("🔥", str(v_gaz_agent), "Gaz",
                                sub=f"sur {ventes_total} ventes", color="orange"), unsafe_allow_html=True)
        c4.markdown(metric_card("📅", f"{kpi_j_agent}/J", "Rythme",
                                sub=f"{jours} jours ouvrés", color="blue"), unsafe_allow_html=True)

        # Bloc récap agent
        st.markdown(
            f"<div class='agent-recap'>"
            f"<h2>{agent}</h2>"
            f"<div style='margin-bottom:8px'>{status_badge(taux)}</div>",
            unsafe_allow_html=True
        )
        st.progress(min(taux, 1.0))
        st.markdown(
            f"<div style='margin-top:6px;font-size:0.9rem;color:#64748B'>"
            f"<strong style='color:{cp}'>{ventes_total}</strong> ventes "
            f"sur <strong>{obj_agent}</strong> objectif "
            f"— <strong style='color:{cp}'>{taux:.0%}</strong>"
            f"</div></div>",
            unsafe_allow_html=True
        )

        st.markdown(section_label("Détail par fournisseur"), unsafe_allow_html=True)

        special = ["HOMESERVE", "FREE"]

        for f in objectifs["Fournisseur"].dropna().unique():
            if f in special:
                continue
            df_f    = df_agent[df_agent["get_provider"] == f]
            obj_row = objectifs[objectifs["Fournisseur"] == f]
            obj_total_f = round_excel(heures * 0.75 * (obj_row["Objectifs Total"].sum() / objectif_total))
            obj_elec_f  = round_excel(heures * 0.75 * (obj_row["Objectif Elec"].sum() / objectif_total))
            obj_gaz_f   = round_excel(heures * 0.75 * (obj_row["Objectif Gaz"].sum() / objectif_total))
            v_total = len(df_f)
            v_elec  = len(df_f[df_f["energie"] == "ELEC"])
            v_gaz   = len(df_f[df_f["energie"] == "GAZ"])
            p       = v_total / obj_total_f if obj_total_f else 0
            cp_f    = color_pct(p)

            with st.container():
                st.markdown("<div class='provider-row'>", unsafe_allow_html=True)
                c1, c2, c3 = st.columns([2, 4, 5])
                c1.markdown(
                    f"<div style='font-weight:700;color:#1A3A5C;font-size:0.88rem;padding-top:6px'>{f}</div>"
                    f"<div style='margin-top:3px'>{status_badge(p)}</div>",
                    unsafe_allow_html=True
                )
                c2.progress(min(p, 1.0))
                c3.markdown(
                    f"<div style='font-size:0.83rem;color:#334155;padding-top:4px'>"
                    f"⚡ <strong>{v_elec}</strong><span style='color:#94A3B8'>/{obj_elec_f}</span>"
                    f" &nbsp; 🔥 <strong>{v_gaz}</strong><span style='color:#94A3B8'>/{obj_gaz_f}</span>"
                    f" &nbsp; 🎯 <strong style='color:{cp_f}'>{v_total}</strong>"
                    f"<span style='color:#94A3B8'>/{obj_total_f}</span>"
                    f" &nbsp; <strong style='color:{cp_f}'>{p:.0%}</strong>"
                    f"</div>",
                    unsafe_allow_html=True
                )
                st.markdown("</div>", unsafe_allow_html=True)

else:
    # Écran d'accueil sans fichier
    st.markdown("""
    <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
                min-height:60vh;text-align:center;padding:40px;">
      <div style="font-size:3rem;margin-bottom:16px;">⚡</div>
      <h1 style="font-size:1.8rem;font-weight:800;color:#1A3A5C;margin-bottom:8px;">
        Tableau de bord commercial
      </h1>
      <p style="color:#64748B;font-size:1rem;max-width:400px;line-height:1.6;">
        Connectez-vous en tant qu'administrateur dans la barre latérale
        pour charger le fichier de données.
      </p>
      <div style="margin-top:24px;background:#E6F4FB;border-radius:12px;padding:16px 24px;
                  color:#00AEEF;font-size:0.85rem;font-weight:600;">
        🔐 Panneau Admin → dans la sidebar
      </div>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🔐 Admin")
        password = st.text_input("Mot de passe", type="password")
        is_admin = password == "hello123"
        if is_admin:
            uploaded_file_admin = st.file_uploader("Uploader fichier Excel", type=["xlsx"])
            if uploaded_file_admin:
                with open(SAVE_PATH, "wb") as f:
                    f.write(uploaded_file_admin.getbuffer())
                st.rerun()
