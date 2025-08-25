#!/usr/bin/env python3
"""
Agent Context Manager Demo

This example demonstrates the new context manager functionality for AgentInstance,
showing proper resource initialization and cleanup.
"""

import logging

from dana.builtin_types.agent.agent_instance import AgentInstance
from dana.builtin_types.agent.agent_types import AgentType

# Set up logging to see the output
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def demo_basic_context_manager():
    """Demonstrate basic context manager usage."""
    print("=== Basic Context Manager Demo ===\n")

    # Create agent type and instance
    agent_type = AgentType(
        name="DemoAgent",
        fields={"name": "str", "config": "dict"},
        field_order=["name", "config"],
        field_comments={},
    )

    agent_instance = AgentInstance(
        agent_type,
        {
            "name": "demo_agent",
            "config": {
                "llm_model": "test-model",
                "llm_temperature": 0.7,
            },
        },
    )

    print("Before context manager:")
    print(f"  Conversation memory: {agent_instance._conversation_memory}")
    print(f"  LLM resource: {agent_instance._llm_resource_instance}")

    # Use context manager
    with agent_instance as agent:
        print("\nInside context manager:")
        print(f"  Agent name: {agent.name}")
        print(f"  Conversation memory: {agent._conversation_memory}")
        print(f"  LLM resource: {agent._llm_resource_instance}")

        # Use agent methods
        agent.log("Hello from context manager!", is_sync=True)
        agent.remember("test_key", "test_value", is_sync=True)

        # Check metrics
        metrics = agent.get_metrics()
        print(f"  Current step: {metrics['current_step']}")

    print("\nAfter context manager:")
    print(f"  Conversation memory: {agent_instance._conversation_memory}")
    print(f"  LLM resource: {agent_instance._llm_resource_instance}")
    print(f"  Current step: {agent_instance.get_metrics()['current_step']}")


def demo_exception_handling():
    """Demonstrate exception handling in context manager."""
    print("\n=== Exception Handling Demo ===\n")

    agent_type = AgentType(
        name="ExceptionAgent",
        fields={"name": "str"},
        field_order=["name"],
        field_comments={},
    )

    agent_instance = AgentInstance(agent_type, {"name": "exception_agent"})

    try:
        with agent_instance as _:
            print("Inside context manager with exception...")
            # This will raise an exception
            raise ValueError("Test exception")
    except ValueError as e:
        print(f"Caught exception: {e}")

    print("After exception:")
    print(f"  Resources cleaned up: {agent_instance._conversation_memory is None}")
    print(f"  Current step: {agent_instance.get_metrics()['current_step']}")


def demo_multiple_agents():
    """Demonstrate multiple agents with context managers."""
    print("\n=== Multiple Agents Demo ===\n")

    agent_type = AgentType(
        name="MultiAgent",
        fields={"name": "str"},
        field_order=["name"],
        field_comments={},
    )

    # Create multiple agents
    agent1 = AgentInstance(agent_type, {"name": "agent_1"})
    agent2 = AgentInstance(agent_type, {"name": "agent_2"})

    # Use them in nested context managers
    with agent1 as a1:
        with agent2 as a2:
            print(f"Agent 1: {a1.name}")
            print(f"Agent 2: {a2.name}")

            a1.log("Hello from agent 1", is_sync=True)
            a2.log("Hello from agent 2", is_sync=True)

    print("After nested context managers:")
    print(f"  Agent 1 resources: {agent1._conversation_memory is None}")
    print(f"  Agent 2 resources: {agent2._conversation_memory is None}")


def demo_memory_management():
    """Demonstrate memory management in context manager."""
    print("\n=== Memory Management Demo ===\n")

    agent_type = AgentType(
        name="MemoryAgent",
        fields={"name": "str"},
        field_order=["name"],
        field_comments={},
    )

    agent_instance = AgentInstance(agent_type, {"name": "memory_agent"})

    with agent_instance as agent:
        # Add data to agent memory
        agent._memory["user_data"] = "important information"
        agent._context["session_id"] = "12345"

        print("Inside context manager:")
        print(f"  Memory: {agent._memory}")
        print(f"  Context: {agent._context}")

        # Use conversation memory
        if agent._conversation_memory:
            agent._conversation_memory.add_turn("user", "Hello")
            agent._conversation_memory.add_turn("assistant", "Hi there!")

            stats = agent._conversation_memory.get_statistics()
            print(f"  Conversation turns: {stats.get('total_turns', 0)}")

    print("After context manager:")
    print(f"  Memory cleared: {len(agent_instance._memory) == 0}")
    print(f"  Context cleared: {len(agent_instance._context) == 0}")
    print(f"  Conversation memory: {agent_instance._conversation_memory is None}")


def main():
    """Run all demos."""
    print("Agent Context Manager Demo\n")
    print("This demo shows how to use AgentInstance as a context manager")
    print("for proper resource initialization and cleanup.\n")

    demo_basic_context_manager()
    demo_exception_handling()
    demo_multiple_agents()
    demo_memory_management()

    print("\n=== Demo Complete ===")
    print("Key benefits of context manager:")
    print("  - Automatic resource initialization")
    print("  - Guaranteed cleanup even with exceptions")
    print("  - Proper memory management")
    print("  - LLM resource lifecycle management")
    print("  - Metrics tracking")


if __name__ == "__main__":
    main()
