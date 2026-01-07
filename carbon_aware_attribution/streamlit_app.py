import os
import math
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import requests
import streamlit as st

# =========================
# Config
# =========================
DEFAULT_API_URL_LOCAL = "http://localhost:8000"
DEFAULT_API_URL_DOCKER = "http://api:8000"

API_BASE_URL = os.getenv("API_BASE_URL", DEFAULT_API_URL_LOCAL)
TIMEOUT_S = float(os.getenv("API_TIMEOUT_S", "10"))

# Carbon factors (used only if backend doesn't return emissions explicitly)
CHANNEL_EMISSIONS_G = {
    "email": 0.3,
    "display": 1.2,
    "search": 1.0,
    "video": 3.5,
    "social": 2.0,
    "tiktok": 2.8,
    "influencer": 2.8,
}
DEFAULT_EMISSIONS_G = 1.5

st.set_page_config(page_title="AdEco Dashboard", page_icon="🌿", layout="wide")

# =========================
# HTTP helpers
# =========================
def _url(path: str) -> str:
    return API_BASE_URL.rstrip("/") + path

def _get(path: str, params: Optional[dict] = None) -> Tuple[int, Any]:
    try:
        r = requests.get(_url(path), params=params, timeout=TIMEOUT_S)
        if not r.content:
            return r.status_code, {}
        return r.status_code, r.json()
    except Exception as e:
        return 0, {"error": str(e), "path": path}

def _post(path: str, payload: dict) -> Tuple[int, Any]:
    try:
        r = requests.post(_url(path), json=payload, timeout=TIMEOUT_S)
        if not r.content:
            return r.status_code, {}
        return r.status_code, r.json()
    except Exception as e:
        return 0, {"error": str(e), "path": path}

@st.cache_data(ttl=10)
def api_health() -> bool:
    sc, js = _get("/v1/health")
    return sc == 200 and isinstance(js, dict) and js.get("ok") is True

# =========================
# Payload -> DataFrame helpers
# =========================
def _to_df(payload: Any) -> pd.DataFrame:
    """
    Converts common response shapes into a DataFrame:
      - list[dict]
      - dict with 'data'/'rows'/'items'/'results'
      - dict[str, number] -> key/value columns
    """
    if payload is None:
        return pd.DataFrame()

    if isinstance(payload, list):
        if len(payload) == 0:
            return pd.DataFrame()
        if isinstance(payload[0], dict):
            return pd.DataFrame(payload)
        return pd.DataFrame({"value": payload})

    if isinstance(payload, dict):
        for k in ("data", "rows", "items", "results"):
            if k in payload and isinstance(payload[k], list):
                return pd.DataFrame(payload[k])

        if all(isinstance(v, (int, float, str, bool, type(None))) for v in payload.values()):
            return pd.DataFrame({"key": list(payload.keys()), "value": list(payload.values())})

    return pd.DataFrame()

def first_working_get(candidates: List[str], params: Optional[dict] = None) -> Tuple[Optional[str], int, Any]:
    for path in candidates:
        sc, js = _get(path, params=params)
        if sc == 200 and js and not (isinstance(js, dict) and js.get("error")):
            return path, sc, js
    return None, 0, {}

# =========================
# Fetchers (auto-detect endpoints)
# =========================
@st.cache_data(ttl=10)
def fetch_channel_weights() -> pd.DataFrame:
    """
    Confirmed endpoint:
      GET /v1/attribution/channels -> {"channel_weights": {...}}
    """
    sc, js = _get("/v1/attribution/channels")
    if sc != 200 or not isinstance(js, dict):
        return pd.DataFrame()
    w = js.get("channel_weights", {})
    if not isinstance(w, dict) or not w:
        return pd.DataFrame()
    df = pd.DataFrame([{"channel": k, "attribution_weight": float(v)} for k, v in w.items()])
    df["__source"] = "/v1/attribution/channels"
    return df

