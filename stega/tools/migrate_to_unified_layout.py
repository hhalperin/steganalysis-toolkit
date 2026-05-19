#!/usr/bin/env python3
"""
Migrate assets to unified dirty/processing/clean layout per Document Management Refactor Plan.
Run from project root: python -m stega.tools.migrate_to_unified_layout
"""

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "assets"


def migrate():
    # 1. Create processing and samples
    (ASSETS / "processing").mkdir(parents=True, exist_ok=True)
    (ASSETS / "samples").mkdir(parents=True, exist_ok=True)

    # 2. Create assets/dirty - merge dirty-images, input, and root Logo
    dirty = ASSETS / "dirty"
    dirty.mkdir(parents=True, exist_ok=True)

    for legacy in [ASSETS / "dirty-images", ASSETS / "input"]:
        if legacy.exists():
            for item in legacy.iterdir():
                dst = dirty / item.name
                if item.is_dir():
                    if dst.exists():
                        for f in item.iterdir():
                            if f.is_file() and not (dst / f.name).exists():
                                shutil.copy2(f, dst / f.name)
                    else:
                        shutil.copytree(item, dst, dirs_exist_ok=True)
                elif item.is_file():
                    shutil.copy2(item, dst)

    # Merge root Logo into assets/dirty/logo
    root_logo = ROOT / "Logo"
    if root_logo.exists():
        logo_dst = dirty / "logo"
        logo_dst.mkdir(parents=True, exist_ok=True)
        for f in root_logo.iterdir():
            if f.is_file():
                shutil.copy2(f, logo_dst / f.name)

    # 3. Create assets/clean - merge cleaned and output
    clean = ASSETS / "clean"
    clean.mkdir(parents=True, exist_ok=True)

    for legacy in [ASSETS / "cleaned", ASSETS / "output"]:
        if legacy.exists():
            for item in legacy.iterdir():
                dst = clean / item.name
                if item.is_dir():
                    if dst.exists():
                        for f in item.iterdir():
                            if f.is_file() and not (dst / f.name).exists():
                                shutil.copy2(f, dst / f.name)
                    else:
                        shutil.copytree(item, dst, dirs_exist_ok=True)
                elif item.is_file():
                    shutil.copy2(item, dst)

    # 4. Merge reports
    reports = ASSETS / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    detection_reports = ASSETS / "detection_reports"
    if detection_reports.exists():
        for f in detection_reports.iterdir():
            if f.is_file() and not (reports / f.name).exists():
                shutil.copy2(f, reports / f.name)

    # 5. Move root cleaned/battle_report.txt
    root_cleaned = ROOT / "cleaned"
    if root_cleaned.exists():
        battle_report = root_cleaned / "battle_report.txt"
        if battle_report.exists():
            shutil.copy2(battle_report, reports / "battle_report.txt")

    # 6. Move visible_watermark_test_results to test-results
    test_results = ASSETS / "test-results"
    test_results.mkdir(parents=True, exist_ok=True)
    vwtr = ASSETS / "visible_watermark_test_results"
    if vwtr.exists():
        vwtr_dst = test_results / "visible_watermark"
        vwtr_dst.mkdir(parents=True, exist_ok=True)
        for f in vwtr.iterdir():
            if f.is_file():
                shutil.copy2(f, vwtr_dst / f.name)

    # 7. Create text_watermark test results dir if referenced
    (test_results / "text_watermark").mkdir(parents=True, exist_ok=True)

    print("Migration complete. New layout: assets/dirty/, assets/processing/, assets/clean/, assets/reports/, assets/samples/, assets/test-results/")


if __name__ == "__main__":
    migrate()
