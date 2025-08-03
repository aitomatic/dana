"""
Test script for ConversationMemory implementation.

This demonstrates basic usage and validates core functionality.
"""

import os
import json
from pathlib import Path
from conversation_memory import ConversationMemory


def test_basic_conversation():
    """Test basic conversation flow with memory."""
    print("=== Testing Basic Conversation ===")

    # Create a memory instance
    memory = ConversationMemory(filepath="test_memory.json", max_turns=10)

    # Simulate a conversation
    conversations = [
        ("Hi, my name is Alice", "Hello Alice! Nice to meet you."),
        ("What's the weather like?", "I don't have access to weather data, but I can help with other questions."),
        ("Can you remember my name?", "Yes, your name is Alice."),
        ("What did I ask about before?", "You asked about the weather."),
    ]

    for user_msg, agent_msg in conversations:
        print(f"\nUser: {user_msg}")
        print(f"Agent: {agent_msg}")
        memory.add_turn(user_msg, agent_msg)

    # Test context building
    print("\n=== Testing Context Building ===")
    context = memory.build_llm_context("Do you remember our conversation?")
    print(context)

    # Test search
    print("\n=== Testing Search ===")
    results = memory.search_history("weather")
    print(f"Found {len(results)} results for 'weather'")
    for result in results:
        print(f"- User: {result['user_input'][:50]}...")

    # Test statistics
    print("\n=== Conversation Statistics ===")
    stats = memory.get_statistics()
    print(f"Total turns: {stats['total_turns']}")
    print(f"Active turns: {stats['active_turns']}")
    print(f"Session count: {stats['session_count']}")

    return memory


def test_persistence():
    """Test saving and loading conversation memory."""
    print("\n=== Testing Persistence ===")

    # Create and populate memory
    memory1 = ConversationMemory(filepath="test_persist.json", max_turns=5)
    memory1.add_turn("First message", "First response")
    memory1.add_turn("Second message", "Second response")

    # Create new instance and load
    memory2 = ConversationMemory(filepath="test_persist.json", max_turns=5)

    # Verify data was loaded
    history = list(memory2.history)
    print(f"Loaded {len(history)} turns from file")
    print(f"Session count after reload: {memory2.metadata['session_count']}")

    # Verify content
    assert len(history) == 2
    assert history[0]["user_input"] == "First message"
    print("✓ Persistence test passed")

    # Cleanup
    os.remove("test_persist.json")


def test_max_turns():
    """Test that memory respects max_turns limit."""
    print("\n=== Testing Max Turns Limit ===")

    memory = ConversationMemory(filepath="test_max.json", max_turns=3)

    # Add more turns than the limit
    for i in range(5):
        memory.add_turn(f"Message {i}", f"Response {i}")

    # Check that only last 3 are kept
    history = list(memory.history)
    print(f"Added 5 turns, kept {len(history)} (max_turns=3)")

    # Verify it's the last 3
    assert len(history) == 3
    assert history[0]["user_input"] == "Message 2"
    assert history[-1]["user_input"] == "Message 4"
    print("✓ Max turns test passed")

    # But total_turns should still be 5
    assert memory.metadata["total_turns"] == 5
    print(f"✓ Total turns tracked correctly: {memory.metadata['total_turns']}")

    # Cleanup
    os.remove("test_max.json")


def test_context_assembly():
    """Test different context assembly scenarios."""
    print("\n=== Testing Context Assembly ===")

    memory = ConversationMemory(filepath="test_context.json")

    # Add some turns
    memory.add_turn("What's your name?", "I'm Claude, an AI assistant.")
    memory.add_turn("Can you help with Python?", "Yes, I can help with Python programming.")
    memory.add_turn("Show me a loop example", "Here's a simple for loop: for i in range(5): print(i)")

    # Test with different parameters
    context1 = memory.build_llm_context("New question", max_turns=2)
    print("Context with 2 turns:")
    print(context1)
    print("-" * 50)

    context2 = memory.build_llm_context("Another question", max_turns=5)
    print("\nContext with 5 turns:")
    print(context2)

    # Cleanup
    os.remove("test_context.json")


def test_error_handling():
    """Test error handling and recovery."""
    print("\n=== Testing Error Handling ===")

    # Test loading non-existent file
    memory = ConversationMemory(filepath="non_existent.json")
    print(f"✓ Handled non-existent file gracefully")

    # Test corrupted JSON
    with open("corrupted.json", "w") as f:
        f.write("{invalid json")

    memory2 = ConversationMemory(filepath="corrupted.json")
    print(f"✓ Handled corrupted JSON gracefully")

    # Add a turn to verify it still works
    memory2.add_turn("Test", "Response")
    assert len(memory2.history) == 1
    print(f"✓ Memory still functional after error")

    # Cleanup
    os.remove("corrupted.json")
    if os.path.exists("non_existent.json"):
        os.remove("non_existent.json")


def main():
    """Run all tests."""
    print("Starting ConversationMemory Tests\n")

    # Run tests
    test_basic_conversation()
    test_persistence()
    test_max_turns()
    test_context_assembly()
    test_error_handling()

    print("\n✅ All tests completed!")

    # Cleanup any remaining test files
    for f in Path(".").glob("test_*.json"):
        f.unlink()


if __name__ == "__main__":
    main()
