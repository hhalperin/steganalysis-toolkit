#!/usr/bin/env python3
"""
Watermark Detection and Analysis Script
Analyzes images for visible watermarks and determines how they were added.
Run from project root: python -m stega.tools.analyze_watermark <dirty_image> [clean_image]
"""

import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import sys
import os
from pathlib import Path

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "src"))


def analyze_watermark_patterns(image_path):
    """Analyze an image for watermark patterns and encoding schemes."""
    print(f"🔍 ANALYZING WATERMARK PATTERNS: {image_path}")

    img = Image.open(image_path).convert('RGB')
    data = np.array(img)

    print("\n📊 IMAGE INFO:")
    print(f"  Size: {img.size}")
    print(f"  Mode: {img.mode}")
    print(f"  Shape: {data.shape}")

    lsb_r = data[:, :, 0] & 1
    lsb_g = data[:, :, 1] & 1
    lsb_b = data[:, :, 2] & 1

    print("\n🔬 LSB PATTERN ANALYSIS:")
    for channel, name in [(lsb_r, 'Red'), (lsb_g, 'Green'), (lsb_b, 'Blue')]:
        ones_ratio = np.mean(channel)
        print(f"  {name} channel - 1s ratio: {ones_ratio:.3f}")
        if ones_ratio > 0.95 or ones_ratio < 0.05:
            print(f"    ⚠️  HIGHLY UNIFORM LSB PATTERN DETECTED in {name} channel!")
        elif 0.45 <= ones_ratio <= 0.55:
            print(f"    ✅ Normal distribution in {name} channel")
        else:
            print(f"    ⚠️  Slightly unusual distribution in {name} channel")

    print("\n🎯 WHITE PIXEL WATERMARK ANALYSIS:")
    white_mask = np.all(data > 240, axis=2)
    white_pixels = data[white_mask]
    print(f"  Found {len(white_pixels)} white/near-white pixels")

    if len(white_pixels) > 100:
        white_lsb_r = white_pixels[:, 0] & 1
        white_lsb_g = white_pixels[:, 1] & 1
        white_lsb_b = white_pixels[:, 2] & 1
        for i, (lsb, name) in enumerate([(white_lsb_r, 'Red'), (white_lsb_g, 'Green'), (white_lsb_b, 'Blue')]):
            unique_vals = np.unique(lsb)
            print(f"  {name} channel LSB in white pixels: {unique_vals}")
            channel_vals = np.unique(white_pixels[:, i])
            if len(channel_vals) >= 3:
                diffs = np.diff(channel_vals)
                if np.all(diffs == 1):
                    print(f"    🎯 STEPPED ENCODING DETECTED in {name} channel!")

    print("\n🔧 TOOL SIGNATURE ANALYSIS:")
    corners = [data[0:50, 0:50], data[0:50, -50:], data[-50:, 0:50], data[-50:, -50:]]
    for i, corner in enumerate(corners):
        corner_lsb = corner & 1
        uniformity = np.std(corner_lsb)
        if uniformity < 0.1:
            print(f"    🎯 CORNER WATERMARK SIGNATURE DETECTED (Corner {i+1})")

    return {
        'image_info': {'size': img.size, 'mode': img.mode},
        'lsb_analysis': {'red': np.mean(lsb_r), 'green': np.mean(lsb_g), 'blue': np.mean(lsb_b)},
        'white_pixels': len(white_pixels),
        'suspicious_patterns': []
    }


def compare_images(dirty_path, clean_path):
    """Compare dirty vs cleaned images to understand watermark removal."""
    print(f"\n🔄 COMPARING IMAGES:")
    print(f"  Dirty: {dirty_path}")
    print(f"  Clean: {clean_path}")

    dirty = Image.open(dirty_path).convert('RGB')
    clean = Image.open(clean_path).convert('RGB')
    dirty_data = np.array(dirty)
    clean_data = np.array(clean)
    diff = np.abs(dirty_data.astype(np.int32) - clean_data.astype(np.int32))

    print("\n📈 DIFFERENCE ANALYSIS:")
    print(f"  Mean difference per channel: {np.mean(diff, axis=(0,1))}")
    print(f"  Max difference per channel: {np.max(diff, axis=(0,1))}")
    print(f"  Total pixels changed: {np.sum(diff > 0)}")
    significant_changes = np.any(diff > 10, axis=2)
    print(f"  Pixels with significant changes (>10): {np.sum(significant_changes)}")

    if np.sum(significant_changes) > 0:
        y_indices, x_indices = np.where(significant_changes)
        min_y, max_y = np.min(y_indices), np.max(y_indices)
        min_x, max_x = np.min(x_indices), np.max(x_indices)
        print("\n📍 WATERMARK LOCATION:")
        print(f"  Bounding box: ({min_x}, {min_y}) to ({max_x}, {max_y})")

    return diff


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m stega.tools.analyze_watermark <dirty_image> [clean_image]")
        sys.exit(1)

    dirty_image = sys.argv[1]
    if not os.path.exists(dirty_image):
        print(f"Error: File not found: {dirty_image}")
        sys.exit(1)

    analysis = analyze_watermark_patterns(dirty_image)

    if len(sys.argv) >= 3:
        clean_image = sys.argv[2]
        if os.path.exists(clean_image):
            compare_images(dirty_image, clean_image)
        else:
            print(f"Warning: Clean image not found: {clean_image}")


if __name__ == "__main__":
    main()
