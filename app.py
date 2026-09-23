# -*- coding: utf-8 -*-
"""
AgriPulse — FPO Operational Dashboard (Streamlit)
=================================================
Class 4 productization of the AgriPulse project
(IBM SkillsBuild / BharatCares CSRBOX internship — Mohammed Aliyan).

Prerequisites: execute MohammedAliyan_AgriPulse.ipynb once so that
./outputs/farmer_scores_live.csv, village_risk.csv, seasonal_summary.csv
and agripulse_results.json exist. (The repo ships with these artefacts
committed, so the dashboard renders out-of-the-box.)

Run locally:
    pip install -r requirements.txt
    streamlit run app.py
"""
import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

BASE = Path(__file__).resolve().parent
OUT = BASE / "outputs"

st.set_page_config(page_title="AgriPulse | FPO Risk Dashboard", page_icon="🌾", layout="wide")

# ---- chart sizing compatibility -------------------------------------------
# ``use_container_width`` is deprecated (removal announced after 2025-12-31);
# the replacement ``width="stretch"`` needs Streamlit >= 1.49. Pick whichever
# the installed version supports so the app runs on old and new releases.
try:
    from packaging.version import Version  # type: ignore

    _STRETCH_KW = (
        {"use_container_width": True}
        if Version(st.__version__) < Version("1.49")
        else {"width": "stretch"}
    )
except Exception:  # pragma: no cover - packaging not installed
    _STRETCH_KW = {"use_container_width": True}

# ---------------------------------------------------------------------------
# DESIGN SYSTEM — mirrors the AgriPulse web preview (Geist · teal · cream)
# ---------------------------------------------------------------------------
FONT_FAMILY = "Geist, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"

_TIER_COLORS = {"Critical": "#7F1D1D", "High": "#C2410C",
                "Moderate": "#B45309", "Low": "#0F766E"}
_SEGMENT_COLORS = ["#15803D", "#0F766E", "#4D7C0F", "#B45309", "#C2410C", "#7F1D1D"]

st.markdown(
    '<link href="https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700;800'
    '&family=Geist+Mono:wght@400;500;600&display=swap" rel="stylesheet">',
    unsafe_allow_html=True,
)

