#!/usr/bin/env python3
"""
Test Agent Log Callback Demo

This example demonstrates the new on_log() callback functionality
for agent logging events.
"""

import logging

from dana.builtin_types.agent import on_log
from dana.builtin_types.agent.agent_instance import AgentInstance
from dana.builtin_types.agent.agent_types import AgentType
from dana.core.lang.sandbox_context import SandboxContext

# Set up logging to see the output
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def log_callback(agent_name: str, message: str, context):
    """Callback function that will be called whenever an agent logs a message."""
    print(f"🔔 CALLBACK: Agent '{agent_name}' logged: '{message}'")
    print(f"   Context type: {type(context)}")


def custom_log_callback(agent_name: str, message: str, context):
    """Another callback function for demonstration."""
    print(f"📝 CUSTOM: [{agent_name}] {message}")


def main():
    print("=== Agent Log Callback Demo ===\n")

    # Register callbacks
    print("Registering log callbacks...")
    on_log(log_callback)
    on_log(custom_log_callback)

    # Create a test agent
    agent_type = AgentType(
        name="DemoAgent",
        fields={"name": "str"},
        field_order=["name"],
        field_comments={},
    )
    agent_instance = AgentInstance(agent_type, {"name": "demo_agent"})
    sandbox_context = SandboxContext()

    print("\nTesting agent logging...")

    # Test the log method - callbacks should be triggered
    agent_instance.log("Hello from the agent!", sandbox_context, is_sync=True)
    agent_instance.log("This is a test message", sandbox_context, is_sync=True)
    agent_instance.log("Agent is working correctly", sandbox_context, is_sync=True)

    print("\n=== Demo Complete ===")


if __name__ == "__main__":
    main()
