"""
Test script for agent chat functionality with conversation memory.
"""

import os
import sys
from pathlib import Path

# Add Dana to path
dana_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(dana_path))

from dana.agent.agent_struct_system import AgentStructType, AgentStructInstance, register_agent_struct_type


def test_basic_chat():
    """Test basic chat functionality without LLM."""
    print("=== Testing Basic Chat (No LLM) ===\n")

    # Create a simple agent type
    agent_type = AgentStructType(
        name="ChatBot", fields={"personality": str, "expertise": str}, field_order=["personality", "expertise"], field_comments={}
    )

    # Register the agent type
    register_agent_struct_type(agent_type)

    # Create an agent instance
    agent = AgentStructInstance(agent_type, {"personality": "friendly", "expertise": "general assistance"})

    # Test conversation
    messages = ["Hello!", "What's your name?", "Can you help me?", "Do you remember my first message?", "What have we talked about?"]

    for msg in messages:
        print(f"User: {msg}")
        response = agent.chat(msg)
        print(f"Bot: {response}\n")

    # Show conversation statistics
    stats = agent.get_conversation_stats()
    print("\n=== Conversation Statistics ===")
    print(f"Total turns: {stats.get('total_turns', 0)}")
    print(f"Active turns: {stats.get('active_turns', 0)}")
    print(f"Session count: {stats.get('session_count', 0)}")


def test_chat_with_mock_llm():
    """Test chat functionality with a mock LLM function."""
    print("\n=== Testing Chat with Mock LLM ===\n")

    # Create a mock LLM function
    def mock_llm(prompt: str) -> str:
        """Simple mock LLM that responds based on prompt content."""
        if "remember" in prompt.lower():
            return "Yes, I remember our conversation. You started by greeting me with 'Hello!'"
        elif "name" in prompt.lower():
            return "I'm ChatBot, your friendly AI assistant with expertise in general assistance."
        elif "help" in prompt.lower():
            return "Of course! I'm here to help with general assistance. What do you need help with?"
        elif "hello" in prompt.lower() or "hi" in prompt.lower():
            return "Hello! It's great to meet you. I'm ChatBot, ready to assist you."
        else:
            return f"I understand. Based on our conversation so far, I'm here to provide general assistance."

    # Create agent with LLM in context
    agent_type = AgentStructType(
        name="SmartBot", fields={"personality": str, "expertise": str}, field_order=["personality", "expertise"], field_comments={}
    )

    agent = AgentStructInstance(agent_type, {"personality": "helpful", "expertise": "technical support"})

    # Add LLM to agent's context
    agent._context["llm"] = mock_llm

    # Test conversation
    messages = ["Hello!", "What's your name?", "Can you help me?", "Do you remember what I said first?"]

    for msg in messages:
        print(f"User: {msg}")
        response = agent.chat(msg)
        print(f"Bot: {response}\n")


def test_conversation_persistence():
    """Test that conversations persist across sessions."""
    print("\n=== Testing Conversation Persistence ===\n")

    # First session
    print("--- Session 1 ---")
    agent_type = AgentStructType(name="PersistentBot", fields={"version": str}, field_order=["version"], field_comments={})

    agent1 = AgentStructInstance(agent_type, {"version": "1.0"})

    agent1.chat("My name is Alice")
    agent1.chat("I'm learning Python")
    agent1.chat("See you later!")

    stats1 = agent1.get_conversation_stats()
    print(f"Session 1 - Total turns: {stats1.get('total_turns', 0)}")

    # Second session (new instance, same agent type)
    print("\n--- Session 2 ---")
    agent2 = AgentStructInstance(agent_type, {"version": "1.0"})

    print("User: Do you remember my name?")
    response = agent2.chat("Do you remember my name?")
    print(f"Bot: {response}\n")

    stats2 = agent2.get_conversation_stats()
    print(f"Session 2 - Total turns: {stats2.get('total_turns', 0)}")
    print(f"Session 2 - Session count: {stats2.get('session_count', 0)}")


def test_multiple_agents():
    """Test that different agents maintain separate conversations."""
    print("\n=== Testing Multiple Agents ===\n")

    # Create two different agent types
    support_agent_type = AgentStructType(name="SupportAgent", fields={"department": str}, field_order=["department"], field_comments={})
    sales_agent_type = AgentStructType(name="SalesAgent", fields={"region": str}, field_order=["region"], field_comments={})

    # Create instances
    support_agent = AgentStructInstance(support_agent_type, {"department": "technical"})
    sales_agent = AgentStructInstance(sales_agent_type, {"region": "north"})

    # Have different conversations
    print("--- Conversation with Support Agent ---")
    support_agent.chat("I have a technical issue")
    support_agent.chat("My computer won't start")

    print("\n--- Conversation with Sales Agent ---")
    sales_agent.chat("I'm interested in your products")
    sales_agent.chat("What's the pricing?")

    # Check that conversations are separate
    print("\n--- Checking Memory Separation ---")
    print("Support Agent asking about products:")
    response = support_agent.chat("What products do you sell?")
    print(f"Response: {response}\n")

    print("Sales Agent asking about technical issues:")
    response = sales_agent.chat("Can you fix my computer?")
    print(f"Response: {response}")


def cleanup_test_memories():
    """Clean up test memory files."""
    memory_dir = Path("agent_memories")
    if memory_dir.exists():
        for memory_file in memory_dir.glob("*.json"):
            memory_file.unlink()
        print("\n✓ Cleaned up test memory files")


def main():
    """Run all tests."""
    print("Starting Agent Chat Tests\n")

    # Run tests
    test_basic_chat()
    test_chat_with_mock_llm()
    test_conversation_persistence()
    test_multiple_agents()

    # Cleanup
    cleanup_test_memories()

    print("\n✅ All tests completed!")


if __name__ == "__main__":
    main()