st.markdown(
    """
<style>
:root {
  --bg: #FAFAF9; --cream: #F5F0E6; --card: #FFFFFF;
  --teal: #0F766E; --teal-deep: #042F2E; --teal-dark: #134E4A;
  --amber: #FDE68A; --amber-deep: #92400E;
  --stone-200: #E7E5E4; --stone-300: #D6D3D1; --stone-400: #A8A29E;
  --stone-500: #78716C; --stone-600: #57534E; --stone-700: #44403C;
  --stone-800: #292524; --stone-900: #1C1917;
}
html, body, .stApp, [class*="css"] { font-family: Geist, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; }
.stApp { background: var(--bg); }

/* ---- hide default Streamlit chrome ------------------------------------ */
#MainMenu { visibility: hidden; }
div[data-testid="stToolbar"] { display: none; }
div[data-testid="stDecoration"] { display: none; }
footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }
div[data-testid="stStatusWidget"] { display: none; }
.stAnchor { display: none; }
.block-container { padding: 1.1rem 1.4rem 2.2rem; max-width: 1240px; }

/* ---- hero banner -------------------------------------------------------- */
.hero {
  position: relative; overflow: hidden; border-radius: 20px;
  background: linear-gradient(128deg, #042F2E 0%, #0F766E 52%, #365314 100%);
  padding: 30px 34px 26px; color: #fff; margin-bottom: 14px;
  box-shadow: 0 12px 32px -14px rgba(4, 47, 46, 0.55);
}
.hero::after {
  content: ""; position: absolute; inset: 0; pointer-events: none;
  background:
    radial-gradient(620px 220px at 88% -30%, rgba(253, 230, 138, 0.16), transparent 60%),
    radial-gradient(420px 260px at -8% 118%, rgba(133, 77, 14, 0.28), transparent 62%);
}
.hero-top { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 14px; position: relative; z-index: 1; }
.hero-badge {
  display: inline-flex; align-items: center; gap: 6px;
  background: rgba(253, 230, 138, 0.14); border: 1px solid rgba(253, 230, 138, 0.35);
  color: #FDE68A; font-size: 11px; font-weight: 600; letter-spacing: 0.10em; text-transform: uppercase;
  padding: 5px 12px; border-radius: 999px;
}
.hero-badge.live {
  background: rgba(255, 255, 255, 0.10); border-color: rgba(255, 255, 255, 0.30); color: #ECFDF5;
  font-family: "Geist Mono", monospace; letter-spacing: 0.08em;
}
.hero-badge.live .dot {
  width: 7px; height: 7px; border-radius: 50%; background: #6EE7B7;
  box-shadow: 0 0 0 3px rgba(110, 231, 183, 0.25);
}
.hero h1 {
  margin: 0 0 6px; font-size: 30px; line-height: 1.15; font-weight: 800; letter-spacing: -0.02em;
  position: relative; z-index: 1;
}
.hero h1 .grain { font-size: 26px; }
.hero-sub { margin: 0 0 14px; font-size: 14.5px; color: rgba(255, 255, 255, 0.82); font-weight: 400; max-width: 760px; line-height: 1.55; position: relative; z-index: 1; }
.hero-meta {
  display: flex; flex-wrap: wrap; gap: 8px 22px; margin: 0; padding-top: 14px;
  border-top: 1px solid rgba(255, 255, 255, 0.18); position: relative; z-index: 1;
}
.hero-meta span { font-size: 12.5px; color: rgba(255, 255, 255, 0.75); }
.hero-meta b { color: #fff; font-weight: 600; font-family: "Geist Mono", monospace; font-size: 12px; }

/* ---- KPI strip ---------------------------------------------------------- */
.kpi-strip {
  display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin: 6px 0 18px;
}
@media (max-width: 1100px) { .kpi-strip { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 640px)  { .kpi-strip { grid-template-columns: repeat(2, 1fr); } }
.kpi-card {
  background: var(--card); border: 1px solid var(--stone-200); border-radius: 16px;
  padding: 16px 18px 14px; position: relative; overflow: hidden;
  box-shadow: 0 1px 3px rgba(28, 25, 17, 0.05); transition: box-shadow .2s ease, transform .2s ease;
}
.kpi-card:hover { box-shadow: 0 10px 24px -12px rgba(28, 25, 17, 0.22); transform: translateY(-2px); }
.kpi-card::before {
  content: ""; position: absolute; top: 0; left: 0; right: 0; height: 3px;
  background: var(--accent, var(--teal)); opacity: .9;
}
.kpi-label {
  font-size: 10.5px; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase;
  color: var(--stone-500); margin-bottom: 6px;
}
.kpi-value {
  font-size: 27px; font-weight: 800; letter-spacing: -0.02em; color: var(--stone-900);
  font-family: "Geist Mono", "Geist", monospace; line-height: 1.1;
}
.kpi-sub { font-size: 11.5px; color: var(--stone-500); margin-top: 5px; line-height: 1.4; }

/* ---- filter summary strip ------------------------------------------------ */
.filter-strip { display: flex; flex-wrap: wrap; gap: 8px; margin: 0 0 16px; align-items: center; }
.chip {
  display: inline-flex; align-items: center; gap: 6px;
  background: var(--card); border: 1px solid var(--stone-200);
  padding: 5px 13px; border-radius: 999px; font-size: 12px; color: var(--stone-600);
  box-shadow: 0 1px 2px rgba(28, 25, 17, 0.04);
}
.chip b { color: var(--teal-deep); font-weight: 700; }
.chip.alert { border-color: #FDE68A; background: #FFFBEB; color: #92400E; }

/* ---- section headings ---------------------------------------------------- */
.sec { margin: 2px 0 10px; }
.sec-eyebrow {
  display: inline-flex; align-items: center; gap: 8px;
  font-size: 10.5px; font-weight: 700; letter-spacing: 0.16em; text-transform: uppercase;
  color: var(--teal); margin-bottom: 4px;
}
.sec-eyebrow::before { content: ""; width: 18px; height: 2px; background: var(--teal); border-radius: 2px; }
.sec-title { margin: 0 0 4px; font-size: 17px; font-weight: 700; color: var(--stone-900); letter-spacing: -0.01em; }
.sec-desc { margin: 0; font-size: 12.8px; color: var(--stone-500); line-height: 1.55; max-width: 720px; }

/* ---- bordered chart cards ------------------------------------------------ */
.stVerticalBlockBorderWrapper, [data-testid="stVerticalBlockBorder"] {
  border: 1px solid var(--stone-200) !important; border-radius: 16px !important;
  background: var(--card); box-shadow: 0 1px 3px rgba(28, 25, 17, 0.05);
  padding: 14px 16px 10px !important;
}
[data-testid="stVerticalBlockBorder"] { border: none !important; padding: 0 !important; }

/* ---- tabs ---------------------------------------------------------------- */
.stTabs [data-baseweb="tab-list"] {
  gap: 4px; background: var(--card); border: 1px solid var(--stone-200);
  border-radius: 14px; padding: 5px; box-shadow: 0 1px 3px rgba(28, 25, 17, 0.05);
  width: fit-content; max-width: 100%; overflow-x: auto;
}
.stTabs [data-baseweb="tab"] {
  border-radius: 10px; padding: 8px 16px; font-size: 13px; font-weight: 500;
  color: var(--stone-600); background: transparent; letter-spacing: 0.01em;
}
.stTabs [data-baseweb="tab"]:hover { background: var(--cream); color: var(--teal-deep); }
.stTabs [aria-selected="true"] { background: var(--teal) !important; color: #fff !important; font-weight: 600; }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none; }

/* ---- sidebar --------------------------------------------------------------- */
section[data-testid="stSidebar"] {
  background: #FFFFFF; border-right: 1px solid var(--stone-200);
}
div[data-testid="stSidebarContent"] { padding-top: 10px; }
.sb-brand { display: flex; align-items: center; gap: 12px; padding: 4px 2px 2px; }
.sb-logo {
  width: 42px; height: 42px; border-radius: 12px; display: flex; align-items: center; justify-content: center;
  background: var(--teal); color: var(--amber); font-size: 21px;
  box-shadow: 0 6px 16px -8px rgba(15, 118, 110, 0.65);
}
.sb-title { font-size: 16px; font-weight: 800; color: var(--stone-900); letter-spacing: -0.01em; }
.sb-sub { font-size: 11px; color: var(--stone-500); }
.sb-divider { height: 1px; background: var(--stone-200); margin: 12px 0 14px; }
.sb-label {
  font-size: 10.5px; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase;
  color: var(--stone-500); margin: 16px 0 4px;
}
.sb-note {
  margin-top: 18px; border: 1px dashed var(--stone-300); background: var(--cream);
  border-radius: 12px; padding: 11px 13px; font-size: 11.5px; line-height: 1.55; color: var(--stone-600);
}
.sb-note b { color: var(--teal-deep); }
.sb-note .warn { color: #92400E; }

/* ---- dataframe / buttons / misc ------------------------------------------ */
div[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; border: 1px solid var(--stone-200); }
.stDownloadButton > button {
  background: var(--teal); color: #fff; border: 1px solid var(--teal);
  border-radius: 10px; font-weight: 600; font-size: 13px; padding: 7px 18px;
  box-shadow: 0 6px 16px -8px rgba(15, 118, 110, 0.55);
}
.stDownloadButton > button:hover { background: var(--teal-dark); border-color: var(--teal-dark); }
.stDownloadButton > button:focus { box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.25); }
hr { border: none; height: 1px; background: var(--stone-200); }
.stCaption, [data-testid="stCaptionContainer"] p { font-size: 11.8px; color: var(--stone-500); }

/* ---- footer ---------------------------------------------------------------- */
.agri-footer {
  margin-top: 26px; background: var(--cream); border: 1px solid var(--stone-200);
  border-radius: 16px; padding: 18px 22px;
}
.agri-footer-row { display: flex; align-items: center; justify-content: space-between; gap: 14px; flex-wrap: wrap; }
.agri-footer-brand { display: flex; align-items: center; gap: 10px; }
.agri-footer-logo {
  width: 34px; height: 34px; border-radius: 10px; background: var(--teal); color: var(--amber);
  display: flex; align-items: center; justify-content: center; font-size: 17px;
}
.agri-footer-name { font-size: 14px; font-weight: 800; color: var(--teal-deep); }
.agri-footer-prog { font-size: 11px; color: var(--stone-500); }
.agri-footer-note { margin: 12px 0 0; padding-top: 12px; border-top: 1px solid var(--stone-300);
  font-size: 11.3px; color: var(--stone-500); line-height: 1.6; }
</style>
""",
    unsafe_allow_html=True,
)


