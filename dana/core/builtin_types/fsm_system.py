"""
FSM (Finite State Machine) system for Dana workflow execution.

This module implements the FSM struct type and utility functions for workflows.
FSMs are pure data structures that define process states and transitions.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any

from dana.core.builtin_types.struct_system import StructType


def _make_transition_key(from_state: str, event: str) -> str:
    """Create a string key for a transition from tuple (from_state, event)."""
    return f"{from_state}:{event}"


def _parse_transition_key(key: str) -> tuple[str, str]:
    """Parse a transition key back into (from_state, event) tuple."""
    if ":" not in key:
        raise ValueError(f"Invalid transition key format: {key}")
    parts = key.split(":", 1)
    return parts[0], parts[1]


def create_fsm_struct_type() -> StructType:
    """Create the FSM struct type definition."""
    return StructType(
        name="FSM",
        fields={"states": "list", "initial_state": "str", "current_state": "str", "transitions": "dict"},
        field_order=["states", "initial_state", "current_state", "transitions"],
        field_comments={
            "states": "All possible states in the FSM",
            "initial_state": "Starting state of the FSM",
            "current_state": "Current execution state",
            "transitions": "Dictionary mapping 'from_state:event' to to_state",
        },
        field_defaults={
            "states": ["START", "COMPLETE"],
            "initial_state": "START",
            "current_state": "START",
            "transitions": {"START:next": "COMPLETE"},
        },
        docstring="Finite State Machine for workflow execution",
    )


def create_linear_fsm(states: list[str]) -> dict[str, Any]:
    """
    Create a linear FSM where each state transitions to the next.

    Args:
        states: List of state names in order

    Returns:
        FSM data dictionary for struct instantiation
    """
    if len(states) < 2:
        raise ValueError("Linear FSM requires at least 2 states")

    transitions = {}
    for i in range(len(states) - 1):
        key = _make_transition_key(states[i], "next")
        transitions[key] = states[i + 1]

    return {"states": states, "initial_state": states[0], "current_state": states[0], "transitions": transitions}


def create_branching_fsm(states: list[str], initial_state: str, transitions: dict[str, str]) -> dict[str, Any]:
    """
    Create a branching FSM with custom transitions.

    Args:
        states: List of all possible states
        initial_state: Starting state
        transitions: Dictionary mapping 'from_state:event' to to_state

    Returns:
        FSM data dictionary for struct instantiation
    """
    return {"states": states, "initial_state": initial_state, "current_state": initial_state, "transitions": transitions}


def create_branching_fsm_from_tuples(states: list[str], initial_state: str, transitions: dict[tuple[str, str], str]) -> dict[str, Any]:
    """
    Create a branching FSM with custom transitions (backward compatibility with tuple keys).

    Args:
        states: List of all possible states
        initial_state: Starting state
        transitions: Dictionary mapping (from_state, event) to to_state

    Returns:
        FSM data dictionary for struct instantiation
    """
    # Convert tuple keys to string keys
    string_transitions = {}
    for (from_state, event), to_state in transitions.items():
        key = _make_transition_key(from_state, event)
        string_transitions[key] = to_state

    return create_branching_fsm(states, initial_state, string_transitions)


# Common FSM patterns
def create_simple_workflow_fsm() -> dict[str, Any]:
    """Create a simple workflow FSM with start, process, and complete states."""
    return create_linear_fsm(["START", "PROCESSING", "COMPLETE"])


def create_error_handling_fsm() -> dict[str, Any]:
    """Create an FSM with error handling states."""
    states = ["START", "PROCESSING", "COMPLETE", "ERROR", "RETRY"]
    transitions = {
        "START:begin": "PROCESSING",
        "PROCESSING:success": "COMPLETE",
        "PROCESSING:error": "ERROR",
        "ERROR:retry": "RETRY",
        "RETRY:begin": "PROCESSING",
        "ERROR:abort": "COMPLETE",  # Abort also goes to complete
    }

    return create_branching_fsm(states, "START", transitions)


# FSM utility functions for Dana code
def reset_fsm(fsm: Any) -> None:
    """Reset FSM to initial state."""
    fsm.current_state = fsm.initial_state


def can_transition(fsm: Any, from_state: str, event: str) -> bool:
    """Check if a transition is valid."""
    key = _make_transition_key(from_state, event)
    return key in fsm.transitions


def get_next_state(fsm: Any, from_state: str, event: str) -> str | None:
    """Get the next state for a given transition, or None if invalid."""
    key = _make_transition_key(from_state, event)
    return fsm.transitions.get(key)


def transition_fsm(fsm: Any, event: str) -> bool:
    """
    Attempt to transition from current state with given event.

    Returns:
        True if transition was successful, False otherwise
    """
    next_state = get_next_state(fsm, fsm.current_state, event)
    if next_state is not None:
        fsm.current_state = next_state
        return True
    return False


def is_terminal_state(fsm: Any, state: str) -> bool:
    """Check if a state is terminal (no outgoing transitions)."""
    for key in fsm.transitions.keys():
        from_state, _ = _parse_transition_key(key)
        if from_state == state:
            return False
    return True


def get_available_events(fsm: Any, state: str) -> list[str]:
    """Get all available events for a given state."""
    events = []
    for key in fsm.transitions.keys():
        from_state, event = _parse_transition_key(key)
        if from_state == state:
            events.append(event)
    return events
