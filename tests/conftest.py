"""Pytest configuration and shared fixtures."""

import sys
import warnings
from pathlib import Path

# Project root on path (see pyproject [tool.pytest.ini_options] pythonpath)
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Suppress numpy overflow warnings in detection (see docs/CLEANING_METHODOLOGIES.md)
warnings.filterwarnings(
    "ignore", category=RuntimeWarning, message=".*overflow.*"
)
