"""
Frame Capture System - Efficiently capture battle progression.
Memory management and compression for progressive snapshots.
"""

import io
from pathlib import Path
from typing import List, Optional, Union

import numpy as np

try:
    import cv2

    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    from PIL import Image

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class FrameCapture:
    """
    Manages frame capture for battle visualization with memory management.
    Supports disk-only mode (low memory) or bounded in-memory buffer.
    """

    def __init__(
        self,
        output_dir: Union[str, Path] = "battle_frames",
        max_memory_frames: int = 0,
        compress_quality: int = 85,
        compress_format: str = "png",
    ):
        """
        Args:
            output_dir: Directory for saved frames.
            max_memory_frames: Max frames to keep in memory (0 = disk-only).
            compress_quality: JPEG quality 1-100 (PNG uses 1-9 via zlib).
            compress_format: "png" or "jpg" for compression.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.frame_paths: List[str] = []
        self._memory_buffer: List[np.ndarray] = []
        self.max_memory_frames = max_memory_frames
        self.compress_quality = min(100, max(1, compress_quality))
        self.compress_format = compress_format.lower()

    def capture_frame(
        self,
        image: np.ndarray,
        round_num: int,
        prefix: str = "frame",
    ) -> str:
        """
        Capture a frame of the battle. Saves to disk and optionally buffers in memory.

        Args:
            image: Frame image (RGB or BGR, uint8).
            round_num: Round number for filename.
            prefix: Filename prefix.

        Returns:
            Path to saved frame.
        """
        ext = ".jpg" if self.compress_format == "jpg" else ".png"
        frame_path = self.output_dir / f"{prefix}_{round_num:04d}{ext}"
        frame_path_str = str(frame_path)

        if CV2_AVAILABLE:
            if image.shape[2] == 3 and image.dtype == np.uint8:
                bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR) if image.shape[2] == 3 else image
            else:
                bgr = image
            if self.compress_format == "jpg":
                cv2.imwrite(
                    frame_path_str,
                    bgr,
                    [cv2.IMWRITE_JPEG_QUALITY, self.compress_quality],
                )
            else:
                cv2.imwrite(frame_path_str, bgr)
        elif PIL_AVAILABLE:
            if len(image.shape) == 3 and image.shape[2] == 3:
                pil_img = Image.fromarray(image, mode="RGB")
            else:
                pil_img = Image.fromarray(image)
            if self.compress_format == "jpg":
                pil_img.save(frame_path_str, "JPEG", quality=self.compress_quality)
            else:
                pil_img.save(frame_path_str, "PNG", optimize=True)
        else:
            raise RuntimeError("Neither cv2 nor PIL available for frame capture")

        self.frame_paths.append(frame_path_str)

        if self.max_memory_frames > 0:
            self._memory_buffer.append(image.copy())
            if len(self._memory_buffer) > self.max_memory_frames:
                self._memory_buffer.pop(0)

        return frame_path_str

    def get_frame_paths(self) -> List[str]:
        """Return list of captured frame paths."""
        return self.frame_paths.copy()

    def clear_memory_buffer(self) -> None:
        """Release in-memory frame buffer to free memory."""
        self._memory_buffer.clear()

    def get_buffered_frames(self) -> List[np.ndarray]:
        """Return buffered frames if any (read-only)."""
        return self._memory_buffer.copy()

    @property
    def frames(self) -> List[str]:
        """Alias for get_frame_paths for backward compatibility."""
        return self.frame_paths
