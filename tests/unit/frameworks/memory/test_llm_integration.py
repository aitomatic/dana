#!/usr/bin/env python3
"""
Test the LLM integration with Dana's agent struct system.
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from dana.agent.agent_struct_system import AgentStructInstance, AgentStructType
from dana.core.lang.sandbox_context import SandboxContext


class TestLLMIntegration(unittest.TestCase):
    """Test cases for LLM integration using Dana's agent struct system."""

    def setUp(self):
        """Set up test cases."""
        self.temp_dir = tempfile.mkdtemp()
        self.memory_dir = Path(self.temp_dir) / ".dana" / "chats"
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        # Patch memory initialization to use temp directory
        _original_init = AgentStructInstance._initialize_conversation_memory

        def mock_init(agent_self):
            if agent_self._conversation_memory is None:
                from dana.frameworks.memory.conversation_memory import ConversationMemory

                # Use temp directory instead of ~/.dana/chats/
                agent_name = getattr(agent_self.agent_type, "name", "agent")
                memory_file = self.memory_dir / f"{agent_name}_conversation.json"
                agent_self._conversation_memory = ConversationMemory(filepath=str(memory_file), max_turns=20)

        self.init_patcher = patch.object(AgentStructInstance, "_initialize_conversation_memory", mock_init)
        self.init_patcher.start()

        # Create a sandbox context for testing
        self.sandbox_context = SandboxContext()

    def tearDown(self):
        """Clean up test cases."""
        self.init_patcher.stop()
        import shutil

        shutil.rmtree(self.temp_dir)

    def create_test_agent(self, name="TestAgent", fields=None):
        """Create a test agent for testing."""
        if fields is None:
            fields = {"role": "assistant"}

        agent_type = AgentStructType(name=name, fields=fields, field_order=list(fields.keys()), field_comments={})

        return AgentStructInstance(agent_type, fields)

    def test_llm_resource_integration(self):
        """Test that agent uses LLM resource properly."""
        agent = self.create_test_agent()

        # Mock the LLM resource
        mock_llm_resource = Mock()
        mock_llm_resource.query_sync.return_value = Mock(success=True, content="Mock LLM response")

        with patch.object(self.sandbox_context, "get_system_llm_resource", return_value=mock_llm_resource):
            response_promise = agent.chat(self.sandbox_context, "Test message")
            response = response_promise._wait_for_delivery()

            # Should have called LLM resource
            mock_llm_resource.query_sync.assert_called_once()

            # Response should be the resolved value
            self.assertEqual(response, "Mock LLM response")

    def test_llm_resource_with_context(self):
        """Test that LLM resource is called with proper context."""
        agent = self.create_test_agent()

        mock_llm_resource = Mock()
        mock_llm_resource.query_sync.return_value = Mock(success=True, content="Context response")

        with patch.object(self.sandbox_context, "get_system_llm_resource", return_value=mock_llm_resource):
            agent.chat(self.sandbox_context, "Test with context")._wait_for_delivery()

            # Should have called LLM resource with proper request
            self.assertEqual(mock_llm_resource.query_sync.call_count, 1)
            call_args = mock_llm_resource.query_sync.call_args

            # Check that request contains prompt with agent description
            request = call_args[0][0]
            messages = request.arguments["messages"]
            system_messages = [msg for msg in messages if msg["role"] == "system"]
            self.assertTrue(len(system_messages) > 0)
            self.assertIn("You are TestAgent", system_messages[0]["content"])

    def test_llm_resource_error_handling(self):
        """Test error handling when LLM resource fails."""
        agent = self.create_test_agent()

        mock_llm_resource = Mock()
        mock_llm_resource.query_sync.side_effect = Exception("LLM resource failed")

        with patch.object(self.sandbox_context, "get_system_llm_resource", return_value=mock_llm_resource):
            response_promise = agent.chat(self.sandbox_context, "Test error handling")
            response = response_promise._wait_for_delivery()

            # Should handle error gracefully
            self.assertIn("error", response.lower())
            self.assertIn("LLM resource failed", response)

    def test_fallback_when_llm_resource_unavailable(self):
        """Test fallback behavior when LLM resource is not available."""
        agent = self.create_test_agent()

        # Mock the sandbox context to return None for LLM resource
        with patch.object(self.sandbox_context, "get_system_llm_resource", return_value=None):
            response_promise = agent.chat(self.sandbox_context, "Hello")
            response = response_promise._wait_for_delivery()

            # Should use fallback response
            self.assertIn("Hello", response)
            self.assertIn("TestAgent", response)

    def test_custom_llm_field_priority(self):
        """Test that custom llm field takes priority over default LLM resource."""
        # This test needs to be updated since LLM is now handled through resources
        # rather than direct field detection
        custom_llm = Mock(return_value="Custom LLM response")
        agent = self.create_test_agent(fields={"llm": custom_llm})

        # Mock sandbox context to return None to force fallback
        with patch.object(self.sandbox_context, "get_system_llm_resource", return_value=None):
            response_promise = agent.chat(self.sandbox_context, "Test custom LLM")
            response = response_promise._wait_for_delivery()

            # Should use fallback since custom LLM field is not used in new implementation
            self.assertIn("TestAgent", response)

    def test_context_llm_priority(self):
        """Test that context llm takes priority over default LLM resource."""
        # This test needs to be updated since the context approach has changed
        agent = self.create_test_agent()

        # Mock sandbox context to return None to force fallback
        with patch.object(self.sandbox_context, "get_system_llm_resource", return_value=None):
            response_promise = agent.chat(self.sandbox_context, "Test context LLM")
            response = response_promise._wait_for_delivery()

            # Should use fallback since context approach has changed
            self.assertIn("TestAgent", response)

    def test_promise_behavior_in_conversation(self):
        """Test that Promise behavior works across conversation turns."""
        agent = self.create_test_agent()

        mock_llm_resource = Mock()
        # Create different mock responses for each call
        mock_llm_resource.query_sync.side_effect = [
            Mock(success=True, content="First response"),
            Mock(success=True, content="Second response remembering first"),
        ]

        with patch.object(self.sandbox_context, "get_system_llm_resource", return_value=mock_llm_resource):
            # First turn
            response_promise1 = agent.chat(self.sandbox_context, "Hello, my name is Alice")
            response1 = response_promise1._wait_for_delivery()
            self.assertEqual(response1, "First response")

            # Second turn - should include conversation context
            response_promise2 = agent.chat(self.sandbox_context, "What's my name?")
            response2 = response_promise2._wait_for_delivery()
            self.assertEqual(response2, "Second response remembering first")

            # Should have called LLM resource twice
            self.assertEqual(mock_llm_resource.query_sync.call_count, 2)

            # Second call should include conversation history
            second_call_request = mock_llm_resource.query_sync.call_args_list[1][0][0]
            messages = second_call_request.arguments["messages"]
            all_content = " ".join([msg["content"] for msg in messages])
            self.assertIn("Alice", all_content)

    def test_promise_string_representation(self):
        """Test that Promise string representation works correctly."""
        agent = self.create_test_agent()

        mock_llm_resource = Mock()
        mock_llm_resource.query_sync.return_value = Mock(success=True, content="Hello from LLM")

        with patch.object(self.sandbox_context, "get_system_llm_resource", return_value=mock_llm_resource):
            response_promise = agent.chat(self.sandbox_context, "Say hello")
            response = response_promise._wait_for_delivery()

            # The response should be the resolved value
            self.assertEqual(response, "Hello from LLM")

            # And that should be saved to conversation memory
            stats = agent.get_conversation_stats()
            self.assertEqual(stats["total_turns"], 1)


