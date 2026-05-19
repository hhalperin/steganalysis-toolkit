"""Unit tests for BattleDashboard."""

import json
import pytest
from pathlib import Path

from stega.visualization.dashboard import BattleDashboard


@pytest.fixture
def sample_battle_state():
    """Sample battle state for export tests."""
    return {
        "image_path": "/tmp/test.png",
        "round": 5,
        "max_rounds": 50,
        "confidence": 0.7,
        "waste_detected": {"lsb_steganography": 0.3},
        "self_healing_detected": False,
        "active_cleaning": [{"method": "lsb_natural", "progress": 0.5}],
        "battle_log": ["[1] Round 1", "[2] Round 2"],
    }


def test_export_report_json(tmp_path, sample_battle_state):
    """Export report to JSON produces valid file."""
    dashboard = BattleDashboard()
    out = tmp_path / "report.json"
    path = dashboard.export_report(sample_battle_state, str(out), format="json")
    assert Path(path).exists()
    with open(path) as f:
        data = json.load(f)
    assert data["round"] == 5
    assert data["confidence"] == 0.7


def test_export_report_txt(tmp_path, sample_battle_state):
    """Export report to TXT produces valid file."""
    dashboard = BattleDashboard()
    out = tmp_path / "report.txt"
    path = dashboard.export_report(sample_battle_state, str(out), format="txt")
    assert Path(path).exists()
    content = Path(path).read_text()
    assert "STEGANOGRAPHY RESILIENCE REPORT" in content
    assert "Round 5" in content or "Rounds" in content


def test_build_layout(sample_battle_state):
    """_build_layout produces valid Layout."""
    dashboard = BattleDashboard()
    layout = dashboard._build_layout(sample_battle_state)
    assert layout is not None
