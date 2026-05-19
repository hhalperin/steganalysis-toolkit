#!/usr/bin/env python3
"""
Script to reorganize src/ directory for better scalability and implement initial visualization structure.
Run from project root: python -m stega.tools.reorganize_src
"""

import os
import shutil
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT / "src"


def reorganize_src():
    """Reorganize src/ directory with new folder structure."""
    # Define the new structure
    new_structure = {
        "core": ["ai_enhanced_analyzer.py", "png_analyzer.py"],
        "cleaning": ["image_cleaner.py", "steganography_sanitizer.py"],
        "detection": ["steganography.py", "unicode_scanner.py", "chunk_analyzer.py", "pattern_identifier.py"],
        "models": [],
        "utils": [],
        "visualization": []
    }

    print("[REORG] Starting src/ reorganization...")

    # Step 1: Create new directories
    for folder in new_structure.keys():
        (SRC_DIR / folder).mkdir(exist_ok=True)
        print(f"[OK] Created directory: src/{folder}/")

    # Step 2: Move ai_models/ to models/
    if (SRC_DIR / "ai_models").exists():
        shutil.move(str(SRC_DIR / "ai_models"), str(SRC_DIR / "models"))
        print("[OK] Moved ai_models/ to models/")

    # Step 3: Move files to their new locations
    for folder, files in new_structure.items():
        for file in files:
            src_file = SRC_DIR / file
            dest_file = SRC_DIR / folder / file

            if src_file.exists():
                shutil.move(str(src_file), str(dest_file))
                print(f"[OK] Moved {file} to src/{folder}/")
            else:
                print(f"[WARN] File not found: {file}")

    # Step 4: Update import statements in moved files
    update_imports()

    # Step 5: Create __init__.py files for new packages
    for folder in new_structure.keys():
        init_file = SRC_DIR / folder / "__init__.py"
        if not init_file.exists():
            init_file.write_text('"""Package for {} functionality."""\n'.format(folder))
            print(f"[OK] Created __init__.py for src/{folder}/")

    # Step 6: Verify the new structure
    print("\n[STRUCTURE] New src/ structure:")
    for root, dirs, files in os.walk(SRC_DIR):
        level = root.replace(str(SRC_DIR), '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            if file.endswith('.py') and file != '__init__.py':
                print(f"{subindent}{file}")

    print("\n[SUCCESS] Reorganization completed successfully!")


def update_imports():
    """Update import statements in files to reflect new paths."""
    print("[IMPORTS] Updating import statements...")

    import_mappings = {
        "ai_enhanced_analyzer": "core.ai_enhanced_analyzer",
        "png_analyzer": "core.png_analyzer",
        "image_cleaner": "cleaning.image_cleaner",
        "steganography_sanitizer": "cleaning.steganography_sanitizer",
        "steganography": "detection.steganography",
        "unicode_scanner": "detection.unicode_scanner",
        "chunk_analyzer": "detection.chunk_analyzer",
        "pattern_identifier": "detection.pattern_identifier",
        "ai_models.ai_cleaner": "cleaning.ai_cleaner",
        "ai_models.ai_detector": "detection.ai_detector",
        "ai_models.model_manager": "models.model_manager",
        "ai_models.training": "models.training",
        "ai_models": "models",
    }

    for py_file in SRC_DIR.rglob("*.py"):
        try:
            content = py_file.read_text(encoding='utf-8')
            original_content = content

            for old, new in import_mappings.items():
                pattern = rf'from\s+{re.escape(old)}\s+import'
                content = re.sub(pattern, f'from {new} import', content)
                pattern = rf'import\s+{re.escape(old)}'
                content = re.sub(pattern, f'import {new}', content)

            if content != original_content:
                py_file.write_text(content, encoding='utf-8')
                print(f"[OK] Updated imports in {py_file}")
        except Exception as e:
            print(f"[WARN] Failed to update {py_file}: {e}")


def create_visualization_structure():
    """Create initial visualization module structure."""
    print("[VIS] Creating visualization module structure...")

    vis_dir = SRC_DIR / "visualization"

    files_to_create = {
        "battle_engine.py": '''"""
Battle Engine - Orchestrates the steganography battle simulation
Manages rounds, confidence tracking, and self-healing detection
"""

import time
from typing import Dict, List, Any
from ..core.ai_enhanced_analyzer import AIEnhancedAnalyzer
from ..detection.advanced_waste_detector import AdvancedWasteDetector

class BattleEngine:
    """Manages the battle between cleaning algorithms and watermarks."""

    def __init__(self):
        self.analyzer = AIEnhancedAnalyzer()
        self.detector = AdvancedWasteDetector()
        self.battle_state = {
            'round': 0,
            'max_rounds': 20,
            'confidence': 0.0,
            'waste_detected': {},
            'battle_log': []
        }

    def run_battle(self, image_path: str) -> Dict[str, Any]:
        """Run the full battle simulation."""
        return self.battle_state

''',
        "metaphors.py": '''"""
Visualization Metaphors - Create visual representations of cleaning process
Heat maps, ripples, particles, and battle visualization
"""

import numpy as np
import cv2
from typing import Dict, Any

def create_heat_map(image: np.ndarray, confidence_map: Dict[str, float]) -> np.ndarray:
    """Create heat map overlay for detected waste."""
    return image

def add_ripple_effect(image: np.ndarray, center: tuple, radius: int) -> np.ndarray:
    """Add ripple effect for cleaning algorithms."""
    return image

''',
        "frame_capture.py": '''"""
Frame Capture System - Efficiently capture battle progression
Memory management and compression for progressive snapshots
"""

import cv2
import os
from pathlib import Path
from typing import List

class FrameCapture:
    """Manages frame capture for battle visualization."""

    def __init__(self, output_dir: str = "battle_frames"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.frames: List[str] = []

    def capture_frame(self, image, round_num: int) -> str:
        """Capture a frame of the battle."""
        import numpy as np
        frame_path = self.output_dir / f"frame_{round_num:03d}.png"
        cv2.imwrite(str(frame_path), image)
        self.frames.append(str(frame_path))
        return str(frame_path)

''',
        "video_generator.py": '''"""
Video Generation Pipeline - Stitch frames into battle video
Multiple export formats with transition effects
"""

import cv2
from .frame_capture import FrameCapture

class VideoGenerator:
    """Generates battle video from captured frames."""

    def __init__(self, frame_capture: FrameCapture):
        self.frames = frame_capture.frames

    def generate_video(self, output_path: str, fps: int = 10) -> str:
        """Generate MP4 video from frames."""
        if not self.frames:
            return ""

        first_frame = cv2.imread(self.frames[0])
        height, width = first_frame.shape[:2]

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        for frame_path in self.frames:
            frame = cv2.imread(frame_path)
            video.write(frame)

        video.release()
        return output_path

''',
        "dashboard.py": '''"""
CLI Dashboard - Rich-based live battle display
Real-time updates and interactive controls
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

class BattleDashboard:
    """Rich-based dashboard for battle visualization."""

    def __init__(self):
        self.console = Console()

    def display_battle_status(self, battle_state):
        """Display current battle status."""
        pass

''',
        "__init__.py": '"""Visualization package for steganography battle simulation."""\n'
    }

    for filename, content in files_to_create.items():
        file_path = vis_dir / filename
        file_path.write_text(content)
        print(f"[OK] Created {filename} in src/visualization/")

    print("[SUCCESS] Visualization structure initialized!")


if __name__ == "__main__":
    reorganize_src()
    create_visualization_structure()
    print("\n[SUCCESS] Reorganization and visualization setup completed!")
