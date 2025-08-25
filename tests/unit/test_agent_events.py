"""
Tests for Agent Events System

Tests the agent events functionality including log() method and on_log() callback.
"""

import unittest
from unittest.mock import Mock

from dana.builtin_types.agent.agent_instance import AgentInstance
from dana.builtin_types.agent.agent_type import AgentType
from dana.core.lang.sandbox_context import SandboxContext


class TestAgentEvents(unittest.TestCase):
    """Test agent events functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a test agent type and instance
        self.agent_type = AgentType(
            name="TestAgent",
            fields={"name": "str"},
            field_order=["name"],
            field_comments={},
        )
        self.agent_instance = AgentInstance(self.agent_type, {"name": "test_agent"})
        self.sandbox_context = SandboxContext()

    def tearDown(self):
        """Clean up after tests."""
        # Clear any registered callbacks
        self.agent_instance._log_callbacks.clear()

    def test_log_method_sync(self):
        """Test log method in synchronous mode."""
        message = "Test log message"

        # Capture logs from the root logger
        with self.assertLogs(level="INFO") as log_context:
            result = self.agent_instance.log(message, "INFO", self.sandbox_context, is_sync=True)

        # Check that the message was logged
        self.assertIn(f"[test_agent] {message}", log_context.output[0])
        self.assertEqual(result, message)

    def test_log_method_async(self):
        """Test log method in asynchronous mode."""
        message = "Test async log message"

        with self.assertLogs(level="INFO") as log_context:
            promise = self.agent_instance.log(message, "INFO", self.sandbox_context, is_sync=False)

            # Wait for the promise to resolve
            result = promise._wait_for_delivery()

        # Check that the message was logged
        self.assertIn(f"[test_agent] {message}", log_context.output[0])
        self.assertEqual(result, message)

    def test_log_callback_registration(self):
        """Test log callback registration and unregistration."""
        callback = Mock()

        # Register callback
        self.agent_instance.register_log_callback(callback)

        # Call log method
        message = "Test callback message"
        self.agent_instance.log(message, "INFO", self.sandbox_context, is_sync=True)

        # Verify callback was called
        callback.assert_called_once_with("test_agent", message, self.sandbox_context)

        # Unregister callback
        self.agent_instance.unregister_log_callback(callback)

        # Call log method again
        callback.reset_mock()
        self.agent_instance.log("Another message", "INFO", self.sandbox_context, is_sync=True)

        # Verify callback was not called
        callback.assert_not_called()

    def test_on_log_convenience_function(self):
        """Test the on_log convenience function."""
        callback = Mock()

        # Register using on_log
        self.agent_instance.on_log(callback)

        # Call log method
        message = "Test on_log message"
        self.agent_instance.log(message, "INFO", self.sandbox_context, is_sync=True)

        # Verify callback was called
        callback.assert_called_once_with("test_agent", message, self.sandbox_context)

    def test_multiple_callbacks(self):
        """Test that multiple callbacks are called."""
        callback1 = Mock()
        callback2 = Mock()

        # Register multiple callbacks
        self.agent_instance.register_log_callback(callback1)
        self.agent_instance.register_log_callback(callback2)

        # Call log method
        message = "Test multiple callbacks"
        self.agent_instance.log(message, "INFO", self.sandbox_context, is_sync=True)

        # Verify both callbacks were called
        callback1.assert_called_once_with("test_agent", message, self.sandbox_context)
        callback2.assert_called_once_with("test_agent", message, self.sandbox_context)

    def test_callback_error_handling(self):
        """Test that callback errors don't break logging."""

        def failing_callback(agent_name, message, context):
            raise Exception("Callback error")

        def working_callback(agent_name, message, context):
            pass

        # Register both callbacks
        self.agent_instance.register_log_callback(failing_callback)
        self.agent_instance.register_log_callback(working_callback)

        # Call log method - should not raise exception
        message = "Test error handling"
        with self.assertLogs(level="INFO") as log_context:
            result = self.agent_instance.log(message, "INFO", self.sandbox_context, is_sync=True)

        # Verify message was still logged
        self.assertIn(f"[test_agent] {message}", log_context.output[0])
        self.assertEqual(result, message)

    def test_agent_instance_log_method(self):
        """Test the log method on AgentInstance."""
        message = "Test agent instance log"

        with self.assertLogs(level="INFO") as log_context:
            result = self.agent_instance.log(message, "INFO", self.sandbox_context, is_sync=True)

        # Verify message was logged
        self.assertIn(f"[test_agent] {message}", log_context.output[0])
        self.assertEqual(result, message)

    def test_agent_instance_log_method_async(self):
        """Test the log method on AgentInstance in async mode."""
        message = "Test agent instance async log"

        with self.assertLogs(level="INFO") as log_context:
            promise = self.agent_instance.log(message, "INFO", self.sandbox_context, is_sync=False)
            result = promise._wait_for_delivery()

        # Verify message was logged
        self.assertIn(f"[test_agent] {message}", log_context.output[0])
        self.assertEqual(result, message)

    def test_agent_instance_log_method_no_context(self):
        """Test the log method on AgentInstance without sandbox context."""
        message = "Test log without context"

        with self.assertLogs(level="INFO") as log_context:
            result = self.agent_instance.log(message, "INFO", self.sandbox_context, is_sync=True)

        # Verify message was logged
        self.assertIn(f"[test_agent] {message}", log_context.output[0])
        self.assertEqual(result, message)

    def test_agent_instance_log_method_with_callback(self):
        """Test the log method on AgentInstance with callback."""
        callback = Mock()
        self.agent_instance.register_log_callback(callback)

        message = "Test agent instance with callback"
        self.agent_instance.log(message, "INFO", self.sandbox_context, is_sync=True)

        # Verify callback was called
        callback.assert_called_once_with("test_agent", message, self.sandbox_context)

    def test_agent_name_fallback(self):
        """Test that agent name fallback works when name attribute is missing."""
        # Create agent instance without name
        agent_type = AgentType(
            name="NoNameAgent",
            fields={},
            field_order=[],
            field_comments={},
        )
        agent_instance = AgentInstance(agent_type, {})

        message = "Test no name agent"

        with self.assertLogs(level="INFO") as log_context:
            result = agent_instance.log(message, "INFO", self.sandbox_context, is_sync=True)

        # Verify message was logged with fallback name
        self.assertIn(f"[unnamed_agent] {message}", log_context.output[0])
        self.assertEqual(result, message)

    def test_invalid_callback_registration(self):
        """Test that invalid callback registration raises error."""
        with self.assertRaises(ValueError):
            self.agent_instance.register_log_callback("not a callable")

    def test_callback_unregistration_nonexistent(self):
        """Test that unregistering non-existent callback doesn't error."""
        callback = Mock()
        # Should not raise an exception
        self.agent_instance.unregister_log_callback(callback)


if __name__ == "__main__":
    unittest.main()
