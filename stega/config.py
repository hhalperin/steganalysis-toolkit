"""
Centralized path configuration for assets and outputs.
Unified layout: assets/dirty, assets/processing, assets/clean, assets/reports.
"""

from pathlib import Path

# Project root (parent of stega/)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

ASSETS_ROOT = _PROJECT_ROOT / "assets"

# Unified semantic paths (preferred)
DIRTY_DIR = ASSETS_ROOT / "dirty"
PROCESSING_DIR = ASSETS_ROOT / "processing"
CLEAN_DIR = ASSETS_ROOT / "clean"
REPORTS_DIR = ASSETS_ROOT / "reports"
SAMPLES_DIR = ASSETS_ROOT / "samples"
TEST_RESULTS_DIR = ASSETS_ROOT / "test-results"
BATTLE_VIDEOS_DIR = ASSETS_ROOT / "battle-videos"

# Aliases for backward compatibility
INPUT_DIR = DIRTY_DIR
OUTPUT_DIR = CLEAN_DIR


def dirty_path(dataset: str = "") -> Path:
    """Raw input directory, optionally for a dataset subdir (e.g. 'sample-emblem', 'logo')."""
    return DIRTY_DIR / dataset if dataset else DIRTY_DIR


def processing_path(dataset: str = "") -> Path:
    """Intermediate output directory."""
    return PROCESSING_DIR / dataset if dataset else PROCESSING_DIR


def clean_path(dataset: str = "") -> Path:
    """Final output directory."""
    return CLEAN_DIR / dataset if dataset else CLEAN_DIR


def input_path(dataset: str = "") -> Path:
    """Input directory (alias for dirty_path)."""
    return dirty_path(dataset)


def output_path(dataset: str = "") -> Path:
    """Output directory (alias for clean_path)."""
    return clean_path(dataset)


def reports_path(dataset: str = "") -> Path:
    """Reports directory."""
    return REPORTS_DIR / dataset if dataset else REPORTS_DIR


def ensure_dirs():
    """Create dirty, processing, clean, reports dirs if they do not exist."""
    DIRTY_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSING_DIR.mkdir(parents=True, exist_ok=True)
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    TEST_RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def resolve_input_dir(dataset: str) -> Path:
    """Resolve input dir: assets/dirty/{dataset}."""
    return DIRTY_DIR / dataset


def resolve_output_dir(dataset: str) -> Path:
    """Resolve output dir: assets/clean/{dataset}."""
    return CLEAN_DIR / dataset


def resolve_reports_dir() -> Path:
    """Resolve reports dir: assets/reports."""
    return REPORTS_DIR