# ---- artefact loaders (cached) ---------------------------------------------
@st.cache_data(ttl=600)
def load_artifacts():
    scores = pd.read_csv(OUT / "farmer_scores_live.csv")
    villages = pd.read_csv(OUT / "village_risk.csv")
    seasonal = pd.read_csv(OUT / "seasonal_summary.csv")
    results = json.loads((OUT / "agripulse_results.json").read_text())
    return scores, villages, seasonal, results


if not (OUT / "farmer_scores_live.csv").exists():
    st.error("Outputs not found — execute MohammedAliyan_AgriPulse.ipynb first, "
             "then restart this app.")
    st.stop()

scores, villages, seasonal, results = load_artifacts()
kpi = results["kpi"]
meta = results["meta"]
tiers = ["Critical", "High", "Moderate", "Low"]

# ---------------------------------------------------------------------------
# Sidebar — branded filter rail
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
<div class="sb-brand">
  <div class="sb-logo">🌾</div>
  <div>
    <div class="sb-title">AgriPulse</div>
    <div class="sb-sub">Field-office control panel</div>
  </div>
</div>
<div class="sb-divider"></div>
""",
        unsafe_allow_html=True,
    )

    st.markdown('<p class="sb-label">Crop mix</p>', unsafe_allow_html=True)
    crops = sorted(scores["main_crop"].dropna().unique())
    sel_crop = st.multiselect("Crop", crops, default=crops, label_visibility="collapsed")

    st.markdown('<p class="sb-label">Risk tier</p>', unsafe_allow_html=True)
    sel_tier = st.multiselect("Risk tier", tiers, default=["Critical", "High"],
                              label_visibility="collapsed")

    st.markdown('<p class="sb-label">Landholding (acres)</p>', unsafe_allow_html=True)
    ac_lo, ac_hi = float(scores.landholding_acres.min()), float(scores.landholding_acres.max())
    acres = st.slider("Landholding", ac_lo, ac_hi, (ac_lo, ac_hi), step=0.25,
                      label_visibility="collapsed")

    st.markdown('<p class="sb-label">Drought context</p>', unsafe_allow_html=True)
    drought_only = st.checkbox("Drought-stressed members only")

    st.markdown(
        """
