"""Unit tests for battle state machine."""

import pytest

from stega.visualization.battle_state_machine import (
    BattleStateMachine,
    BattleState,
    detect_self_healing,
)


def test_state_machine_victory_on_confidence():
    """State machine transitions to VICTORY when confidence threshold reached."""
    sm = BattleStateMachine(confidence_threshold=0.95, max_rounds=50)
    state = sm.transition(5, 0.96, {}, False)
    assert state == BattleState.VICTORY
    assert sm.is_terminal()


def test_state_machine_max_rounds():
    """State machine transitions to MAX_ROUNDS_REACHED at max rounds."""
    sm = BattleStateMachine(confidence_threshold=0.95, max_rounds=10)
    state = sm.transition(10, 0.5, {"lsb": 0.5}, False)
    assert state == BattleState.MAX_ROUNDS_REACHED
    assert sm.is_terminal()


def test_state_machine_cleaning_state():
    """State machine transitions to CLEANING when waste detected."""
    sm = BattleStateMachine(confidence_threshold=0.95, max_rounds=50)
    state = sm.transition(1, 0.5, {"lsb_steganography": 0.5}, False)
    assert state == BattleState.CLEANING
    assert not sm.is_terminal()


def test_state_machine_self_healing_detected():
    """State machine transitions to SELF_HEALING_DETECTED when self-healing."""
    sm = BattleStateMachine(confidence_threshold=0.95, max_rounds=50)
    state = sm.transition(5, 0.4, {"lsb": 0.6}, True)
    assert state == BattleState.SELF_HEALING_DETECTED


def test_detect_self_healing_drop():
    """Detect self-healing when confidence drops significantly."""
    assert detect_self_healing(0.4, 0.6, [], min_drop_ratio=0.8) is True


def test_detect_self_healing_no_drop():
    """No self-healing when confidence stable."""
    assert detect_self_healing(0.6, 0.58, [], min_drop_ratio=0.8) is False


def test_detect_self_healing_low_confidence():
    """No self-healing when current confidence very low."""
    assert detect_self_healing(0.05, 0.5, [], min_drop_ratio=0.8) is False
