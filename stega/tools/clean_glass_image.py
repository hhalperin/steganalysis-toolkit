#!/usr/bin/env python3
"""
Simple image cleaner for glass-d2h.png
Removes steganographic content while preserving visual quality.
Run from project root: python -m stega.tools.clean_glass_image
"""

import sys
import numpy as np
from PIL import Image
import os
from pathlib import Path

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "src"))


def analyze_and_clean_glass_image(input_path=None, output_dir=None):
    """Clean the glass-d2h.png image using multiple methods."""
    from config import PROCESSING_DIR

    input_path = input_path or "glass-d2h.png"
    if not Path(input_path).is_absolute():
        for candidate in [
            project_root / input_path,
            project_root / "assets" / "dirty" / input_path,
        ]:
            if candidate.exists():
                input_path = str(candidate)
                break
        else:
            input_path = str(project_root / input_path)

    output_dir = output_dir or str(PROCESSING_DIR / "glass")
    os.makedirs(output_dir, exist_ok=True)

    print("Loading image...")
    img = Image.open(input_path).convert('RGB')
    data = np.array(img)
    height, width = data.shape[:2]

    print(f"Image size: {width}x{height}")

    # Method 1: Aggressive LSB cleaning
    print("Applying aggressive LSB cleaning...")
    cleaned_aggressive = data.copy()

    for channel in range(3):
        for i in range(height):
            for j in range(width):
                neighbors = []
                for di in [-1, 0, 1]:
                    for dj in [-1, 0, 1]:
                        ni, nj = i + di, j + dj
                        if 0 <= ni < height and 0 <= nj < width and (di != 0 or dj != 0):
                            neighbors.append(data[ni, nj, channel])

                if neighbors:
                    avg_neighbor = np.mean(neighbors)
                    natural_lsb = int(avg_neighbor) & 1

                    if np.random.random() < 0.8:
                        cleaned_aggressive[i, j, channel] = (cleaned_aggressive[i, j, channel] & 0xFE) | natural_lsb
                    else:
                        cleaned_aggressive[i, j, channel] = (cleaned_aggressive[i, j, channel] & 0xFE) | np.random.randint(0, 2)

    aggressive_img = Image.fromarray(cleaned_aggressive.astype(np.uint8))
    aggressive_path = os.path.join(output_dir, "glass-d2h_aggressive_clean.png")
    aggressive_img.save(aggressive_path, 'PNG', optimize=True)
    print(f"Saved: {aggressive_path}")

    # Method 2: Minimal cleaning
    print("Applying minimal cleaning...")
    cleaned_minimal = data.copy()

    white_mask = np.all(data > 252, axis=2)

    if np.sum(white_mask) > 0:
        print(f"Targeting {np.sum(white_mask)} near-white pixels")

        y_coords, x_coords = np.where(white_mask)

        for i, (y, x) in enumerate(zip(y_coords, x_coords)):
            for channel in range(3):
                position_lsb = (x + y + channel) & 1

                if np.random.random() < 0.7:
                    final_lsb = position_lsb
                else:
                    final_lsb = np.random.randint(0, 2)

                cleaned_minimal[y, x, channel] = (cleaned_minimal[y, x, channel] & 0xFE) | final_lsb

    for channel in range(3):
        high_value_mask = data[:, :, channel] > 250
        if np.sum(high_value_mask) > 0:
            random_lsb = np.random.randint(0, 2, np.sum(high_value_mask))
            cleaned_minimal[:, :, channel][high_value_mask] = (
                (cleaned_minimal[:, :, channel][high_value_mask] & 0xFE) |
                random_lsb
            )

    minimal_img = Image.fromarray(cleaned_minimal.astype(np.uint8))
    minimal_path = os.path.join(output_dir, "glass-d2h_minimal_clean.png")
    minimal_img.save(minimal_path, 'PNG', optimize=True)
    print(f"Saved: {minimal_path}")

    # Method 3: Content-preserving cleaning
    print("Applying content-preserving cleaning...")
    cleaned_content = data.copy()

    for channel in range(3):
        channel_data = cleaned_content[:, :, channel]

        grad_x = np.abs(np.gradient(channel_data.astype(float), axis=1))
        grad_y = np.abs(np.gradient(channel_data.astype(float), axis=0))
        gradient_magnitude = grad_x + grad_y

        natural_lsb = (gradient_magnitude.astype(int)) & 1

        random_mask = np.random.random(channel_data.shape) < 0.3
        final_lsb = np.where(random_mask, np.random.randint(0, 2, channel_data.shape), natural_lsb)

        cleaned_content[:, :, channel] = (cleaned_content[:, :, channel] & 0xFE) | final_lsb

    content_img = Image.fromarray(cleaned_content.astype(np.uint8))
    content_path = os.path.join(output_dir, "glass-d2h_content_preserve_clean.png")
    content_img.save(content_path, 'PNG', optimize=True)
    print(f"Saved: {content_path}")

    # Compare quality metrics
    print("\nQuality Comparison:")
    original_size = os.path.getsize(input_path)
    aggressive_size = os.path.getsize(aggressive_path)
    minimal_size = os.path.getsize(minimal_path)
    content_size = os.path.getsize(content_path)

    print(f"Original: {original_size} bytes")
    print(f"Aggressive: {aggressive_size} bytes ({aggressive_size/original_size*100:.1f}% of original)")
    print(f"Minimal: {minimal_size} bytes ({minimal_size/original_size*100:.1f}% of original)")
    print(f"Content-preserving: {content_size} bytes ({content_size/original_size*100:.1f}% of original)")

    def calculate_psnr(original, cleaned):
        mse = np.mean((original.astype(float) - cleaned.astype(float)) ** 2)
        if mse == 0:
            return float('inf')
        return 20 * np.log10(255.0 / np.sqrt(mse))

    aggressive_psnr = calculate_psnr(data, cleaned_aggressive)
    minimal_psnr = calculate_psnr(data, cleaned_minimal)
    content_psnr = calculate_psnr(data, cleaned_content)

    print("\nPSNR (higher is better):")
    print(f"Aggressive: {aggressive_psnr:.2f} dB")
    print(f"Minimal: {minimal_psnr:.2f} dB")
    print(f"Content-preserving: {content_psnr:.2f} dB")

    return {
        'aggressive': aggressive_path,
        'minimal': minimal_path,
        'content_preserving': content_path,
        'metrics': {
            'original_size': original_size,
            'aggressive_size': aggressive_size,
            'minimal_size': minimal_size,
            'content_size': content_size,
            'aggressive_psnr': aggressive_psnr,
            'minimal_psnr': minimal_psnr,
            'content_psnr': content_psnr
        }
    }


if __name__ == "__main__":
    print("GLASS IMAGE STEGANOGRAPHY CLEANER")
    print("=" * 50)
    print("Cleaning glass-d2h.png...")

    results = analyze_and_clean_glass_image()

    print("\nCLEANING COMPLETE!")
    print(f"Generated {len(results) - 1} cleaned versions:")
    for method, path in results.items():
        if method != 'metrics':
            print(f"  - {method}: {path}")

    print("\nRECOMMENDATIONS:")
    print("- Use 'minimal' for best visual quality preservation")
    print("- Use 'aggressive' for maximum steganography removal")
    print("- Use 'content_preserving' for balanced approach")