<div class="sb-note">
  <b>Field capacity</b> — extension officers can visit at most
  <b>50 farms / month</b>, so the operating threshold τ is tuned for
  <b>precision under the visit cap</b>.<br><br>
  <span class="warn">⚠ Drought-stressed members are routed to emergency
  liquidity + insurance — relief, not reprimand.</span>
</div>
""",
        unsafe_allow_html=True,
    )

f = scores[scores.main_crop.isin(sel_crop) & scores.risk_tier.astype(str).isin(sel_tier)
           & scores.landholding_acres.between(acres[0], acres[1])]
if drought_only:
    f = f[f.drought_stress == True]  # noqa: E712

# ---------------------------------------------------------------------------
# Hero + KPI strip
# ---------------------------------------------------------------------------
st.markdown(
    f"""
<div class="hero">
  <div class="hero-top">
    <span class="hero-badge">IBM SkillsBuild · BharatCares × AICTE</span>
    <span class="hero-badge">UN SDG 1 &amp; 2</span>
    <span class="hero-badge live"><span class="dot"></span>LIVE · {kpi['next_cycle']} CYCLE</span>
  </div>
  <h1><span class="grain">🌾</span> AgriPulse — Smallholder Supply &amp; Defection Risk</h1>
  <p class="hero-sub">Turning the FPO's own transaction ledger into an early-warning system:
  Ag-RFM loyalty indices, calibrated defection probabilities and a capacity-aware
  top-50 field dispatch list — with a drought-stress overlay that separates
  <i>rain failure</i> from <i>commercial side-selling</i>.</p>
  <div class="hero-meta">
    <span><b>{meta['n_farmers']:,}</b>&nbsp; registered farmers</span>
    <span><b>{meta['n_villages']}</b>&nbsp; villages</span>
    <span><b>{meta['n_districts']}</b>&nbsp; districts</span>
    <span><b>12</b>&nbsp; seasons of ledger history</span>
    <span><b>τ = 0.82</b>&nbsp; capacity-tuned threshold</span>
    <span><b>{kpi['field_visit_cap']}</b>&nbsp; visits / month</span>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    f"""
<div class="kpi-strip">
  <div class="kpi-card" style="--accent:#0F766E">
    <div class="kpi-label">Members scored</div>
    <div class="kpi-value">{kpi['farmers_scored']:,}</div>
    <div class="kpi-sub">{kpi['next_cycle']} live cycle</div>
  </div>
  <div class="kpi-card" style="--accent:#C2410C">
    <div class="kpi-label">At-risk (≥ τ)</div>
    <div class="kpi-value">{int(kpi['at_risk'])}</div>
    <div class="kpi-sub">flagged for field review</div>
  </div>
  <div class="kpi-card" style="--accent:#B45309">
    <div class="kpi-label">Drought-stressed</div>
    <div class="kpi-value">{int(kpi['drought_stressed'])}</div>
    <div class="kpi-sub">routed to relief, not reprimand</div>
  </div>
  <div class="kpi-card" style="--accent:#042F2E">
    <div class="kpi-label">Model AUC (test)</div>
    <div class="kpi-value">{kpi['auc_test']:.3f}</div>
    <div class="kpi-sub">out-of-time validation</div>
  </div>
  <div class="kpi-card" style="--accent:#15803D">
    <div class="kpi-label">Precision@50</div>
    <div class="kpi-value">{kpi['precision_at_50']:.2f}</div>
    <div class="kpi-sub">top-50 dispatch precision</div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

tier_summary = ", ".join(sel_tier) if sel_tier else "none"
st.markdown(
    f"""
