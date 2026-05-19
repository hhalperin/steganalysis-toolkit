"""Visualization package for steganography battle simulation."""

from .engine import VisualizationEngine, MetaphorMode
from .battle_state_machine import BattleStateMachine, BattleState, detect_self_healing
from .metaphors import (
    create_heat_map,
    add_ripple_effect,
    create_particle_effect,
    create_battle_overlay,
)
from .frame_capture import FrameCapture
from .video_generator import VideoGenerator
from .dashboard import BattleDashboard

__all__ = [
    "VisualizationEngine",
    "MetaphorMode",
    "BattleStateMachine",
    "BattleState",
    "detect_self_healing",
    "create_heat_map",
    "add_ripple_effect",
    "create_particle_effect",
    "create_battle_overlay",
    "FrameCapture",
    "VideoGenerator",
    "BattleDashboard",
]
