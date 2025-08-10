"""
Unit tests for ConversationMemory class.
"""

import os
import tempfile
import unittest

from dana.frameworks.memory.conversation_memory import ConversationMemory


class TestConversationMemory(unittest.TestCase):
    """Test cases for ConversationMemory class."""

    def setUp(self):
        """Set up test cases with temporary files."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_file = os.path.join(self.temp_dir, "test_memory.json")
        self.memory = ConversationMemory(filepath=self.temp_file, max_turns=5)

    def tearDown(self):
        """Clean up temporary files."""
        if os.path.exists(self.temp_file):
            os.remove(self.temp_file)
        if os.path.exists(self.temp_file + ".bak"):
            os.remove(self.temp_file + ".bak")
        os.rmdir(self.temp_dir)

    def test_initialization(self):
        """Test memory initialization."""
        self.assertEqual(len(self.memory.history), 0)
        self.assertEqual(self.memory.max_turns, 5)
        self.assertEqual(len(self.memory.summaries), 0)
        self.assertIn("session_count", self.memory.metadata)
        self.assertIn("total_turns", self.memory.metadata)

    def test_add_turn(self):
        """Test adding conversation turns."""
        turn = self.memory.add_turn("Hello", "Hi there!")

        self.assertEqual(len(self.memory.history), 1)
        self.assertEqual(turn["user_input"], "Hello")
        self.assertEqual(turn["agent_response"], "Hi there!")
        self.assertIn("turn_id", turn)
        self.assertIn("timestamp", turn)
        self.assertEqual(self.memory.metadata["total_turns"], 1)

    def test_max_turns_limit(self):
        """Test that memory respects max_turns limit."""
        # Add more turns than the limit
        for i in range(10):
            self.memory.add_turn(f"Message {i}", f"Response {i}")

        # Should only keep the last 5 turns
        self.assertEqual(len(self.memory.history), 5)
        self.assertEqual(self.memory.metadata["total_turns"], 10)

        # Check that it's the last 5 turns
        history_list = list(self.memory.history)
        self.assertEqual(history_list[0]["user_input"], "Message 5")
        self.assertEqual(history_list[-1]["user_input"], "Message 9")

    def test_get_recent_context(self):
        """Test retrieving recent conversation context."""
        # Add some turns
        for i in range(3):
            self.memory.add_turn(f"Message {i}", f"Response {i}")

        # Get recent context
        recent = self.memory.get_recent_context(2)
        self.assertEqual(len(recent), 2)
        self.assertEqual(recent[0]["user_input"], "Message 1")
        self.assertEqual(recent[1]["user_input"], "Message 2")

        # Test with more than available
        recent = self.memory.get_recent_context(10)
        self.assertEqual(len(recent), 3)

    def test_build_llm_context(self):
        """Test building context for LLM interactions."""
        # Add some conversation history
        self.memory.add_turn("What's your name?", "I'm Claude.")
        self.memory.add_turn("How are you?", "I'm doing well, thank you!")

        # Build context
        context = self.memory.build_llm_context("Tell me more about yourself")

        self.assertIn("Recent conversation:", context)
        self.assertIn("What's your name?", context)
        self.assertIn("I'm Claude.", context)
        self.assertIn("Current user query: Tell me more about yourself", context)

    def test_search_history(self):
        """Test searching through conversation history."""
        # Add some turns
        self.memory.add_turn("I love programming", "That's great!")
        self.memory.add_turn("Python is my favorite", "Python is excellent!")
        self.memory.add_turn("What about Java?", "Java is also good.")

        # Search for "programming"
        results = self.memory.search_history("programming")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["user_input"], "I love programming")

        # Search for "Python"
        results = self.memory.search_history("Python")
        self.assertEqual(len(results), 1)  # Only one turn contains "Python"

        # Search for something in responses
        results = self.memory.search_history("excellent")
        self.assertEqual(len(results), 1)

        # Search for non-existent term
        results = self.memory.search_history("nonexistent")
        self.assertEqual(len(results), 0)

    def test_persistence(self):
        """Test saving and loading conversation memory."""
        # Add some data
        self.memory.add_turn("Test message", "Test response")
        self.memory.add_turn("Another message", "Another response")

        # Save manually (should auto-save anyway)
        self.memory.save()

        # Create new memory instance with same file
        new_memory = ConversationMemory(filepath=self.temp_file, max_turns=5)

        # Check that data was loaded
        self.assertEqual(len(new_memory.history), 2)
        self.assertEqual(new_memory.metadata["total_turns"], 2)
        self.assertEqual(new_memory.metadata["session_count"], 2)  # Incremented on load

        history_list = list(new_memory.history)
        self.assertEqual(history_list[0]["user_input"], "Test message")
        self.assertEqual(history_list[1]["user_input"], "Another message")

    def test_clear(self):
        """Test clearing conversation memory."""
        # Add some data
        self.memory.add_turn("Test", "Response")
        self.assertEqual(len(self.memory.history), 1)

        # Clear memory
        self.memory.clear()

        # Check everything is reset
        self.assertEqual(len(self.memory.history), 0)
        self.assertEqual(len(self.memory.summaries), 0)
        self.assertEqual(self.memory.metadata["total_turns"], 0)
        self.assertEqual(self.memory.metadata["session_count"], 1)

    def test_get_statistics(self):
        """Test getting conversation statistics."""
        # Add some turns
        self.memory.add_turn("Hello", "Hi")
        self.memory.add_turn("Bye", "Goodbye")

        stats = self.memory.get_statistics()

        self.assertEqual(stats["total_turns"], 2)
        self.assertEqual(stats["active_turns"], 2)
        self.assertEqual(stats["summary_count"], 0)
        self.assertEqual(stats["session_count"], 1)
        self.assertIn("conversation_id", stats)
        self.assertIn("created_at", stats)
        self.assertIn("updated_at", stats)

    def test_corrupted_file_handling(self):
        """Test handling of corrupted JSON files."""
        # Create a corrupted JSON file
        with open(self.temp_file, "w") as f:
            f.write("{invalid json")

        # Should handle gracefully and start fresh
        memory = ConversationMemory(filepath=self.temp_file, max_turns=5)
        self.assertEqual(len(memory.history), 0)

    def test_backup_creation(self):
        """Test that backup files are created."""
        # Add data and save
        self.memory.add_turn("Test", "Response")
        self.memory.save()

        # Modify and save again (should create backup)
        self.memory.add_turn("Test2", "Response2")
        self.memory.save()

        # Check backup exists
        backup_file = self.temp_file + ".bak"
        self.assertTrue(os.path.exists(backup_file))

    def test_create_summary(self):
        """Test creating conversation summaries."""
        # Add some turns
        for i in range(3):
            self.memory.add_turn(f"Message {i}", f"Response {i}")

        # Create summary
        summary = self.memory.create_summary(0, 2)

        self.assertIn("summary_id", summary)
        self.assertIn("created_at", summary)
        self.assertIn("turn_count", summary)
        self.assertEqual(summary["turn_count"], 2)
        self.assertEqual(len(self.memory.summaries), 1)

    def test_context_with_summaries(self):
        """Test context building with summaries."""
        # Add a summary
        self.memory.summaries.append(
            {"summary_id": "test", "content": "Previous discussion about weather", "created_at": "2024-01-01T00:00:00Z"}
        )

        # Add recent turns
        self.memory.add_turn("What's the weather?", "It's sunny today.")

        # Build context with summaries
        context = self.memory.build_llm_context("Tell me more", include_summaries=True)

        self.assertIn("Previous conversation summary:", context)
        self.assertIn("Previous discussion about weather", context)
        self.assertIn("Recent conversation:", context)

    def test_memory_with_metadata(self):
        """Test adding turns with custom metadata."""
        metadata = {"priority": "high", "category": "support"}
        turn = self.memory.add_turn("Help me", "How can I help?", metadata=metadata)

        self.assertEqual(turn["metadata"], metadata)

        # Check persistence
        self.memory.save()
        new_memory = ConversationMemory(filepath=self.temp_file, max_turns=5)
        history_list = list(new_memory.history)
        self.assertEqual(history_list[0]["metadata"], metadata)


class TestConversationMemoryEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""

    def test_nonexistent_directory(self):
        """Test creating memory with nonexistent directory."""
        nonexistent_path = "/nonexistent/directory/memory.json"

        # Should create directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = os.path.join(temp_dir, "nested", "dir", "memory.json")
            memory = ConversationMemory(filepath=nested_path, max_turns=5)
            memory.add_turn("Test", "Response")

            # Check file was created
            self.assertTrue(os.path.exists(nested_path))

    def test_empty_inputs(self):
        """Test handling of empty inputs."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            temp_file = f.name

        try:
            memory = ConversationMemory(filepath=temp_file, max_turns=5)

            # Test empty strings
            turn = memory.add_turn("", "")
            self.assertEqual(turn["user_input"], "")
            self.assertEqual(turn["agent_response"], "")

            # Test context building with empty history
            context = memory.build_llm_context("")
            self.assertIn("Current user query:", context)

        finally:
            os.unlink(temp_file)

    def test_zero_max_turns(self):
        """Test memory with zero max turns."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            temp_file = f.name

        try:
            memory = ConversationMemory(filepath=temp_file, max_turns=0)

            # Should still work but keep no history
            memory.add_turn("Test", "Response")
            self.assertEqual(len(memory.history), 0)
            self.assertEqual(memory.metadata["total_turns"], 1)

        finally:
            os.unlink(temp_file)


if __name__ == "__main__":
    unittest.main()
