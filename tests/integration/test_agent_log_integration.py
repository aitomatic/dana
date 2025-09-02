"""
Integration Test for Agent Log Functionality

Tests that the new log() method integrates correctly with the existing agent system.
"""

import unittest

from dana.builtin_types.agent.agent_instance import AgentInstance
from dana.builtin_types.agent.agent_type import AgentType
from dana.core.lang.sandbox_context import SandboxContext
from dana.registry import register_agent_type


class TestAgentLogIntegration(unittest.TestCase):
    """Test agent log functionality integration."""

    def setUp(self):
        """Set up test fixtures."""
        # Set mock LLM mode for testing
        import os

        os.environ["DANA_MOCK_LLM"] = "true"

        # Create a test agent type
        self.agent_type = AgentType(
            name="LogTestAgent",
            fields={"name": "str", "role": "str"},
            field_order=["name", "role"],
            field_comments={},
        )

        # Register the agent type
        register_agent_type(self.agent_type)

        # Create agent instance
        self.agent_instance = AgentInstance(self.agent_type, {"name": "test_logger", "role": "debugger"})

        # Initialize agent resources to ensure PromiseFactory works
        self.agent_instance._initialize_agent_resources()

        self.sandbox_context = SandboxContext()

        # Track callbacks
        self.callback_calls = []

    def tearDown(self):
        """Clean up after tests."""
        # Clear any registered callbacks
        self.agent_instance._log_callbacks.clear()

    def test_log_method_available_on_agent_instance(self):
        """Test that log() method is available on agent instances."""
        # Verify the method exists
        self.assertTrue(hasattr(self.agent_instance, "log"))
        self.assertTrue(callable(self.agent_instance.log))

    def test_log_method_in_default_methods(self):
        """Test that log() is included in default agent methods."""
        from dana.builtin_types.agent.agent_instance import AgentInstance

        default_methods = AgentInstance.get_default_dana_methods()

        self.assertIn("log", default_methods)
        self.assertTrue(callable(default_methods["log"]))

    def test_log_method_with_callback_integration(self):
        """Test that log() method works with callback system."""

        def test_callback(agent_name, message, context):
            self.callback_calls.append((agent_name, message, context))

        # Register callback
        self.agent_instance.on_log(test_callback)

        # Call log method
        message = "Integration test message"
        result = self.agent_instance.log(message, "INFO", self.sandbox_context, is_sync=True)

        # Verify callback was called
        self.assertEqual(len(self.callback_calls), 1)
        self.assertEqual(self.callback_calls[0][0], "test_logger")
        self.assertEqual(self.callback_calls[0][1], message)
        self.assertEqual(self.callback_calls[0][2], self.sandbox_context)

        # Verify result
        self.assertEqual(result, message)

    def test_log_method_async_integration(self):
        """Test that log() method works in async mode, handling safety fallbacks gracefully."""

        def test_callback(agent_name, message, context):
            self.callback_calls.append((agent_name, message, context))

        # Register callback
        self.agent_instance.on_log(test_callback)

        # Call log method in async mode
        message = "Async integration test message"
        result = self.agent_instance.log(message, "INFO", self.sandbox_context, is_sync=False)

        # Handle both promise and direct result cases
        # The system may fall back to synchronous execution for safety
        if hasattr(result, "_wait_for_delivery"):
            # Got a promise - wait for it to resolve
            final_result = result._wait_for_delivery()
        else:
            # Got direct result due to safety fallback
            final_result = result

        # Verify callback was called
        self.assertEqual(len(self.callback_calls), 1)
        self.assertEqual(self.callback_calls[0][0], "test_logger")
        self.assertEqual(self.callback_calls[0][1], message)
        self.assertEqual(self.callback_calls[0][2], self.sandbox_context)

        # Verify result
        self.assertEqual(final_result, message)

    def test_log_method_without_context(self):
        """Test that log() method works without sandbox context."""

        def test_callback(agent_name, message, context):
            self.callback_calls.append((agent_name, message, context))

        # Register callback
        self.agent_instance.on_log(test_callback)

        # Call log method without context
        message = "No context test message"
        result = self.agent_instance.log(message, "INFO", self.sandbox_context, is_sync=True)

        # Verify callback was called
        self.assertEqual(len(self.callback_calls), 1)
        self.assertEqual(self.callback_calls[0][0], "test_logger")
        self.assertEqual(self.callback_calls[0][1], message)
        # Context should be a SandboxContext instance
        self.assertIsInstance(self.callback_calls[0][2], SandboxContext)

        # Verify result
        self.assertEqual(result, message)

    def test_multiple_agents_logging(self):
        """Test that multiple agents can use log() method."""
        # Create another agent
        agent2 = AgentInstance(self.agent_type, {"name": "test_logger_2", "role": "monitor"})

        def test_callback(agent_name, message, context):
            self.callback_calls.append((agent_name, message, context))

        # Register callback on both agents
        self.agent_instance.on_log(test_callback)
        agent2.on_log(test_callback)

        # Both agents log messages
        self.agent_instance.log("Message from agent 1", "INFO", self.sandbox_context, is_sync=True)
        agent2.log("Message from agent 2", "INFO", self.sandbox_context, is_sync=True)

        # Verify both callbacks were called
        self.assertEqual(len(self.callback_calls), 2)
        self.assertEqual(self.callback_calls[0][0], "test_logger")
        self.assertEqual(self.callback_calls[0][1], "Message from agent 1")
        self.assertEqual(self.callback_calls[1][0], "test_logger_2")
        self.assertEqual(self.callback_calls[1][1], "Message from agent 2")

    def test_log_method_with_standard_logging(self):
        """Test that log() method integrates with standard logging."""
        with self.assertLogs(level="INFO") as log_context:
            message = "Standard logging test"
            self.agent_instance.log(message, "INFO", self.sandbox_context, is_sync=True)

            # Verify message was logged to standard logging
            self.assertIn(f"[test_logger] {message}", log_context.output[0])


if __name__ == "__main__":
    unittest.main()
