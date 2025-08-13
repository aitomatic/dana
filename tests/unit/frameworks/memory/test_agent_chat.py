"""
Unit tests for agent chat functionality with conversation memory.
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from dana.agent.agent_instance import AgentInstance, AgentType
from dana.core.lang.sandbox_context import SandboxContext


class TestAgentChat(unittest.TestCase):
    """Test cases for agent chat functionality."""

    def setUp(self):
        """Set up test cases."""
        self.temp_dir = tempfile.mkdtemp()
        # Create chats directory in temp (mimicking ~/.dana/chats/)
        self.memory_dir = Path(self.temp_dir) / ".dana" / "chats"
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        # Patch the memory initialization to use temp directory
        def mock_init(agent_self):
            if agent_self._conversation_memory is None:
                from dana.frameworks.memory.conversation_memory import ConversationMemory

                # Use temp directory instead of ~/.dana/chats/
                agent_name = getattr(agent_self.agent_type, "name", "agent")
                memory_file = self.memory_dir / f"{agent_name}_conversation.json"
                agent_self._conversation_memory = ConversationMemory(filepath=str(memory_file), max_turns=20)

        self.init_patcher = patch.object(AgentInstance, "_initialize_conversation_memory", mock_init)
        self.init_patcher.start()

        # Create a sandbox context for testing
        self.sandbox_context = SandboxContext()

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

        agent_type = AgentType(name=name, fields=fields, field_order=list(fields.keys()), field_comments={})

        return AgentInstance(agent_type, fields)

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
        # Mock the sandbox context to return no LLM resources to force fallback behavior
        with patch.object(self.sandbox_context, "get_resources", return_value={}):
            agent = self.create_test_agent()

            # Test greeting - chat now returns a Promise
            response_promise = agent.chat(self.sandbox_context, "Hello!")
            response = response_promise._wait_for_delivery()
            self.assertIn("Hello", response)
            self.assertIn("TestAgent", response)

            # Memory should now be initialized
            self.assertIsNotNone(agent._conversation_memory)

            # Test name query
            response_promise = agent.chat(self.sandbox_context, "What's your name?")
            response = response_promise._wait_for_delivery()
            self.assertIn("TestAgent", response)

            # Test memory query
            response_promise = agent.chat(self.sandbox_context, "Do you remember what I said?")
            response = response_promise._wait_for_delivery()
            self.assertTrue("hello" in response.lower() or "remember" in response.lower())

    def test_chat_with_mock_llm(self):
        """Test chat functionality with mock LLM."""
        agent = self.create_test_agent()

        # Create mock LLM resource
        mock_llm_resource = Mock()
        mock_llm_resource.kind = "llm"  # Set the kind attribute
        from dana.common.types import BaseResponse

        mock_llm_resource.query_sync.return_value = BaseResponse(success=True, content="This is a mock LLM response.")

        # Mock the get_resources method to return our mock LLM resource
        with patch.object(self.sandbox_context, "get_resources", return_value={"test_llm": mock_llm_resource}):
            # Chat with agent
            response_promise = agent.chat(self.sandbox_context, "Tell me about yourself")
            response = response_promise._wait_for_delivery()

            # Should use LLM
            self.assertEqual(response, "This is a mock LLM response.")
            mock_llm_resource.query_sync.assert_called_once()

            # Check that prompt contains agent description
            call_args = mock_llm_resource.query_sync.call_args[0][0]
            # Look for agent description in system message
            messages = call_args.arguments["messages"]
            system_messages = [msg for msg in messages if msg["role"] == "system"]
            self.assertTrue(len(system_messages) > 0)
            self.assertIn("You are TestAgent", system_messages[0]["content"])

    def test_llm_field_detection(self):
        """Test that LLM is detected from agent fields."""
        # This test needs to be updated since LLM is now handled through resources
        # rather than direct field detection
        agent = self.create_test_agent(fields={"llm": "some_llm_value"})

        # Mock LLM resource
        mock_llm_resource = Mock()
        mock_llm_resource.kind = "llm"  # Set the kind attribute
        from dana.common.types import BaseResponse

        mock_llm_resource.query_sync.return_value = BaseResponse(success=True, content="LLM field response")

        # Mock the get_resources method to return our mock LLM resource
        with patch.object(self.sandbox_context, "get_resources", return_value={"test_llm": mock_llm_resource}):
            response_promise = agent.chat(self.sandbox_context, "Test message")
            response = response_promise._wait_for_delivery()

            self.assertEqual(response, "LLM field response")
            mock_llm_resource.query_sync.assert_called_once()

    def test_default_llm_resource(self):
        """Test that agents try to use default LLMResource."""
        # Mock the sandbox context to return no LLM resources to force fallback behavior
        with patch.object(self.sandbox_context, "get_resources", return_value={}):
            agent = self.create_test_agent()

            response_promise = agent.chat(self.sandbox_context, "Hello")
            response = response_promise._wait_for_delivery()

            # Should fall back to simple responses
            self.assertIn("Hello", response)
            self.assertIn("TestAgent", response)

    def test_conversation_persistence(self):
        """Test that conversations persist across agent instances."""
        # Mock the sandbox context to return no LLM resources to force fallback behavior
        with patch.object(self.sandbox_context, "get_resources", return_value={}):
            # First agent instance
            agent1 = self.create_test_agent()
            agent1.chat(self.sandbox_context, "My name is Alice")._wait_for_delivery()
            agent1.chat(self.sandbox_context, "I like programming")._wait_for_delivery()

            # Second agent instance (same type)
            agent2 = self.create_test_agent()
            response_promise = agent2.chat(self.sandbox_context, "Do you remember my name?")
            response = response_promise._wait_for_delivery()

            # Should remember from previous session
            self.assertTrue("alice" in response.lower() or "programming" in response.lower())

    def test_multiple_agent_separation(self):
        """Test that different agent types maintain separate conversations."""
        # Mock the sandbox context to return no LLM resources to force fallback behavior
        with patch.object(self.sandbox_context, "get_resources", return_value={}):
            # Create two different agent types
            agent1 = self.create_test_agent("Agent1", {"role": "support"})
            agent2 = self.create_test_agent("Agent2", {"role": "sales"})

            # Have different conversations
            agent1.chat(self.sandbox_context, "I have a technical problem")._wait_for_delivery()
            agent2.chat(self.sandbox_context, "I want to buy something")._wait_for_delivery()

            # Check that memories are separate
            response_promise1 = agent1.chat(self.sandbox_context, "What did we talk about?")
            response1 = response_promise1._wait_for_delivery()
            response_promise2 = agent2.chat(self.sandbox_context, "What did we talk about?")
            response2 = response_promise2._wait_for_delivery()

            # Each should only remember their own conversation
            self.assertNotEqual(response1, response2)

    def test_conversation_statistics(self):
        """Test getting conversation statistics."""
        agent = self.create_test_agent()

        # Initially no stats
        stats = agent.get_conversation_stats()
        self.assertIn("error", stats)

        # After chatting
        agent.chat(self.sandbox_context, "Hello")._wait_for_delivery()
        agent.chat(self.sandbox_context, "How are you?")._wait_for_delivery()

        stats = agent.get_conversation_stats()
        self.assertEqual(stats["total_turns"], 2)
        self.assertEqual(stats["active_turns"], 2)
        self.assertIn("conversation_id", stats)

    def test_clear_conversation_memory(self):
        """Test clearing conversation memory."""
        agent = self.create_test_agent()

        # Add some conversation
        agent.chat(self.sandbox_context, "Hello")._wait_for_delivery()
        agent.chat(self.sandbox_context, "Test message")._wait_for_delivery()

        # Clear memory
        result = agent.clear_conversation_memory()
        self.assertTrue(result)

        # Memory should be reset
        stats = agent.get_conversation_stats()
        self.assertEqual(stats["total_turns"], 0)

    def test_chat_with_context(self):
        """Test chat with additional context."""
        mock_llm_resource = Mock()
        mock_llm_resource.kind = "llm"  # Set the kind attribute
        from dana.common.types import BaseResponse

        mock_llm_resource.query_sync.return_value = BaseResponse(success=True, content="Contextual response")
        agent = self.create_test_agent()

        # Mock the get_resources method to return our mock LLM resource
        with patch.object(self.sandbox_context, "get_resources", return_value={"test_llm": mock_llm_resource}):
            # Chat with additional context
            context = {"priority": "high", "category": "support"}
            response_promise = agent.chat(self.sandbox_context, "Help me", context=context)
            _ = response_promise._wait_for_delivery()

            # Check that context was included in prompt
            call_args = mock_llm_resource.query_sync.call_args[0][0]
            # Look for context in system message
            messages = call_args.arguments["messages"]
            system_messages = [msg for msg in messages if msg["role"] == "system"]
            system_content = system_messages[0]["content"] if system_messages else ""
            self.assertIn("Additional context", system_content)
            self.assertIn("priority", system_content)

    def test_max_context_turns(self):
        """Test limiting context turns."""
        mock_llm_resource = Mock()
        mock_llm_resource.kind = "llm"  # Set the kind attribute
        from dana.common.types import BaseResponse

        mock_llm_resource.query_sync.return_value = BaseResponse(success=True, content="Limited context response")
        agent = self.create_test_agent()

        # Mock the get_resources method to return our mock LLM resource
        with patch.object(self.sandbox_context, "get_resources", return_value={"test_llm": mock_llm_resource}):
            # Add several turns
            for i in range(5):
                agent.chat(self.sandbox_context, f"Message {i}")._wait_for_delivery()

            # Chat with limited context
            agent.chat(self.sandbox_context, "New message", max_context_turns=2)._wait_for_delivery()

            # Check that only recent turns are included
            call_args = mock_llm_resource.query_sync.call_args[0][0]
            # Look for messages in system message context
            messages = call_args.arguments["messages"]
            all_content = " ".join([msg["content"] for msg in messages])
            self.assertIn("Message 3", all_content)
            self.assertIn("Message 4", all_content)
            self.assertNotIn("Message 0", all_content)
            self.assertNotIn("Message 1", all_content)

    def test_llm_error_handling(self):
        """Test handling of LLM errors."""
        # Create LLM that throws an error
        mock_llm_resource = Mock()
        mock_llm_resource.kind = "llm"  # Set the kind attribute
        mock_llm_resource.query_sync.side_effect = Exception("LLM error")
        agent = self.create_test_agent()

        # Mock the get_resources method to return our mock LLM resource
        with patch.object(self.sandbox_context, "get_resources", return_value={"test_llm": mock_llm_resource}):
            response_promise = agent.chat(self.sandbox_context, "Test message")
            response = response_promise._wait_for_delivery()

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
        # Mock the sandbox context to return no LLM resources to force fallback behavior
        with patch.object(self.sandbox_context, "get_resources", return_value={}):
            agent = self.create_test_agent()

            # Test different types of queries
            test_cases = [
                ("hello", "hello"),
                ("what's your name", "testagent"),
                ("can you help", "chat"),  # Response mentions chat capability
                ("remember", "remember"),
            ]

            for query, expected_in_response in test_cases:
                response_promise = agent.chat(self.sandbox_context, query)
                response = response_promise._wait_for_delivery()
                self.assertIn(expected_in_response.lower(), response.lower())

    def test_memory_initialization_lazy(self):
        """Test that memory is initialized lazily."""
        agent = self.create_test_agent()

        # Memory should be None initially
        self.assertIsNone(agent._conversation_memory)

        # After first chat, memory should be initialized
        agent.chat(self.sandbox_context, "Hello")._wait_for_delivery()
        self.assertIsNotNone(agent._conversation_memory)

    def test_agent_fields_in_context(self):
        """Test that agent fields are included in context."""
        mock_llm_resource = Mock()
        mock_llm_resource.kind = "llm"  # Set the kind attribute
        from dana.common.types import BaseResponse

        mock_llm_resource.query_sync.return_value = BaseResponse(success=True, content="Response with fields")
        agent = self.create_test_agent("FieldAgent", {"department": "engineering", "specialty": "AI"})

        # Mock the get_resources method to return our mock LLM resource
        with patch.object(self.sandbox_context, "get_resources", return_value={"test_llm": mock_llm_resource}):
            agent.chat(self.sandbox_context, "Test")._wait_for_delivery()

            call_args = mock_llm_resource.query_sync.call_args[0][0]
            # With first message, agent characteristics should be in system prompt
            messages = call_args.arguments["messages"]
            system_messages = [msg for msg in messages if msg["role"] == "system"]
            self.assertTrue(len(system_messages) > 0)
            self.assertIn("FieldAgent", system_messages[0]["content"])


class TestAgentChatIntegration(unittest.TestCase):
    """Integration tests for agent chat functionality."""

    def setUp(self):
        """Set up integration tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.sandbox_context = SandboxContext()

    def tearDown(self):
        """Clean up integration tests."""
        # Clean up temp files
        for file in Path(self.temp_dir).glob("*.json*"):
            file.unlink()
        os.rmdir(self.temp_dir)

    def test_full_conversation_flow(self):
        """Test a complete conversation flow."""
        # Mock the sandbox context to return no LLM resources to force fallback behavior
        with patch.object(self.sandbox_context, "get_resources", return_value={}):
            agent_type = AgentType(
                name="ConversationAgent",
                fields={"role": "assistant", "domain": "general"},
                field_order=["role", "domain"],
                field_comments={},
            )

            agent = AgentInstance(agent_type, {"role": "assistant", "domain": "general"})

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
                response_promise = agent.chat(self.sandbox_context, message)
                response = response_promise._wait_for_delivery()
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
        # Mock the sandbox context to return no LLM resources to force fallback behavior
        with patch.object(self.sandbox_context, "get_resources", return_value={}):
            # Create specialized agent types
            support_type = AgentType(
                name="SupportAgent",
                fields={"department": "technical", "expertise": "troubleshooting"},
                field_order=["department", "expertise"],
                field_comments={},
            )

            sales_type = AgentType(
                name="SalesAgent", fields={"region": "north", "products": "software"}, field_order=["region", "products"], field_comments={}
            )

            support_agent = AgentInstance(support_type, {"department": "technical", "expertise": "troubleshooting"})

            sales_agent = AgentInstance(sales_type, {"region": "north", "products": "software"})

            # Test that they identify differently
            support_response_promise = support_agent.chat(self.sandbox_context, "Who are you?")
            support_response = support_response_promise._wait_for_delivery()
            sales_response_promise = sales_agent.chat(self.sandbox_context, "Who are you?")
            sales_response = sales_response_promise._wait_for_delivery()

            self.assertIn("SupportAgent", support_response)
            self.assertIn("SalesAgent", sales_response)
            self.assertNotEqual(support_response, sales_response)


if __name__ == "__main__":
    unittest.main()
