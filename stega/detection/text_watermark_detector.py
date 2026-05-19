"""
Text Watermark Detector - Specialized detection for repeated text watermarks
Uses OCR and pattern analysis to identify repeated text elements
"""

import cv2
import numpy as np
from PIL import Image
import pytesseract
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import re

@dataclass
class TextWatermarkDetection:
    """Result from text watermark detection."""
    detected: bool
    confidence: float
    text_content: str
    location: Tuple[int, int, int, int]  # (x, y, width, height)
    background_colors: List[Tuple[int, int, int]]
    text_color: Tuple[int, int, int]
    repetition_count: int
    characteristics: Dict[str, Any]


class TextWatermarkDetector:
    """Specialized detector for repeated text watermarks."""

    def __init__(self, image_path: str):
        self.image_path = Path(image_path)
        self.image = None
        self.image_array = None
        self.load_image()

    def load_image(self):
        """Load and prepare image for text analysis."""
        try:
            self.image = Image.open(self.image_path).convert('RGB')
            self.image_array = np.array(self.image)
        except Exception as e:
            print(f"Error loading image: {e}")
            return False
        return True

    def detect_text_watermarks(self) -> List[TextWatermarkDetection]:
        """Comprehensive text watermark detection."""
        if self.image_array is None:
            return []

        detections = []

        # Multiple detection approaches for text
        ocr_detections = self._detect_with_ocr()
        pattern_detections = self._detect_repeated_patterns()
        color_detections = self._detect_color_anomalies()

        # Combine and filter detections
        all_detections = ocr_detections + pattern_detections + color_detections
        filtered_detections = self._filter_text_detections(all_detections)

        return filtered_detections

    def _detect_with_ocr(self) -> List[TextWatermarkDetection]:
        """Use OCR to detect text in the image."""
        detections = []

        try:
            # Configure Tesseract for better accuracy
            config = '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz -c tessedit_pageseg_mode=6'

            # Get image data for OCR
            gray = cv2.cvtColor(self.image_array, cv2.COLOR_RGB2GRAY)

            # Try different preprocessing approaches
            preprocessed_images = [
                gray,  # Original
                cv2.GaussianBlur(gray, (1, 1), 0),  # Slight blur
                cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],  # Threshold
            ]

            for i, img in enumerate(preprocessed_images):
                try:
                    # Extract text
                    text = pytesseract.image_to_string(img, config=config).strip()

                    if text and len(text) > 2:  # Minimum text length
                        # Get bounding boxes for detected text
                        boxes = pytesseract.image_to_boxes(img, config=config)

                        for box in boxes.splitlines():
                            if len(box) >= 6:
                                char, x1, y1, x2, y2 = box[:5]
                                if char.isalnum():  # Only alphanumeric characters
                                    # Convert coordinates (Tesseract uses bottom-left origin)
                                    height, width = img.shape[:2]
                                    x1, x2 = int(x1), int(x2)
                                    y1, y2 = height - int(y2), height - int(y1)

                                    detections.append(TextWatermarkDetection(
                                        detected=True,
                                        confidence=0.8,
                                        text_content=char,
                                        location=(x1, y1, x2 - x1, y2 - y1),
                                        background_colors=self._sample_background_colors(x1, y1, x2 - x1, y2 - y1),
                                        text_color=self._get_text_color(x1, y1, x2 - x1, y2 - y1),
                                        repetition_count=1,
                                        characteristics={
                                            'ocr_method': f'preprocess_{i}',
                                            'char_detected': char,
                                            'confidence': 0.8
                                        }
                                    ))

                except Exception as e:
                    print(f"OCR preprocessing {i} failed: {e}")

        except Exception as e:
            print(f"OCR detection failed: {e}")

        return detections

    def _detect_repeated_patterns(self) -> List[TextWatermarkDetection]:
        """Detect repeated visual patterns that might be text."""
        detections = []

        gray = cv2.cvtColor(self.image_array, cv2.COLOR_RGB2GRAY)

        # Use template matching to find repeated patterns
        # Look for small regions that repeat

        # Find contours that might be text characters
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Group contours by similarity
        similar_groups = self._group_similar_contours(contours)

        for group in similar_groups:
            if len(group) >= 3:  # At least 3 similar shapes (repeated text)
                # Calculate average bounding box
                bboxes = [cv2.boundingRect(c) for c in group]
                x_coords = [b[0] for b in bboxes]
                y_coords = [b[1] for b in bboxes]
                widths = [b[2] for b in bboxes]
                heights = [b[3] for b in bboxes]

                avg_x = int(np.mean(x_coords))
                avg_y = int(np.mean(y_coords))
                avg_w = int(np.mean(widths))
                avg_h = int(np.mean(heights))

                # Sample background and text colors
                bg_colors = self._sample_background_colors(avg_x, avg_y, avg_w, avg_h)
                text_color = self._get_text_color(avg_x, avg_y, avg_w, avg_h)

                detections.append(TextWatermarkDetection(
                    detected=True,
                    confidence=min(0.9, len(group) * 0.1),  # More instances = higher confidence
                    text_content=f"Repeated pattern ({len(group)} instances)",
                    location=(avg_x, avg_y, avg_w, avg_h),
                    background_colors=bg_colors,
                    text_color=text_color,
                    repetition_count=len(group),
                    characteristics={
                        'pattern_type': 'repeated_visual',
                        'instance_count': len(group),
                        'avg_size': (avg_w, avg_h)
                    }
                ))

        return detections

    def _detect_color_anomalies(self) -> List[TextWatermarkDetection]:
        """Detect color anomalies that might indicate text watermarks."""
        detections = []

        # Look for areas with unusual color consistency (like white text on colored background)
        height, width = self.image_array.shape[:2]

        # Sample different regions to find anomalies
        for y in range(0, height - 20, 10):
            for x in range(0, width - 20, 10):
                region = self.image_array[y:y+20, x:x+20]

                if region.size == 0:
                    continue

                # Calculate color statistics
                region_flat = region.reshape(-1, 3)
                colors = region_flat.astype(float)

                # Check for high contrast areas (text vs background)
                brightness = np.mean(colors, axis=1)
                contrast = np.std(brightness)

                # Check for dominant colors (background) vs outliers (text)
                unique_colors, counts = np.unique(region_flat, axis=0, return_counts=True)
                dominant_color = unique_colors[np.argmax(counts)]

                # If there's high contrast and a dominant background color, might be text
                if contrast > 30 and np.max(counts) > len(colors) * 0.6:
                    # Check if the outliers are lighter (white text)
                    outlier_mask = np.all(region_flat != dominant_color, axis=1)
                    if np.any(outlier_mask):
                        outlier_colors = region_flat[outlier_mask]
                        avg_outlier_brightness = np.mean(outlier_colors)

                        if avg_outlier_brightness > np.mean(brightness) + 20:  # Significantly brighter
                            detections.append(TextWatermarkDetection(
                                detected=True,
                                confidence=min(0.7, contrast / 50),
                                text_content="Bright anomaly",
                                location=(x, y, 20, 20),
                                background_colors=[tuple(dominant_color.astype(int))],
                                text_color=tuple(np.mean(outlier_colors, axis=0).astype(int)),
                                repetition_count=1,
                                characteristics={
                                    'color_contrast': float(contrast),
                                    'dominant_color_ratio': float(np.max(counts) / len(colors)),
                                    'outlier_brightness': float(avg_outlier_brightness)
                                }
                            ))

        return detections

    def _group_similar_contours(self, contours: List) -> List[List]:
        """Group contours that are similar in shape and size."""
        if not contours:
            return []

        groups = []

        for contour in contours:
            added_to_group = False

            # Get contour properties
            area = cv2.contourArea(contour)
            perimeter = cv2.arcLength(contour, True)
            bbox = cv2.boundingRect(contour)

            if area < 5 or perimeter < 10:  # Too small
                continue

            # Check against existing groups
            for group in groups:
                # Check if this contour is similar to contours in the group
                group_areas = [cv2.contourArea(c) for c in group]
                group_bboxes = [cv2.boundingRect(c) for c in group]

                # Check area similarity
                if group_areas:
                    area_similarity = all(abs(a - area) / max(a, area) < 0.3 for a in group_areas)

                    # Check size similarity
                    size_similarity = all(
                        abs(b[2] - bbox[2]) / max(b[2], bbox[2]) < 0.3 and
                        abs(b[3] - bbox[3]) / max(b[3], bbox[3]) < 0.3
                        for b in group_bboxes
                    )

                    if area_similarity and size_similarity:
                        group.append(contour)
                        added_to_group = True
                        break

            if not added_to_group:
                groups.append([contour])

        # Filter groups with at least 2 similar contours
        return [g for g in groups if len(g) >= 2]

    def _sample_background_colors(self, x: int, y: int, w: int, h: int) -> List[Tuple[int, int, int]]:
        """Sample background colors around the text region."""
        colors = []
        margin = 5

        # Sample from all four sides
        sides = [
            (x - margin, y, 1, h),  # Left
            (x + w + margin, y, 1, h),  # Right
            (x, y - margin, w, 1),  # Top
            (x, y + h + margin, w, 1),  # Bottom
        ]

        for sx, sy, sw, sh in sides:
            if (sx >= 0 and sy >= 0 and
                sx + sw <= self.image_array.shape[1] and
                sy + sh <= self.image_array.shape[0]):

                region = self.image_array[sy:sy+sh, sx:sx+sw]
                if region.size > 0:
                    # Take median color as background
                    median_color = np.median(region.reshape(-1, 3), axis=0)
                    colors.append(tuple(median_color.astype(int)))

        return colors

    def _get_text_color(self, x: int, y: int, w: int, h: int) -> Tuple[int, int, int]:
        """Get the dominant color in the text region."""
        region = self.image_array[y:y+h, x:x+w]

        if region.size == 0:
            return (255, 255, 255)  # Default to white

        # Find most common color (likely text color)
        unique_colors, counts = np.unique(region.reshape(-1, 3), axis=0, return_counts=True)
        dominant_color = unique_colors[np.argmax(counts)]

        return tuple(dominant_color.astype(int))

    def _filter_text_detections(self, detections: List[TextWatermarkDetection]) -> List[TextWatermarkDetection]:
        """Filter and merge overlapping text detections."""
        if not detections:
            return []

        # Sort by confidence
        detections.sort(key=lambda x: x.confidence, reverse=True)

        filtered = []

        for detection in detections:
            # Check for overlap with existing detections
            overlaps = False
            for existing in filtered:
                if self._calculate_overlap(detection.location, existing.location) > 0.3:
                    # Merge similar detections
                    if detection.text_content == existing.text_content:
                        # Combine the detections
                        existing.repetition_count += 1
                        existing.confidence = max(existing.confidence, detection.confidence)
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

    def generate_text_report(self) -> Dict[str, Any]:
        """Generate comprehensive text watermark report."""
        detections = self.detect_text_watermarks()

        # Convert numpy types for JSON serialization
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
            'total_text_detections': len(detections),
            'text_detections': [
                {
                    'text_content': detection.text_content,
                    'confidence': float(detection.confidence),
                    'location': tuple(int(x) for x in detection.location),
                    'background_colors': [tuple(c) for c in detection.background_colors],
                    'text_color': tuple(detection.text_color),
                    'repetition_count': detection.repetition_count,
                    'characteristics': convert_numpy_types(detection.characteristics)
                }
                for detection in detections
            ],
            'summary': {
                'unique_texts': list(set(d.text_content for d in detections)),
                'avg_confidence': float(np.mean([d.confidence for d in detections])) if detections else 0.0,
                'total_repetitions': sum(d.repetition_count for d in detections),
                'most_repeated_text': max(detections, key=lambda x: x.repetition_count).text_content if detections else None
            }
        }

        return report


