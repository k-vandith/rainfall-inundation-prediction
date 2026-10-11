from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_dashboard_renders_without_browser() -> None:
    app_path = Path(__file__).resolve().parents[1] / "src" / "app.py"
    result = AppTest.from_file(str(app_path)).run(timeout=30)
    assert not result.exception



def test_dashboard_does_not_present_synthetic_terrain_scenario_as_a_flood_warning() -> None:
    app_path = Path(__file__).resolve().parents[1] / "src" / "app.py"
    source = app_path.read_text(encoding="utf-8")

    assert 'risk-title" style="color:{scenario_color}">SCENARIO ONLY' in source
    assert "not a local flood-risk classification or official warning" in source
    assert "Synthetic grid below water level" in source
    assert 'c4.metric("Grid below water level"' not in source