<div class="filter-strip">
  <span class="chip"><b>{len(f):,}</b>&nbsp;members in view</span>
  <span class="chip">{len(sel_crop)} of {len(crops)} crops</span>
  <span class="chip">Tiers:&nbsp;{tier_summary}</span>
  <span class="chip">{acres[0]:.1f}–{acres[1]:.1f} acres</span>
  {"<span class='chip alert'>Drought-stressed only</span>" if drought_only else ""}
</div>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Plotly house style
# ---------------------------------------------------------------------------
def style_fig(fig, height=340):
    fig.update_layout(
        font=dict(family=FONT_FAMILY, size=12.5, color="#44403C"),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=8, r=8, t=6, b=6), height=height,
        hoverlabel=dict(bgcolor="#1C1917", font=dict(family=FONT_FAMILY, color="#FFFFFF",
                                                     size=12), bordercolor="#1C1917"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0,
                    font=dict(size=11.5, color="#57534E")),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#EDEAE2", zeroline=False,
                     tickfont=dict(color="#78716C", size=11.5), linecolor="#D6D3D1")
    fig.update_yaxes(showgrid=True, gridcolor="#EDEAE2", zeroline=False,
                     tickfont=dict(color="#78716C", size=11.5), linecolor="#D6D3D1")
    return fig


