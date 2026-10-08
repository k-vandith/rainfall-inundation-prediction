"""Rainfall prediction and flood-risk estimation from synthetic time series."""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

def generate_series(days: int = 365, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2024-01-01", periods=days, freq="D")
    rain = np.clip(rng.gamma(1.5, 2.0, size=days) * (rng.random(days) > 0.4), 0, 80)
    return pd.DataFrame({"date": dates, "rainfall_mm": rain})

def predict_next(df: pd.DataFrame, window: int = 7) -> float:
    return float(df["rainfall_mm"].tail(window).mean())

def flood_risk(rainfall_mm: float, threshold: float = 25.0) -> dict:
    if rainfall_mm >= threshold * 1.5:
        level = "HIGH"
        score = min(1.0, rainfall_mm / (threshold * 2))
    elif rainfall_mm >= threshold:
        level = "MEDIUM"
        score = 0.5 + 0.3 * (rainfall_mm - threshold) / threshold
    else:
        level = "LOW"
        score = rainfall_mm / threshold * 0.4
    return {"predicted_rainfall_mm": round(rainfall_mm, 2), "risk_level": level, "risk_score": round(float(score), 3),
            "note": "Risk estimation is model-based, not observed flooding."}
