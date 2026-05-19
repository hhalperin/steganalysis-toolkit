"""
Visible Watermark Detector - Advanced detection of visible watermarks in images
Uses computer vision techniques to identify unnatural visual patterns
"""

import numpy as np
from PIL import Image
import cv2
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import math

try:
    import scipy.ndimage as ndimage
    from scipy import signal
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

@dataclass
class VisibleWatermarkDetection:
    """Result from visible watermark detection."""
    detected: bool
    confidence: float
    watermark_type: str
    location: Tuple[int, int, int, int]  # (x, y, width, height)
    characteristics: Dict[str, Any]
    recommended_removal: str


class VisibleWatermarkDetector:
    """Advanced detector for visible watermarks using computer vision techniques."""

    def __init__(self, image_path: str):
        self.image_path = Path(image_path)
        self.image = None
        self.image_array = None
        self.grayscale = None
        self.load_image()

    def load_image(self):
        """Load and prepare image for analysis."""
        try:
            self.image = Image.open(self.image_path).convert('RGB')
            self.image_array = np.array(self.image)

            # Convert to grayscale for many operations
            if len(self.image_array.shape) == 3:
                self.grayscale = cv2.cvtColor(self.image_array, cv2.COLOR_RGB2GRAY)
            else:
                self.grayscale = self.image_array.copy()

        except Exception as e:
            print(f"Error loading image: {e}")
            return False
        return True

    def detect_visible_watermarks(self) -> List[VisibleWatermarkDetection]:
        """Comprehensive visible watermark detection."""
        if self.image_array is None:
            return []

        detections = []

        # Multiple detection approaches
        detections.extend(self._detect_gradient_anomalies())
        detections.extend(self._detect_edge_anomalies())
        detections.extend(self._detect_texture_anomalies())
        detections.extend(self._detect_color_transition_anomalies())
        detections.extend(self._detect_geometric_patterns())
        detections.extend(self._detect_frequency_anomalies())

        # Filter and merge overlapping detections
        filtered_detections = self._filter_and_merge_detections(detections)

        return filtered_detections

    def _detect_gradient_anomalies(self) -> List[VisibleWatermarkDetection]:
        """Detect unnatural gradient patterns that create visible artifacts."""
        detections = []

        if not SCIPY_AVAILABLE:
            return detections

        # Calculate gradients
        grad_x = ndimage.sobel(self.grayscale, axis=1)
        grad_y = ndimage.sobel(self.grayscale, axis=0)
        gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)

        # Find areas with unnatural gradient patterns
        height, width = self.grayscale.shape

        # Look for areas with high gradient variance (unnatural edges)
        for window_size in [32, 64, 128]:
            if window_size >= min(height, width):
                continue

            for y in range(0, height - window_size, window_size // 2):
                for x in range(0, width - window_size, window_size // 2):
                    window = gradient_magnitude[y:y+window_size, x:x+window_size]

                    if window.size == 0:
                        continue

                    # Calculate gradient statistics
                    mean_grad = np.mean(window)
                    std_grad = np.std(window)
                    max_grad = np.max(window)

                    # Unnatural patterns: high local variance in smooth areas
                    # or regular patterns in gradient magnitude
                    if std_grad > mean_grad * 2 and max_grad > mean_grad * 3:
                        # Check for regular patterns (common in watermarks)
                        fft_window = np.fft.fft2(window)
                        fft_magnitude = np.abs(fft_window)

                        # Look for strong frequency components
                        center = fft_magnitude.shape[0] // 2
                        strong_freqs = np.sum(fft_magnitude[center-2:center+2, center-2:center+2])

                        if strong_freqs > np.mean(fft_magnitude) * 5:
                            detections.append(VisibleWatermarkDetection(
                                detected=True,
                                confidence=min(0.9, (std_grad / mean_grad) / 2),
                                watermark_type='gradient_anomaly',
                                location=(x, y, window_size, window_size),
                                characteristics={
                                    'gradient_std': float(std_grad),
                                    'gradient_mean': float(mean_grad),
                                    'gradient_ratio': float(std_grad / mean_grad),
                                    'frequency_strength': float(strong_freqs / np.mean(fft_magnitude))
                                },
                                recommended_removal='gradient_guided_cleaning'
                            ))

        return detections

    def _detect_edge_anomalies(self) -> List[VisibleWatermarkDetection]:
        """Detect watermark boundaries using edge detection."""
        detections = []

        if not cv2:
            return detections

        # Apply Canny edge detection
        edges = cv2.Canny(self.grayscale, 50, 150)

        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            if len(contour) < 10:  # Too small to be a watermark
                continue

            # Get bounding box
            x, y, w, h = cv2.boundingRect(contour)

            # Filter by size and aspect ratio
            area = cv2.contourArea(contour)
            aspect_ratio = w / h if h > 0 else 0

            # Watermark characteristics
            if (50 < area < 50000 and  # Reasonable size range
                0.2 < aspect_ratio < 5.0 and  # Reasonable aspect ratio
                len(contour) > 20):  # Enough detail

                # Calculate edge density
                edge_density = len(contour) / (w * h) if w * h > 0 else 0

                if edge_density > 0.1:  # High edge density suggests artificial boundaries
                    detections.append(VisibleWatermarkDetection(
                        detected=True,
                        confidence=min(0.85, edge_density * 2),
                        watermark_type='edge_anomaly',
                        location=(x, y, w, h),
                        characteristics={
                            'contour_area': int(area),
                            'edge_density': float(edge_density),
                            'aspect_ratio': float(aspect_ratio),
                            'contour_length': len(contour)
                        },
                        recommended_removal='edge_guided_inpaint'
                    ))

        return detections

    def _detect_texture_anomalies(self) -> List[VisibleWatermarkDetection]:
        """Analyze texture consistency to find watermark regions."""
        detections = []

        height, width = self.grayscale.shape

        # Use local binary patterns or similar texture analysis
        for window_size in [16, 32, 64]:
            if window_size >= min(height, width):
                continue

            for y in range(0, height - window_size, window_size // 2):
                for x in range(0, width - window_size, window_size // 2):
                    window = self.grayscale[y:y+window_size, x:x+window_size]

                    if window.size == 0:
                        continue

                    # Calculate texture metrics
                    texture_variance = np.var(window)
                    texture_entropy = self._calculate_entropy(window)

                    # Calculate local contrast
                    kernel = np.ones((3, 3)) / 9
                    local_mean = signal.convolve2d(window, kernel, mode='same', boundary='symm')
                    local_std = np.sqrt(signal.convolve2d((window - local_mean)**2, kernel, mode='same'))

                    contrast = np.mean(local_std)

                    # Unnatural texture patterns
                    if (texture_variance < 100 or  # Too uniform
                        texture_entropy < 2.0 or  # Too predictable
                        contrast > 50):  # Too high contrast

                        detections.append(VisibleWatermarkDetection(
                            detected=True,
                            confidence=min(0.8, (contrast / 50) * 0.5),
                            watermark_type='texture_anomaly',
                            location=(x, y, window_size, window_size),
                            characteristics={
                                'texture_variance': float(texture_variance),
                                'texture_entropy': float(texture_entropy),
                                'local_contrast': float(contrast)
                            },
                            recommended_removal='texture_synthesis'
                        ))

        return detections

    def _detect_color_transition_anomalies(self) -> List[VisibleWatermarkDetection]:
        """Detect sharp color transitions indicative of watermarks."""
        detections = []

        if len(self.image_array.shape) != 3:
            return detections

        # Calculate color gradients
        for channel in range(3):
            channel_data = self.image_array[:, :, channel].astype(float)

            grad_x = np.abs(np.gradient(channel_data, axis=1))
            grad_y = np.abs(np.gradient(channel_data, axis=0))

            # Find areas with sharp transitions
            transition_strength = grad_x + grad_y

            # Find local maxima in transition strength
            height, width = transition_strength.shape

            for y in range(1, height - 1):
                for x in range(1, width - 1):
                    local_window = transition_strength[y-1:y+2, x-1:x+2]

                    if transition_strength[y, x] == np.max(local_window):
                        # Check if this is an unnaturally sharp transition
                        max_transition = np.max(transition_strength)
                        if max_transition > 100:  # Threshold for sharp transitions
                            # Find connected region of high transitions
                            mask = transition_strength > (max_transition * 0.5)
                            component_coords = np.where(mask)

                            if len(component_coords[0]) > 20:  # Minimum region size
                                min_y, max_y = np.min(component_coords[0]), np.max(component_coords[0])
                                min_x, max_x = np.min(component_coords[1]), np.max(component_coords[1])

                                detections.append(VisibleWatermarkDetection(
                                    detected=True,
                                    confidence=min(0.9, max_transition / 255),
                                    watermark_type='color_transition',
                                    location=(min_x, min_y, max_x - min_x, max_y - min_y),
                                    characteristics={
                                        'transition_strength': float(max_transition),
                                        'region_size': len(component_coords[0])
                                    },
                                    recommended_removal='transition_blurring'
                                ))

        return detections

    def _detect_geometric_patterns(self) -> List[VisibleWatermarkDetection]:
        """Detect regular geometric patterns common in watermarks."""
        detections = []

        # Look for rectangular patterns
        edges = cv2.Canny(self.grayscale, 50, 150)

        # Hough transform for lines
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, minLineLength=20, maxLineGap=10)

        if lines is not None:
            # Group lines that form rectangles
            horizontal_lines = []
            vertical_lines = []

            for line in lines:
                x1, y1, x2, y2 = line[0]

                # Determine orientation
                if abs(y2 - y1) < abs(x2 - x1):  # Horizontal-ish
                    horizontal_lines.append((min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)))
                else:  # Vertical-ish
                    vertical_lines.append((min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)))

            # Look for intersecting lines forming rectangles
            for h_line in horizontal_lines:
                for v_line in vertical_lines:
                    # Check if lines intersect or form corners
                    h_x1, h_y1, h_x2, h_y2 = h_line
                    v_x1, v_y1, v_x2, v_y2 = v_line

                    # Simple intersection check
                    if (h_x1 <= v_x1 <= h_x2 and v_y1 <= h_y1 <= v_y2):
                        # Potential corner - expand to find rectangle
                        detections.append(VisibleWatermarkDetection(
                            detected=True,
                            confidence=0.7,
                            watermark_type='geometric_pattern',
                            location=(min(h_x1, v_x1), min(h_y1, v_y1), abs(h_x2 - v_x2), abs(h_y2 - v_y2)),
                            characteristics={
                                'pattern_type': 'rectangle',
                                'line_count': len(horizontal_lines) + len(vertical_lines)
                            },
                            recommended_removal='geometric_inpaint'
                        ))

        return detections

    def _detect_frequency_anomalies(self) -> List[VisibleWatermarkDetection]:
        """Detect anomalies in frequency domain that indicate visible patterns."""
        detections = []

        # Apply FFT to grayscale image
        fft_result = np.fft.fft2(self.grayscale)
        fft_shift = np.fft.fftshift(fft_result)
        magnitude_spectrum = np.log(np.abs(fft_shift) + 1)

        # Look for strong frequency components (indicating regular patterns)
        height, width = magnitude_spectrum.shape
        center_y, center_x = height // 2, width // 2

        # Check different frequency ranges
        for radius in [5, 10, 20, 40]:
            if radius * 2 >= min(height, width):
                continue

            # Create annular regions
            y, x = np.ogrid[:height, :width]
            distance = np.sqrt((x - center_x)**2 + (y - center_y)**2)

            ring_mask = (distance > radius) & (distance < radius + 5)
            ring_energy = np.sum(magnitude_spectrum[ring_mask])

            total_energy = np.sum(magnitude_spectrum)
            ring_ratio = ring_energy / total_energy if total_energy > 0 else 0

            # High energy in specific frequency bands suggests patterns
            if ring_ratio > 0.1:
                detections.append(VisibleWatermarkDetection(
                    detected=True,
                    confidence=min(0.8, ring_ratio * 2),
                    watermark_type='frequency_anomaly',
                    location=(center_x - radius, center_y - radius, radius * 2, radius * 2),
                    characteristics={
                        'frequency_radius': radius,
                        'ring_energy_ratio': float(ring_ratio),
                        'dominant_frequency': True
                    },
                    recommended_removal='frequency_filtering'
                ))

        return detections

    def _calculate_entropy(self, data: np.ndarray) -> float:
        """Calculate Shannon entropy."""
        if data.size == 0:
            return 0.0

        hist, _ = np.histogram(data, bins=256, range=(0, 255))
        hist = hist[hist > 0]
        if len(hist) == 0:
            return 0.0

        probabilities = hist / data.size
        entropy = -np.sum(probabilities * np.log2(probabilities + 1e-10))
        return float(entropy)

    def _filter_and_merge_detections(self, detections: List[VisibleWatermarkDetection]) -> List[VisibleWatermarkDetection]:
        """Filter overlapping detections and remove duplicates."""
        if not detections:
            return []

        # Sort by confidence
        detections.sort(key=lambda x: x.confidence, reverse=True)

        filtered = []

        for detection in detections:
            # Check if this detection overlaps significantly with existing ones
            overlaps = False
            for existing in filtered:
                if self._calculate_overlap(detection.location, existing.location) > 0.5:
                    overlaps = True
                    break

            if not overlaps:
                filtered.append(detection)

        return filtered

    def _calculate_overlap(self, rect1: Tuple[int, int, int, int], rect2: Tuple[int, int, int, int]) -> float:
        """Calculate overlap ratio between two rectangles."""
        x1, y1, w1, h1 = rect1
        x2, y2, w2, h2 = rect2

        # Calculate intersection
        ix = max(x1, x2)
        iy = max(y1, y2)
        iw = min(x1 + w1, x2 + w2) - ix
        ih = min(y1 + h1, y2 + h2) - iy

        if iw <= 0 or ih <= 0:
            return 0.0

        # Calculate union area
        area1 = w1 * h1
        area2 = w2 * h2
        intersection = iw * ih
        union = area1 + area2 - intersection

        return intersection / union if union > 0 else 0.0

    def generate_detection_report(self) -> Dict[str, Any]:
        """Generate comprehensive detection report."""
        detections = self.detect_visible_watermarks()

        # Convert numpy types to Python types for JSON serialization
        def convert_numpy_types(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert_numpy_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            return obj

        report = {
            'image_path': str(self.image_path),
            'image_info': {
                'size': self.image.size if self.image else None,
                'mode': self.image.mode if self.image else None,
                'format': self.image.format if self.image else None
            },
            'total_detections': len(detections),
            'detections': [
                {
                    'type': detection.watermark_type,
                    'confidence': float(detection.confidence),
                    'location': tuple(int(x) for x in detection.location),
                    'characteristics': convert_numpy_types(detection.characteristics),
                    'recommended_removal': detection.recommended_removal
                }
                for detection in detections
            ],
            'summary': {
                'types_found': list(set(d.watermark_type for d in detections)),
                'avg_confidence': float(np.mean([d.confidence for d in detections])) if detections else 0.0,
                'most_confident_type': max(detections, key=lambda x: x.confidence).watermark_type if detections else None
            }
        }

        return report


def detect_visible_watermarks(image_path: str) -> Dict[str, Any]:
    """Convenience function to detect visible watermarks in an image."""
    detector = VisibleWatermarkDetector(image_path)
    return detector.generate_detection_report()


if __name__ == '__main__':
    import sys

    if len(sys.argv) != 2:
        print("Usage: python visible_watermark_detector.py <image_path>")
        sys.exit(1)

    image_path = sys.argv[1]

    if not Path(image_path).exists():
        print(f"File not found: {image_path}")
        sys.exit(1)

    print(f"🔍 DETECTING VISIBLE WATERMARKS: {image_path}")

    result = detect_visible_watermarks(image_path)

    print("\n📊 DETECTION RESULTS:")
    print(f"  Total detections: {result['total_detections']}")
    print(f"  Types found: {result['summary']['types_found']}")
    print(f"  Average confidence: {result['summary']['avg_confidence']:.1%}")

    if result['detections']:
        print("\n🎯 DETAILED DETECTIONS:")
        for i, detection in enumerate(result['detections'], 1):
            print(f"  {i}. {detection['type']} (confidence: {detection['confidence']:.1%})")
            print(f"     Location: {detection['location']}")
            print(f"     Recommended removal: {detection['recommended_removal']}")
    else:
        print("\n✅ No visible watermarks detected!")
