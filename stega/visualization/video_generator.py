"""
Video Generation Pipeline - Stitch frames into battle video.
Multiple export formats with transition effects.
"""

import sys
import os
from pathlib import Path
from typing import List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import cv2
    import numpy as np

    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    from PIL import Image

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class TransitionType:
    """Transition effect types between frames."""

    NONE = "none"
    FADE = "fade"
    CROSSFADE = "crossfade"
    DISSOLVE = "dissolve"


class VideoGenerator:
    """
    Generates battle video from captured frames.
    Supports MP4, GIF, and optional WebM with transition effects.
    """

    def __init__(
        self,
        frame_capture=None,
        frame_paths: Optional[List[str]] = None,
        fps: int = 10,
        transition: str = TransitionType.FADE,
        transition_frames: int = 5,
    ):
        """
        Args:
            frame_capture: FrameCapture instance (extracts frame_paths). Deprecated: use frame_paths.
            frame_paths: List of frame file paths.
            fps: Frames per second for output video.
            transition: Transition type between frames (none, fade, crossfade, dissolve).
            transition_frames: Number of intermediate frames for transition.
        """
        if frame_capture is not None and frame_paths is None:
            frame_paths = getattr(frame_capture, "frames", None) or getattr(
                frame_capture, "frame_paths", None
            ) or getattr(frame_capture, "get_frame_paths", lambda: [])()
        self.frame_paths = frame_paths or []
        self.fps = fps
        self.transition = transition
        self.transition_frames = transition_frames

    @classmethod
    def from_frame_capture(cls, frame_capture, **kwargs) -> "VideoGenerator":
        """Create from a FrameCapture instance."""
        return cls(frame_paths=frame_capture.get_frame_paths(), **kwargs)

    def _load_frame(self, path: str):
        """Load frame as numpy array (RGB)."""
        if not CV2_AVAILABLE:
            if PIL_AVAILABLE:
                img = Image.open(path)
                return np.array(img)
            raise RuntimeError("Neither cv2 nor PIL available for video generation")
        bgr = cv2.imread(path)
        if bgr is None:
            return None
        return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

    def _create_transition_frames(
        self,
        frame_a,
        frame_b,
        num_frames: int,
    ) -> List:
        """Generate intermediate frames for transition between frame_a and frame_b."""
        if num_frames <= 0 or self.transition == TransitionType.NONE:
            return [frame_b] if frame_b is not None else []

        frames = []
        for i in range(1, num_frames + 1):
            alpha = i / (num_frames + 1)
            if self.transition == TransitionType.FADE:
                blended = (frame_a * (1 - alpha) + frame_b * alpha).astype(np.uint8)
            elif self.transition == TransitionType.CROSSFADE:
                blended = (frame_a * (1 - alpha) + frame_b * alpha).astype(np.uint8)
            elif self.transition == TransitionType.DISSOLVE:
                mask = np.random.random(frame_a.shape[:2])
                mask = (mask < alpha).astype(np.float32)[:, :, np.newaxis]
                blended = (frame_a * (1 - mask) + frame_b * mask).astype(np.uint8)
            else:
                blended = frame_b
            frames.append(blended)
        return frames

    def generate_video(
        self,
        output_path: str,
        fps: Optional[int] = None,
        format_hint: Optional[str] = None,
    ) -> str:
        """
        Generate video from frames.

        Args:
            output_path: Output file path (extension determines format: .mp4, .avi, .webm).
            fps: Override default fps.
            format_hint: Force format ('mp4', 'avi', 'webm'). Default from extension.

        Returns:
            Path to generated video.
        """
        if not self.frame_paths:
            return ""

        fps = fps or self.fps
        path = Path(output_path)
        ext = format_hint or path.suffix.lower().lstrip(".")

        if ext in ("mp4", "mov"):
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        elif ext == "avi":
            fourcc = cv2.VideoWriter_fourcc(*"XVID")
        elif ext == "webm":
            fourcc = cv2.VideoWriter_fourcc(*"VP80")
        else:
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            output_path = str(path.with_suffix(".mp4"))

        if not CV2_AVAILABLE:
            raise RuntimeError("cv2 required for video generation")

        first_frame = self._load_frame(self.frame_paths[0])
        if first_frame is None:
            return ""
        height, width = first_frame.shape[:2]

        video = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        prev_frame = None
        for i, frame_path in enumerate(self.frame_paths):
            frame = self._load_frame(frame_path)
            if frame is None:
                continue
            if frame.shape[:2] != (height, width):
                frame = cv2.resize(frame, (width, height))

            bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            if prev_frame is not None and self.transition != TransitionType.NONE:
                prev_rgb = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2RGB)
                trans_frames = self._create_transition_frames(
                    prev_rgb, frame, self.transition_frames
                )
                for tf in trans_frames:
                    video.write(cv2.cvtColor(tf, cv2.COLOR_RGB2BGR))

            video.write(bgr)
            prev_frame = bgr

        video.release()
        return output_path

    def generate_gif(
        self,
        output_path: str,
        fps: Optional[int] = None,
        duration_ms: Optional[int] = None,
        loop: int = 0,
    ) -> str:
        """
        Generate GIF from frames.

        Args:
            output_path: Output .gif path.
            fps: Frames per second (used to compute duration if duration_ms not set).
            duration_ms: Per-frame duration in ms.
            loop: 0 = infinite loop.

        Returns:
            Path to generated GIF.
        """
        if not self.frame_paths or not PIL_AVAILABLE:
            return ""

        frames = []
        for path in self.frame_paths:
            img = Image.open(path)
            if img.mode != "RGB":
                img = img.convert("RGB")
            frames.append(img)

        if not frames:
            return ""

        duration = duration_ms or int(1000 / (fps or self.fps))
        frames[0].save(
            output_path,
            save_all=True,
            append_images=frames[1:],
            duration=duration,
            loop=loop,
        )
        return output_path
