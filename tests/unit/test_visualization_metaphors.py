"""Unit tests for visualization metaphors."""

import numpy as np
import pytest

from stega.visualization.metaphors import (
    create_heat_map,
    add_ripple_effect,
    create_particle_effect,
    create_battle_overlay,
)


@pytest.fixture
def sample_image():
    """Create a small RGB test image."""
    return np.random.randint(0, 256, (64, 64, 3), dtype=np.uint8)


def test_create_heat_map_empty(sample_image):
    """Empty confidence map returns image unchanged."""
    result = create_heat_map(sample_image, {})
    assert result.shape == sample_image.shape
    assert np.array_equal(result, sample_image)


def test_create_heat_map_with_data(sample_image):
    """Heat map with confidence data produces output."""
    confidence_map = {"lsb_steganography": 0.8}
    result = create_heat_map(sample_image, confidence_map)
    assert result.shape == sample_image.shape
    assert result.dtype == np.uint8


def test_add_ripple_effect(sample_image):
    """Ripple effect produces valid output."""
    result = add_ripple_effect(sample_image, (32, 32), 20)
    assert result.shape == sample_image.shape
    assert result.dtype == np.uint8


def test_create_particle_effect_empty(sample_image):
    """Empty particles returns image unchanged."""
    result = create_particle_effect(sample_image, [])
    assert result.shape == sample_image.shape
    assert np.array_equal(result, sample_image)


def test_create_particle_effect_with_particles(sample_image):
    """Particle effect with particles produces output."""
    particles = [(10, 10, 0.8), (50, 50, 0.5)]
    result = create_particle_effect(sample_image, particles)
    assert result.shape == sample_image.shape
    assert result.dtype == np.uint8


def test_create_battle_overlay(sample_image):
    """Battle overlay combines metaphors."""
    battle_state = {
        "waste_detected": {"lsb_steganography": 0.5},
        "active_cleaning": [{"center": (32, 32)}],
        "particles": [(20, 20, 0.6)],
    }
    result = create_battle_overlay(sample_image, battle_state)
    assert result.shape == sample_image.shape
    assert result.dtype == np.uint8
