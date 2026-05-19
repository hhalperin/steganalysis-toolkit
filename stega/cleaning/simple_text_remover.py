"""
Simple Text Watermark Remover (No OCR Required)
Uses computer vision techniques to detect and remove repeated text patterns.
"""

import cv2
import numpy as np
from PIL import Image
from pathlib import Path


class SimpleTextRemover:
    """Removes repeated text watermarks using computer vision."""

    def __init__(self):
        pass

    def detect_repeated_patterns(self, image_path):
        """Detect repeated visual patterns that might be text."""
        try:
            image = Image.open(image_path)
            image_array = np.array(image)

            if len(image_array.shape) == 3:
                gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = image_array

            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            text_like_contours = []
            for contour in contours:
                area = cv2.contourArea(contour)
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h if h > 0 else 0

                if (10 < area < 1000 and 0.2 < aspect_ratio < 5.0 and min(w, h) > 5):
                    text_like_contours.append({
                        "contour": contour,
                        "bbox": (x, y, w, h),
                        "area": area,
                        "aspect_ratio": aspect_ratio,
                    })

            return self._group_similar_contours(text_like_contours)

        except Exception as e:
            print(f"Pattern detection failed: {e}")
            return []

    def _group_similar_contours(self, contours):
        """Group contours that are similar in shape and size."""
        if not contours:
            return []

        groups = []
        for contour_info in contours:
            added_to_group = False
            for group in groups:
                group_areas = [c["area"] for c in group]
                group_bboxes = [c["bbox"] for c in group]
                if group_areas:
                    area_sim = all(
                        abs(a - contour_info["area"]) / max(a, contour_info["area"]) < 0.4
                        for a in group_areas
                    )
                    size_sim = all(
                        abs(b[2] - contour_info["bbox"][2]) / max(b[2], contour_info["bbox"][2]) < 0.4
                        and abs(b[3] - contour_info["bbox"][3]) / max(b[3], contour_info["bbox"][3]) < 0.4
                        for b in group_bboxes
                    )
                    if area_sim and size_sim:
                        group.append(contour_info)
                        added_to_group = True
                        break
            if not added_to_group:
                groups.append([contour_info])

        return [g for g in groups if len(g) >= 2]

    def remove_text_patterns(self, image_path, output_path):
        """Remove detected text patterns."""
        try:
            image = Image.open(image_path)
            image_array = np.array(image)
            patterns = self.detect_repeated_patterns(image_path)

            if not patterns:
                print("No repeated text patterns found")
                image.save(output_path)
                return False

            print(f"Found {len(patterns)} repeated text patterns")
            cleaned_array = image_array.copy()

            for i, pattern in enumerate(patterns):
                print(f"Removing pattern {i+1}: {len(pattern)} instances")
                bboxes = [instance["bbox"] for instance in pattern]
                for bbox in bboxes:
                    x, y, w, h = bbox
                    mask = np.zeros(image_array.shape[:2], dtype=np.uint8)
                    expand = max(2, min(w, h) // 4)
                    x_start, y_start = max(0, x - expand), max(0, y - expand)
                    x_end = min(image_array.shape[1], x + w + expand)
                    y_end = min(image_array.shape[0], y + h + expand)
                    mask[y_start:y_end, x_start:x_end] = 255
                    for channel in range(3):
                        ch = cleaned_array[:, :, channel]
                        inpainted = cv2.inpaint(ch, mask, 3, cv2.INPAINT_TELEA)
                        cleaned_array[:, :, channel] = inpainted

            Image.fromarray(cleaned_array).save(output_path)
            print(f"Saved cleaned image: {output_path}")
            return True

        except Exception as e:
            print(f"Text removal failed: {e}")
            return False
