"""Rainfall/inundation: Open-Meteo fetch + synthetic fallback, ML, bathtub DEM."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd

def fetch_open_meteo(lat: float = 28.6, lon: float = 77.2, days: int = 7) -> pd.DataFrame:
    try:
        import urllib.request
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=precipitation_sum&forecast_days={min(days,16)}&timezone=auto"
        with urllib.request.urlopen(url, timeout=8) as resp:
            data = json.loads(resp.read().decode())
        daily = data.get("daily", {})
        df = pd.DataFrame({"date": daily.get("time", []), "precipitation_mm": daily.get("precipitation_sum", [])})
        if not df.empty:
            df["source"] = "open-meteo"; return df
    except Exception:
        pass
    return synthetic_rainfall(days=days*24)

def synthetic_rainfall(days: int = 168, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2024-06-01", periods=days, freq="h")
    base = rng.exponential(0.5, size=days)
    for _ in range(3):
        start = rng.integers(0, max(1, days-12)); base[start:start+12] += rng.uniform(5, 25)
    return pd.DataFrame({"date": idx, "precipitation_mm": base, "source": "synthetic"})

def train_heavy_rain_model(df: pd.DataFrame, threshold_mm: float = 10.0) -> dict[str, Any]:
    df = df.copy(); df["y"] = (df["precipitation_mm"] >= threshold_mm).astype(int)
    df["lag1"] = df["precipitation_mm"].shift(1).fillna(0); df["lag2"] = df["precipitation_mm"].shift(2).fillna(0)
    df["roll3"] = df["precipitation_mm"].rolling(3, min_periods=1).mean()
    X, y = df[["lag1","lag2","roll3"]].values, df["y"].values
    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import accuracy_score
        clf = LogisticRegression(max_iter=200); clf.fit(X, y)
        return {"backend": "sklearn", "model": clf, "accuracy": float(accuracy_score(y, clf.predict(X))), "threshold_mm": threshold_mm}
    except ImportError:
        return {"backend": "rules", "model": None, "accuracy": None, "threshold_mm": threshold_mm}

def bathtub_inundation(dem: np.ndarray, water_level: float) -> dict[str, Any]:
    dem = np.asarray(dem, float); flooded = dem < water_level; depth = np.where(flooded, water_level-dem, 0.0)
    return {"flooded_cells": int(flooded.sum()), "total_cells": int(dem.size), "flood_fraction": float(flooded.mean()), "max_depth_m": float(depth.max()), "mean_depth_m": float(depth[flooded].mean()) if flooded.any() else 0.0, "depth_grid": depth}

def alert_level(precip_mm: float, flood_fraction: float) -> str:
    if precip_mm >= 50 or flood_fraction >= 0.4: return "severe"
    if precip_mm >= 20 or flood_fraction >= 0.2: return "warning"
    if precip_mm >= 10 or flood_fraction >= 0.05: return "watch"
    return "normal"
