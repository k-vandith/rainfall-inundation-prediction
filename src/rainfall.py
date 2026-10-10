"""Small baseline helpers for rainfall-series CSVs.

These functions provide a transparent trailing-mean baseline, not a trained
meteorological forecast or a calibrated flood model.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def generate_series(days: int = 365, seed: int = 42) -> pd.DataFrame:
    """Generate a reproducible daily demo series."""
    if isinstance(days, bool) or not isinstance(days, (int, np.integer)) or not 1 <= days <= 100_000:
        raise ValueError("days must be an integer between 1 and 100000")
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2024-01-01", periods=int(days), freq="D")
    rain = np.clip(rng.gamma(1.5, 2.0, size=int(days)) * (rng.random(int(days)) > 0.4), 0, 80)
    return pd.DataFrame({"date": dates, "rainfall_mm": rain})


def _rain_column(df: pd.DataFrame) -> pd.Series:
    """Resolve the baseline module's supported rainfall column names."""
    column = "rainfall_mm" if "rainfall_mm" in df else "precipitation_mm" if "precipitation_mm" in df else None
    if column is None:
        raise ValueError("df must include rainfall_mm or precipitation_mm")
    rain = pd.to_numeric(df[column], errors="coerce").astype(float)
    if rain.empty or rain.isna().any() or not np.isfinite(rain.to_numpy()).all() or (rain < 0).any():
        raise ValueError("rainfall observations must be finite, non-negative numbers")
    return rain


def predict_next(df: pd.DataFrame, window: int = 7) -> float:
    """Return the mean of the most recent window as a transparent baseline."""
    if isinstance(window, bool) or not isinstance(window, (int, np.integer)) or window < 1:
        raise ValueError("window must be a positive integer")
    rain = _rain_column(df)
    return float(rain.tail(int(window)).mean())


def flood_risk(rainfall_mm: float, threshold: float = 25.0) -> dict[str, float | str]:
    """Convert a rainfall estimate to a generic demo risk band."""
    rain = float(rainfall_mm)
    limit = float(threshold)
    if not np.isfinite(rain) or rain < 0:
        raise ValueError("rainfall_mm must be finite and non-negative")
    if not np.isfinite(limit) or limit <= 0:
        raise ValueError("threshold must be a positive finite number")

    if rain >= limit * 1.5:
        level = "HIGH"
        score = min(1.0, rain / (limit * 2))
    elif rain >= limit:
        level = "MEDIUM"
        score = 0.5 + 0.3 * (rain - limit) / limit
    else:
        level = "LOW"
        score = rain / limit * 0.4
    return {
        "predicted_rainfall_mm": round(rain, 2),
        "risk_level": level,
        "risk_score": round(float(score), 3),
        "note": "Trailing-mean baseline only; not observed flooding or an official warning.",
    }


def run_pipeline(
    csv_path: str | Path,
    window: int = 7,
    threshold: float = 25.0,
) -> dict[str, float | int | str]:
    """Load a CSV and return a baseline estimate plus the generic risk band."""
    path = Path(csv_path)
    if not path.is_file():
        raise FileNotFoundError(f"Rainfall CSV not found: {path}")
    frame = pd.read_csv(path)
    rain = _rain_column(frame)
    estimate = predict_next(pd.DataFrame({"rainfall_mm": rain}), window=window)
    result = flood_risk(estimate, threshold=threshold)
    return {
        "observations": int(len(rain)),
        "window": int(window),
        "method": "trailing-mean baseline",
        **result,
    }
