"""
FSM (Finite State Machine) system for Dana workflow execution.

This module implements the FSM struct type and utility functions for workflows.
FSMs are pure data structures that define process states and transitions.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any

from dana.builtin_types.struct_system import StructType


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
        fields={
            "states": "list",
            "initial_state": "str",
            "current_state": "str",
            "transitions": "dict",
            "state_metadata": "dict",
            "results": "dict",
            "workflow_metadata": "dict",
        },
        field_order=["states", "initial_state", "current_state", "transitions", "state_metadata", "results", "workflow_metadata"],
        field_comments={
            "states": "All possible states in the FSM",
            "initial_state": "Starting state of the FSM",
            "current_state": "Current execution state",
            "transitions": "Dictionary mapping 'from_state:event' to to_state",
            "state_metadata": "Metadata for each state including action, objective, parameters, conditions, and status",
            "results": "Results from each state execution",
            "workflow_metadata": "Workflow context information including name, description, and other metadata",
        },
        field_defaults={
            "states": ["START", "COMPLETE"],
            "initial_state": "START",
            "current_state": "START",
            "transitions": {"START:next": "COMPLETE"},
            "state_metadata": {},
            "results": {},
            "workflow_metadata": {},
        },
        docstring="Enhanced Finite State Machine for workflow execution with state metadata and execution context",
    )


def create_linear_fsm(
    states: list[str], state_metadata: dict[str, dict] | None = None, workflow_metadata: dict | None = None
) -> dict[str, Any]:
    """
    Create a linear FSM where each state transitions to the next.

    Args:
        states: List of state names in order
        state_metadata: Optional metadata for each state
        workflow_metadata: Optional workflow metadata

    Returns:
        FSM data dictionary for struct instantiation
    """
    if len(states) < 2:
        raise ValueError("Linear FSM requires at least 2 states")

    transitions = {}
    for i in range(len(states) - 1):
        key = _make_transition_key(states[i], "next")
        transitions[key] = states[i + 1]

    # Initialize state metadata if not provided
    if state_metadata is None:
        state_metadata = {}
        for state in states:
            if state not in ["START", "COMPLETE"]:
                state_metadata[state] = {
                    "action": "execute_step",
                    "objective": f"Execute {state}",
                    "parameters": {},
                    "conditions": {},
                    "status": "pending",
                }

    return {
        "states": states,
        "initial_state": states[0],
        "current_state": states[0],
        "transitions": transitions,
        "state_metadata": state_metadata,
        "results": {},
        "workflow_metadata": workflow_metadata or {},
    }


def create_branching_fsm(
    states: list[str],
    initial_state: str,
    transitions: dict[str, str],
    state_metadata: dict[str, dict] | None = None,
    workflow_metadata: dict | None = None,
) -> dict[str, Any]:
    """
    Create a branching FSM with custom transitions.

    Args:
        states: List of all possible states
        initial_state: Starting state
        transitions: Dictionary mapping 'from_state:event' to to_state
        state_metadata: Optional metadata for each state
        workflow_metadata: Optional workflow metadata

    Returns:
        FSM data dictionary for struct instantiation
    """
    # Initialize state metadata if not provided
    if state_metadata is None:
        state_metadata = {}
        for state in states:
            if state not in ["START", "COMPLETE", "ERROR"]:
                state_metadata[state] = {
                    "action": "execute_step",
                    "objective": f"Execute {state}",
                    "parameters": {},
                    "conditions": {},
                    "status": "pending",
                }

    return {
        "states": states,
        "initial_state": initial_state,
        "current_state": initial_state,
        "transitions": transitions,
        "state_metadata": state_metadata,
        "results": {},
        "workflow_metadata": workflow_metadata or {},
    }


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
def create_simple_workflow_fsm(workflow_metadata: dict | None = None) -> dict[str, Any]:
    """Create a simple workflow FSM with start, process, and complete states."""
    state_metadata = {
        "PROCESSING": {
            "action": "execute_workflow",
            "objective": "Execute the main workflow logic",
            "parameters": {},
            "conditions": {},
            "status": "pending",
        }
    }
    return create_linear_fsm(["START", "PROCESSING", "COMPLETE"], state_metadata, workflow_metadata)


def create_error_handling_fsm(workflow_metadata: dict | None = None) -> dict[str, Any]:
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

    state_metadata = {
        "PROCESSING": {
            "action": "execute_workflow",
            "objective": "Execute the main workflow logic",
            "parameters": {},
            "conditions": {},
            "status": "pending",
        },
        "ERROR": {
            "action": "handle_error",
            "objective": "Handle execution errors",
            "parameters": {},
            "conditions": {},
            "status": "pending",
        },
        "RETRY": {
            "action": "retry_execution",
            "objective": "Retry the failed execution",
            "parameters": {},
            "conditions": {},
            "status": "pending",
        },
    }

    return create_branching_fsm(states, "START", transitions, state_metadata, workflow_metadata)


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


def get_state_metadata(fsm: Any, state: str) -> dict | None:
    """Get metadata for a specific state."""
    return fsm.state_metadata.get(state)


def update_state_status(fsm: Any, state: str, status: str) -> None:
    """Update the status of a specific state."""
    if state in fsm.state_metadata:
        fsm.state_metadata[state]["status"] = status


def get_state_status(fsm: Any, state: str) -> str | None:
    """Get the status of a specific state."""
    metadata = get_state_metadata(fsm, state)
    return metadata.get("status") if metadata else None


def set_state_result(fsm: Any, state: str, result: dict) -> None:
    """Set the result for a specific state."""
    fsm.results[state] = result


def get_state_result(fsm: Any, state: str) -> dict | None:
    """Get the result for a specific state."""
    return fsm.results.get(state)


def get_workflow_metadata(fsm: Any) -> dict:
    """Get the workflow metadata."""
    return fsm.workflow_metadata


def set_workflow_metadata(fsm: Any, metadata: dict) -> None:
    """Set the workflow metadata."""
    fsm.workflow_metadata.update(metadata)


def get_current_state_metadata(fsm: Any) -> dict | None:
    """Get metadata for the current state."""
    return get_state_metadata(fsm, fsm.current_state)


def get_current_state_action(fsm: Any) -> str | None:
    """Get the action for the current state."""
    metadata = get_current_state_metadata(fsm)
    return metadata.get("action") if metadata else None


def get_current_state_objective(fsm: Any) -> str | None:
    """Get the objective for the current state."""
    metadata = get_current_state_metadata(fsm)
    return metadata.get("objective") if metadata else None


def get_current_state_parameters(fsm: Any) -> dict:
    """Get the parameters for the current state."""
    metadata = get_current_state_metadata(fsm)
    return metadata.get("parameters", {}) if metadata else {}
