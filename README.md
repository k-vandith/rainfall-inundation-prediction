# Rainfall & Inundation Prediction

<p align="center">
  <img src="assets/rainfall-inundation-logo.svg" alt="Rainfall and inundation prediction logo" width="160" />
</p>

A local Streamlit workspace for exploring hourly rainfall series, a next-step heavy-rain signal, and a simplified inundation-grid scenario.

## Run locally

```bash
python -m pip install -r requirements.txt
streamlit run src/app.py
# Or use: python run.py
```

## Data sources

- **Synthetic demo:** deterministic hourly data; works offline.
- **Open-Meteo:** hourly precipitation forecast by latitude/longitude. If the request fails or the response is invalid, the app shows an error and returns no substitute readings. Choose **Synthetic demo** explicitly for offline sample data.
- **CSV upload:** use `precipitation_mm` or `rainfall_mm`; a `date`, `datetime`, `timestamp`, or `time` column is optional. Uploads are limited to 5 MB / 100,000 rows and require at least five valid non-negative observations. When timestamps are supplied, they must be unique and exactly one hour apart so the next-step signal remains hourly. Use the downloadable template.

The dashboard exports cleaned observations as CSV and scenario details as JSON.

## Tests

```bash
python -m pip install -r requirements-dev.txt
pytest -v
ruff check src/app.py src/rain_features.py src/ui_theme.py run.py tests
```

## Interpretation and limitations

The heavy-rain classifier targets whether the next time step exceeds a rainfall threshold; it is not an inundation model. Holdout accuracy is reported only for uploaded observed rainfall series. Synthetic demo and Open-Meteo forecast input do not provide independent observed ground truth, so the app does not report model accuracy for those sources. If a model cannot be trained, a rules-based rainfall index may be shown; it is not a calibrated probability.

The bathtub calculation uses an illustrative elevation grid, not local surveyed terrain, drainage, or a hydrodynamic model. Alert bands are generic research indicators, not official warnings. Calibrate and validate with local hydrology and observed data before operational use.

## License

MIT
