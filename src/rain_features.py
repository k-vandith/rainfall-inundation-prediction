"""Rainfall data helpers for an exploratory early-warning dashboard.

The inundation calculation is a simple bathtub approximation, not a calibrated
hydraulic or operational flood model.
"""
from __future__ import annotations

from io import BytesIO, StringIO
import json
import math
import re
from typing import Any

import numpy as np
import pandas as pd


RAIN_COLUMNS = {
    "precipitation_mm",
    "rainfall_mm",
    "precipitation",
    "rainfall",
    "rain_mm",
    "precip_mm",
    "precipitation_mm_h",
}
TIME_COLUMNS = {"date", "datetime", "timestamp", "time", "valid_time"}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_UPLOAD_ROWS = 100_000


def synthetic_rainfall(hours: int = 168, seed: int = 42) -> pd.DataFrame:
    """Create a reproducible hourly rainfall series for demo and offline use."""
    if isinstance(hours, bool) or not isinstance(hours, (int, np.integer)) or not 1 <= hours <= MAX_UPLOAD_ROWS:
        raise ValueError("hours must be an integer between 1 and 100000")

    rng = np.random.default_rng(seed)
    idx = pd.date_range("2024-06-01", periods=int(hours), freq="h")
    rain = rng.exponential(0.5, size=int(hours))
    storm_count = min(3, max(1, int(hours) // 24))
    for _ in range(storm_count):
        start = int(rng.integers(0, max(1, int(hours) - 12)))
        rain[start : start + 12] += rng.uniform(5, 25)
    return pd.DataFrame({"date": idx, "precipitation_mm": rain, "source": "synthetic"})


def fetch_open_meteo(
    lat: float = 28.6,
    lon: float = 77.2,
    days: int = 7,
    timeout: float = 8.0,
) -> pd.DataFrame:
    """Fetch hourly forecast precipitation; fall back clearly to synthetic data offline."""
    if not math.isfinite(float(lat)) or not -90 <= float(lat) <= 90:
        raise ValueError("lat must be between -90 and 90")
    if not math.isfinite(float(lon)) or not -180 <= float(lon) <= 180:
        raise ValueError("lon must be between -180 and 180")
    if isinstance(days, bool) or not isinstance(days, (int, np.integer)) or not 1 <= int(days) <= 16:
        raise ValueError("days must be an integer between 1 and 16")
    if not math.isfinite(float(timeout)) or timeout <= 0:
        raise ValueError("timeout must be positive")

    from urllib.parse import urlencode
    from urllib.request import urlopen

    params = urlencode({
        "latitude": float(lat),
        "longitude": float(lon),
        "hourly": "precipitation",
        "forecast_days": int(days),
        "timezone": "auto",
    })
    url = f"https://api.open-meteo.com/v1/forecast?{params}"
    try:
        with urlopen(url, timeout=float(timeout)) as response:
            payload = json.loads(response.read().decode("utf-8"))
        hourly = payload.get("hourly", {})
        times = hourly.get("time", [])
        values = hourly.get("precipitation", [])
        if not times or len(times) != len(values):
            raise ValueError("Open-Meteo returned an incomplete hourly series")
        rain = pd.to_numeric(pd.Series(values), errors="coerce")
        dates = pd.to_datetime(pd.Series(times), errors="coerce")
        if rain.isna().any() or dates.isna().any() or not np.isfinite(rain.to_numpy(dtype=float)).all():
            raise ValueError("Open-Meteo returned invalid observations")
        if (rain < 0).any():
            raise ValueError("Open-Meteo returned negative precipitation")
        return pd.DataFrame({
            "date": dates,
            "precipitation_mm": rain.astype(float),
            "source": "open-meteo",
        })
    except Exception:
        fallback = synthetic_rainfall(hours=int(days) * 24)
        fallback["source"] = "synthetic-fallback"
        return fallback


def load_rainfall_csv(upload: bytes | bytearray | str | Any) -> pd.DataFrame:
    """Parse CSV input within the byte/row limits into sorted, normalized observations."""
    try:
        if isinstance(upload, (bytes, bytearray)):
            raw = bytes(upload)
            if len(raw) > MAX_UPLOAD_BYTES:
                raise ValueError("CSV must be 5 MB or smaller")
            if not raw.strip():
                raise ValueError("CSV contains no observations")
            source = BytesIO(raw)
        elif isinstance(upload, str):
            if len(upload.encode("utf-8")) > MAX_UPLOAD_BYTES:
                raise ValueError("CSV must be 5 MB or smaller")
            if not upload.strip():
                raise ValueError("CSV contains no observations")
            source = StringIO(upload)
        elif hasattr(upload, "read"):
            tell = getattr(upload, "tell", None)
            seek = getattr(upload, "seek", None)
            position = None
            if callable(tell) and callable(seek):
                try:
                    position = tell()
                except (OSError, ValueError):
                    position = None
            try:
                raw = upload.read(MAX_UPLOAD_BYTES + 1)
            finally:
                if position is not None:
                    try:
                        seek(position)
                    except (OSError, ValueError):
                        pass
            if isinstance(raw, str):
                if len(raw.encode("utf-8")) > MAX_UPLOAD_BYTES:
                    raise ValueError("CSV must be 5 MB or smaller")
                if not raw.strip():
                    raise ValueError("CSV contains no observations")
                source = StringIO(raw)
            elif isinstance(raw, (bytes, bytearray)):
                if len(raw) > MAX_UPLOAD_BYTES:
                    raise ValueError("CSV must be 5 MB or smaller")
                if not raw.strip():
                    raise ValueError("CSV contains no observations")
                source = BytesIO(bytes(raw))
            else:
                raise TypeError("file-like upload must return CSV bytes or text")
        else:
            raise TypeError("upload must be CSV bytes, text, or a file-like object")

        frame = pd.read_csv(source, nrows=MAX_UPLOAD_ROWS + 1)
    except pd.errors.EmptyDataError as error:
        raise ValueError("CSV contains no observations") from error

    if frame.empty:
        raise ValueError("CSV contains no observations")
    if len(frame) > MAX_UPLOAD_ROWS:
        raise ValueError("CSV must contain 100000 rows or fewer")

    normalized = {
        column: re.sub(r"[^a-z0-9]+", "_", str(column).strip().casefold()).strip("_")
        for column in frame.columns
    }
    rain_column = next((column for column, name in normalized.items() if name in RAIN_COLUMNS), None)
    time_column = next((column for column, name in normalized.items() if name in TIME_COLUMNS), None)
    if rain_column is None:
        raise ValueError("CSV needs a rainfall column such as precipitation_mm or rainfall_mm")

    rain = pd.to_numeric(frame[rain_column], errors="coerce")
    if rain.isna().any() or not np.isfinite(rain.to_numpy(dtype=float)).all():
        raise ValueError("Rainfall values must all be valid numbers")
    if (rain < 0).any():
        raise ValueError("Rainfall values cannot be negative")

    if time_column is not None:
        dates = pd.to_datetime(frame[time_column], errors="coerce", format="mixed", utc=True)
        if dates.isna().any():
            raise ValueError("Timestamp values must all be valid dates or times")
        if dates.duplicated().any():
            raise ValueError("CSV timestamps must be unique")
        order = np.argsort(dates.to_numpy(), kind="stable")
        dates = dates.iloc[order].reset_index(drop=True)
        rain = rain.iloc[order].reset_index(drop=True)
    else:
        dates = pd.Series(pd.date_range("2024-01-01", periods=len(frame), freq="h", tz="UTC"))

    if len(rain) < 5:
        raise ValueError("CSV needs at least 5 hourly observations")
    return pd.DataFrame({
        "date": dates,
        "precipitation_mm": rain.astype(float),
        "source": "uploaded-csv",
    })

def _ordered_rain_series(df: pd.DataFrame) -> pd.Series:
    """Validate rainfall values and, when present, order them by timestamp."""
    if "precipitation_mm" not in df.columns:
        raise ValueError("df must include precipitation_mm")
    rain = pd.to_numeric(df["precipitation_mm"], errors="coerce").astype(float)
    if rain.empty:
        raise ValueError("df must contain at least one rainfall observation")
    if rain.isna().any() or not np.isfinite(rain.to_numpy()).all() or (rain < 0).any():
        raise ValueError("Rainfall observations must be finite and non-negative")

    normalized = {
        column: re.sub(r"[^a-z0-9]+", "_", str(column).strip().casefold()).strip("_")
        for column in df.columns
    }
    time_column = next((column for column, name in normalized.items() if name in TIME_COLUMNS), None)
    if time_column is not None:
        dates = pd.to_datetime(df[time_column], errors="coerce", format="mixed", utc=True)
        if dates.isna().any():
            raise ValueError("Timestamp values must all be valid dates or times")
        if dates.duplicated().any():
            raise ValueError("Rainfall timestamps must be unique")
        order = np.argsort(dates.to_numpy(), kind="stable")
        rain = rain.iloc[order]
    return rain.reset_index(drop=True)


def train_heavy_rain_model(df: pd.DataFrame, threshold_mm: float = 10.0) -> dict[str, Any]:
    """Train a next-observation classifier and report chronological holdout accuracy.

    This estimates whether the *next time step* exceeds a rainfall threshold; it is
    not a flood-impact prediction. A rules backend is returned when ML is unavailable
    or the series is too short or has only one class in its training segment.
    """
    threshold = float(threshold_mm)
    if not math.isfinite(threshold) or threshold <= 0:
        raise ValueError("threshold_mm must be a positive finite number")
    rain = _ordered_rain_series(df)
    if len(rain) < 8:
        return {"backend": "rules", "model": None, "accuracy": None, "threshold_mm": threshold}

    features = pd.DataFrame({
        "lag1": rain,
        "lag2": rain.shift(1).fillna(0),
        "roll3": rain.rolling(3, min_periods=1).mean(),
    })
    target = (rain.shift(-1) >= threshold).astype(int)
    x = features.iloc[:-1]
    y = target.iloc[:-1]
    split = int(len(x) * 0.8)
    if split < 4 or len(x) - split < 2 or y.iloc[:split].nunique() < 2:
        return {"backend": "rules", "model": None, "accuracy": None, "threshold_mm": threshold}

    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import accuracy_score

        classifier = LogisticRegression(max_iter=300, random_state=42)
        classifier.fit(x.iloc[:split], y.iloc[:split])
        holdout_accuracy = float(accuracy_score(y.iloc[split:], classifier.predict(x.iloc[split:])))
        return {
            "backend": "scikit-learn",
            "model": classifier,
            "accuracy": holdout_accuracy,
            "threshold_mm": threshold,
            "feature_columns": list(features.columns),
        }
    except ImportError:
        return {"backend": "rules", "model": None, "accuracy": None, "threshold_mm": threshold}


def next_hour_heavy_rain_signal(df: pd.DataFrame, model_result: dict[str, Any]) -> dict[str, Any]:
    """Return either a classifier score or a clearly labelled, uncalibrated rule index."""
    rain = _ordered_rain_series(df)
    threshold = float(model_result.get("threshold_mm", 10.0))
    if not math.isfinite(threshold) or threshold <= 0:
        raise ValueError("model_result threshold_mm must be positive")

    classifier = model_result.get("model")
    if classifier is not None and len(rain) >= 3:
        recent = rain.iloc[-3:]
        features = pd.DataFrame([{
            "lag1": float(recent.iloc[-1]),
            "lag2": float(recent.iloc[-2]),
            "roll3": float(recent.mean()),
        }])
        score = float(classifier.predict_proba(features)[0][1])
        return {
            "score": float(np.clip(score, 0, 1)),
            "backend": "scikit-learn",
            "kind": "next-step classifier score; not an inundation probability",
        }

    recent = rain.tail(3).to_numpy(dtype=float)
    weights = np.array([0.15, 0.30, 0.55])[-len(recent):]
    weights = weights / weights.sum()
    index = float(np.clip(np.dot(recent, weights) / threshold, 0, 1))
    return {
        "score": index,
        "backend": "rules",
        "kind": "uncalibrated rainfall index; not a probability",
    }


def bathtub_inundation(dem: np.ndarray, water_level: float) -> dict[str, Any]:
    """Estimate water depth where a supplied elevation grid is below a water level."""
    grid = np.asarray(dem, dtype=float)
    level = float(water_level)
    if grid.ndim != 2 or grid.size == 0 or not np.isfinite(grid).all():
        raise ValueError("dem must be a non-empty 2D grid of finite elevations")
    if not math.isfinite(level):
        raise ValueError("water_level must be finite")

    flooded = grid < level
    depth = np.where(flooded, level - grid, 0.0)
    return {
        "flooded_cells": int(flooded.sum()),
        "total_cells": int(grid.size),
        "flood_fraction": float(flooded.mean()),
        "max_depth_m": float(depth.max()),
        "mean_depth_m": float(depth[flooded].mean()) if flooded.any() else 0.0,
        "depth_grid": depth,
    }


def alert_level(precip_mm: float, flood_fraction: float) -> str:
    """Map simple rainfall and bathtub indicators to a demo alert band."""
    precipitation = float(precip_mm)
    fraction = float(flood_fraction)
    if not math.isfinite(precipitation) or precipitation < 0:
        raise ValueError("precip_mm must be finite and non-negative")
    if not math.isfinite(fraction) or not 0 <= fraction <= 1:
        raise ValueError("flood_fraction must be between 0 and 1")

    if precipitation >= 50 or fraction >= 0.4:
        return "severe"
    if precipitation >= 20 or fraction >= 0.2:
        return "warning"
    if precipitation >= 10 or fraction >= 0.05:
        return "watch"
    return "normal"
