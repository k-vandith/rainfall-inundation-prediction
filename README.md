# Rainfall & Inundation Prediction

A local Streamlit workspace for exploring hourly rainfall series, a next-step heavy-rain signal, and a simplified inundation-grid scenario.

## Run locally

```bash
python -m pip install -r requirements.txt
streamlit run src/app.py
# Or use: python run.py
```

## Data sources

- **Synthetic demo:** deterministic hourly data; works offline.
- **Open-Meteo:** hourly precipitation forecast by latitude/longitude. If unavailable, the UI labels its synthetic fallback.
- **CSV upload:** use `precipitation_mm` or `rainfall_mm`; a `date`, `datetime`, `timestamp`, or `time` column is optional. Uploads are limited to 5 MB / 100,000 rows and require at least five valid non-negative observations. When timestamps are supplied, they must be unique and exactly one hour apart so the next-step signal remains hourly. Use the downloadable template.

The dashboard exports cleaned observations as CSV and scenario details as JSON.

## Tests

```bash
python -m pip install -r requirements-dev.txt
pytest -v
ruff check src/app.py src/rain_features.py src/ui_theme.py run.py tests
```

## Interpretation and limitations

The heavy-rain classifier targets whether the next time step exceeds a rainfall threshold; its accuracy is measured on a chronological holdout. If a model cannot be trained, a rules-based rainfall index is shown instead. Neither is a calibrated flood probability.

The bathtub calculation uses an illustrative elevation grid, not local surveyed terrain, drainage, or a hydrodynamic model. Alert bands are generic research indicators, not official warnings. Calibrate and validate with local hydrology and observed data before operational use.

## License

MIT
