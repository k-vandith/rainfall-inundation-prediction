import pandas as pd
import pytest

from src.rainfall import flood_risk, generate_series, predict_next, run_pipeline


def test_generated_series_is_reproducible_and_daily() -> None:
    first = generate_series(60, seed=7)
    second = generate_series(60, seed=7)
    assert len(first) == 60
    assert first["date"].diff().dropna().eq(pd.Timedelta(days=1)).all()
    pd.testing.assert_frame_equal(first, second)


def test_flow() -> None:
    frame = generate_series(60)
    prediction = predict_next(frame)
    result = flood_risk(prediction)
    assert result["risk_level"] in ("LOW", "MEDIUM", "HIGH")
    assert 0 <= result["risk_score"] <= 1


def test_pipeline_accepts_precipitation_column(tmp_path) -> None:
    file_path = tmp_path / "rainfall.csv"
    pd.DataFrame({"precipitation_mm": [1, 2, 3, 4, 5, 6, 7]}).to_csv(file_path, index=False)
    report = run_pipeline(file_path, window=3, threshold=5)
    assert report["observations"] == 7
    assert report["predicted_rainfall_mm"] == 6.0
    assert report["risk_level"] == "MEDIUM"
    assert report["method"] == "trailing-mean baseline"


@pytest.mark.parametrize("window", [0, -1, 1.5, True])
def test_predict_rejects_invalid_window(window) -> None:
    with pytest.raises(ValueError, match="window"):
        predict_next(generate_series(10), window=window)


@pytest.mark.parametrize("threshold", [0, -1, float("nan")])
def test_risk_rejects_invalid_threshold(threshold) -> None:
    with pytest.raises(ValueError, match="threshold"):
        flood_risk(5, threshold=threshold)



def test_predict_next_uses_latest_timestamps_not_csv_row_order():
    frame = pd.DataFrame(
        {
            "date": [
                "2025-01-06", "2025-01-02", "2025-01-05", "2025-01-01",
                "2025-01-07", "2025-01-03", "2025-01-04",
            ],
            "rainfall_mm": [6, 2, 5, 1, 7, 3, 4],
        }
    )

    assert predict_next(frame, window=2) == 6.5


def test_run_pipeline_uses_latest_timestamp_rows(tmp_path):
    path = tmp_path / "unordered.csv"
    pd.DataFrame(
        {
            "timestamp": [
                "2025-01-06", "2025-01-02", "2025-01-05", "2025-01-01",
                "2025-01-07", "2025-01-03", "2025-01-04",
            ],
            "rainfall_mm": [6, 2, 5, 1, 7, 3, 4],
        }
    ).to_csv(path, index=False)

    result = run_pipeline(path, window=2, threshold=5)

    assert result["predicted_rainfall_mm"] == 6.5


def test_predict_next_rejects_unparseable_timestamps():
    frame = pd.DataFrame({"date": ["not-a-date"] * 5, "rainfall_mm": [1, 2, 3, 4, 5]})

    with pytest.raises(ValueError, match="timestamps must all be valid"):
        predict_next(frame)
