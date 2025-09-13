#!/usr/bin/env python3
"""
Example demonstrating the ConverseMixin functionality.

This example shows how to use the ConverseMixin with an agent instance
to create interactive conversation loops.
"""

import sys
import os

# Add the dana package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dana.core.agent.agent_instance import AgentInstance
from dana.core.agent.agent_type import AgentType
from dana.core.agent.methods.converse import CLIAdapter
from dana.core.resource.builtins.browser_resource import create_browser_resource
from dana.registry import GLOBAL_REGISTRY


def create_example_agent() -> AgentInstance:
    """Create an example agent instance with ConverseMixin and domain support components."""
    # Define agent type
    agent_type = AgentType(
        name="ConversationAgent",
        fields={
            "name": "str",
            "description": "str",
        },
        field_order=["name", "description"],
        field_defaults={
            "name": "ConversationBot",
            "description": "A helpful conversation agent",
        },
        docstring="An agent that can engage in conversations using the ConverseMixin",
    )

    # Create agent instance
    agent = AgentInstance(
        struct_type=agent_type,
        values={
            "name": "ConversationBot",
            "description": "I'm a helpful conversation agent. Ask me anything!",
        },
    )

    # Enable agent-centric persistence
    agent.enable_persistence()

    return agent


def custom_solver(message: str, artifacts=None, sandbox_context=None, **kwargs) -> str:
    """Custom solver function for demonstration with solve_sync signature."""
    if "hello" in message.lower():
        return "Hello! Nice to meet you!"
    elif "help" in message.lower():
        return "I can help you with various tasks. What would you like to know?"
    elif "goodbye" in message.lower():
        return "Goodbye! Have a great day!"
    else:
        return f"I heard you say: '{message}'. How can I help you with that?"


def simple_solver(message: str, artifacts=None, sandbox_context=None, **kwargs) -> str:
    """Simple solver that uses the agent's built-in capabilities."""
    # Get the agent instance from the artifacts or kwargs
    agent = kwargs.get("agent")
    if not agent:
        return "Error: No agent instance available"

    # Use the agent's built-in solve_sync method directly
    try:
        result = agent.solve_sync(
            problem_or_workflow=message,
            artifacts=artifacts,
            sandbox_context=sandbox_context,
            **kwargs,
        )

        # Handle different result types
        if isinstance(result, str):
            return result
        elif isinstance(result, dict):
            # Extract the message from structured responses
            if result.get("type") == "ask":
                return result.get("message", "I need more information to help you.")
            elif result.get("type") == "answer":
                return result.get("deliverable", str(result))
            else:
                return str(result)
        else:
            return str(result)

    except Exception as e:
        return f"Error in simple solver: {str(e)}"


def main():
    """Main function demonstrating ConverseMixin usage."""
    print("=== ConverseMixin Demo ===")
    print("This demo shows how to use the ConverseMixin for conversation loops.")
    print("Type 'quit' or press Ctrl+C to exit.\n")

    # Create and register BrowserResource
    print("Creating and registering BrowserResource...")
    browser_resource = create_browser_resource()
    browser_resource.name = "web_browser"

    # Register the browser resource with the global registry
    GLOBAL_REGISTRY.resources.track_resource(browser_resource, name="web_browser")
    print(f"✅ BrowserResource registered: {browser_resource.name}")

    # Test the browser resource
    print("\nTesting browser resource...")
    try:
        test_result = browser_resource.query("https://httpbin.org/get")
        print(f"✅ Browser test successful: {test_result['success']}")
        print(f"   Content type: {test_result['content_type']}")
        print(f"   Content length: {test_result['content_length']}")
    except Exception as e:
        print(f"❌ Browser test failed: {e}")

    # Create agent instance
    agent = create_example_agent()

    # Initialize LLM resource for the agent
    print("\nInitializing LLM resource...")
    agent._initialize_llm_resource()
    print(f"LLM resource initialized: {agent._llm_resource}")

    # Check what resources the agent can see
    print("\nChecking agent's view of available resources...")
    try:
        dependencies = agent.get_solver_dependencies()
        print("Agent solver dependencies:")
        for solver_name, deps in dependencies.items():
            print(f"  {solver_name}:")
            print(f"    Resources: {deps['resources']['count']} ({deps['resources']['names']})")
            print(f"    Workflows: {deps['workflows']['count']} ({deps['workflows']['names']})")
    except Exception as e:
        print(f"Error checking dependencies: {e}")

    # Create CLI adapter
    cli_adapter = CLIAdapter()

    print("=== Demo with Simple Solver ===")
    print("Using a simple solver with agent's built-in capabilities...\n")

    # Test a message that will trigger solver execution and debug reporting
    print("Testing solver execution with debug reporting...")
    try:
        test_message = "Hello, can you help me browse a website?"
        print(f"Sending test message: '{test_message}'")
        result = agent.solve_sync(test_message)
        print(f"Agent response: {result}")
    except Exception as e:
        print(f"Error in test solve: {e}")

    try:
        # Use simple solver with agent instance
        def solver_with_agent(message, artifacts=None, sandbox_context=None, **kwargs):
            return simple_solver(message, artifacts, sandbox_context, agent=agent, **kwargs)

        result = agent.converse_sync(cli_adapter, solve_fn=solver_with_agent)
        print(f"\nConversation ended: {result}")

    except KeyboardInterrupt:
        print("\n\nConversation interrupted by user.")


if __name__ == "__main__":
    main()
