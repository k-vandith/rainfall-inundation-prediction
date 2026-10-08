from src.rainfall import generate_series, predict_next, flood_risk
def test_flow():
    df = generate_series(60)
    pred = predict_next(df)
    r = flood_risk(pred)
    assert r["risk_level"] in ("LOW", "MEDIUM", "HIGH")
