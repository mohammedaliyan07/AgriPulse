# -*- coding: utf-8 -*-
"""
AgriPulse — FPO Operational Dashboard (Streamlit)
=================================================
Class 4 productization of the AgriPulse project
(IBM SkillsBuild / BharatCares CSRBOX internship — Mohammed Aliyan).

Prerequisites: execute MohammedAliyan_AgriPulse.ipynb once so that
./outputs/farmer_scores_live.csv, village_risk.csv, seasonal_summary.csv
and agripulse_results.json exist.

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

# ---- sidebar filters --------------------------------------------------------
st.sidebar.title("🌾 AgriPulse")
st.sidebar.caption("Cooperative supply & churn risk")

crops = sorted(scores["main_crop"].dropna().unique())
sel_crop = st.sidebar.multiselect("Crop", crops, default=crops)
sel_tier = st.sidebar.multiselect("Risk tier", tiers, default=["Critical", "High"])
ac_lo, ac_hi = float(scores.landholding_acres.min()), float(scores.landholding_acres.max())
acres = st.sidebar.slider("Landholding (acres)", ac_lo, ac_hi, (ac_lo, ac_hi), step=0.25)
drought_only = st.sidebar.checkbox("Drought-stressed members only")

f = scores[scores.main_crop.isin(sel_crop) & scores.risk_tier.astype(str).isin(sel_tier)
           & scores.landholding_acres.between(acres[0], acres[1])]
if drought_only:
    f = f[f.drought_stress == True]  # noqa: E712

st.title("🌾 AgriPulse — Smallholder Supply & Defection Risk")
st.caption(f"{meta['n_farmers']:,} registered farmers · {meta['n_villages']} villages · "
           f"{meta['n_districts']} districts · next cycle {kpi['next_cycle']} · "
           f"field capacity {kpi['field_visit_cap']}/month")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Overview", "Village map", "Seasonal trends", "Risk register", "Dispatch list"])

with tab1:
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Members scored", f"{kpi['farmers_scored']:,}")
    c2.metric("At-risk (≥τ)", int(kpi["at_risk"]))
    c3.metric("Drought-stressed", int(kpi["drought_stressed"]))
    c4.metric("Model AUC (test)", f"{kpi['auc_test']:.3f}")
    c5.metric("Precision@50", f"{kpi['precision_at_50']:.2f}")

    left, right = st.columns(2)
    with left:
        tier_counts = scores.risk_tier.astype(str).value_counts().reindex(tiers).fillna(0)
        fig = px.bar(x=tier_counts.index, y=tier_counts.values,
                     color=tier_counts.index,
                     color_discrete_map={"Critical": "#7F1D1D", "High": "#C2410C",
                                         "Moderate": "#B45309", "Low": "#0F766E"},
                     labels={"x": "Risk tier", "y": "Members"})
        fig.update_layout(showlegend=False, height=330,
                          title="Live membership by risk tier (2025-K)")
        st.plotly_chart(fig, **_STRETCH_KW)
    with right:
        fig = px.pie(scores.groupby("segment", observed=True).size().reset_index(name="n"),
                     values="n", names="segment", hole=0.45,
                     color_discrete_sequence=["#15803D", "#0F766E", "#4D7C0F",
                                              "#B45309", "#C2410C", "#7F1D1D"])
        fig.update_layout(height=330, title="Ag-RFM segments")
        st.plotly_chart(fig, **_STRETCH_KW)

with tab2:
    fig = px.scatter_geo(villages, lat="lat", lon="lon", color="avg_risk", size="farmers",
                         hover_name="village", hover_data={"district": True, "at_risk": True,
                                                           "avg_risk": ":.3f"},
                         scope="asia", center=dict(lat=21.8, lon=76.5),
                         color_continuous_scale=["#F5F0E6", "#B45309", "#7F1D1D"],
                         projection="natural earth2")
    fig.update_layout(height=560, title="Village-level defection risk · 2025-K cycle "
                      "(schematic — village coordinates approximate)",
                      geo=dict(showland=True, landcolor="#EDE9DD",
                               showcountries=True, countrycolor="#A8A29E",
                               showocean=True, oceancolor="#E7F0EC"))
    st.plotly_chart(fig, **_STRETCH_KW)
    st.caption("Bubbles sized by member count; colour = mean P(defection). "
               "Amber/rust villages in the Malwa rabi belt reflect drought-stress context.")

with tab3:
    c1, c2 = st.columns([3, 2])
    with c1:
        fig = px.bar(seasonal, x="season", y="value_inr",
                     color_discrete_sequence=["#0F766E"],
                     labels={"value_inr": "Procurement value (₹)", "season": "Season"})
        fig.update_layout(height=380, title="FPO procurement value by season")
        st.plotly_chart(fig, **_STRETCH_KW)
    with c2:
        fig = px.line(seasonal, x="season", y=seasonal.avg_retention * 100,
                      color_discrete_sequence=["#B45309"], markers=True,
                      labels={"y": "Avg retention (%)", "season": "Season"})
        fig.update_layout(height=380, title="Average yield retention routed to the FPO")
        st.plotly_chart(fig, **_STRETCH_KW)

with tab4:
    st.markdown(f"**{len(f):,} members** match the current filters.")
    fig = px.scatter(f, x="recency_days", y="retention_t", color="segment",
                     size="monetary_12m", hover_name="farmer_id",
                     hover_data={"risk_prob": ":.3f", "village": True},
                     color_discrete_sequence=["#15803D", "#0F766E", "#4D7C0F",
                                              "#B45309", "#C2410C", "#7F1D1D"],
                     labels={"recency_days": "Recency (days since last deposit)",
                             "retention_t": "Yield retention this season"})
    fig.update_layout(height=440, title="Ag-RFM view — recency × retention (size = ₹ value)")
    st.plotly_chart(fig, **_STRETCH_KW)
    st.dataframe(f[["farmer_id", "village", "district", "main_crop", "landholding_acres",
                    "recency_days", "retention_t", "monetary_12m", "risk_prob", "risk_tier",
                    "segment", "drought_stress", "recommended_action"]].round(3),
                 **_STRETCH_KW, height=420)

with tab5:
    st.markdown(f"Top-{int(kpi['field_visit_cap'])} monthly field dispatch — 2025-K cycle "
                f"(ranked by calibrated P(defection)).")
    topn = scores.nlargest(int(kpi["field_visit_cap"]), "risk_prob").copy()
    topn.insert(0, "rank", range(1, len(topn) + 1))
    st.dataframe(topn[["rank", "farmer_id", "village", "district", "main_crop",
                       "landholding_acres", "risk_prob", "retention_t", "recency_days",
                       "drought_stress", "recommended_action"]].round(3),
                 **_STRETCH_KW, height=480)
    csv = topn.to_csv(index=False).encode("utf-8")
    st.download_button("⬇ Download dispatch list (CSV)", csv,
                       "agripulse_dispatch_2025K.csv", "text/csv")

st.divider()
st.caption("AgriPulse · IBM SkillsBuild Data Analytics with AI — BharatCares CSRBOX × AICTE · "
           "Mohammed Aliyan · Synthetic demonstration data (seed 42) · "
           "Association, not causation — all flags reviewed by FPO extension officers.")
