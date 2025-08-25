#!/usr/bin/env python3
"""
Agent Async Context Manager Demo

This example demonstrates the new async context manager functionality for AgentInstance,
showing proper async resource initialization and cleanup.
"""

import asyncio
import logging

from dana.builtin_types.agent.agent_instance import AgentInstance
from dana.builtin_types.agent.agent_types import AgentType

# Set up logging to see the output
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


async def demo_async_context_manager():
    """Demonstrate async context manager usage."""
    print("=== Async Context Manager Demo ===\n")

    # Create agent type and instance
    agent_type = AgentType(
        name="AsyncDemoAgent",
        fields={"name": "str", "config": "dict"},
        field_order=["name", "config"],
        field_comments={},
    )

    agent_instance = AgentInstance(
        agent_type,
        {
            "name": "async_demo_agent",
            "config": {
                "llm_model": "test-model",
                "llm_temperature": 0.7,
            },
        },
    )

    print("Before async context manager:")
    print(f"  Conversation memory: {agent_instance._conversation_memory}")
    print(f"  LLM resource: {agent_instance._llm_resource_instance}")

    # Use async context manager
    async with agent_instance as agent:
        print("\nInside async context manager:")
        print(f"  Agent name: {agent.name}")
        print(f"  Conversation memory: {agent._conversation_memory}")
        print(f"  LLM resource: {agent._llm_resource_instance}")

        # Use agent methods
        agent.log("Hello from async context manager!", is_sync=True)
        agent.remember("async_key", "async_value", is_sync=True)

        # Check metrics
        metrics = agent.get_metrics()
        print(f"  Current step: {metrics['current_step']}")

    print("\nAfter async context manager:")
    print(f"  Conversation memory: {agent_instance._conversation_memory}")
    print(f"  LLM resource: {agent_instance._llm_resource_instance}")
    print(f"  Current step: {agent_instance.get_metrics()['current_step']}")


async def demo_async_exception_handling():
    """Demonstrate async exception handling in context manager."""
    print("\n=== Async Exception Handling Demo ===\n")

    agent_type = AgentType(
        name="AsyncExceptionAgent",
        fields={"name": "str"},
        field_order=["name"],
        field_comments={},
    )

    agent_instance = AgentInstance(agent_type, {"name": "async_exception_agent"})

    try:
        async with agent_instance as _:
            print("Inside async context manager with exception...")
            # This will raise an exception
            raise ValueError("Test async exception")
    except ValueError as e:
        print(f"Caught exception: {e}")

    print("After exception:")
    print(f"  Resources cleaned up: {agent_instance._conversation_memory is None}")
    print(f"  Current step: {agent_instance.get_metrics()['current_step']}")


async def demo_async_multiple_agents():
    """Demonstrate multiple agents with async context managers."""
    print("\n=== Async Multiple Agents Demo ===\n")

    agent_type = AgentType(
        name="AsyncMultiAgent",
        fields={"name": "str"},
        field_order=["name"],
        field_comments={},
    )

    # Create multiple agents
    agent1 = AgentInstance(agent_type, {"name": "async_agent_1"})
    agent2 = AgentInstance(agent_type, {"name": "async_agent_2"})

    # Use them in nested async context managers
    async with agent1 as a1:
        async with agent2 as a2:
            print(f"Agent 1: {a1.name}")
            print(f"Agent 2: {a2.name}")

            a1.log("Hello from async agent 1", is_sync=True)
            a2.log("Hello from async agent 2", is_sync=True)

    print("After nested async context managers:")
    print(f"  Agent 1 resources: {agent1._conversation_memory is None}")
    print(f"  Agent 2 resources: {agent2._conversation_memory is None}")


async def demo_async_vs_sync_compatibility():
    """Demonstrate compatibility between async and sync context managers."""
    print("\n=== Async vs Sync Compatibility Demo ===\n")

    agent_type = AgentType(
        name="CompatibilityAgent",
        fields={"name": "str"},
        field_order=["name"],
        field_comments={},
    )

    agent_instance = AgentInstance(agent_type, {"name": "compatibility_agent"})

    # Test sync context manager
    print("Testing sync context manager:")
    with agent_instance as agent:
        print(f"  Sync: Agent name = {agent.name}")
        print(f"  Sync: Resources initialized = {agent._conversation_memory is not None}")

    print(f"  Sync: Resources cleaned up = {agent_instance._conversation_memory is None}")

    # Test async context manager
    print("\nTesting async context manager:")
    async with agent_instance as agent:
        print(f"  Async: Agent name = {agent.name}")
        print(f"  Async: Resources initialized = {agent._conversation_memory is not None}")

    print(f"  Async: Resources cleaned up = {agent_instance._conversation_memory is None}")


async def demo_concurrent_agents():
    """Demonstrate concurrent agent usage with async context managers."""
    print("\n=== Concurrent Agents Demo ===\n")

    agent_type = AgentType(
        name="ConcurrentAgent",
        fields={"name": "str"},
        field_order=["name"],
        field_comments={},
    )

    async def use_agent(agent_name: str, delay: float):
        """Use an agent with a delay to simulate work."""
        agent_instance = AgentInstance(agent_type, {"name": agent_name})

        async with agent_instance as agent:
            print(f"  {agent_name}: Starting work...")
            await asyncio.sleep(delay)  # Simulate async work
            agent.log(f"Completed work for {agent_name}", is_sync=True)
            print(f"  {agent_name}: Finished work")

    # Run multiple agents concurrently
    print("Running agents concurrently:")
    await asyncio.gather(
        use_agent("concurrent_agent_1", 0.5),
        use_agent("concurrent_agent_2", 0.3),
        use_agent("concurrent_agent_3", 0.7),
    )

    print("All concurrent agents completed!")


async def main():
    """Run all async demos."""
    print("Agent Async Context Manager Demo\n")
    print("This demo shows how to use AgentInstance as an async context manager")
    print("for proper async resource initialization and cleanup.\n")

    await demo_async_context_manager()
    await demo_async_exception_handling()
    await demo_async_multiple_agents()
    await demo_async_vs_sync_compatibility()
    await demo_concurrent_agents()

    print("\n=== Async Demo Complete ===")
    print("Key benefits of async context manager:")
    print("  - Async resource initialization")
    print("  - Async cleanup operations")
    print("  - Better performance for LLM resources")
    print("  - Concurrent agent usage")
    print("  - Compatibility with sync context managers")


if __name__ == "__main__":
    asyncio.run(main())
