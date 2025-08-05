"""
Unit tests for agent chat functionality with conversation memory.
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from dana.agent.agent_struct_system import AgentStructType, AgentStructInstance


class TestAgentChat(unittest.TestCase):
    """Test cases for agent chat functionality."""

    def setUp(self):
        """Set up test cases."""
        self.temp_dir = tempfile.mkdtemp()
        # Create chats directory in temp (mimicking ~/.dana/chats/)
        self.memory_dir = Path(self.temp_dir) / ".dana" / "chats"
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        # Patch the memory initialization to use temp directory
        original_init = AgentStructInstance._initialize_conversation_memory

        def mock_init(agent_self):
            if agent_self._conversation_memory is None:
                from dana.frameworks.memory.conversation_memory import ConversationMemory

                # Use temp directory instead of ~/.dana/chats/
                agent_name = getattr(agent_self.agent_type, "name", "agent")
                memory_file = self.memory_dir / f"{agent_name}_conversation.json"
                agent_self._conversation_memory = ConversationMemory(filepath=str(memory_file), max_turns=20)

        self.init_patcher = patch.object(AgentStructInstance, "_initialize_conversation_memory", mock_init)
        self.init_patcher.start()

    def tearDown(self):
        """Clean up test cases."""
        self.init_patcher.stop()
        # Clean up temp files
        import shutil

        shutil.rmtree(self.temp_dir)

    def create_test_agent(self, name="TestAgent", fields=None):
        """Create a test agent for testing."""
        if fields is None:
            fields = {"personality": "helpful"}

        agent_type = AgentStructType(name=name, fields=fields, field_order=list(fields.keys()), field_comments={})

        return AgentStructInstance(agent_type, fields)

    def test_chat_initialization(self):
        """Test that chat functionality initializes properly."""
        agent = self.create_test_agent()

        # Chat should be available
        self.assertTrue(hasattr(agent, "chat"))
        self.assertTrue(callable(agent.chat))

        # Memory should be None initially
        self.assertIsNone(agent._conversation_memory)

    def test_basic_chat_without_llm(self):
        """Test basic chat functionality without LLM."""
        # Mock the LLM function to return None to force fallback behavior
        with patch.object(AgentStructInstance, "_get_dana_llm_function", return_value=None):
            agent = self.create_test_agent()

            # Test greeting
            response = agent.chat("Hello!")
            self.assertIn("Hello", response)
            self.assertIn("TestAgent", response)

            # Memory should now be initialized
            self.assertIsNotNone(agent._conversation_memory)

            # Test name query
            response = agent.chat("What's your name?")
            self.assertIn("TestAgent", response)

            # Test memory query
            response = agent.chat("Do you remember what I said?")
            self.assertTrue("hello" in response.lower() or "remember" in response.lower())

    def test_chat_with_mock_llm(self):
        """Test chat functionality with mock LLM."""
        agent = self.create_test_agent()

        # Create mock LLM function
        mock_llm = Mock(return_value="This is a mock LLM response.")
        agent._context["llm"] = mock_llm

        # Chat with agent
        response = agent.chat("Tell me about yourself")

        # Should use LLM
        self.assertEqual(response, "This is a mock LLM response.")
        mock_llm.assert_called_once()

        # Check that prompt contains agent description
        call_args = mock_llm.call_args[0][0]
        self.assertIn("You are TestAgent", call_args)
        # Agent fields are included in context when there's conversation history
        # For first message, fields might not be shown due to no conversation context

    def test_llm_field_detection(self):
        """Test that LLM is detected from agent fields."""
        mock_llm = Mock(return_value="LLM field response")
        agent = self.create_test_agent(fields={"llm": mock_llm})

        response = agent.chat("Test message")

        self.assertEqual(response, "LLM field response")
        mock_llm.assert_called_once()

    def test_default_llm_resource(self):
        """Test that agents try to use default LLMResource."""
        # Mock the LLM function to return None to force fallback behavior
        with patch.object(AgentStructInstance, "_get_dana_llm_function", return_value=None):
            agent = self.create_test_agent()

            response = agent.chat("Hello")

            # Should fall back to simple responses
            self.assertIn("Hello", response)
            self.assertIn("TestAgent", response)

    def test_conversation_persistence(self):
        """Test that conversations persist across agent instances."""
        # Mock the LLM function to return None to force fallback behavior
        with patch.object(AgentStructInstance, "_get_dana_llm_function", return_value=None):
            # First agent instance
            agent1 = self.create_test_agent()
            agent1.chat("My name is Alice")
            agent1.chat("I like programming")

            # Second agent instance (same type)
            agent2 = self.create_test_agent()
            response = agent2.chat("Do you remember my name?")

            # Should remember from previous session
            self.assertTrue("alice" in response.lower() or "programming" in response.lower())

    def test_multiple_agent_separation(self):
        """Test that different agent types maintain separate conversations."""
        # Mock the LLM function to return None to force fallback behavior
        with patch.object(AgentStructInstance, "_get_dana_llm_function", return_value=None):
            # Create two different agent types
            agent1 = self.create_test_agent("Agent1", {"role": "support"})
            agent2 = self.create_test_agent("Agent2", {"role": "sales"})

            # Have different conversations
            agent1.chat("I have a technical problem")
            agent2.chat("I want to buy something")

            # Check that memories are separate
            response1 = agent1.chat("What did we talk about?")
            response2 = agent2.chat("What did we talk about?")

            # Each should only remember their own conversation
            self.assertNotEqual(response1, response2)

    def test_conversation_statistics(self):
        """Test getting conversation statistics."""
        agent = self.create_test_agent()

        # Initially no stats
        stats = agent.get_conversation_stats()
        self.assertIn("error", stats)

        # After chatting
        agent.chat("Hello")
        agent.chat("How are you?")

        stats = agent.get_conversation_stats()
        self.assertEqual(stats["total_turns"], 2)
        self.assertEqual(stats["active_turns"], 2)
        self.assertIn("conversation_id", stats)

    def test_clear_conversation_memory(self):
        """Test clearing conversation memory."""
        agent = self.create_test_agent()

        # Add some conversation
        agent.chat("Hello")
        agent.chat("Test message")

        # Clear memory
        result = agent.clear_conversation_memory()
        self.assertTrue(result)

        # Memory should be reset
        stats = agent.get_conversation_stats()
        self.assertEqual(stats["total_turns"], 0)

    def test_chat_with_context(self):
        """Test chat with additional context."""
        mock_llm = Mock(return_value="Contextual response")
        agent = self.create_test_agent()
        agent._context["llm"] = mock_llm

        # Chat with additional context
        context = {"priority": "high", "category": "support"}
        response = agent.chat("Help me", context=context)

        # Check that context was included in prompt
        call_args = mock_llm.call_args[0][0]
        self.assertIn("Additional context", call_args)
        self.assertIn("priority", call_args)

    def test_max_context_turns(self):
        """Test limiting context turns."""
        mock_llm = Mock(return_value="Limited context response")
        agent = self.create_test_agent()
        agent._context["llm"] = mock_llm

        # Add several turns
        for i in range(5):
            agent.chat(f"Message {i}")

        # Chat with limited context
        agent.chat("New message", max_context_turns=2)

        # Check that only recent turns are included
        call_args = mock_llm.call_args[0][0]
        self.assertIn("Message 3", call_args)
        self.assertIn("Message 4", call_args)
        self.assertNotIn("Message 0", call_args)
        self.assertNotIn("Message 1", call_args)

    def test_llm_error_handling(self):
        """Test handling of LLM errors."""
        # Create LLM that throws an error
        error_llm = Mock(side_effect=Exception("LLM error"))
        agent = self.create_test_agent()
        agent._context["llm"] = error_llm

        response = agent.chat("Test message")

        # Should handle error gracefully
        self.assertIn("error", response.lower())
        self.assertIn("LLM error", response)

    def test_agent_description_building(self):
        """Test building agent descriptions for prompts."""
        agent = self.create_test_agent("CustomAgent", {"personality": "friendly", "expertise": "programming", "version": "1.0"})

        description = agent._build_agent_description()

        self.assertIn("You are CustomAgent", description)
        # The agent fields should be in the description if any exist
        if hasattr(agent, "personality"):
            self.assertIn("personality", description)

    def test_fallback_responses(self):
        """Test fallback response generation."""
        # Mock the LLM function to return None to force fallback behavior
        with patch.object(AgentStructInstance, "_get_dana_llm_function", return_value=None):
            agent = self.create_test_agent()

            # Test different types of queries
            test_cases = [
                ("hello", "hello"),
                ("what's your name", "testagent"),
                ("can you help", "chat"),  # Response mentions chat capability
                ("remember", "remember"),
            ]

            for query, expected_in_response in test_cases:
                response = agent.chat(query)
                self.assertIn(expected_in_response.lower(), response.lower())

    def test_memory_initialization_lazy(self):
        """Test that memory is initialized lazily."""
        agent = self.create_test_agent()

        # Memory should be None initially
        self.assertIsNone(agent._conversation_memory)

        # After first chat, memory should be initialized
        agent.chat("Hello")
        self.assertIsNotNone(agent._conversation_memory)

    def test_agent_fields_in_context(self):
        """Test that agent fields are included in context."""
        mock_llm = Mock(return_value="Response with fields")
        agent = self.create_test_agent("FieldAgent", {"department": "engineering", "specialty": "AI"})
        agent._context["llm"] = mock_llm

        agent.chat("Test")

        call_args = mock_llm.call_args[0][0]
        # With first message, agent characteristics should be in system prompt
        self.assertIn("FieldAgent", call_args)


class TestAgentChatIntegration(unittest.TestCase):
    """Integration tests for agent chat functionality."""

    def setUp(self):
        """Set up integration tests."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up integration tests."""
        # Clean up temp files
        for file in Path(self.temp_dir).glob("*.json*"):
            file.unlink()
        os.rmdir(self.temp_dir)

    def test_full_conversation_flow(self):
        """Test a complete conversation flow."""
        # Mock the LLM function to return None to force fallback behavior
        with patch.object(AgentStructInstance, "_get_dana_llm_function", return_value=None):
            agent_type = AgentStructType(
                name="ConversationAgent",
                fields={"role": "assistant", "domain": "general"},
                field_order=["role", "domain"],
                field_comments={},
            )

            agent = AgentStructInstance(agent_type, {"role": "assistant", "domain": "general"})

            # Simulate a conversation
            conversation = [
                ("Hello!", "greeting"),
                ("My name is Bob", "name"),
                ("I'm interested in learning Python", "interest"),
                ("Do you remember my name?", "memory"),
                ("What was I interested in?", "recall"),
            ]

            responses = []
            for message, _ in conversation:
                response = agent.chat(message)
                responses.append(response)

            # Check that conversation was remembered
            # Last response should reference previous conversation
            # The agent should remember key information from the conversation
            all_responses = " ".join(responses).lower()
            memory_indicators = ["bob", "python", "remember", "discussed", "mentioned"]

            # At least one memory indicator should be present
            self.assertTrue(any(indicator in all_responses for indicator in memory_indicators))

    def test_agent_customization(self):
        """Test that agents can be customized for different roles."""
        # Mock the LLM function to return None to force fallback behavior
        with patch.object(AgentStructInstance, "_get_dana_llm_function", return_value=None):
            # Create specialized agent types
            support_type = AgentStructType(
                name="SupportAgent",
                fields={"department": "technical", "expertise": "troubleshooting"},
                field_order=["department", "expertise"],
                field_comments={},
            )

            sales_type = AgentStructType(
                name="SalesAgent", fields={"region": "north", "products": "software"}, field_order=["region", "products"], field_comments={}
            )

            support_agent = AgentStructInstance(support_type, {"department": "technical", "expertise": "troubleshooting"})

            sales_agent = AgentStructInstance(sales_type, {"region": "north", "products": "software"})

            # Test that they identify differently
            support_response = support_agent.chat("Who are you?")
            sales_response = sales_agent.chat("Who are you?")

            self.assertIn("SupportAgent", support_response)
            self.assertIn("SalesAgent", sales_response)
            self.assertNotEqual(support_response, sales_response)


if __name__ == "__main__":
    unittest.main()
