"""Remove a visible watermark/emblem by specifying a region (e.g. bottom-right corner)."""

import numpy as np
from PIL import Image
from pathlib import Path

from ..cleaning.visible_watermark_remover import remove_visible_watermarks


def region_from_bottom_right(img_shape: tuple, frac_w: float = 0.12, frac_h: float = 0.10, min_size: int = 80):
    h, w = img_shape[:2]
    box_w = max(min_size, int(w * frac_w))
    box_h = max(min_size, int(h * frac_h))
    return (w - box_w, h - box_h, box_w, box_h)


def run_remove_region(
    input_path: Path,
    output_path: Path,
    frac_w: float = 0.12,
    frac_h: float = 0.10,
    box: str | None = None,
    method: str = "lama",
) -> tuple[bool, str]:
    img = np.array(Image.open(input_path).convert("RGB"))
    h, w = img.shape[:2]

    if box:
        parts = [int(x.strip()) for x in box.split(",")]
        if len(parts) != 4:
            return False, "--box must be x,y,w,h"
        x, y, box_w, box_h = parts
    else:
        x, y, box_w, box_h = region_from_bottom_right(img.shape, frac_w, frac_h)

    x = max(0, min(x, w - 1))
    y = max(0, min(y, h - 1))
    box_w = min(box_w, w - x)
    box_h = min(box_h, h - y)
    if box_w < 2 or box_h < 2:
        return False, "Region too small"

    fake_detections = [
        {"type": "manual_region", "confidence": 1.0, "location": (x, y, box_w, box_h), "characteristics": {}, "recommended_removal": "inpainting"}
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    result = remove_visible_watermarks(str(input_path), {"detections": fake_detections}, str(output_path), method=method)
    if result.success:
        return True, f"Removed region ({x},{y},{box_w}x{box_h}) -> {output_path}"
    err = result.technical_details.get("error", result.technical_details) if isinstance(result.technical_details, dict) else result.technical_details
    return False, str(err)