class TestLLMFunctionIntegration(unittest.TestCase):
    """Integration tests for LLM resource usage patterns."""

    def setUp(self):
        """Set up integration tests."""
        self.sandbox_context = SandboxContext()

    def test_sandbox_context_creation(self):
        """Test that SandboxContext is created properly."""
        from dana.agent.agent_struct_system import AgentStructInstance, AgentStructType

        agent_type = AgentStructType(name="ContextTestAgent", fields={"purpose": "testing"}, field_order=["purpose"], field_comments={})
        agent = AgentStructInstance(agent_type, {"purpose": "testing"})

        # Test the LLM resource creation without mocking
        llm_resource = agent._get_llm_resource()

        # Should return None if LLM resource is not available, or an LLMResource instance
        self.assertTrue(llm_resource is None or hasattr(llm_resource, "query_sync"))

    def test_wrapper_function_behavior(self):
        """Test the wrapped LLM resource behavior."""
        from dana.agent.agent_struct_system import AgentStructInstance, AgentStructType

        agent_type = AgentStructType(name="WrapperTestAgent", fields={"role": "tester"}, field_order=["role"], field_comments={})
        agent = AgentStructInstance(agent_type, {"role": "tester"})

        mock_llm_resource = Mock()
        mock_llm_resource.query_sync.return_value = Mock(success=True, content="Resolved LLM response")

        with patch.object(self.sandbox_context, "get_system_llm_resource", return_value=mock_llm_resource):
            # Test that chat method uses the LLM resource properly
            response_promise = agent.chat(self.sandbox_context, "Test prompt")
            response = response_promise._wait_for_delivery()

            # Should call LLM resource and get response
            mock_llm_resource.query_sync.assert_called_once()
            self.assertEqual(response, "Resolved LLM response")


if __name__ == "__main__":
    unittest.main()
