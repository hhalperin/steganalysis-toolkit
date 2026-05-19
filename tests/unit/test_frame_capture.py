"""Unit tests for FrameCapture."""

import numpy as np
import pytest
from pathlib import Path

from stega.visualization.frame_capture import FrameCapture


@pytest.fixture
def sample_image():
    """Create a small RGB test image."""
    return np.random.randint(0, 256, (32, 32, 3), dtype=np.uint8)


def test_capture_frame(tmp_path, sample_image):
    """Capture frame saves file and returns path."""
    fc = FrameCapture(output_dir=str(tmp_path))
    path = fc.capture_frame(sample_image, 1)
    assert Path(path).exists()
    assert path in fc.get_frame_paths()
    assert fc.frames == fc.get_frame_paths()


def test_capture_multiple_frames(tmp_path, sample_image):
    """Multiple captures accumulate frame paths."""
    fc = FrameCapture(output_dir=str(tmp_path))
    fc.capture_frame(sample_image, 1)
    fc.capture_frame(sample_image, 2)
    assert len(fc.get_frame_paths()) == 2


def test_memory_buffer_bounded(tmp_path, sample_image):
    """Memory buffer respects max_memory_frames."""
    fc = FrameCapture(output_dir=str(tmp_path), max_memory_frames=2)
    fc.capture_frame(sample_image, 1)
    fc.capture_frame(sample_image, 2)
    fc.capture_frame(sample_image, 3)
    assert len(fc.get_buffered_frames()) == 2


def test_clear_memory_buffer(tmp_path, sample_image):
    """clear_memory_buffer releases buffer."""
    fc = FrameCapture(output_dir=str(tmp_path), max_memory_frames=5)
    fc.capture_frame(sample_image, 1)
    fc.clear_memory_buffer()
    assert len(fc.get_buffered_frames()) == 0
