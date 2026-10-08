# Rainfall & Inundation Prediction

Time-series rainfall prediction and flood-risk estimation using synthetic data.

Distinguishes **rainfall prediction**, **flood-risk estimation**, and **observed flooding**.

## Installation

```bash
python3 -m venv .venv && source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

Windows: `python -m venv .venv` then `.venv\Scripts\Activate.ps1`

## Demo
```bash
python scripts/generate_demo_data.py
pytest -v
```

## License
MIT
