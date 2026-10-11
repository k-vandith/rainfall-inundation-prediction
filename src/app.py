"""Rainfall early-warning workspace — synthetic, forecast, and CSV workflows."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.rain_features import (
    alert_level,
    bathtub_inundation,
    fetch_open_meteo,
    load_rainfall_csv,
    next_hour_heavy_rain_signal,
    synthetic_rainfall,
    train_heavy_rain_model,
)
from src.ui_theme import theme_css


@st.cache_data
def _rain(hours: int, seed: int = 7) -> pd.DataFrame:
    return synthetic_rainfall(hours=hours, seed=seed)


def _sample_csv() -> bytes:
    sample = synthetic_rainfall(hours=48, seed=11).drop(columns="source")
    return sample.to_csv(index=False).encode("utf-8")


def _hourly_frame(frame: pd.DataFrame) -> pd.DataFrame:
    clean = frame.copy()
    clean["date"] = pd.to_datetime(clean["date"], errors="coerce")
    clean["precipitation_mm"] = pd.to_numeric(clean["precipitation_mm"], errors="coerce")
    clean = clean.dropna(subset=["date", "precipitation_mm"]).sort_values("date").reset_index(drop=True)
    if clean.empty:
        raise ValueError("There are no valid rainfall observations to plot.")
    clean["source"] = clean.get("source", pd.Series(["unknown"] * len(clean))).fillna("unknown")
    return clean


def main() -> None:
    st.set_page_config(
        page_title="Rainfall / Inundation Monitor",
        page_icon="🌧️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(theme_css("#2dd4bf", danger="#fb7185", ok="#34d399", warn="#fbbf24"), unsafe_allow_html=True)
    st.markdown(
        """
        <div class="top">
          <div>
            <div class="kicker">Hydrometeorology · Field console 01</div>
            <p class="title">Rainfall / inundation monitor</p>
            <p class="muted">Explore hourly rainfall signals and a simplified elevation-grid scenario.</p>
          </div>
          <div class="pill">LOCAL WORKSPACE · RESEARCH USE</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown("### Scenario controls")
        source_mode = st.radio(
            "Rainfall source",
            ["CSV upload", "Open-Meteo forecast", "Synthetic demo"],
            help="Synthetic data works offline. Open-Meteo requires internet. CSV upload expects hourly observations.",
        )
        window_hours = st.slider("Window / horizon (hours)", min_value=48, max_value=240, value=120, step=24)
        threshold = st.slider(
            "Heavy-rain threshold (mm/hour)",
            min_value=5.0,
            max_value=50.0,
            value=10.0,
            step=1.0,
        )
        water_level = st.slider("Scenario water level (m)", min_value=0.5, max_value=8.0, value=3.2, step=0.1)
        st.divider()
        st.caption("The water level and elevation grid are illustrative inputs, not measured local terrain.")

    preview_only = False
    if source_mode == "Open-Meteo forecast":
        left, right = st.columns(2)
        with left:
            latitude = st.number_input("Latitude", min_value=-90.0, max_value=90.0, value=17.3850, step=0.01, format="%.4f")
        with right:
            longitude = st.number_input("Longitude", min_value=-180.0, max_value=180.0, value=78.4867, step=0.01, format="%.4f")
        with st.spinner("Loading hourly forecast or offline fallback…"):
            df = fetch_open_meteo(
                lat=float(latitude),
                lon=float(longitude),
                days=max(1, min(16, math.ceil(window_hours / 24))),
            ).tail(window_hours).reset_index(drop=True)
        source_label = str(df["source"].iloc[0])
        if source_label == "synthetic-fallback":
            st.warning("Open-Meteo could not be reached. This view is using synthetic fallback data, not a live forecast.")
    elif source_mode == "CSV upload":
        uploaded = st.file_uploader(
            "Upload rainfall CSV",
            type=["csv"],
            help="Required rainfall column: precipitation_mm or rainfall_mm. A date/time column is optional.",
        )
        st.download_button(
            "Download CSV template",
            data=_sample_csv(),
            file_name="rainfall-template.csv",
            mime="text/csv",
            use_container_width=True,
        )
        if uploaded is None:
            st.info("Upload a CSV to analyse observed rainfall. No synthetic prediction is shown until you choose Synthetic demo explicitly.")
            st.stop()
        else:
            try:
                df = load_rainfall_csv(uploaded.getvalue()).tail(window_hours).reset_index(drop=True)
                source_label = "uploaded CSV"
            except (ValueError, TypeError, UnicodeDecodeError, pd.errors.ParserError) as exc:
                st.error(f"Could not read this CSV: {exc}")
                st.stop()
    else:
        df = _rain(window_hours)
        source_label = "synthetic demo"

    try:
        df = _hourly_frame(df)
        if len(df) < 5:
            st.warning("Fewer than five valid observations: results should be treated as a minimal demonstration.")
        rain = df["precipitation_mm"].astype(float)
        latest = float(rain.iloc[-1])
        peak = float(rain.max())
        rolling_24h = float(rain.tail(24).sum())
        dem = np.linspace(0, 6, 40)[:, None] + np.linspace(0, 2, 40)[None, :]
        flood = bathtub_inundation(dem, float(water_level))
        alert = alert_level(latest, flood["flood_fraction"])
        model = train_heavy_rain_model(df, threshold_mm=float(threshold))
        signal = next_hour_heavy_rain_signal(df, model)
    except (ValueError, TypeError, KeyError) as exc:
        st.error(f"Unable to build this scenario: {exc}")
        st.stop()

    alert_colors = {
        "normal": "#34d399",
        "watch": "#fbbf24",
        "warning": "#fb923c",
        "severe": "#fb7185",
    }
    alert_color = alert_colors[alert]
    st.markdown(
        f"""
        <div class="panel risk-panel">
          <div>
            <div class="kicker">Scenario status</div>
            <p class="risk-title" style="color:{alert_color}">{alert.upper()}</p>
            <p class="muted">Current indicator · latest observation {latest:.1f} mm/hour · source: {source_label}</p>
          </div>
          <div class="risk-mark" style="border-color:{alert_color};color:{alert_color}">●</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Latest rainfall", f"{latest:.1f} mm", help="Last available observation; it may be forecast or uploaded data.")
    c2.metric("Peak in series", f"{peak:.1f} mm/h")
    c3.metric("Rain in last 24 rows", f"{rolling_24h:.1f} mm")
    c4.metric("Grid below water level", f"{flood['flood_fraction']:.0%}")

    if model.get("backend") == "scikit-learn" and model.get("accuracy") is not None:
        st.caption(
            f"Next-step classifier · chronological holdout accuracy {model['accuracy']:.0%} · "
            "measures heavy-rain classification only, not flood probability."
        )
    else:
        st.caption(
            "Next-step signal is using a rules-based rainfall index. It is not a calibrated probability or a flood forecast."
        )

    left, right = st.columns([1.35, 1])
    with left:
        chart = go.Figure()
        chart.add_trace(
            go.Scatter(
                x=df["date"], y=rain, mode="lines",
                line={"color": "#2dd4bf", "width": 2},
                fill="tozeroy", fillcolor="rgba(45,212,191,0.12)", name="Hourly rainfall",
            )
        )
        chart.add_trace(
            go.Scatter(
                x=df["date"], y=rain.rolling(6, min_periods=1).sum(),
                mode="lines", line={"color": "#60a5fa", "width": 1.5, "dash": "dot"},
                name="Rolling 6-row total",
            )
        )
        chart.update_layout(
            title="Rainfall timeline",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e7ecf3",
            height=370,
            margin={"l": 8, "r": 8, "t": 48, "b": 8},
            legend={"orientation": "h", "y": 1.12, "x": 0},
            xaxis_title=None,
            yaxis_title="Precipitation (mm)",
        )
        st.plotly_chart(chart, width="stretch", config={"displayModeBar": False})

    with right:
        heat = px.imshow(
            flood["depth_grid"],
            color_continuous_scale=[[0, "#101821"], [0.2, "#155e75"], [0.65, "#2dd4bf"], [1, "#d9f99d"]],
            origin="lower",
            title="Illustrative bathtub depth",
            labels={"x": "Grid column", "y": "Grid row", "color": "Depth (m)"},
        )
        heat.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e7ecf3",
            height=370,
            margin={"l": 8, "r": 8, "t": 48, "b": 8},
        )
        st.plotly_chart(heat, width="stretch", config={"displayModeBar": False})

    detail_a, detail_b, detail_c = st.columns(3)
    detail_a.metric("Flooded grid cells", f"{flood['flooded_cells']:,} / {flood['total_cells']:,}")
    detail_b.metric("Maximum modelled depth", f"{flood['max_depth_m']:.2f} m")
    detail_c.metric("Heavy-rain signal index", f"{signal['score']:.0%}", help=signal["kind"])

    with st.expander("Inspect observations"):
        st.dataframe(df.tail(48).sort_values("date", ascending=False), use_container_width=True, hide_index=True)

    report = {
        "generated_at_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "source": source_label,
        "preview_only": preview_only,
        "observations": int(len(df)),
        "period_start": str(df["date"].iloc[0]),
        "period_end": str(df["date"].iloc[-1]),
        "latest_precipitation_mm": round(latest, 3),
        "peak_precipitation_mm": round(peak, 3),
        "last_24_rows_total_mm": round(rolling_24h, 3),
        "scenario_alert": alert,
        "water_level_m": float(water_level),
        "bathtub_flood_fraction": round(float(flood["flood_fraction"]), 4),
        "bathtub_max_depth_m": round(float(flood["max_depth_m"]), 3),
        "heavy_rain_signal_score": round(float(signal["score"]), 4),
        "heavy_rain_signal_backend": signal["backend"],
        "heavy_rain_signal_interpretation": signal["kind"],
        "classifier_holdout_accuracy": model.get("accuracy"),
        "limitations": [
            "The alert band is a simple rule, not a warning issued by a local authority.",
            "The bathtub grid is synthetic and does not represent surveyed terrain or drainage.",
            "The heavy-rain signal does not estimate flood probability or impacts.",
        ],
    }
    st.divider()
    st.markdown("### Export this run")
    out_a, out_b = st.columns(2)
    with out_a:
        st.download_button(
            "Download cleaned rainfall CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="rainfall-observations.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with out_b:
        st.download_button(
            "Download scenario report (JSON)",
            data=json.dumps(report, indent=2, default=str),
            file_name="rainfall-scenario-report.json",
            mime="application/json",
            use_container_width=True,
        )
    st.caption(
        "Research/demo tool only. The elevation grid is invented, the alert thresholds are generic, "
        "and the model is not validated for operational flood warnings."
    )


if __name__ == "__main__":
    main()