def section(eyebrow, title, desc):
    st.markdown(
        f"""
<div class="sec">
  <div class="sec-eyebrow">{eyebrow}</div>
  <div class="sec-title">{title}</div>
  <div class="sec-desc">{desc}</div>
</div>
""",
        unsafe_allow_html=True,
    )


tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Overview", "Village map", "Seasonal trends", "Risk register", "Dispatch list"])

# ---- Overview --------------------------------------------------------------
with tab1:
    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            section("01 · Live membership",
                    "Risk-tier composition of the scored membership",
                    f"Calibrated P(defection) for {kpi['farmers_scored']:,} members, "
                    "bucketed by the operating tiers used by the field programme.")
            tier_counts = scores.risk_tier.astype(str).value_counts().reindex(tiers).fillna(0)
            fig = px.bar(x=tier_counts.index, y=tier_counts.values,
                         color=tier_counts.index,
                         color_discrete_map=_TIER_COLORS,
                         labels={"x": "Risk tier", "y": "Members"})
            fig.update_traces(marker=dict(line=dict(width=0)))
            fig.update_layout(bargap=0.55)
            style_fig(fig, 330)
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, **_STRETCH_KW)
    with c2:
        with st.container(border=True):
            section("02 · Ag-RFM segments",
                    "Where the membership sits in the loyalty lattice",
                    "Recency × Frequency × Monetary segments — the behavioural "
                    "backbone the churn model reads.")
            fig = px.pie(scores.groupby("segment", observed=True).size().reset_index(name="n"),
                         values="n", names="segment", hole=0.52,
                         color_discrete_sequence=_SEGMENT_COLORS)
            fig.update_traces(textposition="inside", textinfo="percent",
                              insidetextfont=dict(size=11.5, color="#FFFFFF"),
                              marker=dict(line=dict(color="#FFFFFF", width=2)))
            style_fig(fig, 330)
            st.plotly_chart(fig, **_STRETCH_KW)

# ---- Village map -----------------------------------------------------------
with tab2:
    with st.container(border=True):
        section("03 · Geography",
                "Village-level defection risk — 2025-K cycle",
                "Bubble size = member count · colour = mean calibrated P(defection). "
                "Amber/rust villages in the Malwa rabi belt reflect drought-stress context. "
                "Coordinates are approximate (schematic map).")
        fig = px.scatter_geo(villages, lat="lat", lon="lon", color="avg_risk", size="farmers",
                             hover_name="village",
                             hover_data={"district": True, "at_risk": True,
                                         "avg_risk": ":.3f"},
                             scope="asia", center=dict(lat=21.8, lon=76.5),
                             color_continuous_scale=["#F5F0E6", "#B45309", "#7F1D1D"],
                             projection="natural earth2")
        fig.update_layout(
            geo=dict(showland=True, landcolor="#EDE9DD", showcountries=True,
                     countrycolor="#A8A29E", showocean=True, oceancolor="#E7F0EC",
                     showframe=False, coastlinecolor="#D6D3D1"),
            coloraxis_colorbar=dict(title=dict(text="P(defection)",
                                               font=dict(size=11.5, color="#57534E")),
                                    thickness=14, len=0.75,
                                    tickfont=dict(size=11, color="#78716C")),
        )
        style_fig(fig, 560)
        st.plotly_chart(fig, **_STRETCH_KW)

