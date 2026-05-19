"""
Watermark Inpaintor - Specialized inpainting techniques for watermark removal
Uses advanced inpainting algorithms to naturally fill watermark regions
"""

import numpy as np
from PIL import Image
import cv2
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import math

@dataclass
class InpaintingResult:
    """Result from watermark inpainting."""
    success: bool
    original_path: str
    cleaned_path: str
    inpainting_method: str
    mask_generation_method: str
    quality_metrics: Dict[str, float]
    regions_processed: int
    processing_time: float
    technical_details: Dict[str, Any]


class WatermarkInpaintor:
    """Advanced inpainting-based remover for visible watermarks."""

    def __init__(self, image_path: str):
        self.image_path = Path(image_path)
        self.image = None
        self.image_array = None
        self.load_image()

    def load_image(self):
        """Load and prepare image for inpainting."""
        try:
            self.image = Image.open(self.image_path).convert('RGB')
            self.image_array = np.array(self.image)

        except Exception as e:
            print(f"Error loading image: {e}")
            return False
        return True

    def generate_masks(self, detection_results: List[Dict], method: str = "adaptive") -> List[np.ndarray]:
        """Generate inpainting masks from detection results."""
        masks = []

        for detection in detection_results:
            x, y, w, h = detection['location']

            if method == "adaptive":
                mask = self._generate_adaptive_mask(x, y, w, h)
            elif method == "dilated":
                mask = self._generate_dilated_mask(x, y, w, h)
            elif method == "feathered":
                mask = self._generate_feathered_mask(x, y, w, h)
            else:
                # Simple rectangular mask
                mask = np.zeros(self.image_array.shape[:2], dtype=np.uint8)
                mask[y:y+h, x:x+w] = 255

            masks.append(mask)

        return masks

    def _generate_adaptive_mask(self, x: int, y: int, w: int, h: int) -> np.ndarray:
        """Generate adaptive mask that follows watermark boundaries."""
        mask = np.zeros(self.image_array.shape[:2], dtype=np.uint8)

        # Get region
        region = self.image_array[y:y+h, x:x+w]

        # Calculate gradients to find boundaries
        gray_region = cv2.cvtColor(region, cv2.COLOR_RGB2GRAY) if len(region.shape) == 3 else region

        # Sobel edge detection
        sobel_x = cv2.Sobel(gray_region, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(gray_region, cv2.CV_64F, 0, 1, ksize=3)
        gradient_magnitude = np.sqrt(sobel_x**2 + sobel_y**2)

        # Threshold to find edges
        threshold = np.percentile(gradient_magnitude, 75)
        edge_mask = gradient_magnitude > threshold

        # Dilate edges to create mask
        kernel = np.ones((5, 5), np.uint8)
        dilated_mask = cv2.dilate(edge_mask.astype(np.uint8) * 255, kernel, iterations=2)

        # Place mask in correct position
        mask[y:y+h, x:x+w] = dilated_mask

        return mask

    def _generate_dilated_mask(self, x: int, y: int, w: int, h: int) -> np.ndarray:
        """Generate dilated mask for better inpainting coverage."""
        mask = np.zeros(self.image_array.shape[:2], dtype=np.uint8)

        # Create base mask
        mask[y:y+h, x:x+w] = 255

        # Dilate to expand coverage
        kernel_sizes = [3, 5, 7]
        for kernel_size in kernel_sizes:
            kernel = np.ones((kernel_size, kernel_size), np.uint8)
            mask = cv2.dilate(mask, kernel, iterations=1)

        return mask

    def _generate_feathered_mask(self, x: int, y: int, w: int, h: int) -> np.ndarray:
        """Generate feathered mask for smooth transitions."""
        mask = np.zeros(self.image_array.shape[:2], dtype=np.uint8)

        # Create base rectangular mask
        mask[y:y+h, x:x+w] = 255

        # Create distance transform
        dist_transform = cv2.distanceTransform(mask, cv2.DIST_L2, 5)

        # Normalize and invert
        max_dist = np.max(dist_transform)
        if max_dist > 0:
            normalized_dist = dist_transform / max_dist
            feathered_mask = (255 * (1 - normalized_dist)).astype(np.uint8)
        else:
            feathered_mask = mask

        return feathered_mask

    def inpaint_watermarks(self, detection_results: List[Dict], output_path: str,
                          method: str = "telea", mask_method: str = "adaptive") -> InpaintingResult:
        """Remove watermarks using advanced inpainting techniques."""
        if self.image_array is None:
            return InpaintingResult(
                success=False,
                original_path=str(self.image_path),
                cleaned_path="",
                inpainting_method=method,
                mask_generation_method=mask_method,
                quality_metrics={},
                regions_processed=0,
                processing_time=0.0,
                technical_details={'error': 'Failed to load image'}
            )

        import time
        start_time = time.time()

        try:
            cleaned_array = self.image_array.copy()

            # Generate masks for each detection
            masks = self.generate_masks(detection_results, mask_method)

            # Apply inpainting to each masked region
            for i, (detection, mask) in enumerate(zip(detection_results, masks)):
                x, y, w, h = detection['location']

                # Choose inpainting algorithm
                if method == "telea":
                    inpaint_method = cv2.INPAINT_TELEA
                elif method == "ns":
                    inpaint_method = cv2.INPAINT_NS
                else:
                    inpaint_method = cv2.INPAINT_TELEA

                # Apply inpainting to each channel
                for channel in range(3):
                    channel_data = cleaned_array[:, :, channel]
                    inpainted_channel = cv2.inpaint(channel_data, mask, 3, inpaint_method)
                    cleaned_array[:, :, channel] = inpainted_channel

            # Save cleaned image
            cleaned_image = Image.fromarray(cleaned_array)
            cleaned_image.save(output_path, 'PNG', optimize=True)

            # Calculate quality metrics
            quality_metrics = self._calculate_inpainting_quality(self.image_array, cleaned_array, detection_results)

            processing_time = time.time() - start_time

            return InpaintingResult(
                success=True,
                original_path=str(self.image_path),
                cleaned_path=output_path,
                inpainting_method=method,
                mask_generation_method=mask_method,
                quality_metrics=quality_metrics,
                regions_processed=len(detection_results),
                processing_time=processing_time,
                technical_details={
                    'detection_count': len(detection_results),
                    'mask_count': len(masks),
                    'image_size': self.image_array.shape
                }
            )

        except Exception as e:
            processing_time = time.time() - start_time
            return InpaintingResult(
                success=False,
                original_path=str(self.image_path),
                cleaned_path="",
                inpainting_method=method,
                mask_generation_method=mask_method,
                quality_metrics={},
                regions_processed=0,
                processing_time=processing_time,
                technical_details={'error': str(e)}
            )

    def _calculate_inpainting_quality(self, original: np.ndarray, cleaned: np.ndarray, detections: List[Dict]) -> Dict[str, float]:
        """Calculate quality metrics specifically for inpainting results."""
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
            print(f"Error calculating inpainting quality metrics: {e}")
            metrics['error'] = str(e)

        return metrics

    def batch_inpaint_watermarks(self, detection_results_list: List[Dict], output_dir: str,
                               method: str = "telea", mask_method: str = "adaptive") -> List[InpaintingResult]:
        """Inpaint watermarks from multiple images."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        results = []

        for i, detection_results in enumerate(detection_results_list):
            image_name = Path(detection_results.get('image_path', f'image_{i}.png')).stem
            output_file = output_path / f"{image_name}_inpainted.png"

            result = self.inpaint_watermarks(detection_results.get('detections', []), str(output_file), method, mask_method)
            results.append(result)

        return results


def inpaint_watermarks(image_path: str, detection_results: Dict, output_path: str,
                      method: str = "telea", mask_method: str = "adaptive") -> InpaintingResult:
    """Convenience function to inpaint watermarks from an image."""
    inpaintor = WatermarkInpaintor(image_path)
    return inpaintor.inpaint_watermarks(detection_results.get('detections', []), output_path, method, mask_method)


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 3:
        print("Usage: python watermark_inpaintor.py <image_path> <detection_results> [output_path] [method] [mask_method]")
        print("Example: python watermark_inpaintor.py image.jpg detection.json cleaned.jpg telea adaptive")
        sys.exit(1)

    image_path = sys.argv[1]
    detection_file = sys.argv[2]
    output_path = sys.argv[3] if len(sys.argv) > 3 else f"{Path(image_path).stem}_inpainted.png"
    method = sys.argv[4] if len(sys.argv) > 4 else "telea"
    mask_method = sys.argv[5] if len(sys.argv) > 5 else "adaptive"

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

    print(f"🎨 INPAINTING WATERMARKS: {image_path}")
    print(f"   Inpainting method: {method}")
    print(f"   Mask method: {mask_method}")

    result = inpaint_watermarks(image_path, detection_results, output_path, method, mask_method)

    if result.success:
        print("✅ Watermark inpainting successful!")
        print(f"   Output: {result.cleaned_path}")
        print(f"   Method: {result.inpainting_method}")
        print(f"   Regions processed: {result.regions_processed}")
        print(f"   Processing time: {result.processing_time:.2f}s")
        print(f"   Quality (PSNR): {result.quality_metrics.get('psnr', 'N/A'):.1f}")
    else:
        print(f"❌ Watermark inpainting failed: {result.technical_details.get('error', 'Unknown error')}")
