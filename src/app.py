"""Rainfall and inundation operations view."""
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from src.rain_features import alert_level, bathtub_inundation, synthetic_rainfall, train_heavy_rain_model
from src.ui_theme import theme_css

@st.cache_data
def _rain(hours: int):
    df = synthetic_rainfall(days=hours, seed=7)
    model = train_heavy_rain_model(df)
    return df, {k: v for k, v in model.items() if k != "model"}

def main() -> None:
    st.set_page_config(page_title="Rainfall EWS", layout="wide")
    st.markdown(theme_css("#4aa3df"), unsafe_allow_html=True)
    st.markdown('<div class="top"><div><div class="kicker">Early warning</div><p class="title">Rainfall and inundation</p></div><div class="pill">Synthetic series · offline</div></div>', unsafe_allow_html=True)
    hours = st.sidebar.slider("Hours", 48, 240, 120, 24)
    level = st.sidebar.slider("Water level (m)", 0.5, 8.0, 3.2, 0.1)
    df, model = _rain(hours)
    latest = float(df["precipitation_mm"].iloc[-1])
    dem = np.linspace(0, 6, 40)[:, None] + np.linspace(0, 2, 40)[None, :]
    flood = bathtub_inundation(dem, level)
    alert = alert_level(latest, flood["flood_fraction"])
    st.markdown(f'<div class="panel"><div class="kicker">Current risk</div><p class="title">{alert}</p><p class="muted">Latest hour {latest:.1f} mm · flood fraction {flood["flood_fraction"]:.0%} · model {model.get("backend")}</p></div>', unsafe_allow_html=True)
    fig = go.Figure(go.Scatter(x=df["date"], y=df["precipitation_mm"], name="Rain", line=dict(color="#4aa3df")))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e7ecf3", height=300, title="Precipitation")
    st.plotly_chart(fig, use_container_width=True)
    depth = flood["depth_grid"]
    heat = px.imshow(depth, color_continuous_scale="Blues", origin="lower", title="Bathtub inundation depth (m)")
    heat.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#e7ecf3", height=420)
    st.plotly_chart(heat, use_container_width=True)

if __name__ == "__main__":
    main()
