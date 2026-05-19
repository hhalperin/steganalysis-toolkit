#!/usr/bin/env python3
"""
Simple Text Watermark Remover CLI - No OCR required.
Uses computer vision to detect and remove repeated text patterns.
Run from project root: python -m stega.tools.simple_text_remover [image(s)] [-o output_dir]
"""

import sys
import argparse
from pathlib import Path

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from stega.cleaning.simple_text_remover import SimpleTextRemover
from stega.config import resolve_input_dir, clean_path, ensure_dirs


def main():
    parser = argparse.ArgumentParser(description="Simple text watermark remover (no OCR)")
    parser.add_argument("input", nargs="*", help="Input image(s); if empty, uses assets/dirty/visible-dirt samples")
    parser.add_argument("-o", "--output", help="Output directory (default: assets/clean)")
    args = parser.parse_args()

    ensure_dirs()
    out_dir = Path(args.output) if args.output else clean_path()
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.input:
        test_files = [Path(f) for f in args.input if Path(f).exists()]
    else:
        visible_dirt = resolve_input_dir("visible-dirt")
        test_files = [
            visible_dirt / "grad-image.jpg",
            visible_dirt / "copy.png",
        ]
        test_files = [f for f in test_files if f.exists()]

    if not test_files:
        print("No input files found.")
        return 1

    remover = SimpleTextRemover()
    for image_file in test_files:
        print(f"\nProcessing: {image_file.name}")
        output_file = out_dir / f"{image_file.stem}_simple_cleaned.png"
        success = remover.remove_text_patterns(str(image_file), str(output_file))
        if success:
            print(f"   Saved: {output_file}")
        else:
            print("   Cleaning failed or no patterns found")

    return 0


if __name__ == "__main__":
    sys.exit(main())