def detect_text_watermarks(image_path: str) -> Dict[str, Any]:
    """Convenience function to detect text watermarks in an image."""
    detector = TextWatermarkDetector(image_path)
    return detector.generate_text_report()


if __name__ == '__main__':
    import sys

    if len(sys.argv) != 2:
        print("Usage: python text_watermark_detector.py <image_path>")
        sys.exit(1)

    image_path = sys.argv[1]

    if not Path(image_path).exists():
        print(f"File not found: {image_path}")
        sys.exit(1)

    print(f"🔤 DETECTING TEXT WATERMARKS: {image_path}")

    result = detect_text_watermarks(image_path)

    print("\n📊 TEXT DETECTION RESULTS:")
    print(f"  Total detections: {result['total_text_detections']}")
    print(f"  Unique texts: {result['summary']['unique_texts']}")
    print(f"  Average confidence: {result['summary']['avg_confidence']:.1%}")
    print(f"  Total repetitions: {result['summary']['total_repetitions']}")

    if result['text_detections']:
        print("\n📝 DETAILED TEXT DETECTIONS:")
        for i, detection in enumerate(result['text_detections'], 1):
            print(f"  {i}. '{detection['text_content']}' (confidence: {detection['confidence']:.1%})")
            print(f"     Location: {detection['location']}")
            print(f"     Repetitions: {detection['repetition_count']}")
            print(f"     Text color: {detection['text_color']}")
            print(f"     Background colors: {detection['background_colors']}")
    else:
        print("\n✅ No text watermarks detected!")