@st.cache_data(ttl=10)
def fetch_channel_kpis() -> pd.DataFrame:
    """
    Tries common “channel analytics” endpoints your backend may already have.
    Expected (any of these):
      list[dict] with columns like:
        channel, emissions_g, conversions, revenue_usd, cost_usd
    """
    candidates = [
        "/v1/metrics/channels",
        "/v1/kpis/channels",
        "/v1/esg/channels",
        "/v1/analytics/channels",
        "/v1/channels/metrics",
        "/v1/channels/kpis",
    ]
    path, sc, js = first_working_get(candidates)
    df = _to_df(js)
    if not df.empty and path:
        df["__source"] = path
    return df

@st.cache_data(ttl=10)
def fetch_journeys() -> pd.DataFrame:
    """
    Tries common “journey-level” endpoints.
    Expected columns (any reasonable subset):
      journey_id/user_id, emissions_g, conversions, revenue_usd, cost_usd, channel/path
    """
    candidates = [
        "/v1/journeys",
        "/v1/analytics/journeys",
        "/v1/metrics/journeys",
        "/v1/esg/journeys",
        "/v1/journey/rows",
    ]
    path, sc, js = first_working_get(candidates)
    df = _to_df(js)
    if not df.empty and path:
        df["__source"] = path
    return df

# =========================
# Metric computation (uses backend data if present)
# =========================
def ensure_numeric(df: pd.DataFrame, col: str) -> None:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

