#!/usr/bin/env python3
"""
Test the LLM integration with Dana's llm_function pattern.
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from dana.agent.agent_struct_system import AgentStructType, AgentStructInstance


class TestLLMIntegration(unittest.TestCase):
    """Test cases for LLM integration using Dana's llm_function."""

    def setUp(self):
        """Set up test cases."""
        self.temp_dir = tempfile.mkdtemp()
        self.memory_dir = Path(self.temp_dir) / ".dana" / "chats"
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        # Patch memory initialization to use temp directory
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
        import shutil

        shutil.rmtree(self.temp_dir)

    def create_test_agent(self, name="TestAgent", fields=None):
        """Create a test agent for testing."""
        if fields is None:
            fields = {"role": "assistant"}

        agent_type = AgentStructType(name=name, fields=fields, field_order=list(fields.keys()), field_comments={})

        return AgentStructInstance(agent_type, fields)

    def test_llm_function_integration(self):
        """Test that agent uses Dana's llm_function."""
        agent = self.create_test_agent()

        # Mock the llm_function to return a Promise
        with patch("dana.libs.corelib.py.py_llm.py_llm") as mock_llm_func:
            # Create a mock promise that resolves to a value
            mock_promise = Mock()
            mock_promise._ensure_resolved = Mock(return_value="Mock LLM response")
            mock_promise.resolve = Mock(return_value="Mock LLM response")
            mock_llm_func.return_value = mock_promise

            response = agent.chat("Test message")

            # Should have called Dana's llm_function
            mock_llm_func.assert_called_once()

            # Response should be the resolved value
            self.assertEqual(response, "Mock LLM response")

    def test_llm_function_with_context(self):
        """Test that llm_function is called with proper context."""
        agent = self.create_test_agent()

        with patch("dana.libs.corelib.py.py_llm.py_llm") as mock_llm_func:
            with patch("dana.core.lang.sandbox_context.SandboxContext") as mock_context_class:
                mock_context = Mock()
                mock_context_class.return_value = mock_context

                mock_promise = Mock()
                mock_promise.resolve = Mock(return_value="Context response")
                mock_llm_func.return_value = mock_promise

                agent.chat("Test with context")

                # Should have created a SandboxContext
                mock_context_class.assert_called_once()

                # Should have called llm_function with context and prompt
                self.assertEqual(mock_llm_func.call_count, 1)
                call_args = mock_llm_func.call_args

                # Check that context was passed
                self.assertEqual(call_args[0][0], mock_context)

                # Check that prompt contains agent description and conversation
                prompt = call_args[0][1]
                self.assertIn("You are TestAgent", prompt)

    def test_llm_function_error_handling(self):
        """Test error handling when llm_function fails."""
        agent = self.create_test_agent()

        with patch("dana.libs.corelib.py.py_llm.py_llm") as mock_llm_func:
            # Make llm_function raise an exception
            mock_llm_func.side_effect = Exception("LLM function failed")

            response = agent.chat("Test error handling")

            # Should fall back to simple response since LLM failed
            self.assertIn("LLM call failed", response)

    def test_fallback_when_llm_function_unavailable(self):
        """Test fallback behavior when llm_function is not available."""
        agent = self.create_test_agent()

        # Mock the import to fail
        with patch("dana.agent.agent_struct_system.AgentStructInstance._get_dana_llm_function") as mock_get_llm:
            mock_get_llm.return_value = None

            response = agent.chat("Hello")

            # Should use fallback response
            self.assertIn("Hello", response)
            self.assertIn("TestAgent", response)

    def test_custom_llm_field_priority(self):
        """Test that custom llm field takes priority over Dana's llm_function."""
        custom_llm = Mock(return_value="Custom LLM response")
        agent = self.create_test_agent(fields={"llm": custom_llm})

        with patch("dana.libs.corelib.py.py_llm.py_llm") as mock_llm_func:
            response = agent.chat("Test custom LLM")

            # Should use custom LLM, not Dana's llm_function
            custom_llm.assert_called_once()
            mock_llm_func.assert_not_called()

            self.assertEqual(response, "Custom LLM response")

    def test_context_llm_priority(self):
        """Test that context llm takes priority over Dana's llm_function."""
        agent = self.create_test_agent()
        context_llm = Mock(return_value="Context LLM response")
        agent._context["llm"] = context_llm

        with patch("dana.libs.corelib.py.py_llm.py_llm") as mock_llm_func:
            response = agent.chat("Test context LLM")

            # Should use context LLM, not Dana's llm_function
            context_llm.assert_called_once()
            mock_llm_func.assert_not_called()

            self.assertEqual(response, "Context LLM response")

    def test_promise_behavior_in_conversation(self):
        """Test that Promise behavior works across conversation turns."""
        agent = self.create_test_agent()

        with patch("dana.libs.corelib.py.py_llm.py_llm") as mock_llm_func:
            # Create different mock promises for each call
            promise1 = Mock()
            promise1._ensure_resolved = Mock(return_value="First response")
            promise1.resolve = Mock(return_value="First response")

            promise2 = Mock()
            promise2._ensure_resolved = Mock(return_value="Second response remembering first")
            promise2.resolve = Mock(return_value="Second response remembering first")

            mock_llm_func.side_effect = [promise1, promise2]

            # First turn
            response1 = agent.chat("Hello, my name is Alice")
            self.assertEqual(response1, "First response")

            # Second turn - should include conversation context
            response2 = agent.chat("What's my name?")
            self.assertEqual(response2, "Second response remembering first")

            # Should have called llm_function twice
            self.assertEqual(mock_llm_func.call_count, 2)

            # Second call should include conversation history
            second_call_prompt = mock_llm_func.call_args_list[1][0][1]
            self.assertIn("Alice", second_call_prompt)
            self.assertIn("Recent conversation", second_call_prompt)

    def test_promise_string_representation(self):
        """Test that Promise string representation works correctly."""
        agent = self.create_test_agent()

        with patch("dana.libs.corelib.py.py_llm.py_llm") as mock_llm_func:
            # Create a promise that behaves like EagerPromise
            mock_promise = Mock()
            mock_promise._ensure_resolved = Mock(return_value="Hello from LLM")
            mock_promise.resolve = Mock(return_value="Hello from LLM")

            mock_llm_func.return_value = mock_promise

            response = agent.chat("Say hello")

            # The response should be the resolved value
            self.assertEqual(response, "Hello from LLM")

            # And that should be saved to conversation memory
            stats = agent.get_conversation_stats()
            self.assertEqual(stats["total_turns"], 1)


