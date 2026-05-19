"""
Comprehensive Image Cleaner - Remove steganographic content with multiple methods
Provides visual comparison and quality assessment
"""

import numpy as np
from PIL import Image
import os
from pathlib import Path


def aggressive_lsb_cleaning(image_path, output_path, quiet=False):
    """
    Aggressively clean LSB steganography while preserving visual quality.
    This method specifically targets the 100% LSB bias pattern found.
    """
    if not quiet:
        print(f"[AGGRESSIVE LSB CLEANING] {image_path}")

    img = Image.open(image_path).convert('RGB')
    data = np.array(img).astype(np.int16)  # Use int16 to prevent overflow

    # Method 1: Randomize LSB based on neighboring pixels
    cleaned = data.copy()
    height, width = data.shape[:2]

    # For each pixel, set LSB based on neighboring pixel content
    for i in range(height):
        for j in range(width):
            for channel in range(3):
                # Use neighboring pixels to determine "natural" LSB
                neighbors = []
                for di in [-1, 0, 1]:
                    for dj in [-1, 0, 1]:
                        ni, nj = i + di, j + dj
                        if 0 <= ni < height and 0 <= nj < width and (di != 0 or dj != 0):
                            neighbors.append(data[ni, nj, channel])

                if neighbors:
                    # Use average of neighbors to determine LSB
                    avg_neighbor = np.mean(neighbors)
                    natural_lsb = int(avg_neighbor) & 1

                    # Apply with some randomness to avoid artifacts
                    if np.random.random() < 0.8:  # 80% natural, 20% random
                        cleaned[i, j, channel] = (cleaned[i, j, channel] & 0xFE) | natural_lsb
                    else:
                        cleaned[i, j, channel] = (cleaned[i, j, channel] & 0xFE) | np.random.randint(0, 2)

    # Ensure values stay in valid range
    cleaned = np.clip(cleaned, 0, 255).astype(np.uint8)

    # Save cleaned image
    cleaned_img = Image.fromarray(cleaned)
    cleaned_img.save(output_path, 'PNG', optimize=True)

    if not quiet:
        print(f"[SAVED] {output_path}")
    return output_path


def minimal_cleaning(image_path, output_path, quiet=False):
    """
    Minimal cleaning that only targets suspicious patterns.
    Preserves maximum visual quality.
    """
    if not quiet:
        print(f"[MINIMAL CLEANING] {image_path}")

    img = Image.open(image_path).convert('RGB')
    data = np.array(img)
    cleaned = data.copy()

    # Only modify pixels that are clearly part of steganographic encoding

    # Method 1: Target near-white pixels with perfect LSB patterns
    white_mask = np.all(data > 252, axis=2)  # Very white pixels

    if np.sum(white_mask) > 0 and not quiet:
        print(f"   Targeting {np.sum(white_mask)} near-white pixels")

        # For white pixels, use a more natural LSB based on position
        y_coords, x_coords = np.where(white_mask)

        for i, (y, x) in enumerate(zip(y_coords, x_coords)):
            for channel in range(3):
                # Use pixel coordinates to create pseudo-natural LSB
                position_lsb = (x + y + channel) & 1

                # Add some randomness
                if np.random.random() < 0.7:
                    final_lsb = position_lsb
                else:
                    final_lsb = np.random.randint(0, 2)

                cleaned[y, x, channel] = (cleaned[y, x, channel] & 0xFE) | final_lsb

    # Method 2: Break perfect sequential patterns
    for channel in range(3):
        # Find pixels with values 251-255 and randomize their LSB slightly
        high_value_mask = data[:, :, channel] > 250
        if np.sum(high_value_mask) > 0:
            # Only modify LSB, keep the rest
            random_lsb = np.random.randint(0, 2, np.sum(high_value_mask))
            cleaned[:, :, channel][high_value_mask] = (
                (cleaned[:, :, channel][high_value_mask] & 0xFE) |
                random_lsb
            )

    # Save
    cleaned_img = Image.fromarray(cleaned)
    cleaned_img.save(output_path, 'PNG', optimize=True)

    if not quiet:
        print(f"[SAVED] {output_path}")
    return output_path


def compare_cleaning_methods(original_path, cleaned_paths):
    """Compare different cleaning methods and assess quality."""
    print("\n[CLEANING COMPARISON]")

    original = np.array(Image.open(original_path).convert('RGB'))

    for cleaned_path in cleaned_paths:
        if os.path.exists(cleaned_path):
            cleaned = np.array(Image.open(cleaned_path).convert('RGB'))

            # Calculate PSNR (Peak Signal-to-Noise Ratio)
            mse = np.mean((original.astype(float) - cleaned.astype(float)) ** 2)
            if mse == 0:
                psnr = float('inf')
            else:
                psnr = 20 * np.log10(255.0 / np.sqrt(mse))

            # Calculate SSIM-like metric (simplified)
            mean_orig = np.mean(original)
            mean_clean = np.mean(cleaned)
            var_orig = np.var(original)
            var_clean = np.var(cleaned)
            covar = np.mean((original - mean_orig) * (cleaned - mean_clean))

            ssim_like = (2 * mean_orig * mean_clean + 1) / (mean_orig**2 + mean_clean**2 + 1)

            print(f"   {Path(cleaned_path).name}:")
            print(f"     PSNR: {psnr:.2f} dB (higher is better, >30 is good)")
            print(f"     Similarity: {ssim_like:.4f} (closer to 1.0 is better)")


def clean_all_suspicious_images():
    """Clean all suspicious images found in the Logo directory."""
    from ..config import DIRTY_DIR, PROCESSING_DIR
    logo_dir = DIRTY_DIR / "logo"
    out_dir = PROCESSING_DIR / "logo"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Support both PNG and SVG (SVG from root Logo; PNG if present)
    suspicious_files = list(logo_dir.glob("*.png")) if logo_dir.exists() else []
    if not suspicious_files:
        suspicious_files = [
            logo_dir / "H (Logo).png",
            logo_dir / "Simple H logo with background.png",
            logo_dir / "white_bg-HappyHealthy_logo.png",
            logo_dir / "blue_bg-HappyHealthy_logo.png",
        ]

    results = {}

    for image_path in suspicious_files:
        image_path = str(image_path) if hasattr(image_path, "as_posix") else image_path
        if os.path.exists(image_path):
            print(f"\\n{'='*60}")
            print(f"PROCESSING: {image_path}")
            print(f"{'='*60}")

            filename = Path(image_path).stem

            # Apply different cleaning methods
            aggressive_path = str(out_dir / f"{filename}_aggressive.png")
            minimal_path = str(out_dir / f"{filename}_minimal.png")

            # Apply cleaning
            aggressive_lsb_cleaning(image_path, aggressive_path)
            minimal_cleaning(image_path, minimal_path)

            # Compare results
            cleaned_paths = [aggressive_path, minimal_path]
            compare_cleaning_methods(image_path, cleaned_paths)

            results[image_path] = {
                'aggressive': aggressive_path,
                'minimal': minimal_path
            }

    return results


if __name__ == '__main__':
    print("[ADVANCED IMAGE STEGANOGRAPHY CLEANER]")
    print("=" * 50)

    results = clean_all_suspicious_images()

    print("\n[CLEANING SUMMARY]")
    print("Generated cleaned versions for all suspicious images.")
    print("\n[RECOMMENDATIONS]")
    print("• Use 'minimal' versions for best visual quality")
    print("• Use 'aggressive' versions for maximum steganography removal")
    print("• Compare visually before deploying cleaned images")
    print("• Re-analyze cleaned images to verify removal")
