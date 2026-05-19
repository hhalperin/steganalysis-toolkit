"""
Advanced Waste Detector - Detects sophisticated and lesser-known steganographic patterns
Covers patterns missed by traditional detectors: multi-layer, geometric, semantic, etc.
"""

import os
import numpy as np
from PIL import Image
import cv2
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
import hashlib
import re
from datetime import datetime


@dataclass
class AdvancedWasteFindings:
    """Results from advanced waste detection."""
    pattern_type: str
    detected: bool
    confidence: float
    details: Dict[str, Any]
    recommended_removal: str


class AdvancedWasteDetector:
    """
    Detects sophisticated steganographic patterns that traditional methods miss.

    Covers:
    - Multi-layer steganography
    - Geometric/transform-resistant watermarks
    - Color space exploits
    - Blockchain/NFT watermarks
    - Printer tracking dots
    - Semantic steganography
    - File system side-channels
    - Format-specific exploits
    """

    def __init__(self, image_path: str, geometric_persistence_threshold: float = None,
                 geometric_min_confidence: float = None):
        self.image_path = Path(image_path)
        self.image = None
        self.image_array = None
        self.findings: List[AdvancedWasteFindings] = []
        # Configurable geometric watermark detection (env overrides: GEOMETRIC_PERSISTENCE_THRESHOLD, GEOMETRIC_MIN_CONFIDENCE)
        self._geo_persistence_threshold = geometric_persistence_threshold
        self._geo_min_confidence = geometric_min_confidence

    def analyze(self) -> Dict[str, Any]:
        """Run all advanced detection methods."""
        self.image = Image.open(self.image_path)
        self.image_array = np.array(self.image.convert('RGB'))

        results = {
            'multi_layer': self.detect_multi_layer_steganography(),
            'geometric_watermarks': self.detect_geometric_watermarks(),
            'color_space_exploits': self.detect_color_space_encoding(),
            'blockchain_watermarks': self.detect_blockchain_watermarks(),
            'printer_tracking': self.detect_printer_tracking_dots(),
            'semantic_encoding': self.detect_semantic_steganography(),
            'format_exploits': self.detect_format_specific_exploits(),
            'side_channels': self.detect_side_channel_encoding(),
            'ai_model_fingerprints': self.detect_ai_fingerprints(),
            'temporal_patterns': self.detect_temporal_encoding()
        }

        return results

    def detect_multi_layer_steganography(self) -> AdvancedWasteFindings:
        """
        Detect nested/stacked steganography where data is hidden multiple times.
        """
        details = {}

        # Extract LSB layer
        lsb_data = self.image_array & 1
        lsb_flat = lsb_data.flatten()

        # Check if LSB itself has patterns (nested encoding)
        # Convert LSB bits to bytes and analyze
        if len(lsb_flat) >= 64:
            # Check if LSB contains another layer
            byte_data = []
            for i in range(0, min(len(lsb_flat), 1000), 8):
                if i + 8 <= len(lsb_flat):
                    byte_val = 0
                    for j in range(8):
                        byte_val += lsb_flat[i + j] << j
                    byte_data.append(byte_val)

            byte_array = np.array(byte_data)

            # Check entropy of extracted bytes (high entropy = encrypted/compressed)
            if len(byte_array) > 10:
                unique_ratio = len(np.unique(byte_array)) / len(byte_array)
                byte_entropy = self._calculate_entropy(byte_array)

                details['lsb_extraction_entropy'] = float(byte_entropy)
                details['lsb_unique_ratio'] = float(unique_ratio)

                # High entropy suggests encrypted layer
                detected = byte_entropy > 7.5 or unique_ratio > 0.8
                confidence = min(0.95, byte_entropy / 8.0)

                if detected:
                    details['likely_nested'] = True
                    details['nested_type'] = 'encrypted_payload' if byte_entropy > 7.8 else 'compressed_data'

                return AdvancedWasteFindings(
                    pattern_type='multi_layer_steganography',
                    detected=detected,
                    confidence=confidence,
                    details=details,
                    recommended_removal='recursive_lsb_randomization'
                )

        return AdvancedWasteFindings(
            pattern_type='multi_layer_steganography',
            detected=False,
            confidence=0.0,
            details=details,
            recommended_removal='none'
        )

    def detect_geometric_watermarks(self) -> AdvancedWasteFindings:
        """
        Detect watermarks that survive geometric transformations.
        Uses Scale-Invariant Feature Transform (SIFT) and rotation testing.
        """
        details = {}

        try:
            import cv2

            # Convert to grayscale for feature detection
            gray = cv2.cvtColor(self.image_array, cv2.COLOR_RGB2GRAY)

            # Detect SIFT features
            sift = cv2.SIFT_create()
            keypoints, descriptors = sift.detectAndCompute(gray, None)

            details['keypoint_count'] = len(keypoints)

            # Suspicious if too many or too few keypoints for image size
            image_area = gray.shape[0] * gray.shape[1]
            kp_density = len(keypoints) / image_area

            details['keypoint_density'] = float(kp_density)

            # Check for regular pattern in keypoint locations
            if len(keypoints) > 10:
                kp_positions = np.array([kp.pt for kp in keypoints])

                # Check for grid-like patterns
                x_coords = kp_positions[:, 0]
                y_coords = kp_positions[:, 1]

                x_variance = np.var(np.diff(np.sort(x_coords)))
                y_variance = np.var(np.diff(np.sort(y_coords)))

                details['position_variance_x'] = float(x_variance)
                details['position_variance_y'] = float(y_variance)

                # Low variance in spacing = regular grid = suspicious
                regular_pattern = x_variance < 100 or y_variance < 100

                details['regular_grid_detected'] = regular_pattern

                # Rotation-test: rotate image and check if features persist
                rotated = self._rotate_image(gray, 45)
                kp_rot, _ = sift.detectAndCompute(rotated, None)

                persistence_ratio = len(kp_rot) / len(keypoints)
                details['rotation_persistence'] = float(persistence_ratio)

                # Configurable thresholds (env: GEOMETRIC_PERSISTENCE_THRESHOLD, GEOMETRIC_MIN_CONFIDENCE)
                persist_thresh = self._geo_persistence_threshold
                if persist_thresh is None:
                    persist_thresh = float(os.environ.get("GEOMETRIC_PERSISTENCE_THRESHOLD", "0.7"))
                min_conf = self._geo_min_confidence
                if min_conf is None:
                    min_conf = float(os.environ.get("GEOMETRIC_MIN_CONFIDENCE", "0.65"))

                # Features that survive rotation are suspicious
                detected = regular_pattern or persistence_ratio > persist_thresh
                confidence = min_conf if regular_pattern else (persistence_ratio * 0.8)
                if confidence < min_conf:
                    detected = False

                return AdvancedWasteFindings(
                    pattern_type='geometric_watermark',
                    detected=detected,
                    confidence=confidence,
                    details=details,
                    recommended_removal='geometric_transformation'
                )

        except Exception as e:
            details['error'] = str(e)

        return AdvancedWasteFindings(
            pattern_type='geometric_watermark',
            detected=False,
            confidence=0.0,
            details=details,
            recommended_removal='none'
        )

    def detect_color_space_encoding(self) -> AdvancedWasteFindings:
        """
        Check for encoding in alternative color spaces (HSV, YCbCr, Lab).
        """
        details = {}
        detected_spaces = []

        try:
            from skimage import color

            # Convert to various color spaces
            hsv = color.rgb2hsv(self.image_array / 255.0)
            ycbcr = color.rgb2ycbcr(self.image_array)
            lab = color.rgb2lab(self.image_array)

            # Check HSV - Hue channel for encoding
            hue = hsv[:, :, 0]
            hue_lsb = (hue * 255).astype(np.uint8) & 1
            hue_bias = np.mean(hue_lsb)

            details['hsv_hue_lsb_bias'] = float(hue_bias)

            if abs(hue_bias - 0.5) > 0.3:
                detected_spaces.append('HSV_hue')
                details['hsv_suspicious'] = True

            # Check YCbCr - Chroma channels
            cb = ycbcr[:, :, 1]
            cr = ycbcr[:, :, 2]

            cb_lsb = cb.astype(np.uint8) & 1
            cr_lsb = cr.astype(np.uint8) & 1

            cb_bias = np.mean(cb_lsb)
            cr_bias = np.mean(cr_lsb)

            details['ycbcr_cb_bias'] = float(cb_bias)
            details['ycbcr_cr_bias'] = float(cr_bias)

            if abs(cb_bias - 0.5) > 0.3 or abs(cr_bias - 0.5) > 0.3:
                detected_spaces.append('YCbCr_chroma')
                details['ycbcr_suspicious'] = True

            # Check Lab - Lightness channel
            l_channel = lab[:, :, 0]
            l_lsb = (l_channel).astype(np.uint8) & 1
            l_bias = np.mean(l_lsb)

            details['lab_lightness_lsb_bias'] = float(l_bias)

            if abs(l_bias - 0.5) > 0.3:
                detected_spaces.append('Lab_lightness')
                details['lab_suspicious'] = True

            detected = len(detected_spaces) > 0
            confidence = min(0.9, len(detected_spaces) * 0.4)

            details['suspicious_color_spaces'] = detected_spaces

            return AdvancedWasteFindings(
                pattern_type='color_space_encoding',
                detected=detected,
                confidence=confidence,
                details=details,
                recommended_removal='multi_colorspace_cleaning'
            )

        except Exception as e:
            details['error'] = str(e)

        return AdvancedWasteFindings(
            pattern_type='color_space_encoding',
            detected=False,
            confidence=0.0,
            details=details,
            recommended_removal='none'
        )

    def detect_blockchain_watermarks(self) -> AdvancedWasteFindings:
        """
        Detect blockchain/NFT-related watermarks and signatures.
        """
        details = {}
        patterns_found = []

        # Check EXIF/metadata for blockchain markers
        try:
            exif = self.image.getexif()

            if exif:
                exif_str = str(exif)

                # Common blockchain patterns
                blockchain_patterns = {
                    'ethereum': r'0x[a-fA-F0-9]{40}',  # Ethereum address
                    'bitcoin': r'[13][a-km-zA-HJ-NP-Z1-9]{25,34}',  # Bitcoin address
                    'ipfs': r'Qm[1-9A-HJ-NP-Za-km-z]{44}',  # IPFS hash
                    'nft_metadata': r'token(Id|URI|Hash)',
                    'smart_contract': r'contract|0x[a-fA-F0-9]{64}',  # Contract or tx hash
                }

                for pattern_name, regex in blockchain_patterns.items():
                    if re.search(regex, exif_str, re.IGNORECASE):
                        patterns_found.append(pattern_name)
                        details[f'{pattern_name}_detected'] = True

            # Check image comment fields
            if hasattr(self.image, 'info'):
                info_str = str(self.image.info)

                for pattern_name, regex in blockchain_patterns.items():
                    if re.search(regex, info_str, re.IGNORECASE):
                        patterns_found.append(pattern_name)
                        details[f'{pattern_name}_in_comment'] = True

            detected = len(patterns_found) > 0
            confidence = min(0.95, len(patterns_found) * 0.4)

            details['blockchain_patterns_found'] = patterns_found

            return AdvancedWasteFindings(
                pattern_type='blockchain_watermark',
                detected=detected,
                confidence=confidence,
                details=details,
                recommended_removal='metadata_strip'
            )

        except Exception as e:
            details['error'] = str(e)

        return AdvancedWasteFindings(
            pattern_type='blockchain_watermark',
            detected=False,
            confidence=0.0,
            details=details,
            recommended_removal='none'
        )

    def detect_printer_tracking_dots(self) -> AdvancedWasteFindings:
        """
        Detect printer tracking dots (Machine Identification Code).
        These are typically yellow dots arranged in specific patterns.
        """
        details = {}

        try:
            # Convert to HSV to isolate yellow channel
            from skimage import color

            hsv = color.rgb2hsv(self.image_array / 255.0)

            # Yellow is around hue = 0.15-0.17 (50-60 degrees)
            # High saturation, medium-high value
            yellow_mask = (
                (hsv[:, :, 0] > 0.12) & (hsv[:, :, 0] < 0.20) &  # Hue
                (hsv[:, :, 1] > 0.3) &  # Saturation
                (hsv[:, :, 2] > 0.7)    # Value (brightness)
            )

            yellow_pixel_count = np.sum(yellow_mask)
            total_pixels = yellow_mask.size
            yellow_ratio = yellow_pixel_count / total_pixels

            details['yellow_pixel_ratio'] = float(yellow_ratio)
            details['yellow_pixel_count'] = int(yellow_pixel_count)

            # If very few yellow pixels in a regular pattern, suspicious
            if 0 < yellow_ratio < 0.01:  # Less than 1% but present
                # Check for regular spacing (tracking dots are in grids)
                y_coords, x_coords = np.where(yellow_mask)

                if len(x_coords) > 5:
                    # Check for regular spacing
                    x_diffs = np.diff(np.sort(x_coords))
                    y_diffs = np.diff(np.sort(y_coords))

                    x_mode_diff = np.median(x_diffs[x_diffs > 0]) if len(x_diffs) > 0 else 0
                    y_mode_diff = np.median(y_diffs[y_diffs > 0]) if len(y_diffs) > 0 else 0

                    details['x_spacing_median'] = float(x_mode_diff)
                    details['y_spacing_median'] = float(y_mode_diff)

                    # Regular spacing suggests tracking dots
                    regular_spacing = (x_mode_diff > 10 and x_mode_diff < 50) or \
                                     (y_mode_diff > 10 and y_mode_diff < 50)

                    detected = regular_spacing
                    confidence = 0.7 if regular_spacing else 0.3

                    details['tracking_dots_pattern'] = regular_spacing

                    return AdvancedWasteFindings(
                        pattern_type='printer_tracking_dots',
                        detected=detected,
                        confidence=confidence,
                        details=details,
                        recommended_removal='yellow_channel_cleaning'
                    )

        except Exception as e:
            details['error'] = str(e)

        return AdvancedWasteFindings(
            pattern_type='printer_tracking_dots',
            detected=False,
            confidence=0.0,
            details=details,
            recommended_removal='none'
        )

    def detect_semantic_steganography(self) -> AdvancedWasteFindings:
        """
        Detect semantic steganography - encoding through object placement,
        color choices, or texture patterns that carry meaning.
        """
        details = {}

        try:
            # Check for suspicious color palette
            unique_colors = np.unique(self.image_array.reshape(-1, 3), axis=0)
            color_count = len(unique_colors)
            total_possible = self.image_array.shape[0] * self.image_array.shape[1]

            color_diversity = color_count / min(total_possible, 16777216)  # Max RGB colors

            details['unique_color_count'] = int(color_count)
            details['color_diversity'] = float(color_diversity)

            # Very specific color palette might encode data
            if color_count < 256 and color_count > 10:
                # Check if colors are suspiciously selected
                # (e.g., all prime number values, all sequential, etc.)
                color_values = unique_colors.flatten()

                # Check for patterns in color values
                sequential_count = np.sum(np.diff(np.sort(color_values)) == 1)
                sequential_ratio = sequential_count / len(color_values) if len(color_values) > 0 else 0

                details['sequential_color_ratio'] = float(sequential_ratio)

                detected = sequential_ratio > 0.5 or (color_count % 16 == 0)
                confidence = 0.6 if detected else 0.2

                details['palette_suspicious'] = detected

                return AdvancedWasteFindings(
                    pattern_type='semantic_steganography',
                    detected=detected,
                    confidence=confidence,
                    details=details,
                    recommended_removal='color_normalization'
                )

        except Exception as e:
            details['error'] = str(e)

        return AdvancedWasteFindings(
            pattern_type='semantic_steganography',
            detected=False,
            confidence=0.0,
            details=details,
            recommended_removal='none'
        )

    def detect_format_specific_exploits(self) -> AdvancedWasteFindings:
        """
        Detect format-specific steganography (JPEG comments, GIF extensions, etc.).
        """
        details = {}
        exploits_found = []

        try:
            file_ext = self.image_path.suffix.lower()
            details['format'] = file_ext

            # Check for suspicious chunks/segments
            if file_ext == '.png':
                # Already covered by png_analyzer
                pass

            elif file_ext in ['.jpg', '.jpeg']:
                # Check for JPEG comments and APP markers
                with open(self.image_path, 'rb') as f:
                    data = f.read()

                    # Look for comment markers (0xFFFE)
                    if b'\xFF\xFE' in data:
                        exploits_found.append('jpeg_comment')
                        details['jpeg_comment_found'] = True

                    # Check for excessive APP markers
                    app_count = sum(1 for i in range(len(data) - 1) if data[i] == 0xFF and 0xE0 <= data[i + 1] <= 0xEF)
                    if app_count > 10:
                        exploits_found.append('excessive_app_markers')
                        details['app_marker_count'] = app_count

            elif file_ext == '.gif':
                # Check for comment extensions
                with open(self.image_path, 'rb') as f:
                    data = f.read()

                    # GIF comment extension: 0x21 0xFE
                    if b'\x21\xFE' in data:
                        exploits_found.append('gif_comment_extension')
                        details['gif_comment_found'] = True

            elif file_ext in ['.webp']:
                # WebP can have extended chunks
                with open(self.image_path, 'rb') as f:
                    data = f.read()

                    # Check for EXIF/XMP chunks
                    if b'EXIF' in data or b'XMP ' in data:
                        exploits_found.append('webp_metadata_chunks')
                        details['webp_metadata'] = True

            detected = len(exploits_found) > 0
            confidence = min(0.8, len(exploits_found) * 0.4)

            details['exploits_found'] = exploits_found

            return AdvancedWasteFindings(
                pattern_type='format_specific_exploit',
                detected=detected,
                confidence=confidence,
                details=details,
                recommended_removal='format_conversion'
            )

        except Exception as e:
            details['error'] = str(e)

        return AdvancedWasteFindings(
            pattern_type='format_specific_exploit',
            detected=False,
            confidence=0.0,
            details=details,
            recommended_removal='none'
        )

    def detect_side_channel_encoding(self) -> AdvancedWasteFindings:
        """
        Detect side-channel encoding (file size, timestamps, filename patterns).
        """
        details = {}
        channels_found = []

        try:
            file_stat = self.image_path.stat()

            # Check file size
            file_size = file_stat.st_size
            details['file_size_bytes'] = file_size

            # Suspicious if file size is a round number or follows pattern
            size_str = str(file_size)
            if size_str.endswith('000') or size_str.endswith('024'):
                channels_found.append('suspicious_file_size')
                details['round_file_size'] = True

            # Check timestamps
            mtime = datetime.fromtimestamp(file_stat.st_mtime)
            ctime = datetime.fromtimestamp(file_stat.st_ctime)

            # Suspicious if timestamp has specific pattern (e.g., all zeros in seconds)
            if mtime.second == 0 and mtime.microsecond == 0:
                channels_found.append('timestamp_pattern')
                details['zeroed_timestamp'] = True

            # Check filename for patterns
            filename = self.image_path.stem

            # Check for Base64-like patterns
            if re.match(r'^[A-Za-z0-9+/=]{16,}$', filename):
                channels_found.append('base64_filename')
                details['encoded_filename'] = True

            # Check for hex patterns
            if re.match(r'^[0-9A-Fa-f]{32,}$', filename):
                channels_found.append('hex_filename')
                details['hex_filename'] = True

            detected = len(channels_found) > 0
            confidence = min(0.7, len(channels_found) * 0.3)

            details['side_channels_found'] = channels_found

            return AdvancedWasteFindings(
                pattern_type='side_channel_encoding',
                detected=detected,
                confidence=confidence,
                details=details,
                recommended_removal='filesystem_sanitization'
            )

        except Exception as e:
            details['error'] = str(e)

        return AdvancedWasteFindings(
            pattern_type='side_channel_encoding',
            detected=False,
            confidence=0.0,
            details=details,
            recommended_removal='none'
        )

    def detect_ai_fingerprints(self) -> AdvancedWasteFindings:
        """
        Detect AI model fingerprints (specific to diffusion models, GANs, etc.).
        """
        details = {}
        fingerprints_found = []

        try:
            # Check for Gaussian noise patterns (common in diffusion models)
            # Calculate noise in smooth regions
            from scipy import ndimage

            gray = np.mean(self.image_array, axis=2)

            # Find smooth regions (low gradient)
            gradient = ndimage.sobel(gray)
            smooth_mask = gradient < np.percentile(gradient, 10)

            if np.sum(smooth_mask) > 100:
                smooth_pixels = gray[smooth_mask]
                noise_std = np.std(smooth_pixels)

                details['smooth_region_noise_std'] = float(noise_std)

                # Diffusion models often have specific noise characteristics
                if 2 < noise_std < 8:
                    fingerprints_found.append('diffusion_noise_pattern')
                    details['diffusion_fingerprint'] = True

            # Check for GAN artifacts (checkerboard patterns)
            # FFT to detect periodic artifacts
            from scipy import fft

            fft_result = fft.fft2(gray)
            fft_magnitude = np.abs(fft_result)

            # Look for strong frequency components at GAN-typical frequencies
            # (often at multiples of 2, 4, 8 due to upsampling)
            suspicious_freq_energy = np.sum(fft_magnitude[2:10, 2:10])
            total_energy = np.sum(fft_magnitude)

            freq_ratio = suspicious_freq_energy / total_energy if total_energy > 0 else 0
            details['frequency_concentration'] = float(freq_ratio)

            if freq_ratio > 0.01:
                fingerprints_found.append('gan_upsampling_artifacts')
                details['gan_fingerprint'] = True

            detected = len(fingerprints_found) > 0
            confidence = min(0.85, len(fingerprints_found) * 0.5)

            details['ai_fingerprints'] = fingerprints_found

            return AdvancedWasteFindings(
                pattern_type='ai_model_fingerprint',
                detected=detected,
                confidence=confidence,
                details=details,
                recommended_removal='ai_denoising'
            )

        except Exception as e:
            details['error'] = str(e)

        return AdvancedWasteFindings(
            pattern_type='ai_model_fingerprint',
            detected=False,
            confidence=0.0,
            details=details,
            recommended_removal='none'
        )

    def detect_temporal_encoding(self) -> AdvancedWasteFindings:
        """
        Detect encoding across image sequences (for multi-frame formats).
        """
        details = {}

        # Check if this is an animated format
        if hasattr(self.image, 'n_frames'):
            frame_count = self.image.n_frames
            details['frame_count'] = frame_count

            if frame_count > 1:
                # Analyze frame-to-frame differences
                frame_diffs = []

                for i in range(min(10, frame_count - 1)):
                    self.image.seek(i)
                    frame1 = np.array(self.image.convert('RGB'))

                    self.image.seek(i + 1)
                    frame2 = np.array(self.image.convert('RGB'))

                    diff = np.mean(np.abs(frame1.astype(float) - frame2.astype(float)))
                    frame_diffs.append(diff)

                if frame_diffs:
                    avg_diff = np.mean(frame_diffs)
                    diff_std = np.std(frame_diffs)

                    details['avg_frame_difference'] = float(avg_diff)
                    details['frame_diff_std'] = float(diff_std)

                    # Very consistent frame differences might indicate encoding
                    detected = diff_std < 1.0 and avg_diff > 0
                    confidence = 0.6 if detected else 0.1

                    return AdvancedWasteFindings(
                        pattern_type='temporal_encoding',
                        detected=detected,
                        confidence=confidence,
                        details=details,
                        recommended_removal='frame_normalization'
                    )

        return AdvancedWasteFindings(
            pattern_type='temporal_encoding',
            detected=False,
            confidence=0.0,
            details={'static_image': True},
            recommended_removal='none'
        )

    # Helper methods

    def _calculate_entropy(self, data: np.ndarray) -> float:
        """Calculate Shannon entropy of data."""
        if len(data) == 0:
            return 0.0

        _, counts = np.unique(data, return_counts=True)
        probabilities = counts / len(data)
        entropy = -np.sum(probabilities * np.log2(probabilities + 1e-10))

        return float(entropy)

    def _rotate_image(self, image: np.ndarray, angle: float) -> np.ndarray:
        """Rotate image by given angle."""
        try:
            import cv2
            center = (image.shape[1] // 2, image.shape[0] // 2)
            matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(image, matrix, (image.shape[1], image.shape[0]))
            return rotated
        except:
            return image


def analyze_advanced_waste(image_path: str) -> Dict[str, Any]:
    """Convenience function to run all advanced waste detection."""
    detector = AdvancedWasteDetector(image_path)
    return detector.analyze()


if __name__ == '__main__':
    import sys
    from rich.console import Console
    from rich.table import Table

    if len(sys.argv) < 2:
        print("Usage: python advanced_waste_detector.py <image_path>")
        sys.exit(1)

    console = Console()

    console.print("\n[bold cyan]🔬 Advanced Waste Detection[/bold cyan]\n")

    results = analyze_advanced_waste(sys.argv[1])

    # Display results
    table = Table(title="Detection Results")
    table.add_column("Pattern Type", style="cyan")
    table.add_column("Detected", style="yellow")
    table.add_column("Confidence", style="green")
    table.add_column("Removal Method", style="magenta")

    for pattern_type, finding in results.items():
        if isinstance(finding, AdvancedWasteFindings):
            status = "✓ YES" if finding.detected else "✗ No"
            status_color = "green" if finding.detected else "dim"

            table.add_row(
                finding.pattern_type.replace('_', ' ').title(),
                f"[{status_color}]{status}[/{status_color}]",
                f"{finding.confidence:.1%}",
                finding.recommended_removal
            )

    console.print(table)

    # Show details for detected patterns
    console.print("\n[bold yellow]Detailed Findings:[/bold yellow]\n")
    for pattern_type, finding in results.items():
        if isinstance(finding, AdvancedWasteFindings) and finding.detected:
            console.print(f"[bold]{finding.pattern_type}:[/bold]")
            for key, value in finding.details.items():
                console.print(f"  • {key}: {value}")
            console.print()
