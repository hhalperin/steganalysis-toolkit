"""Unit tests for PNGChunkAnalyzer."""

import pytest
from pathlib import Path

from stega.detection.chunk_analyzer import PNGChunkAnalyzer, analyze_png_chunks


def test_analyze_png_chunks_nonexistent():
    """analyze_png_chunks on nonexistent file returns error."""
    result = analyze_png_chunks("/nonexistent/path.png")
    assert "error" in result


def test_analyze_png_chunks_invalid_file(tmp_path):
    """analyze_png_chunks on non-PNG file returns error or empty chunks."""
    bad_file = tmp_path / "not_png.txt"
    bad_file.write_text("not a png")
    result = analyze_png_chunks(str(bad_file))
    assert "total_chunks" in result or "error" in result


def test_chunk_analyzer_invalid_file(tmp_path):
    """PNGChunkAnalyzer parse_chunks on non-PNG returns False."""
    bad_file = tmp_path / "not_png.txt"
    bad_file.write_text("not a png")
    analyzer = PNGChunkAnalyzer(bad_file)
    result = analyzer.parse_chunks()
    assert result is False
    assert len(analyzer.suspicious_findings) > 0
