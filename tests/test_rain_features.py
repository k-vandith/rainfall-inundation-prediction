import numpy as np
import pandas as pd
import pytest

from src.rain_features import alert_level, bathtub_inundation, synthetic_rainfall, train_heavy_rain_model


def test_hourly_rain_is_deterministic() -> None:
    first = synthetic_rainfall(hours=48, seed=7)
    second = synthetic_rainfall(hours=48, seed=7)
    assert len(first) == 48
    assert first["date"].diff().dropna().eq(pd.Timedelta(hours=1)).all()
    pd.testing.assert_frame_equal(first, second)


def test_model_and_inundation_smoke() -> None:
    frame = synthetic_rainfall(hours=120)
    model = train_heavy_rain_model(frame)
    assert model["backend"] in ("scikit-learn", "rules")
    flood = bathtub_inundation(np.linspace(0, 8, 100).reshape(10, 10), 5.0)
    assert flood["flooded_cells"] > 0
    assert 0 <= flood["flood_fraction"] <= 1
    assert alert_level(60, flood["flood_fraction"]) == "severe"


def test_inundation_rejects_bad_grids() -> None:
    with pytest.raises(ValueError):
        bathtub_inundation(np.array([1, 2, 3]), 2.0)



def test_synthetic_rain_does_not_claim_operational_holdout_accuracy() -> None:
    frame = synthetic_rainfall(hours=120, seed=42)
    model = train_heavy_rain_model(frame)

    assert model["backend"] == "rules"
    assert model["model"] is None
    assert model["accuracy"] is None
    assert model["evaluation_scope"] == "demo_or_forecast_input_not_observed_ground_truth"
    assert model["operationally_validated"] is False
