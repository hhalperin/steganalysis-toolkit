"""
Visualization Metaphors - Create visual representations of cleaning process
Heat maps, ripples, particles, and battle visualization
"""

import numpy as np
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
from typing import Dict, Any, Tuple, List

def create_heat_map(image: np.ndarray, confidence_map: Dict[str, float]) -> np.ndarray:
    """
    Create heat map overlay for detected waste.
    Maps confidence scores to color intensity (red=high, blue=low).
    """
    if not CV2_AVAILABLE:
        return image

    if not confidence_map:
        return image

    # Create base overlay
    overlay = np.zeros_like(image, dtype=np.float32)

    # Color mapping for different waste types
    color_map = {
        'lsb_steganography': (0, 0, 255),      # Red for LSB
        'ai_fingerprint': (255, 0, 255),       # Magenta for AI
        'unicode_markers': (0, 255, 0),        # Green for Unicode
        'blockchain_watermark': (255, 165, 0), # Orange for blockchain
        'printer_tracking': (255, 255, 0),     # Yellow for printer dots
        'default': (255, 0, 0)                 # Default red
    }

    # Apply heat map for each detected waste type
    for waste_type, confidence in confidence_map.items():
        if confidence > 0.1:  # Only show if confidence > 10%
            # Get color for this waste type
            color = color_map.get(waste_type, color_map['default'])

            # Create intensity based on confidence (0.1-1.0 -> 0.2-0.8 opacity)
            intensity = 0.2 + (confidence * 0.6)

            # Add color overlay with varying intensity
            color_overlay = np.full_like(image, color, dtype=np.float32)
            overlay += color_overlay * intensity

    # Blend overlay with original image
    blended = (image.astype(np.float32) * 0.7 + overlay * 0.3).clip(0, 255).astype(np.uint8)

    return blended

def add_ripple_effect(image: np.ndarray, center: Tuple[int, int], radius: int, color: Tuple[int, int, int] = (0, 255, 255)) -> np.ndarray:
    """
    Add ripple effect emanating from a center point.
    Used to show cleaning algorithms targeting specific areas.
    """
    if not CV2_AVAILABLE:
        return image
    height, width = image.shape[:2]
    center_y, center_x = center

    # Create ripple mask
    y, x = np.ogrid[:height, :width]
    distance = np.sqrt((x - center_x)**2 + (y - center_y)**2)

    # Create ripple pattern (concentric circles)
    ripple_mask = np.sin(distance / radius * np.pi * 2)  # 2 full waves per radius
    ripple_mask = (ripple_mask + 1) / 2  # Normalize to 0-1
    ripple_mask = (ripple_mask > 0.5).astype(np.uint8)  # Binary mask

    # Expand ripple slightly for visibility
    kernel = np.ones((3, 3), np.uint8)
    ripple_mask = cv2.dilate(ripple_mask, kernel, iterations=1)

    # Apply color to ripple area
    colored_ripple = np.zeros_like(image)
    for i in range(3):
        colored_ripple[:, :, i] = ripple_mask * color[i]

    # Blend with original image (higher opacity for ripple)
    result = (image.astype(np.float32) * 0.6 + colored_ripple.astype(np.float32) * 0.4).clip(0, 255).astype(np.uint8)

    return result

def create_particle_effect(image: np.ndarray, particles: List[Tuple[int, int, float]], color: Tuple[int, int, int] = (255, 255, 0)) -> np.ndarray:
    """
    Add particle effect for showing watermark elements being consumed.
    Particles represent individual watermark detections.
    """
    if not CV2_AVAILABLE or not particles:
        return image
    result = image.copy()

    for x, y, intensity in particles:
        # Draw particle as small circle
        cv2.circle(result, (x, y), max(1, int(intensity * 5)), color, -1)

        # Add glow effect for larger particles
        if intensity > 0.7:
            glow_radius = int(intensity * 10)
            cv2.circle(result, (x, y), glow_radius, color, 2)

    return result

def create_battle_overlay(image: np.ndarray, battle_state: Dict[str, Any]) -> np.ndarray:
    """
    Create comprehensive battle visualization overlay.
    Combines heat maps, ripples, and particles for the full experience.
    """
    result = image.copy()

    # Add heat map for detected waste
    if battle_state.get('waste_detected'):
        result = create_heat_map(result, battle_state['waste_detected'])

    # Add ripple effects for active cleaning
    if battle_state.get('active_cleaning'):
        for cleaning_target in battle_state['active_cleaning']:
            center = cleaning_target.get('center', (image.shape[1]//2, image.shape[0]//2))
            result = add_ripple_effect(result, center, 50, (0, 255, 255))

    # Add particles for watermark elements
    if battle_state.get('particles'):
        result = create_particle_effect(result, battle_state['particles'])

    return result

