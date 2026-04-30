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

st.set_page_config(page_title="Dashboard", layout="wide")

# ================================================================
# CSS
# ================================================================
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
.metric-card {
    background: linear-gradient(135deg, #F0F9FF 0%, #E0F2FE 100%);
    border: 1px solid #BAE6FD;
    border-radius: 12px;
    padding: 14px 16px;
    text-align: center;
    margin-bottom: 8px;
}
.metric-card .metric-value {
    font-size: 1.6rem;
    font-weight: 700;
    color: #0369A1;
    line-height: 1.2;
}
.metric-card .metric-label {
    font-size: 0.75rem;
    color: #64748B;
    margin-top: 4px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.agent-row {
    background-color: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 6px 12px;
    margin-bottom: 4px;
}
.agent-row-alt {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 6px 12px;
    margin-bottom: 4px;
}
.top-badge {
    font-size: 1.1rem;
    font-weight: 700;
    display: inline-block;
    margin-right: 6px;
}
.period-banner {
    background-color: #EFF6FF;
    border-left: 4px solid #3B82F6;
    border-radius: 0 8px 8px 0;
    padding: 8px 16px;
    margin-bottom: 16px;
    color: #1E40AF;
    font-size: 0.9rem;
}
.section-title {
    font-size: 0.85rem;
    font-weight: 600;
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 4px;
    margin-top: 12px;
}
.fournisseur-row {
    border-bottom: 1px solid #F1F5F9;
    padding: 3px 0;
}
.fournisseur-row:last-child {
    border-bottom: none;
}
.filter-summary {
    background-color: #DBEAFE;
    border-radius: 8px;
    padding: 10px 12px;
    font-size: 0.8rem;
    color: #1E3A8A;
    margin-top: 8px;
}
</style>
""", unsafe_allow_html=True)

SAVE_PATH = "last_uploaded.xlsx"

# ================================================================
# UTILS
# ================================================================
def clean_text(col):
    return col.astype(str).str.strip().str.replace('"','').str.replace("'","").str.upper()

def emoji(p):
    return "🟢" if p >= 1 else "🟠" if p >= 0.7 else "🔴"

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

@st.cache_data
def load_data(path):
    xls = pd.ExcelFile(path)
    df = pd.read_excel(xls, "Extraction")
    code = pd.read_excel(xls, "Code")
    objectifs = pd.read_excel(xls, "Objectifs")
    return df, code, objectifs

# ================================================================
# GÉNÉRATION PNG RAPPORT
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
    fig, axes = plt.subplots(
        2, 1,
        figsize=(13, fig_height),
        gridspec_kw={"height_ratios": [n * 0.52 + 3.5, 4.5]},
        facecolor="#FFFFFF"
    )
    ax_table = axes[0]
    ax_chart = axes[1]

    # Header
    ax_table.set_facecolor("#FFFFFF")
    ax_table.set_xlim(0, 1)
    ax_table.set_ylim(0, 1)
    ax_table.axis("off")

    header_rect = FancyBboxPatch(
        (0, 0.90), 1, 0.10,
        boxstyle="round,pad=0.005",
        facecolor="#0F8BC6", edgecolor="none",
        transform=ax_table.transAxes, clip_on=False
    )
    ax_table.add_patch(header_rect)
    ax_table.text(0.02, 0.945, "Dashboard", transform=ax_table.transAxes,
                  fontsize=15, fontweight="bold", color="white", va="center")

    if len(dates) == 2:
        periode_str = f"Période : {dates[0].strftime('%d/%m/%Y')} → {dates[1].strftime('%d/%m/%Y')}"
    else:
        periode_str = f"Généré le {datetime.today().strftime('%d/%m/%Y')}"

    ax_table.text(0.98, 0.945, periode_str, transform=ax_table.transAxes,
                  fontsize=9, color="white", va="center", ha="right")

    col_x = [0.01, 0.22, 0.39, 0.54, 0.69, 0.79, 0.89]
    col_labels = ["Fournisseur", "⚡ Elec", "🔥 Gaz", "🎯 Total", "Obj", "Taux", "Barre"]
    header_y = 0.86

    for cx, cl in zip(col_x, col_labels):
        ax_table.text(cx, header_y, cl, transform=ax_table.transAxes,
                      fontsize=8.5, fontweight="bold", color="#334155", va="center")

    ax_table.plot(
        [0, 1], [header_y - 0.022, header_y - 0.022],
        color="#CBD5E1", linewidth=1, transform=ax_table.transAxes, clip_on=False
    )

    row_h = (0.86 - 0.05) / max(n, 1)

    for i, d in enumerate(fournisseurs_data):
        y = header_y - 0.045 - i * row_h
        if i % 2 == 0:
            bg = FancyBboxPatch(
                (0, y - row_h * 0.45), 1, row_h * 0.90,
                boxstyle="square,pad=0",
                facecolor="#F8FAFC", edgecolor="none",
                transform=ax_table.transAxes, clip_on=True
            )
            ax_table.add_patch(bg)

        pct = d["pct"]
        color_pct = "#16A34A" if pct >= 1 else "#EA580C" if pct >= 0.7 else "#DC2626"

        ax_table.text(col_x[0], y, d["nom"], transform=ax_table.transAxes,
                      fontsize=8, color="#1E293B", va="center", fontweight="500")
        ax_table.text(col_x[1], y, f"{d['v_elec']}/{d['obj_elec']}",
                      transform=ax_table.transAxes, fontsize=8, color="#334155", va="center")
        ax_table.text(col_x[2], y, f"{d['v_gaz']}/{d['obj_gaz']}",
                      transform=ax_table.transAxes, fontsize=8, color="#334155", va="center")
        ax_table.text(col_x[3], y, f"{d['ventes']}",
                      transform=ax_table.transAxes, fontsize=8.5, fontweight="bold",
                      color="#0F172A", va="center")
        ax_table.text(col_x[4], y, f"{d['obj']}",
                      transform=ax_table.transAxes, fontsize=8, color="#64748B", va="center")
        ax_table.text(col_x[5], y, f"{pct:.0%}",
                      transform=ax_table.transAxes, fontsize=9, fontweight="bold",
                      color=color_pct, va="center")

        bar_x_start = col_x[6]
        bar_width = 0.10
        bar_h = row_h * 0.35
        ax_table.add_patch(FancyBboxPatch(
            (bar_x_start, y - bar_h / 2), bar_width, bar_h,
            boxstyle="round,pad=0.002", facecolor="#E2E8F0", edgecolor="none",
            transform=ax_table.transAxes, clip_on=True
        ))
        fill_w = bar_width * min(pct, 1.0)
        if fill_w > 0:
            ax_table.add_patch(FancyBboxPatch(
                (bar_x_start, y - bar_h / 2), fill_w, bar_h,
                boxstyle="round,pad=0.002", facecolor=color_pct, edgecolor="none",
                transform=ax_table.transAxes, clip_on=True
            ))

    # Graphique
    ax_chart.set_facecolor("#FAFAFA")
    ax_chart.spines["top"].set_visible(False)
    ax_chart.spines["right"].set_visible(False)
    ax_chart.spines["left"].set_color("#E2E8F0")
    ax_chart.spines["bottom"].set_color("#E2E8F0")

    noms = [d["nom"] for d in fournisseurs_data]
    ventes_vals = [d["ventes"] for d in fournisseurs_data]
    obj_vals = [d["obj"] for d in fournisseurs_data]
    y_pos = range(len(noms))
    bar_h_chart = 0.35

    ax_chart.barh([y + bar_h_chart / 2 for y in y_pos], obj_vals,
                  height=bar_h_chart, color="#E2E8F0", label="Objectif", zorder=2)

    colors_bars = [
        "#16A34A" if d["pct"] >= 1 else "#0F8BC6" if d["pct"] >= 0.7 else "#F97316"
        for d in fournisseurs_data
    ]
    ax_chart.barh([y - bar_h_chart / 2 for y in y_pos], ventes_vals,
                  height=bar_h_chart, color=colors_bars, label="Ventes", zorder=3)

    ax_chart.set_yticks(list(y_pos))
    ax_chart.set_yticklabels(noms, fontsize=8)
    ax_chart.set_xlabel("Nombre de ventes", fontsize=8, color="#64748B")
    ax_chart.tick_params(axis="x", labelsize=7, colors="#64748B")
    ax_chart.tick_params(axis="y", labelsize=8, colors="#334155")
    ax_chart.set_title("Ventes vs Objectif par fournisseur", fontsize=10,
                       fontweight="bold", color="#1E293B", pad=8)
    ax_chart.grid(axis="x", color="#E2E8F0", linewidth=0.8, zorder=1)

    legend_patches = [
        mpatches.Patch(color="#0F8BC6", label="Ventes"),
        mpatches.Patch(color="#E2E8F0", label="Objectif"),
    ]
    ax_chart.legend(handles=legend_patches, fontsize=8, loc="lower right",
                    framealpha=0.8, edgecolor="#CBD5E1")

    plt.tight_layout(pad=1.2)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="#FFFFFF")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


# ================================================================
# HEADER
# ================================================================
st.title("Dashboard")
st.markdown("<br>", unsafe_allow_html=True)

# ================================================================
# SIDEBAR — Navigation
# ================================================================
page = st.sidebar.radio("Navigation", ["📊 Dashboard", "👤 Agents", "🎯 Objectifs"])
st.sidebar.markdown("---")

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

    # ---- FILTRES ----
    st.sidebar.markdown("### 🔎 Filtres")
    agents = st.sidebar.multiselect("Agents", df["agent"].unique(), df["agent"].unique())
    fournisseurs = st.sidebar.multiselect("Fournisseurs", df["get_provider"].unique(), df["get_provider"].unique())
    energie = st.sidebar.multiselect("Énergie", df["energie"].unique(), df["energie"].unique())
    min_d, max_d = df["date"].min(), df["date"].max()
    dates = st.sidebar.date_input("Période", [min_d, max_d])

    # ---- MODIFICATION 1 : BANNIÈRE PÉRIODE juste après les filtres ----
    if len(dates) == 2:
        d_start = dates[0].strftime("%d/%m/%Y")
        d_end = dates[1].strftime("%d/%m/%Y")
        st.sidebar.markdown(
            f"<div class='period-banner' style='margin-top:8px;'>"
            f"📅 <strong>{d_start}</strong> → <strong>{d_end}</strong>"
            f"</div>",
            unsafe_allow_html=True
        )
        period_html = (
            f"<div class='period-banner'>📅 Période active : "
            f"<strong>{d_start}</strong> → <strong>{d_end}</strong></div>"
        )
    else:
        d_start, d_end = "", ""
        period_html = ""

    # ---- RÉSUMÉ FILTRES ----
    n_agents_actifs = len(agents)
    n_fournisseurs_actifs = len(fournisseurs)
    energie_label = " + ".join(energie) if energie else "—"
    st.sidebar.markdown(
        f"<div class='filter-summary'>"
        f"👤 {n_agents_actifs} agent(s)<br>"
        f"🏢 {n_fournisseurs_actifs} fournisseur(s)<br>"
        f"⚡ {energie_label}"
        f"</div>",
        unsafe_allow_html=True
    )

    # ---- MODIFICATION 1 : ADMIN tout en bas ----
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔐 Admin")
    password = st.sidebar.text_input("Mot de passe", type="password")
    is_admin = password == "hello123"
    if is_admin:
        uploaded_file_admin = st.sidebar.file_uploader("Uploader fichier Excel", type=["xlsx"])
        if uploaded_file_admin:
            with open(SAVE_PATH, "wb") as f:
                f.write(uploaded_file_admin.getbuffer())
            load_data.clear()
            st.rerun()
        if os.path.exists(SAVE_PATH):
            if st.sidebar.button("🗑 Supprimer"):
                os.remove(SAVE_PATH)
                load_data.clear()
                st.rerun()
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

    # ================================================================
    # PAGE DASHBOARD
    # ================================================================
    if page == "📊 Dashboard":

        st.header("🏢 Objectifs Globaux")
        st.markdown(period_html, unsafe_allow_html=True)

        # ---- MODIFICATION 2 : 6 cartes métriques ----
        total_ventes = len(df_filtered)
        total_obj = int(objectifs["Objectifs Total"].sum())
        total_obj_elec = int(objectifs["Objectif Elec"].sum())
        total_obj_gaz = int(objectifs["Objectif Gaz"].sum())

        v_elec_global = len(df_filtered[df_filtered["energie"] == "ELEC"])
        v_gaz_global = len(df_filtered[df_filtered["energie"] == "GAZ"])
        v_elec_gaz_global = v_elec_global + v_gaz_global
        obj_elec_gaz = total_obj_elec + total_obj_gaz

        taux_global = total_ventes / total_obj if total_obj else 0
        taux_elec = v_elec_global / total_obj_elec if total_obj_elec else 0
        taux_gaz = v_gaz_global / total_obj_gaz if total_obj_gaz else 0

        c1, c2, c3 = st.columns(3)
        c4, c5, c6 = st.columns(3)

        c1.markdown(
            f"<div class='metric-card'>"
            f"<div class='metric-value'>{v_elec_gaz_global}/{obj_elec_gaz}</div>"
            f"<div class='metric-label'>Ventes (Elec+Gaz) / Objectif</div>"
            f"</div>", unsafe_allow_html=True
        )
        c2.markdown(
            f"<div class='metric-card'>"
            f"<div class='metric-value'>⚡ {v_elec_global}/{total_obj_elec}</div>"
            f"<div class='metric-label'>Ventes Elec / Objectif Elec</div>"
            f"</div>", unsafe_allow_html=True
        )
        c3.markdown(
            f"<div class='metric-card'>"
            f"<div class='metric-value'>🔥 {v_gaz_global}/{total_obj_gaz}</div>"
            f"<div class='metric-label'>Ventes Gaz / Objectif Gaz</div>"
            f"</div>", unsafe_allow_html=True
        )
        # Rangée du bas alignée sous la rangée du haut : Total | Elec | Gaz
        c4.markdown(
            f"<div class='metric-card'>"
            f"<div class='metric-value'>{emoji(taux_global)} {taux_global:.0%}</div>"
            f"<div class='metric-label'>% Total</div>"
            f"</div>", unsafe_allow_html=True
        )
        c5.markdown(
            f"<div class='metric-card'>"
            f"<div class='metric-value'>{emoji(taux_elec)} {taux_elec:.0%}</div>"
            f"<div class='metric-label'>% Elec</div>"
            f"</div>", unsafe_allow_html=True
        )
        c6.markdown(
            f"<div class='metric-card'>"
            f"<div class='metric-value'>{emoji(taux_gaz)} {taux_gaz:.0%}</div>"
            f"<div class='metric-label'>% Gaz</div>"
            f"</div>", unsafe_allow_html=True
        )

        # ---- MODIFICATION 3 : Tableau fournisseurs exportable ----
        st.markdown("<div class='section-title'>Détail par fournisseur</div>", unsafe_allow_html=True)

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
            df_obj_export.at[idx, "obj_gaz"] = obj_row["Objectif Gaz"].sum()

        # Construction des lignes HTML du tableau
        n_rows = len(df_obj)
        table_html_rows = ""
        for i, (_, r) in enumerate(df_obj.iterrows()):
            obj_row = objectifs[objectifs["Fournisseur"] == r["Fournisseur"]]
            obj_elec = int(obj_row["Objectif Elec"].sum())
            obj_gaz = int(obj_row["Objectif Gaz"].sum())
            v_elec = int(r.get("v_elec", 0))
            v_gaz = int(r.get("v_gaz", 0))
            p = r["ventes"] / r["Objectifs Total"] if r["Objectifs Total"] else 0
            color = "#16A34A" if p >= 1 else "#EA580C" if p >= 0.7 else "#DC2626"
            pct_fill = min(p * 100, 100)
            bg = "#F8FAFC" if i % 2 == 0 else "#FFFFFF"

            table_html_rows += f"""
            <tr style="background:{bg};">
              <td style="padding:5px 10px;font-weight:500;color:#1E293B;">{r['Fournisseur']}</td>
              <td style="padding:5px 10px;text-align:center;color:#334155;">⚡ {v_elec}/{obj_elec}</td>
              <td style="padding:5px 10px;text-align:center;color:#334155;">🔥 {v_gaz}/{obj_gaz}</td>
              <td style="padding:5px 10px;text-align:center;font-weight:700;color:#0F172A;">{int(r['ventes'])}/{int(r['Objectifs Total'])}</td>
              <td style="padding:5px 10px;text-align:center;font-weight:700;color:{color};">{p:.0%}</td>
              <td style="padding:5px 10px;width:120px;">
                <div style="background:#E2E8F0;border-radius:6px;height:10px;width:100%;">
                  <div style="background:{color};border-radius:6px;height:10px;width:{pct_fill:.1f}%;"></div>
                </div>
              </td>
            </tr>"""

        # Boutons export — visibles uniquement pour l'admin
        fname = f"rapport_{datetime.today().strftime('%Y%m%d')}.png"
        show_buttons = "flex" if is_admin else "none"
        html2canvas_component = f"""
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>

<style>
  body {{ margin:0; padding:0; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; }}
  .btn-bar {{
    display:{show_buttons}; gap:8px; justify-content:flex-end;
    margin-bottom:8px;
  }}
  .btn-export {{
    padding:7px 16px; border:none; border-radius:8px; cursor:pointer;
    font-size:13px; font-weight:600; transition:opacity .15s;
  }}
  .btn-export:hover {{ opacity:0.85; }}
  .btn-dl  {{ background:#0F8BC6; color:#fff; }}
  .btn-cp  {{ background:#F1F5F9; color:#334155; border:1px solid #CBD5E1; }}
</style>

<div class="btn-bar">
  <button class="btn-export btn-cp" onclick="doCapture('copy')">📋 Copier</button>
  <button class="btn-export btn-dl" onclick="doCapture('download')">⬇️ Télécharger PNG</button>
</div>

<div id="rapport-table" style="background:#FFFFFF;border-radius:12px;overflow:hidden;border:1px solid #E2E8F0;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
  <div style="background:#0F8BC6;padding:10px 16px;display:flex;justify-content:space-between;align-items:center;">
    <span style="color:rgba(255,255,255,0.9);font-size:12px;font-weight:500;">📅 {d_start} → {d_end}</span>
    <span style="color:rgba(255,255,255,0.7);font-size:11px;">{datetime.today().strftime('%d/%m/%Y')}</span>
  </div>
  <table style="width:100%;border-collapse:collapse;font-size:13px;">
    <thead>
      <tr style="background:#F1F5F9;border-bottom:2px solid #CBD5E1;">
        <th style="padding:8px 10px;text-align:left;color:#475569;font-size:11px;text-transform:uppercase;letter-spacing:0.05em;">Fournisseur</th>
        <th style="padding:8px 10px;text-align:center;color:#475569;font-size:11px;text-transform:uppercase;">Elec</th>
        <th style="padding:8px 10px;text-align:center;color:#475569;font-size:11px;text-transform:uppercase;">Gaz</th>
        <th style="padding:8px 10px;text-align:center;color:#475569;font-size:11px;text-transform:uppercase;">Total</th>
        <th style="padding:8px 10px;text-align:center;color:#475569;font-size:11px;text-transform:uppercase;">Taux</th>
        <th style="padding:8px 10px;text-align:center;color:#475569;font-size:11px;text-transform:uppercase;">Progression</th>
      </tr>
    </thead>
    <tbody>{table_html_rows}</tbody>
  </table>
  <div style="background:#F8FAFC;padding:6px 16px;border-top:1px solid #E2E8F0;text-align:right;">
    <span style="color:#94A3B8;font-size:11px;">Généré le {datetime.today().strftime('%d/%m/%Y à %H:%M')}</span>
  </div>
</div>

<script>
function doCapture(action) {{
  const el = document.getElementById('rapport-table');
  html2canvas(el, {{ backgroundColor: '#FFFFFF', scale: 2, useCORS: true, logging: false }})
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
              setTimeout(() => {{
                btn.textContent = orig;
                btn.style.background = '';
                btn.style.color = '';
              }}, 2000);
            }})
            .catch(() => {{
              // Fallback Chrome si clipboard API refusée : ouvre dans un onglet
              const url = URL.createObjectURL(blob);
              window.open(url, '_blank');
            }});
        }});
      }}
    }});
}}
</script>"""

        components.html(html2canvas_component, height=n_rows * 38 + 160, scrolling=False)

    # ================================================================
    # PAGE AGENTS
    # ================================================================
    elif page == "👤 Agents":

        st.header("👤 Performance Agents")
        st.markdown(period_html, unsafe_allow_html=True)

        jours = get_working_days()
        obj_agent = math.ceil(185 * 0.75)

        ventes_agent = df_filtered.groupby("agent").size().reset_index(name="ventes")
        ventes_energie = (
            df_filtered.groupby(["agent", "energie"]).size()
            .unstack(fill_value=0).reset_index()
        )
        ventes_energie = ensure_energie_cols(ventes_energie)
        ventes_agent = ventes_agent.merge(ventes_energie, on="agent", how="left").fillna(0)
        ventes_agent["taux"] = ventes_agent["ventes"] / obj_agent
        ventes_agent["kpi"] = ventes_agent["ventes"] / jours if jours else 0
        ventes_agent = ventes_agent.sort_values("taux", ascending=False)

        total_ventes_agents = int(ventes_agent["ventes"].sum())
        meilleur = ventes_agent.iloc[0]["agent"] if not ventes_agent.empty else "—"

        m1, m2, m3 = st.columns(3)
        m1.markdown(
            f"<div class='metric-card'><div class='metric-value'>{total_ventes_agents}</div>"
            f"<div class='metric-label'>Ventes totales</div></div>", unsafe_allow_html=True
        )
        m2.markdown(
            f"<div class='metric-card'><div class='metric-value'>{meilleur}</div>"
            f"<div class='metric-label'>Meilleur agent</div></div>", unsafe_allow_html=True
        )
        m3.markdown(
            f"<div class='metric-card'><div class='metric-value'>{jours}</div>"
            f"<div class='metric-label'>Jours ouvrés (mois)</div></div>", unsafe_allow_html=True
        )

        st.markdown("<div class='section-title'>Classement agents</div>", unsafe_allow_html=True)

        BADGES = {0: "🥇", 1: "🥈", 2: "🥉"}

        for i, (_, r) in enumerate(ventes_agent.iterrows()):
            v_total = int(r["ventes"])
            v_elec = int(r["ELEC"])
            v_gaz = int(r["GAZ"])
            taux = r["taux"]
            row_class = "agent-row" if i % 2 == 0 else "agent-row-alt"
            with st.container():
                st.markdown(f"<div class='{row_class}'>", unsafe_allow_html=True)
                c1, c2, c3, c4 = st.columns([3, 5, 4, 2])
                badge = BADGES.get(i, "")
                c1.markdown(f"<span class='top-badge'>{badge}</span> {r['agent']}", unsafe_allow_html=True)
                c2.progress(min(taux, 1.0))
                c3.markdown(
                    f"⚡ {v_elec} &nbsp;&nbsp; 🔥 {v_gaz} &nbsp;&nbsp; "
                    f"🎯 {v_total}/{obj_agent} &nbsp;&nbsp; {emoji(taux)} {taux:.0%}",
                    unsafe_allow_html=True
                )
                c4.write(f"📅 {round(r['kpi'], 1)}/J")
                st.markdown("</div>", unsafe_allow_html=True)

    # ================================================================
    # PAGE OBJECTIFS
    # ================================================================
    elif page == "🎯 Objectifs":

        st.header("🎯 Performance détaillée")
        st.markdown(period_html, unsafe_allow_html=True)

        colA, colB = st.columns(2)
        heures = colA.number_input("Heures", value=185.0)
        agent = colB.selectbox("Agent", df_filtered["agent"].unique())

        df_agent = df_filtered[df_filtered["agent"] == agent]
        obj_agent = round_excel(heures * 0.75)
        ventes_total = len(df_agent)
        taux = ventes_total / obj_agent if obj_agent else 0

        v_elec_agent = len(df_agent[df_agent["energie"] == "ELEC"])
        v_gaz_agent = len(df_agent[df_agent["energie"] == "GAZ"])

        m1, m2, m3 = st.columns(3)
        m1.markdown(
            f"<div class='metric-card'><div class='metric-value'>{ventes_total}</div>"
            f"<div class='metric-label'>Ventes totales</div></div>", unsafe_allow_html=True
        )
        m2.markdown(
            f"<div class='metric-card'><div class='metric-value'>⚡ {v_elec_agent} &nbsp; 🔥 {v_gaz_agent}</div>"
            f"<div class='metric-label'>Elec / Gaz</div></div>", unsafe_allow_html=True
        )
        m3.markdown(
            f"<div class='metric-card'><div class='metric-value'>{emoji(taux)} {taux:.0%}</div>"
            f"<div class='metric-label'>Taux objectif</div></div>", unsafe_allow_html=True
        )

        st.markdown("<div class='block'>", unsafe_allow_html=True)
        st.subheader(agent)
        st.progress(min(taux, 1.0))
        st.write(f"{emoji(taux)} {ventes_total}/{obj_agent} ({taux:.0%})")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='section-title'>⚡ Ventes par fournisseur</div>", unsafe_allow_html=True)

        special = ["HOMESERVE", "FREE"]

        for f in objectifs["Fournisseur"].dropna().unique():
            if f in special:
                continue
            df_f = df_agent[df_agent["get_provider"] == f]
            obj_row = objectifs[objectifs["Fournisseur"] == f]
            obj_total_f = round_excel(heures * 0.75 * (obj_row["Objectifs Total"].sum() / objectif_total))
            obj_elec_f = round_excel(heures * 0.75 * (obj_row["Objectif Elec"].sum() / objectif_total))
            obj_gaz_f = round_excel(heures * 0.75 * (obj_row["Objectif Gaz"].sum() / objectif_total))
            v_total = len(df_f)
            v_elec = len(df_f[df_f["energie"] == "ELEC"])
            v_gaz = len(df_f[df_f["energie"] == "GAZ"])
            p = v_total / obj_total_f if obj_total_f else 0

            with st.container():
                st.markdown("<div class='fournisseur-row'>", unsafe_allow_html=True)
                c1, c2, c3 = st.columns([2, 5, 5])
                c1.write(f)
                c2.progress(min(p, 1.0))
                c3.markdown(
                    f"⚡ {v_elec}/{obj_elec_f} &nbsp;&nbsp; 🔥 {v_gaz}/{obj_gaz_f} &nbsp;&nbsp; "
                    f"🎯 {v_total}/{obj_total_f} &nbsp;&nbsp; {emoji(p)} {p:.0%}",
                    unsafe_allow_html=True
                )
                st.markdown("</div>", unsafe_allow_html=True)

else:
    st.info("🔒 Ajoute un fichier via le panneau Admin ci-dessous.")
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
