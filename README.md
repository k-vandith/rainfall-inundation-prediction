# Rainfall & Inundation Prediction

Early-warning oriented rainfall and inundation risk scoring from time-series inputs, with synthetic data for offline demos.

## Problem Statement

Municipal and emergency planners need lightweight models that convert rainfall intensity time series into inundation risk indicators when full hydrodynamic models are unavailable.

## Overview

Ingest rainfall series, compute rolling statistics and risk bands, and visualise forecasts in Streamlit. Demo mode generates synthetic storms for training and tests.

## Features

- **Time-series risk scoring**
- **Rolling window features**
- **Inundation risk bands** (low / medium / high)
- **Streamlit + Plotly dashboards**
- **Synthetic storm generator**

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Streamlit  │────▶│  Rainfall    │────▶│  Risk model │
│     UI      │     │  pipeline    │     │             │
└─────────────┘     └──────┬───────┘     └─────────────┘
                           │
                    ┌──────▼───────┐
                    │  CSV series  │
                    └──────────────┘
```

## Tech Stack

- Python 3.11+
- Pandas / NumPy
- Streamlit + Plotly
- pytest

## Repository Structure

```
rainfall-inundation-prediction/
├── README.md
├── requirements.txt
├── src/
│   └── rainfall.py
├── tests/
│   └── test_rain.py
├── data/
├── scripts/
│   ├── setup_env.py
│   ├── setup.sh
│   ├── setup.ps1
│   └── generate_demo_data.py
└── docs/
```

## System Requirements

| Mode | CPU | RAM | Disk | GPU |
|------|-----|-----|------|-----|
| Demo | Any | 1 GB | 500 MB | Not needed |

## Installation

### Recommended (all platforms) — automated bootstrap

Handles missing `ensurepip`, symlink restrictions, and installs dependencies into `.venv`:

```bash
git clone https://github.com/k-vandith/rainfall-inundation-prediction.git
cd rainfall-inundation-prediction
python3 scripts/setup_env.py    # or:  python scripts/setup_env.py
```

Then activate:

```bash
# Linux / macOS
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

### Manual setup

#### Windows (PowerShell)

```powershell
git clone https://github.com/k-vandith/rainfall-inundation-prediction.git
cd rainfall-inundation-prediction
python -m venv .venv --copies
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

#### Linux / macOS

```bash
git clone https://github.com/k-vandith/rainfall-inundation-prediction.git
cd rainfall-inundation-prediction
# If venv fails with ensurepip errors:
#   sudo apt install python3-venv python3-pip
python3 -m venv .venv --copies
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Why `--copies`?

Some environments cannot create symlinks inside a venv (`Operation not permitted` on `lib64 → lib`). Using `--copies` avoids that. `scripts/setup_env.py` tries `--copies` first automatically.

## Environment Variables

None required.

## Dataset / Demo Mode

```bash
python scripts/generate_demo_data.py
```

## Running the Application

```bash
streamlit run src/rainfall.py
```

## API Usage

```python
from src.rainfall import run_pipeline
print(run_pipeline("data/demo_rain.csv"))
```

## Testing

```bash
pytest -v
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError: src` | Run from project root; ensure `PYTHONPATH=.` |
| `venv` / ensurepip fails | Run `python3 scripts/setup_env.py` or install `python3-venv` |
| `Operation not permitted` on lib64 | Use `python3 -m venv .venv --copies` |
| Missing dependency | Activate `.venv` and re-run `pip install -r requirements.txt` |

## Limitations

- Not a full 2D hydrodynamic flood model.
- Local calibration required for operational use.
- Synthetic data only approximates real catchments.

## Security / Privacy

- No personal data required.
- Operational deployments should validate against local hydrology expertise.

## Future Improvements

- Coupling with DEM / drainage layers
- Multi-station spatial interpolation
- Alert webhook integrations

## License

MIT
