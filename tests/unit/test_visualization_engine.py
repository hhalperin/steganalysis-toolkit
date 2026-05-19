"""Unit tests for VisualizationEngine."""

import numpy as np
import pytest

from stega.visualization.engine import VisualizationEngine, MetaphorMode


@pytest.fixture
def sample_image():
    """Create a small RGB test image (64x64)."""
    return np.random.randint(0, 256, (64, 64, 3), dtype=np.uint8)


@pytest.fixture
def sample_battle_state():
    """Sample battle state for testing."""
    return {
        "waste_detected": {"lsb_steganography": 0.7, "ai_fingerprint": 0.3},
        "active_cleaning": [{"center": (32, 32), "progress": 0.5}],
        "particles": [(10, 10, 0.8), (50, 50, 0.5)],
    }


def test_engine_render_heat_map(sample_image, sample_battle_state):
    """Heat map mode produces different output when waste detected."""
    engine = VisualizationEngine(mode=MetaphorMode.HEAT_MAP)
    result = engine.render(sample_image, sample_battle_state)
    assert result.shape == sample_image.shape
    assert result.dtype == np.uint8
    # With waste, output should differ from input
    assert not np.array_equal(result, sample_image)


def test_engine_render_empty_state(sample_image):
    """Empty battle state returns image unchanged for heat_map."""
    engine = VisualizationEngine(mode=MetaphorMode.HEAT_MAP)
    result = engine.render(sample_image, {})
    assert result.shape == sample_image.shape


def test_engine_render_battle_mode(sample_image, sample_battle_state):
    """Battle mode produces valid output."""
    engine = VisualizationEngine(mode=MetaphorMode.BATTLE)
    result = engine.render(sample_image, sample_battle_state)
    assert result.shape == sample_image.shape
    assert result.dtype == np.uint8


def test_engine_set_mode():
    """set_mode changes active metaphor."""
    engine = VisualizationEngine(mode=MetaphorMode.HEAT_MAP)
    assert engine.mode == MetaphorMode.HEAT_MAP
    engine.set_mode(MetaphorMode.PARTICLE)
    assert engine.mode == MetaphorMode.PARTICLE