class TestLLMFunctionIntegration(unittest.TestCase):
    """Integration tests for llm_function usage patterns."""

    def test_sandbox_context_creation(self):
        """Test that SandboxContext is created properly."""
        from dana.agent.agent_struct_system import AgentStructInstance, AgentStructType

        agent_type = AgentStructType(name="ContextTestAgent", fields={"purpose": "testing"}, field_order=["purpose"], field_comments={})
        agent = AgentStructInstance(agent_type, {"purpose": "testing"})

        # Test the context creation without mocking
        llm_func = agent._get_dana_llm_function()

        # Should return None if llm_function is not available, or a callable
        self.assertTrue(llm_func is None or callable(llm_func))

    def test_wrapper_function_behavior(self):
        """Test the wrapped llm_function behavior."""
        from dana.agent.agent_struct_system import AgentStructInstance, AgentStructType

        agent_type = AgentStructType(name="WrapperTestAgent", fields={"role": "tester"}, field_order=["role"], field_comments={})
        agent = AgentStructInstance(agent_type, {"role": "tester"})

        with patch("dana.libs.corelib.py.py_llm.py_llm") as mock_llm_func:
            # Mock promise with resolve method
            mock_promise = Mock()
            mock_promise._ensure_resolved = Mock(return_value="Resolved LLM response")
            mock_promise.resolve = Mock(return_value="Resolved LLM response")
            mock_llm_func.return_value = mock_promise

            llm_func = agent._get_dana_llm_function()

            if llm_func:
                result = llm_func("Test prompt")

                # Should call llm_function and use _ensure_resolved
                mock_llm_func.assert_called_once()
                mock_promise._ensure_resolved.assert_called_once()
                self.assertEqual(result, "Resolved LLM response")


if __name__ == "__main__":
    unittest.main()
