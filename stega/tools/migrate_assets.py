#!/usr/bin/env python3
"""
One-time migration: move assets from legacy layout to unified layout.
Use consolidate_assets_final for full consolidation (includes removal of legacy dirs).
Run from project root: python -m stega.tools.migrate_assets
"""

import shutil
from pathlib import Path

project_root = Path(__file__).resolve().parents[2]
new_dirty = project_root / "assets" / "dirty"
new_clean = project_root / "assets" / "clean"
new_reports = project_root / "assets" / "reports"

# Legacy paths (may not exist after consolidate_assets_final)
legacy_sources = [
    (project_root / "assets" / "dirty-images", new_dirty),
    (project_root / "assets" / "input", new_dirty),
    (project_root / "assets" / "cleaned", new_clean),
    (project_root / "assets" / "output", new_clean),
]


def migrate():
    for legacy, new_base in legacy_sources:
        if legacy.exists():
            for sub in legacy.iterdir():
                if sub.is_dir():
                    dst = new_base / sub.name
                    dst.mkdir(parents=True, exist_ok=True)
                    for f in sub.iterdir():
                        if f.is_file() and not (dst / f.name).exists():
                            shutil.copy2(f, dst / f.name)
                    print(f"Migrated to {new_base.name}: {sub.name}")
                elif sub.is_file():
                    if not (new_base / sub.name).exists():
                        shutil.copy2(sub, new_base / sub.name)
    new_dirty.mkdir(parents=True, exist_ok=True)
    new_clean.mkdir(parents=True, exist_ok=True)
    new_reports.mkdir(parents=True, exist_ok=True)

    legacy_reports = project_root / "assets" / "detection_reports"
    if legacy_reports.exists():
        for f in legacy_reports.iterdir():
            if f.is_file() and not (new_reports / f.name).exists():
                shutil.copy2(f, new_reports / f.name)
        print("Migrated reports")
    print("Migration complete. New layout: assets/dirty/, assets/clean/, assets/reports/")


if __name__ == "__main__":
    migrate()