def ensure_emissions(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "emissions_g" not in df.columns:
        # compute from channel if available, else default
        if "channel" in df.columns:
            df["emissions_g"] = (
                df["channel"].astype(str).str.lower().map(CHANNEL_EMISSIONS_G).fillna(DEFAULT_EMISSIONS_G)
            )
        else:
            df["emissions_g"] = DEFAULT_EMISSIONS_G
    ensure_numeric(df, "emissions_g")
    df["emissions_kg"] = df["emissions_g"] / 1000.0
    return df

def compute_green_score(channel_df: pd.DataFrame) -> pd.DataFrame:
    df = channel_df.copy()
    if "attribution_weight" in df.columns:
        df = ensure_emissions(df)
        df["green_score"] = df.apply(
            lambda r: (r["attribution_weight"] / r["emissions_g"]) if r["emissions_g"] and r["emissions_g"] > 0 else math.nan,
            axis=1,
        )
    return df

def summarize_esg(df: pd.DataFrame) -> Dict[str, float]:
    """
    Computes ESG KPIs from available columns:
      - conversions
      - revenue_usd
      - emissions_g
    """
    if df is None or df.empty:
        return {
            "total_emissions_g": 0.0,
            "total_conversions": 0.0,
            "total_revenue_usd": 0.0,
            "CCPA_g_per_conv": math.nan,
            "eROAS_usd_per_kg": math.nan,
            "sustainability_eff_conv_per_kg": math.nan,
        }

    df = ensure_emissions(df)
    for c in ("conversions", "revenue_usd", "cost_usd"):
        if c in df.columns:
            ensure_numeric(df, c)
        else:
            df[c] = 0.0

    total_em_g = float(df["emissions_g"].sum(skipna=True))
    total_conv = float(df["conversions"].sum(skipna=True))
    total_rev = float(df["revenue_usd"].sum(skipna=True))
    total_em_kg = total_em_g / 1000.0

    ccpa = (total_em_g / total_conv) if total_conv > 0 else math.nan
    eroas = (total_rev / total_em_kg) if total_em_kg > 0 else math.nan
    seff = (total_conv / total_em_kg) if total_em_kg > 0 else math.nan

    return {
        "total_emissions_g": total_em_g,
        "total_conversions": total_conv,
        "total_revenue_usd": total_rev,
        "CCPA_g_per_conv": ccpa,
        "eROAS_usd_per_kg": eroas,
        "sustainability_eff_conv_per_kg": seff,
    }

def fmt(x: float, digits: int = 2) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "—"
    try:
        return f"{x:,.{digits}f}"
    except Exception:
        return str(x)

# =========================
# UI
# =========================
st.title("🌿 AdEco — Carbon-Aware Ad Attribution & Emission-Adjusted ROI")
st.caption("Streamlit dashboard for attribution, Green Score, and ESG-aware KPIs.")


st.sidebar.header("Settings")
API_BASE_URL = st.sidebar.text_input("API Base URL", value=API_BASE_URL)
st.sidebar.caption("Use http://localhost:8000 locally, or http://api:8000 in Docker Compose.")

# Optional: Add a refresh button for cache invalidation
if st.sidebar.button("Refresh data"):
    st.cache_data.clear()

if api_health():
    st.sidebar.success("API healthy ✅")
else:
    st.sidebar.warning("API not reachable / unhealthy ⚠️")

# Fetch data
channel_weights_df = fetch_channel_weights()
channel_kpis_df = fetch_channel_kpis()
journeys_df = fetch_journeys()

# Tabs
tabs = st.tabs([
    "Overview",
    "Journeys",
    "Channels",
    "Attribution vs Green Score",
    "Downloads",
])

# -------------------------
# Overview
# -------------------------
with tabs[0]:
    st.subheader("Derived ESG KPI Cards")

    # Prefer journey-level for totals; fallback to channel KPIs; fallback to channel weights with emissions only
    base_df = None
    source_note = ""
    if not journeys_df.empty:
        base_df = journeys_df
        source_note = f"Using journey-level data from {journeys_df.get('__source', ['?'])[0] if '__source' in journeys_df.columns else 'journeys endpoint'}"
    elif not channel_kpis_df.empty:
        base_df = channel_kpis_df
        source_note = f"Using channel KPI data from {channel_kpis_df.get('__source', ['?'])[0] if '__source' in channel_kpis_df.columns else 'channel KPI endpoint'}"
    else:
        base_df = channel_weights_df.copy()
        base_df["conversions"] = 0.0
        base_df["revenue_usd"] = 0.0
        base_df = ensure_emissions(base_df)
        source_note = "Using attribution weights only (no conversions/revenue returned by KPIs endpoints)."

    k = summarize_esg(base_df)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Emissions (gCO₂)", fmt(k["total_emissions_g"], 0))
    c2.metric("Total Conversions", fmt(k["total_conversions"], 0))
    c3.metric("Total Revenue ($)", fmt(k["total_revenue_usd"], 2))
    c4.metric("CCPA (gCO₂ / conv)", fmt(k["CCPA_g_per_conv"], 2))

    c5, c6, c7 = st.columns(3)
    c5.metric("eROAS ($ / kgCO₂)", fmt(k["eROAS_usd_per_kg"], 2))
    c6.metric("Sustainability Eff (conv / kgCO₂)", fmt(k["sustainability_eff_conv_per_kg"], 2))

    # Simple sustainability alert
    alert = ""
    if isinstance(k["CCPA_g_per_conv"], float) and not math.isnan(k["CCPA_g_per_conv"]) and k["CCPA_g_per_conv"] > 5000:
        alert = "High CCPA: consider shifting spend to lower-carbon channels."
    elif isinstance(k["eROAS_usd_per_kg"], float) and not math.isnan(k["eROAS_usd_per_kg"]) and k["eROAS_usd_per_kg"] < 10:
        alert = "Low eROAS: emissions-adjusted ROI is weak; optimize allocation."
    c7.metric("Sustainability Alert", alert or "—")

    st.caption(source_note)

# -------------------------
# Journeys
# -------------------------
with tabs[1]:
    st.subheader("Journey-level ESG visibility")
    if journeys_df.empty:
        st.info("No journey endpoint data detected. If you have it, add your endpoint path to fetch_journeys() candidates.")
    else:
        df = ensure_emissions(journeys_df)
        for c in ("conversions", "revenue_usd", "cost_usd"):
            if c in df.columns:
                ensure_numeric(df, c)
        # Total & avg emissions per journey
        st.write("**Total and average emissions per journey**")
        total_em = df["emissions_g"].sum()
        avg_em = df["emissions_g"].mean()
        a1, a2 = st.columns(2)
        a1.metric("Total journey emissions (gCO₂)", fmt(float(total_em), 0))
        a2.metric("Avg emissions per journey (gCO₂)", fmt(float(avg_em), 2))

        st.dataframe(df, use_container_width=True)

        st.download_button(
            "⬇️ Download journey-level CSV",
            df.to_csv(index=False).encode("utf-8"),
            file_name="adeco_journeys.csv",
            mime="text/csv",
            key="journey_csv_main"
        )

# -------------------------
# Channels
# -------------------------
with tabs[2]:
    st.subheader("Channel-level emissions + ESG KPIs")
    # Prefer backend channel KPIs; fallback to weights
    if not channel_kpis_df.empty:
        df = channel_kpis_df.copy()
        if "channel" not in df.columns and "key" in df.columns:
            # In case backend returned key/value (unlikely for channel KPIs)
            df = pd.DataFrame()
        if df.empty:
            st.warning("Channel KPI payload shape wasn't table-like. Check endpoint output.")
        else:
            df = ensure_emissions(df)
            for c in ("conversions", "revenue_usd", "cost_usd"):
                if c in df.columns:
                    ensure_numeric(df, c)

            # Per-channel derived ESG metrics
            df["CCPA_g_per_conv"] = df.apply(lambda r: (r["emissions_g"] / r["conversions"]) if r.get("conversions", 0) and r["conversions"] > 0 else math.nan, axis=1)
            df["eROAS_usd_per_kg"] = df.apply(lambda r: (r["revenue_usd"] / (r["emissions_g"]/1000.0)) if r["emissions_g"] > 0 else math.nan, axis=1)
            df["sust_eff_conv_per_kg"] = df.apply(lambda r: (r["conversions"] / (r["emissions_g"]/1000.0)) if r["emissions_g"] > 0 else math.nan, axis=1)

            show_cols = [c for c in ["channel","emissions_g","conversions","revenue_usd","CCPA_g_per_conv","eROAS_usd_per_kg","sust_eff_conv_per_kg"] if c in df.columns]
            st.dataframe(df[show_cols], use_container_width=True)

            st.write("**Emissions breakdown per ad channel**")
            if "channel" in df.columns:
                em = df.groupby("channel", as_index=False)["emissions_g"].sum()
                st.bar_chart(em, x="channel", y="emissions_g")

            st.download_button(
                "⬇️ Download channel-level CSV",
                df.to_csv(index=False).encode("utf-8"),
                file_name="adeco_channels.csv",
                mime="text/csv",
                key="channel_csv_main"
            )
    else:
        st.info("No channel KPI endpoint detected; showing attribution weights + emissions/Green Score only.")
        df = compute_green_score(channel_weights_df)
        if df.empty:
            st.warning("No attribution channel weights available.")
        else:
            st.dataframe(df, use_container_width=True)

# -------------------------
# Attribution vs Green Score
# -------------------------
with tabs[3]:
    st.subheader("Attribution vs Green Score")
    df = compute_green_score(channel_weights_df)
    if df.empty:
        st.info("No channel weights available.")
    else:
        # Table
        st.dataframe(df[["channel","attribution_weight","emissions_g","green_score"]], use_container_width=True)

        # Chart
        chart_df = df.set_index("channel")[["attribution_weight","green_score"]]
        st.bar_chart(chart_df)

# -------------------------
# Downloads
# -------------------------
with tabs[4]:
    st.subheader("Downloadable outputs")
    if not journeys_df.empty:
        st.download_button(
            "⬇️ Download journey-level CSV",
            ensure_emissions(journeys_df).to_csv(index=False).encode("utf-8"),
            file_name="adeco_journeys.csv",
            mime="text/csv",
            key="journey_csv_downloads"
        )

    if not channel_kpis_df.empty:
        st.download_button(
            "⬇️ Download channel-level CSV",
            ensure_emissions(channel_kpis_df).to_csv(index=False).encode("utf-8"),
            file_name="adeco_channels.csv",
            mime="text/csv",
            key="channel_csv_downloads"
        )

    # Always provide weights + green score
    w = compute_green_score(channel_weights_df)
    if not w.empty:
        st.download_button(
            "⬇️ Download attribution weights + Green Score CSV",
            w.to_csv(index=False).encode("utf-8"),
            file_name="adeco_attribution_green.csv",
            mime="text/csv",
            key="weights_green_csv_downloads"
        )

st.caption("Green Score = Attribution Score / Emissions (gCO₂)")
