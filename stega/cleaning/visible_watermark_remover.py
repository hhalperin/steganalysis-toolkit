"""
Visible overlay disruption — inpainting / texture methods for resilience experiments.
Uses inpainting, texture synthesis, and gradient-guided techniques on detector-supplied regions.
"""

import numpy as np
from PIL import Image
import cv2
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import math

try:
    from scipy import ndimage
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

try:
    from simple_lama_inpainting import SimpleLama
    LAMA_AVAILABLE = True
except ImportError:
    SimpleLama = None
    LAMA_AVAILABLE = False

@dataclass
class WatermarkRemovalResult:
    """Result from visible watermark removal."""
    success: bool
    original_path: str
    cleaned_path: str
    removal_method: str
    quality_metrics: Dict[str, float]
    regions_cleaned: int
    processing_time: float
    technical_details: Dict[str, Any]


class VisibleWatermarkRemover:
    """Apply CV-backed disruption techniques to visible overlays flagged by detectors."""

    def __init__(self, image_path: str):
        self.image_path = Path(image_path)
        self.image = None
        self.image_array = None
        self.grayscale = None
        self.load_image()

    def load_image(self):
        """Load and prepare image for processing."""
        self.image = Image.open(self.image_path).convert('RGB')
        self.image_array = np.array(self.image)
        if len(self.image_array.shape) == 3:
            self.grayscale = cv2.cvtColor(self.image_array, cv2.COLOR_RGB2GRAY)
        else:
            self.grayscale = self.image_array.copy()

    def remove_watermarks(self, detection_results: List[Dict], output_path: str, method: str = "auto") -> WatermarkRemovalResult:
        """Remove visible watermarks using specified method."""
        if self.image_array is None:
            return WatermarkRemovalResult(
                success=False,
                original_path=str(self.image_path),
                cleaned_path="",
                removal_method=method,
                quality_metrics={},
                regions_cleaned=0,
                processing_time=0.0,
                technical_details={'error': 'Failed to load image'}
            )

        import time
        start_time = time.time()

        try:
            cleaned_array = self.image_array.copy()
            if method == "auto":
                method = self._choose_best_method(detection_results)
            if method == "lama":
                cleaned_array = self._apply_lama_inpainting(cleaned_array, detection_results)
            elif method == "inpainting":
                cleaned_array = self._apply_inpainting(cleaned_array, detection_results)
            elif method == "texture_synthesis":
                cleaned_array = self._apply_texture_synthesis(cleaned_array, detection_results)
            elif method == "gradient_guided":
                cleaned_array = self._apply_gradient_guided(cleaned_array, detection_results)
            elif method == "multi_scale_blending":
                cleaned_array = self._apply_multi_scale_blending(cleaned_array, detection_results)
            elif method == "opencv_ns":
                cleaned_array = self._apply_inpainting(cleaned_array, detection_results, use_ns=True)
            else:
                raise ValueError(f"Unknown removal method: {method}")
            cleaned_image = Image.fromarray(cleaned_array)
            cleaned_image.save(output_path, 'PNG', optimize=True)
            quality_metrics = self._calculate_removal_quality(self.image_array, cleaned_array, detection_results)

            processing_time = time.time() - start_time

            return WatermarkRemovalResult(
                success=True,
                original_path=str(self.image_path),
                cleaned_path=output_path,
                removal_method=method,
                quality_metrics=quality_metrics,
                regions_cleaned=len(detection_results),
                processing_time=processing_time,
                technical_details={
                    'detection_count': len(detection_results),
                    'method_used': method,
                    'image_size': self.image_array.shape
                }
            )

        except Exception as e:
            processing_time = time.time() - start_time
            return WatermarkRemovalResult(
                success=False,
                original_path=str(self.image_path),
                cleaned_path="",
                removal_method=method,
                quality_metrics={},
                regions_cleaned=0,
                processing_time=processing_time,
                technical_details={'error': str(e)}
            )

    def _choose_best_method(self, detection_results: List[Dict]) -> str:
        """Choose the best removal method based on detection types."""
        types = [d.get('type', 'unknown') for d in detection_results]

        if 'edge_anomaly' in types or 'geometric_pattern' in types:
            return "inpainting"  # Good for structured watermarks

        if 'texture_anomaly' in types:
            return "texture_synthesis"  # Good for texture-based watermarks

        if 'gradient_anomaly' in types:
            return "gradient_guided"
        return "multi_scale_blending"

    def _apply_lama_inpainting(self, image_array: np.ndarray, detection_results: List[Dict]) -> np.ndarray:
        """Apply LaMa learning-based inpainting for texture-aware removal. Falls back to OpenCV if unavailable."""
        if not LAMA_AVAILABLE or SimpleLama is None:
            import warnings
            warnings.warn("LaMa not available (pip install simple-lama-inpainting). Falling back to OpenCV inpainting.")
            return self._apply_inpainting(image_array, detection_results)

        mask = np.zeros(image_array.shape[:2], dtype=np.uint8)
        expand = 5
        for detection in detection_results:
            x, y, w, h = detection['location']
            x_start = max(0, x - expand)
            y_start = max(0, y - expand)
            x_end = min(image_array.shape[1], x + w + expand)
            y_end = min(image_array.shape[0], y + h + expand)
            mask[y_start:y_end, x_start:x_end] = 255

        if np.sum(mask > 0) == 0:
            return image_array.copy()

        try:
            simple_lama = SimpleLama()
            img_pil = Image.fromarray(image_array)
            mask_pil = Image.fromarray(mask).convert('L')
            result_pil = simple_lama(img_pil, mask_pil)
            return np.array(result_pil)
        except Exception as e:
            import warnings
            warnings.warn(f"LaMa inpainting failed ({e}). Falling back to OpenCV.")
            return self._apply_inpainting(image_array, detection_results)

    def _apply_inpainting(self, image_array: np.ndarray, detection_results: List[Dict], use_ns: bool = False) -> np.ndarray:
        """Apply OpenCV inpainting to remove watermarks (TELEA or NS)."""
        if not cv2:
            return image_array

        inpaint_flag = cv2.INPAINT_NS if use_ns else cv2.INPAINT_TELEA
        cleaned = image_array.copy()

        for detection in detection_results:
            x, y, w, h = detection['location']
            mask = np.zeros(image_array.shape[:2], dtype=np.uint8)
            expand = 10
            x_start = max(0, x - expand)
            y_start = max(0, y - expand)
            x_end = min(image_array.shape[1], x + w + expand)
            y_end = min(image_array.shape[0], y + h + expand)

            mask[y_start:y_end, x_start:x_end] = 255
            for channel in range(3):
                channel_data = cleaned[:, :, channel]
                inpainted = cv2.inpaint(channel_data, mask, 3, inpaint_flag)
                cleaned[:, :, channel] = inpainted

        return cleaned

    def _apply_texture_synthesis(self, image_array: np.ndarray, detection_results: List[Dict]) -> np.ndarray:
        """Replace watermark regions by copying from clean adjacent areas (left/above)."""
        cleaned = image_array.copy()
        img_h, img_w = image_array.shape[:2]

        for detection in detection_results:
            x, y, w, h = detection['location']
            margin = 8

            # Prefer left and above (clean for corner watermarks)
            best = None

            if x >= w + margin:
                src = image_array[y : y + h, x - w - margin : x - margin]
                if src.shape[0] == h and src.shape[1] == w:
                    best = src.copy()
                elif src.size > 0:
                    best = cv2.resize(src, (w, h))

            if best is None and y >= h + margin:
                src = image_array[y - h - margin : y - margin, x : x + w]
                if src.shape[0] == h and src.shape[1] == w:
                    best = src.copy()
                elif src.size > 0:
                    best = cv2.resize(src, (w, h))

            if best is None and x >= w + margin and y >= h + margin:
                src = image_array[y - h - margin : y - margin, x - w - margin : x - margin]
                if src.shape[0] >= h and src.shape[1] >= w:
                    best = src[:h, :w].copy()

            if best is not None:
                cleaned[y : y + h, x : x + w] = best

        return cleaned

    def _apply_gradient_guided(self, image_array: np.ndarray, detection_results: List[Dict]) -> np.ndarray:
        """Apply gradient-guided cleaning to remove watermarks."""
        cleaned = image_array.copy().astype(np.float32)

        for detection in detection_results:
            x, y, w, h = detection['location']
            region = image_array[y:y+h, x:x+w]
            if region.size == 0:
                continue
            grad_x = np.gradient(region.astype(float), axis=1)
            grad_y = np.gradient(region.astype(float), axis=0)

            gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
            gradient_threshold = np.percentile(gradient_magnitude, 75)
            mask = gradient_magnitude > gradient_threshold
            for channel in range(3):
                channel_data = cleaned[y:y+h, x:x+w, channel]
                if cv2:
                    filtered = cv2.bilateralFilter(channel_data.astype(np.uint8), 9, 75, 75)
                    cleaned[y:y+h, x:x+w, channel] = filtered.astype(np.float32)
                blend_factor = 0.7
                cleaned[y:y+h, x:x+w, channel] = (
                    blend_factor * cleaned[y:y+h, x:x+w, channel] +
                    (1 - blend_factor) * image_array[y:y+h, x:x+w, channel].astype(np.float32)
                )

        return np.clip(cleaned, 0, 255).astype(np.uint8)

    def _apply_multi_scale_blending(self, image_array: np.ndarray, detection_results: List[Dict]) -> np.ndarray:
        """Apply multi-scale blending to seamlessly remove watermarks."""
        cleaned = image_array.copy().astype(np.float32)

        for detection in detection_results:
            x, y, w, h = detection['location']
            scales = [1.0, 0.5, 0.25]
            for scale in scales:
                if scale < 1.0:
                    scaled_w = max(32, int(w * scale))
                    scaled_h = max(32, int(h * scale))
                    scaled_x = max(0, int(x * scale))
                    scaled_y = max(0, int(y * scale))
                    scaled_region = image_array[scaled_y:scaled_y+scaled_h, scaled_x:scaled_x+scaled_w]
                    if scaled_region.size == 0:
                        continue
                    smoothed = cv2.GaussianBlur(scaled_region, (5, 5), 0)
                    upscaled = cv2.resize(smoothed, (w, h))
                    blend_factor = 0.6 / len(scales)
                    cleaned[y:y+h, x:x+w] = (
                        (1 - blend_factor) * cleaned[y:y+h, x:x+w] +
                        blend_factor * upscaled.astype(np.float32)
                    )

        return np.clip(cleaned, 0, 255).astype(np.uint8)

    def _calculate_removal_quality(self, original: np.ndarray, cleaned: np.ndarray, detections: List[Dict]) -> Dict[str, float]:
        """Calculate quality metrics for watermark removal."""
        metrics = {}

        try:
            mse = np.mean((original.astype(float) - cleaned.astype(float))**2)
            if mse > 0:
                psnr = 20 * math.log10(255.0 / math.sqrt(mse))
            else:
                psnr = float('inf')
            metrics['psnr'] = float(psnr)
            if cv2:
                try:
                    original_gray = cv2.cvtColor(original, cv2.COLOR_RGB2GRAY)
                    cleaned_gray = cv2.cvtColor(cleaned, cv2.COLOR_RGB2GRAY)
                    if hasattr(cv2, 'quality') and hasattr(cv2.quality, 'QualitySSIM_compute'):
                        ssim = cv2.quality.QualitySSIM_compute(original_gray, cleaned_gray)[0][0]
                        metrics['ssim'] = float(ssim)
                except Exception:
                    pass
            metrics['mse'] = float(mse)
            total_pixels = original.shape[0] * original.shape[1]
            cleaned_pixels = 0

            for detection in detections:
                x, y, w, h = detection['location']
                region_size = w * h
                cleaned_pixels += region_size

            metrics['cleaned_pixel_ratio'] = float(cleaned_pixels / total_pixels)
            ssim_val = metrics.get('ssim', 0.0)
            quality_score = (min(psnr / 40.0, 1.0) + min(ssim_val, 1.0)) / 2 if 'ssim' in metrics else min(psnr / 40.0, 1.0)
            metrics['overall_quality'] = float(quality_score)

        except Exception as e:
            print(f"Error calculating quality metrics: {e}")
            metrics['error'] = str(e)

        return metrics

    def batch_remove_watermarks(self, detection_results_list: List[Dict], output_dir: str, method: str = "auto") -> List[WatermarkRemovalResult]:
        """Remove watermarks from multiple images."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        results = []

        for i, detection_results in enumerate(detection_results_list):
            image_name = Path(detection_results.get('image_path', f'image_{i}.png')).stem
            output_file = output_path / f"{image_name}_cleaned.png"

            result = self.remove_watermarks(detection_results.get('detections', []), str(output_file), method)
            results.append(result)

        return results


def remove_visible_watermarks(image_path: str, detection_results: Dict, output_path: str, method: str = "auto") -> WatermarkRemovalResult:
    """Convenience function to remove visible watermarks from an image."""
    remover = VisibleWatermarkRemover(image_path)
    return remover.remove_watermarks(detection_results.get('detections', []), output_path, method)


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 3:
        print("Usage: python visible_watermark_remover.py <image_path> <detection_results> [output_path] [method]")
        print("Example: python visible_watermark_remover.py image.jpg detection.json cleaned.jpg inpainting")
        sys.exit(1)

    image_path = sys.argv[1]
    detection_file = sys.argv[2]
    output_path = sys.argv[3] if len(sys.argv) > 3 else f"{Path(image_path).stem}_cleaned.png"
    method = sys.argv[4] if len(sys.argv) > 4 else "auto"

    if not Path(image_path).exists():
        print(f"Image file not found: {image_path}")
        sys.exit(1)

    if not Path(detection_file).exists():
        print(f"Detection results file not found: {detection_file}")
        sys.exit(1)

    import json
    with open(detection_file, 'r') as f:
        detection_results = json.load(f)

    print(f"🧹 REMOVING VISIBLE WATERMARKS: {image_path}")
    print(f"   Method: {method}")

    result = remove_visible_watermarks(image_path, detection_results, output_path, method)

    if result.success:
        print("✅ Watermark removal successful!")
        print(f"   Output: {result.cleaned_path}")
        print(f"   Method: {result.removal_method}")
        print(f"   Regions cleaned: {result.regions_cleaned}")
        print(f"   Processing time: {result.processing_time:.2f}s")
        print(f"   Quality (PSNR): {result.quality_metrics.get('psnr', 'N/A'):.1f}")
    else:
        print(f"❌ Watermark removal failed: {result.technical_details.get('error', 'Unknown error')}")
