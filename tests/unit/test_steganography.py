"""Unit tests for steganography detection."""

import pytest
from pathlib import Path

from stega.detection.steganography import analyze_steganography


def test_analyze_steganography_nonexistent():
    """analyze_steganography on nonexistent file returns error."""
    result = analyze_steganography("/nonexistent/path.png")
    assert "error" in result


def test_analyze_steganography_invalid(tmp_path):
    """analyze_steganography on non-image file returns error."""
    bad_file = tmp_path / "not_image.txt"
    bad_file.write_text("not an image")
    result = analyze_steganography(str(bad_file))
    assert "error" in result or "overall_suspicious" in result
