"""
Battle State Machine - Adaptive states for steganography battle simulation.
Manages transitions between detecting, cleaning, self-healing counter-measures, victory, and defeat.
"""

from enum import Enum, auto
from typing import Dict, Any, Optional


class BattleState(Enum):
    """Battle phase states."""

    INITIAL = auto()
    DETECTING = auto()
    CLEANING = auto()
    SELF_HEALING_DETECTED = auto()
    COUNTER_MEASURING = auto()
    VICTORY = auto()
    DEFEAT = auto()
    MAX_ROUNDS_REACHED = auto()


class BattleStateMachine:
    """
    Adaptive state machine for battle flow.
    Tracks confidence history for self-healing detection.
    """

    def __init__(
        self,
        confidence_threshold: float = 0.95,
        max_rounds: int = 50,
        self_healing_threshold: float = 0.8,
        no_improvement_rounds_limit: int = 5,
    ):
        self.confidence_threshold = confidence_threshold
        self.max_rounds = max_rounds
        self.self_healing_threshold = self_healing_threshold
        self.no_improvement_rounds_limit = no_improvement_rounds_limit

        self.state = BattleState.INITIAL
        self._confidence_history: list = []
        self._no_improvement_count = 0
        self._consecutive_clean_rounds = 0

    def transition(
        self,
        round_num: int,
        confidence: float,
        waste_detected: Dict[str, float],
        self_healing_detected: bool,
    ) -> BattleState:
        """
        Compute next state from current battle metrics.

        Returns:
            New BattleState.
        """
        self._confidence_history.append(confidence)
        if len(self._confidence_history) > 20:
            self._confidence_history.pop(0)

        # Victory
        if confidence >= self.confidence_threshold:
            self.state = BattleState.VICTORY
            return self.state

        # Max rounds
        if round_num >= self.max_rounds:
            self.state = BattleState.MAX_ROUNDS_REACHED
            return self.state

        # No improvement
        if len(self._confidence_history) >= 2 and confidence <= self._confidence_history[-2]:
            self._no_improvement_count += 1
        else:
            self._no_improvement_count = 0

        if self._no_improvement_count >= self.no_improvement_rounds_limit:
            self.state = BattleState.DEFEAT
            return self.state

        # Consecutive clean rounds (no waste)
        if not waste_detected:
            self._consecutive_clean_rounds += 1
            if self._consecutive_clean_rounds >= 3:
                self.state = BattleState.VICTORY
                return self.state
        else:
            self._consecutive_clean_rounds = 0

        # Self-healing branch
        if self_healing_detected:
            self.state = BattleState.SELF_HEALING_DETECTED
            return self.state

        if self.state == BattleState.SELF_HEALING_DETECTED:
            self.state = BattleState.COUNTER_MEASURING
            return self.state

        # Normal flow
        if waste_detected:
            self.state = BattleState.CLEANING
        else:
            self.state = BattleState.DETECTING

        return self.state

    def should_apply_counter_measures(self) -> bool:
        """Whether counter-measures should be applied (self-healing branch)."""
        return self.state in (
            BattleState.SELF_HEALING_DETECTED,
            BattleState.COUNTER_MEASURING,
        )

    def is_terminal(self) -> bool:
        """Whether the battle has ended."""
        return self.state in (
            BattleState.VICTORY,
            BattleState.DEFEAT,
            BattleState.MAX_ROUNDS_REACHED,
        )


def detect_self_healing(
    current_confidence: float,
    last_confidence: float,
    confidence_history: list,
    min_drop_ratio: float = 0.8,
    min_history_len: int = 3,
) -> bool:
    """
    Detect if watermarks appear to be regenerating (confidence dropping).

    Args:
        current_confidence: Current round confidence.
        last_confidence: Previous round confidence.
        confidence_history: Recent confidence values.
        min_drop_ratio: Ratio below which drop is considered self-healing (e.g. 0.8 = 20% drop).
        min_history_len: Minimum history length for trend analysis.

    Returns:
        True if self-healing is suspected.
    """
    if current_confidence <= 0.1:
        return False

    # Simple drop detection
    if last_confidence > 0 and current_confidence < last_confidence * min_drop_ratio:
        return True

    # Trend: declining over recent rounds
    if len(confidence_history) >= min_history_len:
        recent = confidence_history[-min_history_len:]
        if all(recent[i] >= recent[i + 1] for i in range(len(recent) - 1)):
            if recent[0] - recent[-1] > 0.1:
                return True

    return False
