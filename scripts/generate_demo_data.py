from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.rainfall import generate_series
p = Path(__file__).resolve().parents[1] / "data" / "sample" / "rainfall.csv"
p.parent.mkdir(parents=True, exist_ok=True)
generate_series().to_csv(p, index=False)
print("Wrote", p)
