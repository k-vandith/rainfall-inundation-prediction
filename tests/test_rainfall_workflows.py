from __future__ import annotations

import json
import urllib.request

import numpy as np
import pandas as pd
import pytest

from src.rain_features import (
    alert_level,
    bathtub_inundation,
    fetch_open_meteo,
    load_rainfall_csv,
    next_hour_heavy_rain_signal,
    synthetic_rainfall,
    train_heavy_rain_model,
)


def test_synthetic_rainfall_is_hourly_and_reproducible() -> None:
    first = synthetic_rainfall(hours=48, seed=5)
    second = synthetic_rainfall(hours=48, seed=5)
    assert len(first) == 48
    assert first["date"].diff().dropna().eq(pd.Timedelta(hours=1)).all()
    assert (first["precipitation_mm"] >= 0).all()
    pd.testing.assert_frame_equal(first, second)


@pytest.mark.parametrize("value", [0, -1, 1.5, True, 100001])
def test_synthetic_rainfall_rejects_invalid_hours(value: object) -> None:
    with pytest.raises(ValueError):
        synthetic_rainfall(hours=value)  # type: ignore[arg-type]


def test_csv_upload_normalizes_columns_and_sorts_time() -> None:
    csv = (
        "Timestamp,Rainfall (mm)\n"
        "2025-01-01 03:00,3.0\n"
        "2025-01-01 01:00,1.0\n"
        "2025-01-01 05:00,5.0\n"
        "2025-01-01 02:00,2.0\n"
        "2025-01-01 04:00,4.0\n"
    )
    frame = load_rainfall_csv(csv.encode("utf-8"))
    assert list(frame["precipitation_mm"]) == [1, 2, 3, 4, 5]
    assert frame["source"].eq("uploaded-csv").all()
    assert frame["date"].is_monotonic_increasing


@pytest.mark.parametrize(
    ("csv", "message"),
    [
        ("date,temperature\n2025-01-01,20\n2025-01-02,22\n2025-01-03,18\n2025-01-04,23\n2025-01-05,19\n", "rainfall column"),
        ("precipitation_mm\n1\n2\n-3\n4\n5\n", "cannot be negative"),
        ("precipitation_mm\n1\n2\n", "at least 5"),
        ("date,precipitation_mm\nnot-a-date,1\n2025-01-02,2\n2025-01-03,3\n2025-01-04,4\n2025-01-05,5\n", "valid dates"),
    ],
)
def test_csv_upload_rejects_invalid_data(csv: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        load_rainfall_csv(csv)


def test_csv_upload_limits_bytes() -> None:
    with pytest.raises(ValueError, match="5 MB"):
        load_rainfall_csv(b"x" * (5 * 1024 * 1024 + 1))


def test_open_meteo_returns_hourly_observations(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "hourly": {
            "time": ["2026-10-10T00:00", "2026-10-10T01:00"],
            "precipitation": [0.0, 2.5],
        }
    }

    class Response:
        def __enter__(self) -> "Response":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps(payload).encode("utf-8")

    def fake_urlopen(url: str, timeout: float) -> Response:
        assert "hourly=precipitation" in url
        assert timeout > 0
        return Response()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    frame = fetch_open_meteo(lat=17.3, lon=78.4, days=1)
    assert len(frame) == 2
    assert list(frame["precipitation_mm"]) == [0.0, 2.5]
    assert frame["source"].eq("open-meteo").all()


def test_open_meteo_failure_is_visible_as_synthetic_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(url: str, timeout: float) -> None:
        raise OSError("offline")

    monkeypatch.setattr(urllib.request, "urlopen", fail)
    frame = fetch_open_meteo(days=1)
    assert len(frame) == 24
    assert frame["source"].eq("synthetic-fallback").all()


@pytest.mark.parametrize(
    ("lat", "lon", "days"),
    [(91, 0, 1), (0, 181, 1), (0, 0, 17), (float("nan"), 0, 1)],
)
def test_open_meteo_rejects_invalid_parameters(lat: float, lon: float, days: int) -> None:
    with pytest.raises(ValueError):
        fetch_open_meteo(lat=lat, lon=lon, days=days)


def _storm_series() -> pd.DataFrame:
    cycle = [0, 0, 0, 15, 20, 5, 0, 0, 12, 18, 0, 1]
    rain = (cycle * 10)[:120]
    return pd.DataFrame({
        "date": pd.date_range("2025-01-01", periods=len(rain), freq="h"),
        "precipitation_mm": rain,
    })


def test_model_uses_next_step_target_and_holdout_metric() -> None:
    frame = _storm_series()
    model = train_heavy_rain_model(frame, threshold_mm=10)
    assert model["backend"] == "scikit-learn"
    assert model["accuracy"] is not None
    assert 0 <= model["accuracy"] <= 1
    signal = next_hour_heavy_rain_signal(frame, model)
    assert signal["backend"] == "scikit-learn"
    assert 0 <= signal["score"] <= 1
    assert "not an inundation probability" in signal["kind"]


def test_short_series_uses_labeled_rules_index() -> None:
    frame = synthetic_rainfall(hours=4)
    model = train_heavy_rain_model(frame)
    signal = next_hour_heavy_rain_signal(frame, model)
    assert model["backend"] == "rules"
    assert signal["backend"] == "rules"
    assert 0 <= signal["score"] <= 1
    assert "not a probability" in signal["kind"]


def test_inundation_depth_and_edge_cases() -> None:
    result = bathtub_inundation(np.array([[0.0, 1.0], [2.0, 3.0]]), water_level=2.0)
    assert result["flooded_cells"] == 2
    assert result["flood_fraction"] == 0.5
    assert result["max_depth_m"] == 2.0
    assert result["mean_depth_m"] == 1.5
    with pytest.raises(ValueError, match="2D"):
        bathtub_inundation(np.array([0, 1, 2]), water_level=2.0)
    with pytest.raises(ValueError, match="finite"):
        bathtub_inundation(np.array([[float("nan")]]), water_level=2.0)


@pytest.mark.parametrize(
    ("rain", "fraction", "expected"),
    [
        (0, 0, "normal"),
        (10, 0, "watch"),
        (20, 0, "warning"),
        (50, 0, "severe"),
        (0, 0.4, "severe"),
    ],
)
def test_alert_bands(rain: float, fraction: float, expected: str) -> None:
    assert alert_level(rain, fraction) == expected


@pytest.mark.parametrize(("rain", "fraction"), [(-1, 0), (float("nan"), 0), (1, 1.2)])
def test_alert_rejects_invalid_values(rain: float, fraction: float) -> None:
    with pytest.raises(ValueError):
        alert_level(rain, fraction)