# ---- Seasonal trends --------------------------------------------------------
with tab3:
    c1, c2 = st.columns([3, 2])
    with c1:
        with st.container(border=True):
            section("04 · Procurement",
                    "FPO procurement value by season",
                    "₹ value routed through the cooperative across the 12-season ledger "
                    "(kharif & rabi).")
            fig = px.bar(seasonal, x="season", y="value_inr",
                         color_discrete_sequence=["#0F766E"],
                         labels={"value_inr": "Procurement value (₹)", "season": "Season"})
            fig.update_traces(marker=dict(line=dict(width=0)))
            fig.update_layout(bargap=0.45, showlegend=False)
            style_fig(fig, 380)
            st.plotly_chart(fig, **_STRETCH_KW)
    with c2:
        with st.container(border=True):
            section("05 · Retention",
                    "Average yield retention routed to the FPO",
                    "Share of surveyed yield deposited with the cooperative — the early "
                    "signature of side-selling.")
            fig = px.line(seasonal, x="season", y=seasonal.avg_retention * 100,
                          color_discrete_sequence=["#B45309"], markers=True,
                          labels={"y": "Avg retention (%)", "season": "Season"})
            fig.update_traces(marker=dict(size=7, line=dict(width=2.5)),
                              line=dict(shape="spline"))
            fig.update_layout(showlegend=False)
            style_fig(fig, 380)
            st.plotly_chart(fig, **_STRETCH_KW)

# ---- Risk register ----------------------------------------------------------
with tab4:
    with st.container(border=True):
        section("06 · Risk register",
                f"{len(f):,} members match the current filters",
                "Ag-RFM view — recency × yield-retention, sized by ₹ value routed through "
                "the cooperative. Every flag is association, not causation, and is reviewed "
                "by extension officers before any action.")
        fig = px.scatter(f, x="recency_days", y="retention_t", color="segment",
                         size="monetary_12m", hover_name="farmer_id",
                         hover_data={"risk_prob": ":.3f", "village": True},
                         color_discrete_sequence=_SEGMENT_COLORS,
                         labels={"recency_days": "Recency (days since last deposit)",
                                 "retention_t": "Yield retention this season"})
        fig.update_traces(marker=dict(opacity=0.78, line=dict(width=1, color="#FFFFFF")))
        style_fig(fig, 430)
        st.plotly_chart(fig, **_STRETCH_KW)
        st.dataframe(f[["farmer_id", "village", "district", "main_crop", "landholding_acres",
                        "recency_days", "retention_t", "monetary_12m", "risk_prob", "risk_tier",
                        "segment", "drought_stress", "recommended_action"]].round(3),
                     **_STRETCH_KW, height=420)

# ---- Dispatch list ------------------------------------------------------------
with tab5:
    with st.container(border=True):
        section("07 · Field dispatch",
                f"Top-{int(kpi['field_visit_cap'])} monthly field dispatch — {kpi['next_cycle']} cycle",
                "Ranked by calibrated P(defection). Drought-flagged members are routed to "
                "emergency liquidity + insurance instead of a loyalty intervention.")
        topn = scores.nlargest(int(kpi["field_visit_cap"]), "risk_prob").copy()
        topn.insert(0, "rank", range(1, len(topn) + 1))
        st.dataframe(topn[["rank", "farmer_id", "village", "district", "main_crop",
                           "landholding_acres", "risk_prob", "retention_t", "recency_days",
                           "drought_stress", "recommended_action"]].round(3),
                     **_STRETCH_KW, height=480)
        csv = topn.to_csv(index=False).encode("utf-8")
        st.download_button("⬇  Download dispatch list (CSV)", csv,
                           "agripulse_dispatch_2025K.csv", "text/csv")

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown(
    """
<div class="agri-footer">
  <div class="agri-footer-row">
    <div class="agri-footer-brand">
      <div class="agri-footer-logo">🌾</div>
      <div>
        <div class="agri-footer-name">AgriPulse</div>
        <div class="agri-footer-prog">IBM SkillsBuild — Data Analytics with AI · BharatCares CSRBOX × AICTE</div>
      </div>
    </div>
    <div class="agri-footer-prog">Mohammed Aliyan · Random Forest (isotonic-calibrated) · AUC 0.926 · Precision@50 0.68</div>
  </div>
  <p class="agri-footer-note">Synthetic demonstration data (seed 42) · Association, not causation —
  all flags reviewed by FPO extension officers · Farmers are pseudonymous IDs (DPDP Act 2023-aligned
  data minimisation) · Fairness audited across landholding classes.</p>
</div>
""",
    unsafe_allow_html=True,
)
