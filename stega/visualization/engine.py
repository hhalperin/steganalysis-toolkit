"""
Core Visualization Engine - Centralizes metaphor systems for battle simulation.
Supports heat maps, ripples, particles, and battle visualization with pluggable metaphor selection.
Optimized for memory and processing speed with optional downscaling.
"""

from enum import Enum
from typing import Dict, Any, List, Tuple, Optional
import numpy as np

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

from .metaphors import (
    create_heat_map,
    add_ripple_effect,
    create_particle_effect,
    create_battle_overlay,
)


class MetaphorMode(Enum):
    """Visualization metaphor modes."""

    HEAT_MAP = "heat_map"
    RIPPLE = "ripple"
    PARTICLE = "particle"
    BATTLE = "battle"  # Full combined overlay


class VisualizationEngine:
    """
    Core engine that applies visualization metaphors to battle frames.
    Supports multiple metaphor systems with configurable intensity and blending.
    """

    def __init__(
        self,
        mode: MetaphorMode = MetaphorMode.BATTLE,
        heat_map_intensity: float = 0.3,
        ripple_intensity: float = 0.4,
        particle_intensity: float = 0.8,
        max_dimension: Optional[int] = None,
    ):
        """
        Args:
            max_dimension: If set, downscale images larger than this (max of width/height) for faster processing.
        """
        self.mode = mode
        self.max_dimension = max_dimension
        self.heat_map_intensity = heat_map_intensity
        self.ripple_intensity = ripple_intensity
        self.particle_intensity = particle_intensity

    def _maybe_downscale(self, image: np.ndarray) -> Tuple[np.ndarray, Optional[Tuple[int, int]]]:
        """Downscale if exceeds max_dimension. Returns (image, original_size for upscale)."""
        if not self.max_dimension or not CV2_AVAILABLE:
            return image, None
        h, w = image.shape[:2]
        if max(h, w) <= self.max_dimension:
            return image, None
        scale = self.max_dimension / max(h, w)
        new_w, new_h = int(w * scale), int(h * scale)
        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        return resized, (w, h)

    def render(
        self,
        image: np.ndarray,
        battle_state: Dict[str, Any],
        round_num: int = 0,
    ) -> np.ndarray:
        """
        Render a battle frame using the configured metaphor mode.

        Args:
            image: Base image array (RGB, uint8).
            battle_state: Current battle state (waste_detected, active_cleaning, particles).
            round_num: Current round number for effect variation.

        Returns:
            Rendered frame with applied metaphors.
        """
        work, orig_size = self._maybe_downscale(image)
        result = work.copy()

        if self.mode == MetaphorMode.HEAT_MAP:
            result = self._apply_heat_map_only(result, battle_state)
        elif self.mode == MetaphorMode.RIPPLE:
            result = self._apply_ripple_only(result, battle_state)
        elif self.mode == MetaphorMode.PARTICLE:
            result = self._apply_particle_only(result, battle_state)
        elif self.mode == MetaphorMode.BATTLE:
            result = create_battle_overlay(result, battle_state)

        if orig_size and CV2_AVAILABLE:
            result = cv2.resize(result, orig_size, interpolation=cv2.INTER_LINEAR)
        return result

    def _apply_heat_map_only(self, image: np.ndarray, battle_state: Dict[str, Any]) -> np.ndarray:
        """Apply only heat map metaphor."""
        waste = battle_state.get("waste_detected", {})
        if waste:
            return create_heat_map(image, waste)
        return image

    def _apply_ripple_only(self, image: np.ndarray, battle_state: Dict[str, Any]) -> np.ndarray:
        """Apply only ripple effects from active cleaning targets."""
        active = battle_state.get("active_cleaning", [])
        result = image.copy()
        for target in active:
            center = target.get("center", (image.shape[1] // 2, image.shape[0] // 2))
            radius = int(50 * (1 + target.get("progress", 0.5)))
            result = add_ripple_effect(result, center, radius, (0, 255, 255))
        return result

    def _apply_particle_only(self, image: np.ndarray, battle_state: Dict[str, Any]) -> np.ndarray:
        """Apply only particle effects."""
        particles = battle_state.get("particles", [])
        if particles:
            return create_particle_effect(image, particles, (255, 255, 0))
        return image

    def set_mode(self, mode: MetaphorMode) -> None:
        """Change the active metaphor mode."""
        self.mode = mode
