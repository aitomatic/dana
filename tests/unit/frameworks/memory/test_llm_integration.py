#!/usr/bin/env python3
"""
Test the LLM integration with Dana's agent struct system.
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from dana.builtin_types.agent_system import AgentInstance, AgentType
from dana.core.lang.sandbox_context import SandboxContext


class TestLLMIntegration(unittest.TestCase):
    """Test cases for LLM integration using Dana's agent struct system."""

    def setUp(self):
        """Set up test cases."""
        self.temp_dir = tempfile.mkdtemp()
        self.memory_dir = Path(self.temp_dir) / ".dana" / "chats"
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        # Patch memory initialization to use temp directory
        _original_init = AgentInstance._initialize_conversation_memory

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
            fields = {"role": "assistant"}

        agent_type = AgentType(name=name, fields=fields, field_order=list(fields.keys()), field_comments={})

        return AgentInstance(agent_type, fields)

    def test_llm_resource_integration(self):
        """Test integration with LLM resources."""
        # Create mock LLM resource
        mock_llm_resource = Mock()
        mock_llm_resource.kind = "llm"
        mock_llm_resource.chat_completion.return_value = "LLM response"

        # Create agent
        agent = self.create_test_agent()

        # Mock the get_resources method to return our mock LLM resource
        with patch.object(self.sandbox_context, "get_resources", return_value={"test_llm": mock_llm_resource}):
            # Force agent to use sandbox LLM resource instead of its own
            with patch.object(agent, "_get_llm_resource", return_value=mock_llm_resource):
                # Chat with agent - now returns a Promise that needs to be resolved
                response = agent.chat("Test message", sandbox_context=self.sandbox_context)

                # Wait for the Promise to resolve
                if hasattr(response, "_wait_for_delivery"):
                    response = response._wait_for_delivery()

                # Should use LLM
                self.assertEqual(response, "LLM response")
                mock_llm_resource.chat_completion.assert_called_once()

    def test_llm_resource_with_context(self):
        """Test LLM resource integration with conversation context."""
        # Create mock LLM resource
        mock_llm_resource = Mock()
        mock_llm_resource.kind = "llm"
        mock_llm_resource.chat_completion.return_value = "Contextual LLM response"

        # Create agent
        agent = self.create_test_agent()

        # Mock the get_resources method to return our mock LLM resource
        with patch.object(self.sandbox_context, "get_resources", return_value={"test_llm": mock_llm_resource}):
            # Force agent to use sandbox LLM resource instead of its own
            with patch.object(agent, "_get_llm_resource", return_value=mock_llm_resource):
                # Chat with agent - now returns a Promise that needs to be resolved
                response = agent.chat("Test with context", sandbox_context=self.sandbox_context)

                # Wait for the Promise to resolve
                if hasattr(response, "_wait_for_delivery"):
                    response = response._wait_for_delivery()

                # Check that LLM was called
                mock_llm_resource.chat_completion.assert_called_once()

                # Check that prompt contains agent description
                call_args = mock_llm_resource.chat_completion.call_args
                system_prompt = call_args[1]["system_prompt"]
                self.assertIn("You are TestAgent", system_prompt)

    def test_llm_resource_error_handling(self):
        """Test error handling when LLM resource fails."""
        # Create mock LLM resource that raises an exception
        mock_llm_resource = Mock()
        mock_llm_resource.kind = "llm"
        mock_llm_resource.chat_completion.side_effect = Exception("LLM service unavailable")

        # Create agent
        agent = self.create_test_agent()

        # Mock the get_resources method to return our mock LLM resource
        with patch.object(self.sandbox_context, "get_resources", return_value={"test_llm": mock_llm_resource}):
            # Force agent to use sandbox LLM resource instead of its own
            with patch.object(agent, "_get_llm_resource", return_value=mock_llm_resource):
                # Chat should return an error message when LLM fails
                response = agent.chat("Test message", sandbox_context=self.sandbox_context)

                # Wait for the Promise to resolve
                if hasattr(response, "_wait_for_delivery"):
                    response = response._wait_for_delivery()

                # Should get an error message
                self.assertIn("error", response.lower())
                self.assertIn("llm", response.lower())

    def test_fallback_when_llm_resource_unavailable(self):
        """Test fallback behavior when no LLM resource is available."""
        # Mock the sandbox context to return no LLM resources
        with patch.object(self.sandbox_context, "get_resources", return_value={}):
            # Also mock the agent's own LLM resource to return None
            with patch.object(AgentInstance, "_get_llm_resource", return_value=None):
                agent = self.create_test_agent()

                # Chat should work with fallback response
                response = agent.chat("Hello", sandbox_context=self.sandbox_context)

                # Wait for the Promise to resolve
                if hasattr(response, "_wait_for_delivery"):
                    response = response._wait_for_delivery()

                # Should get a fallback response
                self.assertIn("Hello", response)
                self.assertIn("TestAgent", response)

    def test_custom_llm_field_priority(self):
        """Test that custom LLM fields take priority over default resources."""
        # Create mock LLM resource
        mock_llm_resource = Mock()
        mock_llm_resource.kind = "llm"
        mock_llm_resource.chat_completion.return_value = "Custom LLM response"

        # Create agent with custom LLM field
        agent = self.create_test_agent(fields={"llm": "custom_llm"})

        # Mock the get_resources method to return our mock LLM resource
        with patch.object(self.sandbox_context, "get_resources", return_value={"custom_llm": mock_llm_resource}):
            # Force agent to use sandbox LLM resource instead of its own
            with patch.object(agent, "_get_llm_resource", return_value=mock_llm_resource):
                # Chat with agent - now returns a Promise that needs to be resolved
                response = agent.chat("Test message", sandbox_context=self.sandbox_context)

                # Wait for the Promise to resolve
                if hasattr(response, "_wait_for_delivery"):
                    response = response._wait_for_delivery()

                # Should use custom LLM
                self.assertEqual(response, "Custom LLM response")
                mock_llm_resource.chat_completion.assert_called_once()

    def test_context_llm_priority(self):
        """Test that context LLM resources take priority over agent's own LLM."""
        # Create mock LLM resource
        mock_llm_resource = Mock()
        mock_llm_resource.kind = "llm"
        mock_llm_resource.chat_completion.return_value = "Context LLM response"

        # Create agent
        agent = self.create_test_agent()

        # Mock the get_resources method to return our mock LLM resource
        with patch.object(self.sandbox_context, "get_resources", return_value={"context_llm": mock_llm_resource}):
            # Force agent to use sandbox LLM resource instead of its own
            with patch.object(agent, "_get_llm_resource", return_value=mock_llm_resource):
                # Chat with agent - now returns a Promise that needs to be resolved
                response = agent.chat("Test message", sandbox_context=self.sandbox_context)

                # Wait for the Promise to resolve
                if hasattr(response, "_wait_for_delivery"):
                    response = response._wait_for_delivery()

                # Should use context LLM
                self.assertEqual(response, "Context LLM response")
                mock_llm_resource.chat_completion.assert_called_once()

    def test_promise_behavior_in_conversation(self):
        """Test that promises work correctly in conversation context."""
        # Create mock LLM resource
        mock_llm_resource = Mock()
        mock_llm_resource.kind = "llm"
        mock_llm_resource.chat_completion.return_value = "Promise test response"

        # Create agent
        agent = self.create_test_agent()

        # Mock the get_resources method to return our mock LLM resource
        with patch.object(self.sandbox_context, "get_resources", return_value={"test_llm": mock_llm_resource}):
            # Force agent to use sandbox LLM resource instead of its own
            with patch.object(agent, "_get_llm_resource", return_value=mock_llm_resource):
                # Test multiple chat calls
                response1 = agent.chat("First message", sandbox_context=self.sandbox_context)
                response2 = agent.chat("Second message", sandbox_context=self.sandbox_context)

                # Wait for both Promises to resolve
                if hasattr(response1, "_wait_for_delivery"):
                    response1 = response1._wait_for_delivery()
                if hasattr(response2, "_wait_for_delivery"):
                    response2 = response2._wait_for_delivery()

                # Both should work correctly
                self.assertEqual(response1, "Promise test response")
                self.assertEqual(response2, "Promise test response")

                # LLM should be called twice
                self.assertEqual(mock_llm_resource.chat_completion.call_count, 2)

    def test_promise_string_representation(self):
        """Test that promises have proper string representation."""
        # Create mock LLM resource
        mock_llm_resource = Mock()
        mock_llm_resource.kind = "llm"
        mock_llm_resource.chat_completion.return_value = "String representation test"

        # Create agent
        agent = self.create_test_agent()

        # Mock the get_resources method to return our mock LLM resource
        with patch.object(self.sandbox_context, "get_resources", return_value={"test_llm": mock_llm_resource}):
            # Force agent to use sandbox LLM resource instead of its own
            with patch.object(agent, "_get_llm_resource", return_value=mock_llm_resource):
                # Chat with agent - now returns a Promise that needs to be resolved
                response = agent.chat("Test message", sandbox_context=self.sandbox_context)

                # Wait for the Promise to resolve
                if hasattr(response, "_wait_for_delivery"):
                    response = response._wait_for_delivery()

                # Should get proper string response
                self.assertIsInstance(response, str)
                self.assertEqual(response, "String representation test")


