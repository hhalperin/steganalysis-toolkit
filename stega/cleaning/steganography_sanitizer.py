"""
Steganography Sanitizer - Remove hidden content while preserving image quality
Cleans LSB steganography and other hidden data without breaking visual appearance
"""

import os
import numpy as np
from PIL import Image
import random
import os
from pathlib import Path


def _log(msg, *args, quiet=False):
    """Windows-safe logging: ASCII only, no emoji."""
    if not quiet:
        print(msg % args if args else msg)


class SteganographySanitizer:
    """Remove steganographic content while maintaining visual fidelity."""

    def __init__(self, geometric_angle_deg=None):
        """
        Args:
            geometric_angle_deg: Optional rotation angle for geometric_transformation (degrees).
                If None, uses env GEOMETRIC_ANGLE_DEG or derives from preserve_quality (~0.25-0.5).
        """
        self._geometric_angle_deg = geometric_angle_deg
        self.methods = {
            'lsb_randomize': self._randomize_lsb,
            'lsb_natural': self._naturalize_lsb,
            'noise_injection': self._inject_noise,
            'compression_cycle': self._compression_cycle,
            'channel_adjustment': self._adjust_channels,
            'selective_clean': self._selective_clean,
            'geometric_transformation': self._geometric_transformation,
        }

    def detect_patterns(self, image_path, quiet=False):
        """Detect specific steganographic patterns in the image."""
        _log("[PATTERN DETECTION] %s", image_path, quiet=quiet)

        img = Image.open(image_path).convert('RGB')
        data = np.array(img)
        height, width = data.shape[:2]

        patterns = {
            'lsb_bias': self._detect_lsb_bias(data),
            'sequential_encoding': self._detect_sequential_encoding(data),
            'channel_correlation': self._detect_channel_correlation(data),
            'white_pixel_encoding': self._detect_white_pixel_encoding(data),
            'systematic_patterns': self._detect_systematic_patterns(data),
            'metadata_correlation': self._check_metadata_correlation(image_path)
        }

        return patterns

    def _detect_lsb_bias(self, data):
        """Detect LSB bias across color channels."""
        lsb_r = data[:, :, 0] & 1
        lsb_g = data[:, :, 1] & 1
        lsb_b = data[:, :, 2] & 1

        r_bias = np.mean(lsb_r)
        g_bias = np.mean(lsb_g)
        b_bias = np.mean(lsb_b)

        # Natural images should have ~0.5 bias
        suspicious = abs(r_bias - 0.5) > 0.4 or abs(g_bias - 0.5) > 0.4 or abs(b_bias - 0.5) > 0.4

        return {
            'r_bias': r_bias,
            'g_bias': g_bias,
            'b_bias': b_bias,
            'suspicious': suspicious,
            'pattern_type': 'LSB manipulation'
        }

    def _detect_sequential_encoding(self, data):
        """Detect sequential color value patterns."""
        # Check near-white pixels for sequential patterns
        white_mask = np.all(data > 250, axis=2)
        if np.sum(white_mask) > 100:
            white_pixels = data[white_mask]

            for channel in range(3):
                channel_vals = np.unique(white_pixels[:, channel])
                if len(channel_vals) >= 4:
                    # Check if values are sequential (251, 252, 253, 254, 255)
                    diff_pattern = np.diff(channel_vals)
                    if np.all(diff_pattern == 1):
                        return {
                            'channel': channel,
                            'values': channel_vals.tolist(),
                            'suspicious': True,
                            'pattern_type': 'Sequential encoding'
                        }

        return {'suspicious': False, 'pattern_type': 'Sequential encoding'}

    def _detect_channel_correlation(self, data):
        """Detect unusual correlation between color channels."""
        # Calculate correlation between channels
        r_flat = data[:, :, 0].flatten()
        g_flat = data[:, :, 1].flatten()
        b_flat = data[:, :, 2].flatten()

        rg_corr = np.corrcoef(r_flat, g_flat)[0, 1]
        rb_corr = np.corrcoef(r_flat, b_flat)[0, 1]
        gb_corr = np.corrcoef(g_flat, b_flat)[0, 1]

        # High correlation alone is normal for grayscale/near-grayscale images (logos, icons).
        # Only flag as suspicious if correlation > 0.99 AND image has meaningful chroma variance.
        high_corr = rg_corr > 0.99 or rb_corr > 0.99 or gb_corr > 0.99
        rg_diff_std = np.std(r_flat.astype(float) - g_flat.astype(float))
        rb_diff_std = np.std(r_flat.astype(float) - b_flat.astype(float))
        is_likely_grayscale = rg_diff_std < 5 and rb_diff_std < 5
        suspicious = high_corr and not is_likely_grayscale

        return {
            'rg_correlation': rg_corr,
            'rb_correlation': rb_corr,
            'gb_correlation': gb_corr,
            'suspicious': suspicious,
            'pattern_type': 'Channel correlation'
        }

    def _detect_white_pixel_encoding(self, data):
        """Detect encoding specifically in white/near-white pixels."""
        white_threshold = 250
        near_white = np.all(data > white_threshold, axis=2)

        if np.sum(near_white) > 100:
            white_pixels = data[near_white]

            # Check LSB patterns in white pixels only
            r_lsb = white_pixels[:, 0] & 1
            g_lsb = white_pixels[:, 1] & 1
            b_lsb = white_pixels[:, 2] & 1

            r_bias = np.mean(r_lsb)
            g_bias = np.mean(g_lsb)
            b_bias = np.mean(b_lsb)

            suspicious = (abs(r_bias - 0.5) > 0.4 or
                         abs(g_bias - 0.5) > 0.4 or
                         abs(b_bias - 0.5) > 0.4)

            return {
                'white_pixel_count': len(white_pixels),
                'r_bias': r_bias,
                'g_bias': g_bias,
                'b_bias': b_bias,
                'suspicious': suspicious,
                'pattern_type': 'White pixel LSB encoding'
            }

        return {'suspicious': False, 'pattern_type': 'White pixel LSB encoding'}

    def _detect_systematic_patterns(self, data):
        """Detect systematic patterns across the entire image."""
        # Check for repeating patterns in LSB
        lsb_data = data & 1

        # Flatten and check for patterns
        lsb_flat = lsb_data.flatten()

        # Look for repeating sequences
        pattern_found = False
        for pattern_len in [8, 16, 32]:
            if len(lsb_flat) >= pattern_len * 3:
                first_pattern = lsb_flat[:pattern_len]
                second_pattern = lsb_flat[pattern_len:pattern_len*2]
                third_pattern = lsb_flat[pattern_len*2:pattern_len*3]

                if np.array_equal(first_pattern, second_pattern) and np.array_equal(second_pattern, third_pattern):
                    pattern_found = True
                    break

        return {
            'repeating_pattern': pattern_found,
            'suspicious': pattern_found,
            'pattern_type': 'Systematic repetition'
        }

    def _check_metadata_correlation(self, image_path):
        """Check if metadata correlates with steganographic patterns."""
        # This would check XMP data for encoding hints
        try:
            img = Image.open(image_path)
            if hasattr(img, 'info') and img.info:
                return {
                    'has_metadata': True,
                    'suspicious': True,  # Extensive metadata can hide encoding info
                    'pattern_type': 'Metadata correlation'
                }
        except:
            pass

        return {'suspicious': False, 'pattern_type': 'Metadata correlation'}

    def sanitize_image(self, input_path, output_path, method='lsb_natural', preserve_quality=0.95, quiet=False):
        """
        Sanitize an image to remove steganographic content.

        Args:
            input_path: Path to input image
            output_path: Path for cleaned output image
            method: Sanitization method to use
            preserve_quality: Quality preservation factor (0.9-1.0)
            quiet: If True, suppress console output (Windows-safe)
        """
        _log("[SANITIZING] %s -> %s", input_path, output_path, quiet=quiet)
        _log("  Method: %s", method, quiet=quiet)

        if method not in self.methods:
            raise ValueError(f"Unknown method: {method}")

        img = Image.open(input_path).convert('RGB')
        data = np.array(img)

        # Apply sanitization method
        cleaned_data = self.methods[method](data, preserve_quality)

        # Save cleaned image
        cleaned_img = Image.fromarray(cleaned_data.astype(np.uint8))
        cleaned_img.save(output_path, 'PNG', optimize=True)

        _log("[SANITIZED] Saved to %s", output_path, quiet=quiet)
        return output_path

    def _randomize_lsb(self, data, preserve_quality):
        """Randomize LSB while preserving visual quality."""
        cleaned = data.copy()

        # Randomize LSB of each channel
        for channel in range(3):
            # Generate random LSB values
            random_lsb = np.random.randint(0, 2, cleaned.shape[:2])

            # Clear existing LSB and set new random LSB
            cleaned[:, :, channel] = (cleaned[:, :, channel] & 0xFE) | random_lsb

        return cleaned

    def _naturalize_lsb(self, data, preserve_quality):
        """Make LSB patterns more natural while preserving image."""
        cleaned = data.copy()

        # Apply natural randomization based on image content
        for channel in range(3):
            # Use image gradients to determine LSB
            channel_data = cleaned[:, :, channel]

            # Calculate simple gradient
            grad_x = np.diff(channel_data, axis=1, prepend=channel_data[:, 0:1])
            grad_y = np.diff(channel_data, axis=0, prepend=channel_data[0:1, :])

            # Use gradient to determine "natural" LSB
            natural_lsb = (np.abs(grad_x) + np.abs(grad_y)) & 1

            # Apply with some randomness
            mask = np.random.random(cleaned.shape[:2]) < preserve_quality
            final_lsb = np.where(mask, natural_lsb, np.random.randint(0, 2, cleaned.shape[:2]))

            cleaned[:, :, channel] = (cleaned[:, :, channel] & 0xFE) | final_lsb

        return cleaned

    def _inject_noise(self, data, preserve_quality):
        """Inject minimal noise to break steganographic patterns."""
        cleaned = data.copy().astype(np.float32)

        # Add very small random noise
        noise_strength = 1.0 - preserve_quality
        noise = np.random.normal(0, noise_strength, cleaned.shape)

        cleaned = cleaned + noise
        cleaned = np.clip(cleaned, 0, 255)

        return cleaned

    def _compression_cycle(self, data, preserve_quality):
        """Use compression/decompression to remove steganographic data."""
        # Convert to PIL Image
        img = Image.fromarray(data.astype(np.uint8))

        # Save and reload with JPEG compression to break LSB patterns
        import io
        buffer = io.BytesIO()
        quality = int(preserve_quality * 100)
        img.save(buffer, format='JPEG', quality=quality)
        buffer.seek(0)

        # Reload and convert back to RGB
        cleaned_img = Image.open(buffer).convert('RGB')
        return np.array(cleaned_img)

    def _adjust_channels(self, data, preserve_quality):
        """Slightly adjust color channels to break patterns."""
        cleaned = data.copy().astype(np.float32)

        # Apply very small systematic adjustments
        adjustment = (1.0 - preserve_quality) * 2

        # Adjust each channel slightly differently
        cleaned[:, :, 0] *= (1.0 + adjustment)
        cleaned[:, :, 1] *= (1.0 - adjustment * 0.5)
        cleaned[:, :, 2] *= (1.0 + adjustment * 0.3)

        cleaned = np.clip(cleaned, 0, 255)
        return cleaned

    def _selective_clean(self, data, preserve_quality):
        """Clean only pixels identified as containing steganographic data."""
        cleaned = data.copy()

        # Target near-white pixels (most suspicious)
        white_mask = np.all(data > 250, axis=2)

        if np.sum(white_mask) > 0:
            # For white pixels, randomize LSB only
            for channel in range(3):
                random_lsb = np.random.randint(0, 2, cleaned.shape[:2])
                cleaned[:, :, channel] = np.where(
                    white_mask,
                    (cleaned[:, :, channel] & 0xFE) | random_lsb,
                    cleaned[:, :, channel]
                )

        return cleaned

    def _geometric_transformation(self, data, preserve_quality):
        """
        Apply mild geometric transform to break SIFT/keypoint-based geometric watermarks.
        Uses a small rotation + center crop to preserve dimensions with minimal visual change.
        """
        # Angle: configurable via __init__ or env GEOMETRIC_ANGLE_DEG; else derive from preserve_quality
        angle_deg = self._geometric_angle_deg
        if angle_deg is None:
            env_val = os.environ.get("GEOMETRIC_ANGLE_DEG")
            angle_deg = float(env_val) if env_val else (1.0 - preserve_quality) * 0.5 + 0.25
        img = Image.fromarray(data.astype(np.uint8))
        w, h = img.size
        # Rotate with expand=True to get full rotated image
        rotated = img.rotate(-angle_deg, resample=Image.BICUBIC, expand=True)
        rw, rh = rotated.size
        # Center crop back to original size
        left = (rw - w) // 2
        top = (rh - h) // 2
        cropped = rotated.crop((left, top, left + w, top + h))
        return np.array(cropped)


