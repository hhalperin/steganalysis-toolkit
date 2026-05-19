#!/usr/bin/env python3
"""
Final asset consolidation: rename dirs, merge content, remove empty/legacy.
Run from project root: python -m stega.tools.consolidate_assets_final
"""

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "assets"


def consolidate():
    # 1. Ensure target dirs exist
    for d in ["dirty", "clean", "processing", "reports", "samples", "test-results", "battle-videos"]:
        (ASSETS / d).mkdir(parents=True, exist_ok=True)

    # 2. Merge dirty-images -> dirty (by dataset subdir or root files)
    legacy_dirty = ASSETS / "dirty-images"
    if legacy_dirty.exists():
        for item in legacy_dirty.iterdir():
            dst = ASSETS / "dirty" / item.name
            if item.is_dir():
                dst.mkdir(parents=True, exist_ok=True)
                for f in item.iterdir():
                    if f.is_file():
                        target = dst / f.name
                        if not target.exists() or target.stat().st_mtime < f.stat().st_mtime:
                            shutil.copy2(f, target)
            elif item.is_file():
                if not (ASSETS / "dirty" / item.name).exists():
                    shutil.copy2(item, ASSETS / "dirty" / item.name)

    # 3. Merge cleaned -> clean
    legacy_clean = ASSETS / "cleaned"
    if legacy_clean.exists():
        for item in legacy_clean.iterdir():
            dst = ASSETS / "clean" / item.name
            if item.is_dir():
                dst.mkdir(parents=True, exist_ok=True)
                for f in item.iterdir():
                    if f.is_file():
                        target = dst / f.name
                        if not target.exists() or target.stat().st_mtime < f.stat().st_mtime:
                            shutil.copy2(f, target)
            elif item.is_file():
                if not (ASSETS / "clean" / item.name).exists():
                    shutil.copy2(item, ASSETS / "clean" / item.name)

    # 4. Merge input -> dirty, output -> clean (if exist)
    for legacy, target_name in [(ASSETS / "input", "dirty"), (ASSETS / "output", "clean")]:
        if legacy.exists():
            for item in legacy.iterdir():
                dst = ASSETS / target_name / item.name
                if item.is_dir():
                    dst.mkdir(parents=True, exist_ok=True)
                    for f in item.iterdir():
                        if f.is_file():
                            target = dst / f.name
                            if not target.exists():
                                shutil.copy2(f, target)
                elif item.is_file():
                    if not (ASSETS / target_name / item.name).exists():
                        shutil.copy2(item, ASSETS / target_name / item.name)

    # 5. Merge detection_reports -> reports
    if (ASSETS / "detection_reports").exists():
        for f in (ASSETS / "detection_reports").iterdir():
            if f.is_file() and not (ASSETS / "reports" / f.name).exists():
                shutil.copy2(f, ASSETS / "reports" / f.name)

    # 6. Merge visible_watermark_test_results -> test-results/visible_watermark
    vwtr = ASSETS / "visible_watermark_test_results"
    if vwtr.exists():
        dst = ASSETS / "test-results" / "visible_watermark"
        dst.mkdir(parents=True, exist_ok=True)
        for f in vwtr.iterdir():
            if f.is_file():
                target = dst / f.name
                if not target.exists() or target.stat().st_mtime < f.stat().st_mtime:
                    shutil.copy2(f, target)

    # 7. Move root Logo -> assets/dirty/logo
    root_logo = ROOT / "Logo"
    if root_logo.exists():
        logo_dst = ASSETS / "dirty" / "logo"
        logo_dst.mkdir(parents=True, exist_ok=True)
        for f in root_logo.iterdir():
            if f.is_file():
                shutil.copy2(f, logo_dst / f.name)

    # 8. Move root cleaned/battle_report.txt -> assets/reports
    root_cleaned = ROOT / "cleaned"
    if root_cleaned.exists():
        br = root_cleaned / "battle_report.txt"
        if br.exists():
            shutil.copy2(br, ASSETS / "reports" / "battle_report.txt")

    # 9. Move root sample PNGs -> assets/samples (if exist)
    for name in ["copy_simple_cleaned.png", "grad-image_simple_cleaned.png", "sample_clean.png", "sample_with_lsb.png", "sample_with_unicode.png"]:
        f = ROOT / name
        if f.exists():
            shutil.copy2(f, ASSETS / "samples" / name)

    # 10. Remove legacy/duplicate directories
    for to_remove in [
        "dirty-images", "cleaned", "input", "output", "detection_reports",
        "visible_watermark_test_results"
    ]:
        path = ASSETS / to_remove
        if path.exists():
            shutil.rmtree(path)
            print(f"Removed: assets/{to_remove}")

    # 11. Remove root cleaned and Logo (after copy)
    if root_cleaned.exists():
        shutil.rmtree(root_cleaned)
        print("Removed: root cleaned/")
    if root_logo.exists():
        shutil.rmtree(root_logo)
        print("Removed: root Logo/")

    # 12. Remove only legacy empty dirs (keep processing, samples for structure)
    legacy_empty = ["input", "output"]
    for name in legacy_empty:
        path = ASSETS / name
        if path.exists() and path.is_dir() and not any(path.iterdir()):
            path.rmdir()
            print(f"Removed empty: assets/{name}")

    # 13. Add .gitkeep to processing/samples if empty (preserve structure)
    for d in ["processing", "samples"]:
        p = ASSETS / d
        p.mkdir(parents=True, exist_ok=True)
        if not any(p.iterdir()):
            (p / ".gitkeep").touch()
            print(f"Added .gitkeep to assets/{d}")

    print("Consolidation complete.")


if __name__ == "__main__":
    consolidate()
