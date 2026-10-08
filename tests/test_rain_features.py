from src.rain_features import synthetic_rainfall, bathtub_inundation, alert_level, train_heavy_rain_model
import numpy as np
def test_rain():
    df = synthetic_rainfall(48)
    train_heavy_rain_model(df)
    dem = np.linspace(0, 10, 100).reshape(10, 10)
    assert bathtub_inundation(dem, 5.0)["flooded_cells"] > 0
    assert alert_level(60, 0.5) == "severe"