def analyze_and_clean_image(input_path, output_dir="cleaned"):
    """Complete analysis and cleaning workflow."""
    sanitizer = SteganographySanitizer()

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Detect patterns
    patterns = sanitizer.detect_patterns(input_path)

    print("\n[PATTERN ANALYSIS RESULTS]")
    for pattern_name, pattern_data in patterns.items():
        if pattern_data.get('suspicious', False):
            print(f"  [!] {pattern_name}: {pattern_data['pattern_type']} - SUSPICIOUS")
            # Print relevant details
            for key, value in pattern_data.items():
                if key not in ['suspicious', 'pattern_type'] and isinstance(value, (int, float)):
                    if isinstance(value, float):
                        print(f"    {key}: {value:.3f}")
                    else:
                        print(f"    {key}: {value}")
        else:
            print(f"  [OK] {pattern_name}: Clean")

    # Determine best cleaning method based on detected patterns
    best_method = 'lsb_natural'  # Default

    if patterns['lsb_bias']['suspicious']:
        if patterns['lsb_bias']['r_bias'] > 0.9:
            best_method = 'selective_clean'
        elif patterns['sequential_encoding']['suspicious']:
            best_method = 'lsb_natural'
        else:
            best_method = 'lsb_randomize'

    print(f"\n[RECOMMENDED] Cleaning method: {best_method}")

    # Apply multiple cleaning methods for comparison
    methods_to_try = ['lsb_randomize', 'lsb_natural', 'selective_clean', 'noise_injection']

    input_filename = Path(input_path).stem
    cleaned_files = []

    for method in methods_to_try:
        output_path = f"{output_dir}/{input_filename}_cleaned_{method}.png"
        try:
            sanitizer.sanitize_image(input_path, output_path, method, preserve_quality=0.98)
            cleaned_files.append(output_path)
        except Exception as e:
            print(f"[ERROR] {method}: {e}")

    return cleaned_files, patterns


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python steganography_sanitizer.py <image_path>")
        sys.exit(1)

    image_path = sys.argv[1]

    if not os.path.exists(image_path):
        print(f"File not found: {image_path}")
        sys.exit(1)

    print("[STEGANOGRAPHY SANITIZER]")
    print(f"Input: {image_path}")
    print("=" * 50)

    cleaned_files, patterns = analyze_and_clean_image(image_path)

    print("\n[CLEANING COMPLETE]")
    print(f"Generated {len(cleaned_files)} cleaned versions:")
    for file in cleaned_files:
        print(f"  - {file}")

    print("\n[RECOMMENDATIONS]")
    print("• Compare cleaned versions visually to ensure quality")
    print("• Re-run steganographic analysis on cleaned files")
    print("• Use 'lsb_natural' for best quality preservation")
    print("• Use 'selective_clean' for targeted LSB removal")
