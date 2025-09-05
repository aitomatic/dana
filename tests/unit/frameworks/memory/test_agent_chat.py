"""
Unit tests for agent chat functionality with conversation memory.
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from dana.core.agent import AgentInstance, AgentType
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
                from dana.core.agent.mind.memory.conversation import ConversationMemory

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
        import os
        import shutil

        # Clean up any temporary files created by ConversationMemory
        if hasattr(self, "memory_dir") and self.memory_dir.exists():
            for file_path in self.memory_dir.iterdir():
                if file_path.is_file():
                    try:
                        file_path.unlink()
                    except OSError:
                        pass  # File might already be deleted

        # Clean up temp directory
        try:
            shutil.rmtree(self.temp_dir)
        except OSError as e:
            # If directory is not empty, try to remove files individually
            if e.errno == 39:  # Directory not empty
                for root, dirs, files in os.walk(self.temp_dir, topdown=False):
                    for file in files:
                        try:
                            os.remove(os.path.join(root, file))
                        except OSError:
                            pass
                    for dir in dirs:
                        try:
                            os.rmdir(os.path.join(root, dir))
                        except OSError:
                            pass
                try:
                    os.rmdir(self.temp_dir)
                except OSError:
                    pass  # Final cleanup attempt

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
        """Test basic chat functionality without LLM (fallback responses)."""

        # Mock the sandbox context to return no LLM resources to force fallback behavior
        with patch.object(self.sandbox_context, "get_resources", return_value={}):
            # Also mock the agent's own LLM resource to return None (no LLM available)
            with patch.object(AgentInstance, "get_llm_resource", return_value=None):
                agent = self.create_test_agent()

                # Test greeting - chat now returns the actual result directly
                response = agent.chat_sync("Hello!", sandbox_context=self.sandbox_context)
                self.assertIn("Hello", response)
                self.assertIn("TestAgent", response)

                # Memory should now be initialized
                self.assertIsNotNone(agent._conversation_memory)

                # Test name query
                response = agent.chat_sync("What's your name?", sandbox_context=self.sandbox_context)
                self.assertIn("TestAgent", response)

                # Test memory query
                response = agent.chat_sync("Do you remember what I said?", sandbox_context=self.sandbox_context)
                self.assertTrue("hello" in response.lower() or "remember" in response.lower())

    def test_chat_with_mock_llm(self):
        """Test chat functionality with mock LLM."""

        agent = self.create_test_agent()

        # Create mock LLM resource
        mock_llm_resource = Mock()
        mock_llm_resource.kind = "llm"  # Set the kind attribute
        mock_llm_resource.chat_completion.return_value = "This is a mock LLM response."

        # Mock the sandbox context to return our mock LLM resource
        with patch.object(self.sandbox_context, "get_system_llm_resource", return_value=mock_llm_resource):
            # Chat with agent - now returns a Promise that needs to be resolved
            response = agent.chat_sync("Tell me about yourself", sandbox_context=self.sandbox_context)

            # Resolve the promise to get the actual response

            # Should use LLM
            self.assertEqual(response, "This is a mock LLM response.")
            mock_llm_resource.chat_completion.assert_called_once()

            # Check that prompt contains agent description
            call_args = mock_llm_resource.chat_completion.call_args
            system_prompt = call_args[1]["system_prompt"]
            self.assertIn("You are TestAgent", system_prompt)

    def test_llm_field_detection(self):
        """Test that LLM is detected from agent fields."""

        # This test needs to be updated since LLM is now handled through resources
        # rather than direct field detection
        agent = self.create_test_agent(fields={"llm": "some_llm_value"})

        # Mock LLM resource
        mock_llm_resource = Mock()
        mock_llm_resource.kind = "llm"  # Set the kind attribute
        mock_llm_resource.chat_completion.return_value = "LLM field response"

        # Mock the sandbox context to return our mock LLM resource
        with patch.object(self.sandbox_context, "get_system_llm_resource", return_value=mock_llm_resource):
            response = agent.chat_sync("Test message", sandbox_context=self.sandbox_context)

            # Resolve the promise to get the actual response

            self.assertEqual(response, "LLM field response")
            mock_llm_resource.chat_completion.assert_called_once()

    def test_default_llm_resource(self):
        """Test that agents try to use default LLMResource."""

        # Mock the sandbox context to return no LLM resources to force fallback behavior
        with patch.object(self.sandbox_context, "get_resources", return_value={}):
            # Also mock the agent's own LLM resource to return None (no LLM available)
            with patch.object(AgentInstance, "get_llm_resource", return_value=None):
                agent = self.create_test_agent()

                response = agent.chat_sync("Hello", sandbox_context=self.sandbox_context)

                # Should fall back to simple responses
                self.assertIn("Hello", response)
                self.assertIn("TestAgent", response)

    def test_conversation_persistence(self):
        """Test that conversations persist across agent instances."""
        # Mock the sandbox context to return no LLM resources to force fallback behavior
        with patch.object(self.sandbox_context, "get_resources", return_value={}):
            # Also mock the agent's own LLM resource to return None (no LLM available)
            with patch.object(AgentInstance, "get_llm_resource", return_value=None):
                # First agent instance
                agent1 = self.create_test_agent("Agent1")
                response1 = agent1.chat_sync("My name is Alice", sandbox_context=self.sandbox_context)
                if hasattr(response1, "_wait_for_delivery"):
                    response1._wait_for_delivery()
                response2 = agent1.chat_sync("I like programming", sandbox_context=self.sandbox_context)
                if hasattr(response2, "_wait_for_delivery"):
                    response2._wait_for_delivery()

                # Second agent instance (should have separate memory)
                agent2 = self.create_test_agent("Agent2")
                response3 = agent2.chat_sync("My name is Bob", sandbox_context=self.sandbox_context)
                if hasattr(response3, "_wait_for_delivery"):
                    response3._wait_for_delivery()

                # Check that agents have separate conversation memories
                self.assertNotEqual(agent1._conversation_memory, agent2._conversation_memory)

                # Check conversation statistics
                stats1 = agent1.get_conversation_stats()
                stats2 = agent2.get_conversation_stats()

                # Each chat call creates 1 turn (user message + agent response = 1 turn)
                self.assertEqual(stats1["total_messages"], 2)  # 2 turns
                self.assertEqual(stats2["total_messages"], 1)  # 1 turn

    def test_multiple_agent_separation(self):
        """Test that different agent types maintain separate conversations."""
        # Mock the sandbox context to return no LLM resources to force fallback behavior
        with patch.object(self.sandbox_context, "get_resources", return_value={}):
            # Also mock the agent's own LLM resource to return None (no LLM available)
            with patch.object(AgentInstance, "get_llm_resource", return_value=None):
                # Create two different agent types
                agent1 = self.create_test_agent("Agent1", {"role": "support"})
                agent2 = self.create_test_agent("Agent2", {"role": "sales"})

                # Have different conversations
                agent1.chat_sync("I have a technical problem", sandbox_context=self.sandbox_context)
                agent2.chat_sync("I want to buy something", sandbox_context=self.sandbox_context)

                # Check that memories are separate
                response1 = agent1.chat_sync("What did we talk about?", sandbox_context=self.sandbox_context)
                response2 = agent2.chat_sync("What did we talk about?", sandbox_context=self.sandbox_context)

                # Each should only remember their own conversation
                self.assertNotEqual(response1, response2)

    def test_conversation_statistics(self):
        """Test conversation statistics tracking."""
        # Mock the sandbox context to return no LLM resources to force fallback behavior
        with patch.object(self.sandbox_context, "get_resources", return_value={}):
            # Also mock the agent's own LLM resource to return None (no LLM available)
            with patch.object(AgentInstance, "get_llm_resource", return_value=None):
                agent = self.create_test_agent("TestAgentStats")

                # Initial stats should show no messages
                initial_stats = agent.get_conversation_stats()
                self.assertEqual(initial_stats["total_messages"], 0)

                # Send a message
                response = agent.chat_sync("Hello", sandbox_context=self.sandbox_context)

                # Wait for the Promise to resolve to ensure conversation memory is updated
                if hasattr(response, "_wait_for_delivery"):
                    response._wait_for_delivery()

                # Stats should now show one message
                updated_stats = agent.get_conversation_stats()
                self.assertEqual(updated_stats["total_messages"], 1)

    def test_clear_conversation_memory(self):
        """Test clearing conversation memory."""
        # Mock the sandbox context to return no LLM resources to force fallback behavior
        with patch.object(self.sandbox_context, "get_resources", return_value={}):
            # Also mock the agent's own LLM resource to return None (no LLM available)
            with patch.object(AgentInstance, "get_llm_resource", return_value=None):
                agent = self.create_test_agent("TestAgentClear")

                # Send a message to initialize memory
                response = agent.chat_sync("Hello", sandbox_context=self.sandbox_context)

                # Wait for the Promise to resolve to ensure conversation memory is updated
                if hasattr(response, "_wait_for_delivery"):
                    response._wait_for_delivery()

                # Check that memory is initialized
                self.assertIsNotNone(agent._conversation_memory)
                initial_stats = agent.get_conversation_stats()
                self.assertEqual(initial_stats["total_messages"], 1)

                # Clear memory
                success = agent.clear_conversation_memory()
                self.assertTrue(success)

                # Check that memory is cleared
                cleared_stats = agent.get_conversation_stats()
                self.assertEqual(cleared_stats["total_messages"], 0)

    def test_agent_fields_in_context(self):
        """Test that agent fields are available in context."""
        # Mock the sandbox context to return no LLM resources to force fallback behavior
        with patch.object(self.sandbox_context, "get_resources", return_value={}):
            # Also mock the agent's own LLM resource to return None (no LLM available)
            with patch.object(AgentInstance, "get_llm_resource", return_value=None):
                # Create agent with custom fields
                agent = self.create_test_agent("CustomAgent", {"personality": "friendly", "expertise": "programming"})

                # Test that agent fields are accessible
                self.assertEqual(agent.agent_type.name, "CustomAgent")
                self.assertEqual(agent.personality, "friendly")
                self.assertEqual(agent.expertise, "programming")

                # Test chat functionality
                response = agent.chat_sync("Hello", sandbox_context=self.sandbox_context)
                self.assertIn("Hello", response)

    def test_chat_with_context(self):
        """Test chat functionality with additional context."""
        # Mock the sandbox context to return no LLM resources to force fallback behavior
        with patch.object(self.sandbox_context, "get_resources", return_value={}):
            # Also mock the agent's own LLM resource to return None (no LLM available)
            with patch.object(AgentInstance, "get_llm_resource", return_value=None):
                agent = self.create_test_agent()

                # Test chat with additional context
                context = {"user_id": "123", "session_id": "abc"}
                response = agent.chat_sync("Hello", context=context, sandbox_context=self.sandbox_context)

                # Should get a response
                self.assertIn("Hello", response)
                self.assertIn("TestAgent", response)

    def test_max_context_turns(self):
        """Test that conversation context is limited by max_context_turns."""
        # Mock the sandbox context to return no LLM resources to force fallback behavior
        with patch.object(self.sandbox_context, "get_resources", return_value={}):
            # Also mock the agent's own LLM resource to return None (no LLM available)
            with patch.object(AgentInstance, "get_llm_resource", return_value=None):
                agent = self.create_test_agent("TestAgentMaxTurns")

                # Send multiple messages to test context limiting
                for i in range(10):
                    response = agent.chat_sync(f"Message {i}", sandbox_context=self.sandbox_context)
                    # Wait for the Promise to resolve to ensure conversation memory is updated
                    if hasattr(response, "_wait_for_delivery"):
                        response._wait_for_delivery()

                # Check that conversation memory is maintained
                stats = agent.get_conversation_stats()
                self.assertEqual(stats["total_messages"], 10)

    def test_llm_error_handling(self):
        """Test error handling when LLM fails."""

        # Create mock LLM resource that raises an exception
        mock_llm_resource = Mock()
        mock_llm_resource.kind = "llm"
        mock_llm_resource.chat_completion.side_effect = Exception("LLM service unavailable")

        agent = self.create_test_agent()

        # Mock the sandbox context to return our mock LLM resource
        with patch.object(self.sandbox_context, "get_system_llm_resource", return_value=mock_llm_resource):
            # Chat should return an error message when LLM fails
            response = agent.chat_sync("Hello", sandbox_context=self.sandbox_context)

            # Resolve the promise to get the actual response

            # Should get an error message
            self.assertIn("error", response.lower())
            self.assertIn("llm", response.lower())

    def test_fallback_responses(self):
        """Test fallback responses when no LLM is available."""
        # Mock the sandbox context to return no LLM resources to force fallback behavior
        with patch.object(self.sandbox_context, "get_resources", return_value={}):
            # Also mock the agent's own LLM resource to return None (no LLM available)
            with patch.object(AgentInstance, "get_llm_resource", return_value=None):
                agent = self.create_test_agent()

                # Test various messages
                test_messages = ["Hello", "What's your name?", "Can you help me?", "What can you do?", "Tell me a joke"]

                for message in test_messages:
                    response = agent.chat_sync(message, sandbox_context=self.sandbox_context)

                    # With universal EagerPromise wrapping, response might be an EagerPromise
                    # Wait for the response to resolve
                    if hasattr(response, "_wait_for_delivery"):
                        response = response._wait_for_delivery()

                    # Should get a reasonable response
                    self.assertIsInstance(response, str)
                    self.assertGreater(len(response), 0)

    def test_memory_initialization_lazy(self):
        """Test that conversation memory is initialized lazily."""
        # Mock the sandbox context to return no LLM resources to force fallback behavior
        with patch.object(self.sandbox_context, "get_resources", return_value={}):
            # Also mock the agent's own LLM resource to return None (no LLM available)
            with patch.object(AgentInstance, "get_llm_resource", return_value=None):
                agent = self.create_test_agent()

                # Memory should not be initialized initially
                self.assertIsNone(agent._conversation_memory)

                # Send a message to trigger memory initialization
                response = agent.chat_sync("Hello")

                # Wait for the Promise to resolve to ensure conversation memory is updated
                if hasattr(response, "_wait_for_delivery"):
                    response._wait_for_delivery()

                # Memory should now be initialized
                self.assertIsNotNone(agent._conversation_memory)


class TestAgentChatIntegration(unittest.TestCase):
    """Integration tests for agent chat functionality."""

    def setUp(self):
        """Set up test environment."""
        self.sandbox_context = SandboxContext()

    def test_full_conversation_flow(self):
        """Test a complete conversation flow with multiple agents."""
        # Mock the sandbox context to return no LLM resources to force fallback behavior
        with patch.object(self.sandbox_context, "get_resources", return_value={}):
            # Also mock the agent's own LLM resource to return None (no LLM available)
            with patch.object(AgentInstance, "get_llm_resource", return_value=None):
                # Create two different agents
                support_agent_type = AgentType(
                    name="SupportAgent",
                    docstring="A helpful support agent",
                    fields={"domain": "str", "tasks": "str"},
                    field_order=["domain", "tasks"],
                )
                support_agent = AgentInstance(
                    struct_type=support_agent_type,
                    values={"domain": "customer support", "tasks": "help customers, resolve issues"},
                )

                tech_agent_type = AgentType(
                    name="TechAgent",
                    docstring="A technical specialist",
                    fields={"domain": "str", "tasks": "str"},
                    field_order=["domain", "tasks"],
                )
                tech_agent = AgentInstance(
                    struct_type=tech_agent_type,
                    values={"domain": "technical support", "tasks": "debug issues, provide technical guidance"},
                )

                # Simulate a conversation flow
                response = support_agent.chat_sync("I have a technical problem")
                # With Promise wrapping, we need to wait for the response
                if hasattr(response, "_wait_for_delivery"):
                    response = response._wait_for_delivery()
                # With fallback responses, we just check that we get a response
                self.assertIsInstance(response, str)
                self.assertGreater(len(response), 0)

                response = tech_agent.chat_sync("Can you help me debug this code?")
                # With Promise wrapping, we need to wait for the response
                if hasattr(response, "_wait_for_delivery"):
                    response = response._wait_for_delivery()
                # With fallback responses, we just check that we get a response
                self.assertIsInstance(response, str)
                self.assertGreater(len(response), 0)

    def test_agent_customization(self):
        """Test that agents can be customized with different fields and behaviors."""
        # Mock the sandbox context to return no LLM resources to force fallback behavior
        with patch.object(self.sandbox_context, "get_resources", return_value={}):
            # Also mock the agent's own LLM resource to return None (no LLM available)
            with patch.object(AgentInstance, "get_llm_resource", return_value=None):
                # Create a specialized agent
                agent_type = AgentType(
                    name="SupportAgent",
                    docstring="A helpful support agent",
                    fields={"domain": "str", "tasks": "str"},
                    field_order=["domain", "tasks"],
                )
                support_agent = AgentInstance(
                    struct_type=agent_type,
                    values={"domain": "customer support", "tasks": "help customers, resolve issues"},
                )

                # Test that agent fields are properly set
                self.assertEqual(support_agent.domain, "customer support")
                self.assertEqual(support_agent.tasks, "help customers, resolve issues")

                # Test chat functionality
                support_response = support_agent.chat_sync("I need help with my bill")
                # With Promise wrapping, we need to wait for the response
                if hasattr(support_response, "_wait_for_delivery"):
                    support_response = support_response._wait_for_delivery()
                # With fallback responses, we just check that we get a response
                self.assertIsInstance(support_response, str)
                self.assertGreater(len(support_response), 0)


if __name__ == "__main__":
    unittest.main()
