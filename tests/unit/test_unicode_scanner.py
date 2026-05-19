"""Unit tests for unicode scanner."""

import pytest

from stega.detection.unicode_scanner import scan_unicode_in_text


def test_scan_unicode_in_text_structure():
    """scan_unicode_in_text returns expected structure."""
    result = scan_unicode_in_text("a")
    assert "suspicious_characters" in result
    assert "patterns" in result


def test_scan_unicode_in_text_normal():
    """scan_unicode_in_text on normal ASCII returns no suspicious."""
    result = scan_unicode_in_text("Hello world 123")
    assert len(result.get("suspicious_characters", [])) == 0
