"""Unit tests for SimpleTextRemover."""

import pytest
from pathlib import Path

# Add project root to path
import sys
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from stega.cleaning.simple_text_remover import SimpleTextRemover


def test_simple_text_remover_initialization():
    """Test SimpleTextRemover initializes correctly."""
    remover = SimpleTextRemover()
    assert remover is not None


def test_detect_repeated_patterns_empty_image():
    """Test detect_repeated_patterns on non-existent file returns empty."""
    remover = SimpleTextRemover()
    result = remover.detect_repeated_patterns("/nonexistent/path.png")
    assert result == []


def test_group_similar_contours_empty():
    """Test _group_similar_contours with empty input."""
    remover = SimpleTextRemover()
    result = remover._group_similar_contours([])
    assert result == []
