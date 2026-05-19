"""
Text Watermark Remover - Specialized removal of repeated text watermarks
Uses color matching and inpainting to seamlessly remove text
"""

import cv2
import numpy as np
from PIL import Image
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import math

@dataclass
class TextRemovalResult:
    """Result from text watermark removal."""
    success: bool
    original_path: str
    cleaned_path: str
    removal_method: str
    quality_metrics: Dict[str, float]
    text_instances_removed: int
    processing_time: float
    technical_details: Dict[str, Any]


class TextWatermarkRemover:
    """Specialized remover for text watermarks using color matching."""

    def __init__(self, image_path: str):
        self.image_path = Path(image_path)
        self.image = None
        self.image_array = None
        self.load_image()

    def load_image(self):
        """Load and prepare image for text removal."""
        try:
            self.image = Image.open(self.image_path).convert('RGB')
            self.image_array = np.array(self.image)
        except Exception as e:
            print(f"Error loading image: {e}")
            return False
        return True

    def remove_text_watermarks(self, detection_results: List[Dict], output_path: str, method: str = "color_matching") -> TextRemovalResult:
        """Remove text watermarks using specified method."""
        if self.image_array is None:
            return TextRemovalResult(
                success=False,
                original_path=str(self.image_path),
                cleaned_path="",
                removal_method=method,
                quality_metrics={},
                text_instances_removed=0,
                processing_time=0.0,
                technical_details={'error': 'Failed to load image'}
            )

        import time
        start_time = time.time()

        try:
            cleaned_array = self.image_array.copy()

            if method == "color_matching":
                cleaned_array = self._apply_color_matching(cleaned_array, detection_results)
            elif method == "inpainting":
                cleaned_array = self._apply_text_inpainting(cleaned_array, detection_results)
            elif method == "blurring":
                cleaned_array = self._apply_text_blurring(cleaned_array, detection_results)
            elif method == "pattern_replacement":
                cleaned_array = self._apply_pattern_replacement(cleaned_array, detection_results)
            else:
                raise ValueError(f"Unknown removal method: {method}")

            # Save cleaned image
            cleaned_image = Image.fromarray(cleaned_array)
            cleaned_image.save(output_path, 'PNG', optimize=True)

            # Calculate quality metrics
            quality_metrics = self._calculate_text_removal_quality(self.image_array, cleaned_array, detection_results)

            processing_time = time.time() - start_time

            return TextRemovalResult(
                success=True,
                original_path=str(self.image_path),
                cleaned_path=output_path,
                removal_method=method,
                quality_metrics=quality_metrics,
                text_instances_removed=len(detection_results),
                processing_time=processing_time,
                technical_details={
                    'detection_count': len(detection_results),
                    'method_used': method,
                    'image_size': self.image_array.shape
                }
            )

        except Exception as e:
            processing_time = time.time() - start_time
            return TextRemovalResult(
                success=False,
                original_path=str(self.image_path),
                cleaned_path="",
                removal_method=method,
                quality_metrics={},
                text_instances_removed=0,
                processing_time=processing_time,
                technical_details={'error': str(e)}
            )

    def _apply_color_matching(self, image_array: np.ndarray, detection_results: List[Dict]) -> np.ndarray:
        """Replace text with background colors."""
        cleaned = image_array.copy()

        for detection in detection_results:
            x, y, w, h = detection['location']

            # Skip if region is too small or invalid
            if w < 3 or h < 3 or x + w > image_array.shape[1] or y + h > image_array.shape[0]:
                continue

            # Get background colors from detection
            background_colors = detection.get('background_colors', [])

            if background_colors:
                # Use the first background color as replacement
                replacement_color = background_colors[0]
            else:
                # Fallback: sample from surrounding area
                replacement_color = self._sample_surrounding_color(x, y, w, h)

            # Create mask for the text region
            mask = np.ones((h, w), dtype=np.uint8) * 255

            # Apply color replacement
            for channel in range(3):
                channel_data = cleaned[y:y+h, x:x+w, channel]
                cleaned[y:y+h, x:x+w, channel] = replacement_color[channel]

        return cleaned

    def _apply_text_inpainting(self, image_array: np.ndarray, detection_results: List[Dict]) -> np.ndarray:
        """Use inpainting to remove text regions."""
        cleaned = image_array.copy()

        for detection in detection_results:
            x, y, w, h = detection['location']

            # Create mask for inpainting
            mask = np.zeros(image_array.shape[:2], dtype=np.uint8)

            # Expand region slightly for better inpainting
            expand = max(2, min(w, h) // 4)
            x_start = max(0, x - expand)
            y_start = max(0, y - expand)
            x_end = min(image_array.shape[1], x + w + expand)
            y_end = min(image_array.shape[0], y + h + expand)

            mask[y_start:y_end, x_start:x_end] = 255

            # Apply inpainting to each channel
            for channel in range(3):
                channel_data = cleaned[:, :, channel]
                inpainted_channel = cv2.inpaint(channel_data, mask, 3, cv2.INPAINT_TELEA)
                cleaned[:, :, channel] = inpainted_channel

        return cleaned

    def _apply_text_blurring(self, image_array: np.ndarray, detection_results: List[Dict]) -> np.ndarray:
        """Apply blurring to text regions to make them less visible."""
        cleaned = image_array.copy()

        for detection in detection_results:
            x, y, w, h = detection['location']

            # Apply Gaussian blur to text region
            if w > 0 and h > 0:
                # Use a small blur kernel
                kernel_size = min(5, max(1, min(w, h) // 2))
                if kernel_size % 2 == 0:
                    kernel_size += 1

                for channel in range(3):
                    channel_data = cleaned[y:y+h, x:x+w, channel]
                    blurred = cv2.GaussianBlur(channel_data, (kernel_size, kernel_size), 0)
                    cleaned[y:y+h, x:x+w, channel] = blurred

        return cleaned

    def _apply_pattern_replacement(self, image_array: np.ndarray, detection_results: List[Dict]) -> np.ndarray:
        """Replace text with natural background patterns."""
        cleaned = image_array.copy()

        for detection in detection_results:
            x, y, w, h = detection['location']

            # Sample surrounding texture
            texture_patches = self._extract_texture_patches(x, y, w, h)

            if texture_patches:
                # Use texture synthesis to replace the text
                replacement_patch = self._synthesize_texture(texture_patches, w, h)
                if replacement_patch is not None:
                    cleaned[y:y+h, x:x+w] = replacement_patch

        return cleaned

    def _sample_surrounding_color(self, x: int, y: int, w: int, h: int) -> Tuple[int, int, int]:
        """Sample a color from the surrounding area."""
        # Sample from multiple directions
        sample_points = [
            (x - 5, y + h // 2),  # Left
            (x + w + 5, y + h // 2),  # Right
            (x + w // 2, y - 5),  # Top
            (x + w // 2, y + h + 5),  # Bottom
        ]

        valid_colors = []

        for px, py in sample_points:
            if (0 <= px < self.image_array.shape[1] and
                0 <= py < self.image_array.shape[0]):
                color = self.image_array[py, px]
                valid_colors.append(tuple(color))

        if valid_colors:
            # Use median color
            colors_array = np.array(valid_colors)
            median_color = np.median(colors_array, axis=0)
            return tuple(median_color.astype(int))

        # Fallback to gray
        return (128, 128, 128)

    def _extract_texture_patches(self, x: int, y: int, w: int, h: int) -> List[np.ndarray]:
        """Extract texture patches from surrounding areas."""
        patches = []
        patch_size = min(16, min(w, h) * 2)  # Reasonable patch size

        # Sample from different directions
        directions = [
            (-patch_size, 0),  # Left
            (w, 0),  # Right
            (0, -patch_size),  # Top
            (0, h),  # Bottom
            (-patch_size, -patch_size),  # Top-left
            (w, -patch_size),  # Top-right
            (-patch_size, h),  # Bottom-left
            (w, h),  # Bottom-right
        ]

        for dx, dy in directions:
            px = x + dx
            py = y + dy

            if (px >= 0 and py >= 0 and
                px + patch_size <= self.image_array.shape[1] and
                py + patch_size <= self.image_array.shape[0]):

                patch = self.image_array[py:py+patch_size, px:px+patch_size]
                patches.append(patch)

        return patches

    def _synthesize_texture(self, patches: List[np.ndarray], target_w: int, target_h: int) -> Optional[np.ndarray]:
        """Synthesize texture from patches to match target size."""
        if not patches:
            return None

        # For simplicity, use the first patch and resize it
        base_patch = patches[0]

        # Resize to target size
        resized = cv2.resize(base_patch, (target_w, target_h))

        return resized

    def _calculate_text_removal_quality(self, original: np.ndarray, cleaned: np.ndarray, detections: List[Dict]) -> Dict[str, float]:
        """Calculate quality metrics specifically for text removal."""
        metrics = {}

        try:
            # Basic PSNR
            mse = np.mean((original.astype(float) - cleaned.astype(float))**2)
            if mse > 0:
                psnr = 20 * math.log10(255.0 / math.sqrt(mse))
            else:
                psnr = float('inf')
            metrics['psnr'] = float(psnr)

            # SSIM
            if cv2:
                original_gray = cv2.cvtColor(original, cv2.COLOR_RGB2GRAY)
                cleaned_gray = cv2.cvtColor(cleaned, cv2.COLOR_RGB2GRAY)
                ssim = cv2.quality.QualitySSIM_compute(original_gray, cleaned_gray)[0][0]
                metrics['ssim'] = float(ssim)

            # Calculate metrics in cleaned regions
            total_region_pixels = 0
            region_mse = 0

            for detection in detections:
                x, y, w, h = detection['location']
                region_original = original[y:y+h, x:x+w]
                region_cleaned = cleaned[y:y+h, x:x+w]

                region_mse += np.sum((region_original.astype(float) - region_cleaned.astype(float))**2)
                total_region_pixels += region_original.size

            if total_region_pixels > 0:
                region_mse = region_mse / total_region_pixels
                region_psnr = 20 * math.log10(255.0 / math.sqrt(region_mse)) if region_mse > 0 else float('inf')
                metrics['region_psnr'] = float(region_psnr)
                metrics['region_mse'] = float(region_mse)

            # Overall quality score
            quality_score = (min(psnr / 40.0, 1.0) + min(ssim, 1.0)) / 2 if 'ssim' in metrics else min(psnr / 40.0, 1.0)
            metrics['overall_quality'] = float(quality_score)

        except Exception as e:
            print(f"Error calculating text removal quality metrics: {e}")
            metrics['error'] = str(e)

        return metrics

    def batch_remove_text_watermarks(self, detection_results_list: List[Dict], output_dir: str, method: str = "color_matching") -> List[TextRemovalResult]:
        """Remove text watermarks from multiple images."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        results = []

        for i, detection_results in enumerate(detection_results_list):
            image_name = Path(detection_results.get('image_path', f'image_{i}.png')).stem
            output_file = output_path / f"{image_name}_text_cleaned.png"

            result = self.remove_text_watermarks(detection_results.get('text_detections', []), str(output_file), method)
            results.append(result)

        return results


def remove_text_watermarks(image_path: str, detection_results: Dict, output_path: str, method: str = "color_matching") -> TextRemovalResult:
    """Convenience function to remove text watermarks from an image."""
    remover = TextWatermarkRemover(image_path)
    return remover.remove_text_watermarks(detection_results.get('text_detections', []), output_path, method)


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 3:
        print("Usage: python text_watermark_remover.py <image_path> <detection_results> [output_path] [method]")
        print("Example: python text_watermark_remover.py image.jpg text_detection.json cleaned.jpg color_matching")
        sys.exit(1)

    image_path = sys.argv[1]
    detection_file = sys.argv[2]
    output_path = sys.argv[3] if len(sys.argv) > 3 else f"{Path(image_path).stem}_text_cleaned.png"
    method = sys.argv[4] if len(sys.argv) > 4 else "color_matching"

    if not Path(image_path).exists():
        print(f"Image file not found: {image_path}")
        sys.exit(1)

    if not Path(detection_file).exists():
        print(f"Detection results file not found: {detection_file}")
        sys.exit(1)

    # Load detection results
    import json
    with open(detection_file, 'r') as f:
        detection_results = json.load(f)

    print(f"📝 REMOVING TEXT WATERMARKS: {image_path}")
    print(f"   Method: {method}")

    result = remove_text_watermarks(image_path, detection_results, output_path, method)

    if result.success:
        print("✅ Text watermark removal successful!")
        print(f"   Output: {result.cleaned_path}")
        print(f"   Method: {result.removal_method}")
        print(f"   Text instances removed: {result.text_instances_removed}")
        print(f"   Processing time: {result.processing_time:.2f}")
        print(f"   Quality (PSNR): {result.quality_metrics.get('psnr', 'N/A'):.1f}")
    else:
        print(f"❌ Text watermark removal failed: {result.technical_details.get('error', 'Unknown error')}")