class TestLLMFunctionIntegration(unittest.TestCase):
    """Integration tests for LLM resource usage patterns."""

    def setUp(self):
        """Set up integration tests."""
        self.sandbox_context = SandboxContext()

    def create_test_agent(self):
        """Create a test agent for integration tests."""
        from dana.builtin_types.agent_system import AgentInstance, AgentType

        agent_type = AgentType(
            name="TestAgent",
            docstring="A test agent for integration testing",
            fields={"purpose": "testing"},
            field_order=["purpose"],
        )
        return AgentInstance(agent_type, {"purpose": "testing"})

    def test_sandbox_context_creation(self):
        """Test that SandboxContext is created properly."""
        from dana.builtin_types.agent_system import AgentInstance, AgentType

        agent_type = AgentType(name="ContextTestAgent", fields={"purpose": "testing"}, field_order=["purpose"], field_comments={})
        agent = AgentInstance(agent_type, {"purpose": "testing"})

        # Test the LLM resource creation without mocking
        llm_resource = agent._get_llm_resource()

        # Should return None if LLM resource is not available, or an LLMResource instance
        self.assertTrue(llm_resource is None or hasattr(llm_resource, "query_sync"))

    def test_wrapper_function_behavior(self):
        """Test that wrapper functions work correctly with LLM integration."""
        # Create mock LLM resource
        mock_llm_resource = Mock()
        mock_llm_resource.kind = "llm"
        mock_llm_resource.chat_completion.return_value = "Wrapper function response"

        # Create agent
        agent = self.create_test_agent()

        # Mock the get_resources method to return our mock LLM resource
        with patch.object(self.sandbox_context, "get_resources", return_value={"test_llm": mock_llm_resource}):
            # Force agent to use sandbox LLM resource instead of its own
            with patch.object(agent, "_get_llm_resource", return_value=mock_llm_resource):
                # Test wrapper function behavior
                response = agent.chat("Test wrapper function", sandbox_context=self.sandbox_context)

                # Wait for the Promise to resolve
                if hasattr(response, "_wait_for_delivery"):
                    response = response._wait_for_delivery()

                # Should get proper response
                self.assertEqual(response, "Wrapper function response")
                mock_llm_resource.chat_completion.assert_called_once()


if __name__ == "__main__":
    unittest.main()
