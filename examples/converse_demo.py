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

    # Create agent instance
    agent = create_example_agent()

    # Initialize LLM resource for the agent
    print("Initializing LLM resource...")
    agent._initialize_llm_resource()
    print(f"LLM resource initialized: {agent._llm_resource}")

    # Create CLI adapter
    cli_adapter = CLIAdapter()

    print("=== Demo with Simple Solver ===")
    print("Using a simple solver with agent's built-in capabilities...\n")

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
