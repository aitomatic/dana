"""
FSM (Finite State Machine) System Initialization

This module initializes the FSM struct type and makes it available to Dana code.
"""

from dana.core.builtin_types.workflow_system import register_fsm_struct_type


def initialize_fsm_system():
    """Initialize the FSM system by registering the FSM struct type."""
    try:
        register_fsm_struct_type()
        print("✅ FSM system initialized successfully")
    except Exception as e:
        print(f"⚠️ FSM system initialization failed: {e}")
        # Non-fatal - continue without FSM support
