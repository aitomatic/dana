"""
Tests for Agent Context Manager

Tests the context manager functionality (__enter__/__exit__) for AgentInstance
to ensure proper resource initialization and cleanup.
"""

import asyncio
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dana.builtin_types.agent.agent_instance import AgentInstance
from dana.builtin_types.agent.agent_type import AgentType
from dana.core.lang.sandbox_context import SandboxContext


class TestAgentContextManager(unittest.TestCase):
    """Test agent context manager functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Set mock LLM mode for testing
        import os

        os.environ["DANA_MOCK_LLM"] = "true"

        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)

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

        from unittest.mock import patch

        self.init_patcher = patch.object(AgentInstance, "_initialize_conversation_memory", mock_init)
        self.init_patcher.start()

        # Create a test agent type
        self.agent_type = AgentType(
            name="ContextTestAgent",
            fields={"name": "str", "config": "dict"},
            field_order=["name", "config"],
            field_comments={},
        )

        # Create agent instance with config
        self.agent_instance = AgentInstance(
            self.agent_type,
            {
                "name": "context_test_agent",
                "config": {
                    "llm_model": "test-model",
                    "llm_temperature": 0.5,
                    "llm_max_tokens": 1024,
                },
            },
        )

        self.sandbox_context = SandboxContext()

    def tearDown(self):
        """Clean up after tests."""
        # Stop the patcher
        self.init_patcher.stop()

        # Clear any registered callbacks
        self.agent_instance._log_callbacks.clear()

    def test_context_manager_basic_functionality(self):
        """Test basic context manager functionality."""
        # Test that agent can be used as context manager
        with self.agent_instance as agent:
            # Verify agent is accessible
            self.assertEqual(agent.name, "context_test_agent")

            # Verify resources are initialized
            self.assertIsNotNone(agent._conversation_memory)
            self.assertIsNotNone(agent._llm_resource_instance)

            # Verify metrics are updated
            metrics = agent.get_metrics()
            self.assertEqual(metrics["current_step"], "initialized")

    def test_context_manager_initialization(self):
        """Test that context manager properly initializes resources."""
        # Before context manager
        self.assertIsNone(self.agent_instance._conversation_memory)
        self.assertIsNone(self.agent_instance._llm_resource_instance)

        # Use context manager
        with self.agent_instance as agent:
            # After initialization
            self.assertIsNotNone(agent._conversation_memory)
            self.assertIsNotNone(agent._llm_resource_instance)

            # Verify LLM resource is initialized (may not be available in test env)
            # The important thing is that it was created, not that it's available
            self.assertIsNotNone(agent._llm_resource_instance)

    def test_context_manager_cleanup(self):
        """Test that context manager properly cleans up resources."""
        # Use context manager
        with self.agent_instance as agent:
            # Resources should be initialized
            self.assertIsNotNone(agent._conversation_memory)
            self.assertIsNotNone(agent._llm_resource_instance)

        # After context manager exit
        self.assertIsNone(self.agent_instance._conversation_memory)
        self.assertIsNone(self.agent_instance._llm_resource_instance)
        self.assertIsNone(self.agent_instance._llm_resource)

        # Verify metrics are updated
        metrics = self.agent_instance.get_metrics()
        self.assertEqual(metrics["current_step"], "cleaned_up")
        self.assertFalse(metrics["is_running"])

    def test_context_manager_exception_handling(self):
        """Test that context manager handles exceptions properly."""
        # Test that exceptions are not suppressed
        with self.assertRaises(ValueError):
            with self.agent_instance as _:
                # This should raise an exception
                raise ValueError("Test exception")

        # Verify cleanup still happened despite exception
        self.assertIsNone(self.agent_instance._conversation_memory)
        self.assertIsNone(self.agent_instance._llm_resource_instance)

    def test_context_manager_logging(self):
        """Test that context manager logs initialization and cleanup."""
        with self.assertLogs(level="INFO") as log_context:
            with self.agent_instance as _:
                pass

            # Check for initialization and cleanup log messages
            log_messages = [record.getMessage() for record in log_context.records]
            self.assertTrue(any("Agent resources initialized" in msg for msg in log_messages))
            self.assertTrue(any("Agent resources cleaned up" in msg for msg in log_messages))

    def test_context_manager_multiple_uses(self):
        """Test that context manager can be used multiple times."""
        # First use
        with self.agent_instance as agent:
            self.assertIsNotNone(agent._conversation_memory)
            self.assertIsNotNone(agent._llm_resource_instance)

        # Verify cleanup
        self.assertIsNone(self.agent_instance._conversation_memory)
        self.assertIsNone(self.agent_instance._llm_resource_instance)

        # Second use - should work again
        with self.agent_instance as agent:
            self.assertIsNotNone(agent._conversation_memory)
            self.assertIsNotNone(agent._llm_resource_instance)

    def test_context_manager_memory_cleanup(self):
        """Test that agent memory is properly cleared on cleanup."""
        # Use context manager
        with self.agent_instance as agent:
            # Add some data to memory
            agent._memory["test_key"] = "test_value"
            agent._context["test_context"] = "test_context_value"

            # Verify data is there
            self.assertEqual(agent._memory["test_key"], "test_value")
            self.assertEqual(agent._context["test_context"], "test_context_value")

        # After cleanup, memory should be cleared
        self.assertEqual(len(self.agent_instance._memory), 0)
        self.assertEqual(len(self.agent_instance._context), 0)

    def test_context_manager_metrics_reset(self):
        """Test that metrics are properly reset on cleanup."""
        # Use context manager
        with self.agent_instance as agent:
            # Update some metrics
            agent.update_metric("is_running", True)
            agent.update_metric("elapsed_time", 10.5)
            agent.update_metric("tokens_per_sec", 100.0)

            # Verify metrics are set
            metrics = agent.get_metrics()
            self.assertTrue(metrics["is_running"])
            self.assertEqual(metrics["elapsed_time"], 10.5)
            self.assertEqual(metrics["tokens_per_sec"], 100.0)

        # After cleanup, metrics should be reset
        metrics = self.agent_instance.get_metrics()
        self.assertFalse(metrics["is_running"])
        self.assertEqual(metrics["elapsed_time"], 0.0)
        self.assertEqual(metrics["tokens_per_sec"], 0.0)
        self.assertEqual(metrics["current_step"], "cleaned_up")

    def test_context_manager_conversation_memory_cleanup(self):
        """Test that conversation memory is properly cleared on cleanup."""
        # Use context manager
        with self.agent_instance as agent:
            # Initialize conversation memory
            agent._initialize_conversation_memory()

            # Add some conversation data
            if agent._conversation_memory:
                agent._conversation_memory.add_turn("user", "Hello")
                agent._conversation_memory.add_turn("assistant", "Hi there!")

                # Verify data is there
                stats = agent._conversation_memory.get_statistics()
                self.assertGreater(stats.get("total_turns", 0), 0)

        # After cleanup, conversation memory should be None
        self.assertIsNone(self.agent_instance._conversation_memory)

    def test_context_manager_llm_resource_cleanup(self):
        """Test that LLM resource is properly stopped and cleaned up."""
        # Use context manager
        with self.agent_instance as agent:
            # Initialize LLM resource
            agent._initialize_llm_resource()

            # Verify LLM resource is initialized (may not be available in test env)
            self.assertIsNotNone(agent._llm_resource_instance)

        # After cleanup, LLM resources should be None
        self.assertIsNone(self.agent_instance._llm_resource_instance)
        self.assertIsNone(self.agent_instance._llm_resource)

    def test_context_manager_initialization_failure_handling(self):
        """Test that initialization failures are handled gracefully."""
        # Mock LLM resource initialization to fail
        with patch.object(self.agent_instance, "_initialize_llm_resource", side_effect=Exception("LLM init failed")):
            with self.assertLogs(level="ERROR") as log_context:
                with self.agent_instance as agent:
                    # Should still work despite LLM initialization failure
                    self.assertEqual(agent.name, "context_test_agent")

                # Check for error log
                log_messages = [record.getMessage() for record in log_context.records]
                self.assertTrue(any("Failed to initialize agent resources" in msg for msg in log_messages))

    def test_context_manager_cleanup_failure_handling(self):
        """Test that cleanup failures are handled gracefully."""
        # Use context manager to initialize resources
        with self.agent_instance as _:
            pass

        # Mock cleanup to fail
        with patch.object(self.agent_instance, "_llm_resource_instance") as mock_llm:
            mock_llm.stop.side_effect = Exception("Stop failed")
            mock_llm.cleanup.side_effect = Exception("Cleanup failed")

            with self.assertLogs(level="WARNING") as log_context:
                # This should not raise an exception
                self.agent_instance._cleanup_agent_resources()

                # Check for warning logs
                log_messages = [record.getMessage() for record in log_context.records]
                self.assertTrue(any("Failed to stop LLM resource" in msg for msg in log_messages))
                self.assertTrue(any("Failed to cleanup LLM resource" in msg for msg in log_messages))

    def test_context_manager_nested_usage(self):
        """Test nested context manager usage."""
        # Create another agent instance
        agent2 = AgentInstance(self.agent_type, {"name": "nested_test_agent", "config": {"llm_model": "test-model-2"}})

        # Nested usage
        with self.agent_instance as agent1:
            with agent2 as agent2_inst:
                # Both agents should be initialized
                self.assertIsNotNone(agent1._conversation_memory)
                self.assertIsNotNone(agent2_inst._conversation_memory)
                self.assertIsNotNone(agent1._llm_resource_instance)
                self.assertIsNotNone(agent2_inst._llm_resource_instance)

        # Both should be cleaned up
        self.assertIsNone(self.agent_instance._conversation_memory)
        self.assertIsNone(agent2._conversation_memory)


class TestAgentAsyncContextManager(unittest.TestCase):
    """Test agent async context manager functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)

        # Create a test agent type
        self.agent_type = AgentType(
            name="AsyncContextTestAgent",
            fields={"name": "str", "config": "dict"},
            field_order=["name", "config"],
            field_comments={},
        )

        # Create agent instance with config
        self.agent_instance = AgentInstance(
            self.agent_type,
            {
                "name": "async_context_test_agent",
                "config": {
                    "llm_model": "test-model",
                    "llm_temperature": 0.5,
                    "llm_max_tokens": 1024,
                },
            },
        )

        self.sandbox_context = SandboxContext()

    def tearDown(self):
        """Clean up after tests."""
        # Clear any registered callbacks
        self.agent_instance._log_callbacks.clear()

    def test_async_context_manager_basic_functionality(self):
        """Test basic async context manager functionality."""

        async def test_async_context():
            # Test that agent can be used as async context manager
            async with self.agent_instance as agent:
                # Verify agent is accessible
                self.assertEqual(agent.name, "async_context_test_agent")

                # Verify resources are initialized
                self.assertIsNotNone(agent._conversation_memory)
                self.assertIsNotNone(agent._llm_resource_instance)

                # Verify metrics are updated
                metrics = agent.get_metrics()
                self.assertEqual(metrics["current_step"], "initialized")

        # Run the async test
        asyncio.run(test_async_context())

    def test_async_context_manager_initialization(self):
        """Test that async context manager properly initializes resources."""

        async def test_async_init():
            # Before context manager
            self.assertIsNone(self.agent_instance._conversation_memory)
            self.assertIsNone(self.agent_instance._llm_resource_instance)

            # Use async context manager
            async with self.agent_instance as agent:
                # After initialization
                self.assertIsNotNone(agent._conversation_memory)
                self.assertIsNotNone(agent._llm_resource_instance)

                # Verify LLM resource is initialized (may not be available in test env)
                self.assertIsNotNone(agent._llm_resource_instance)

        # Run the async test
        asyncio.run(test_async_init())

    def test_async_context_manager_cleanup(self):
        """Test that async context manager properly cleans up resources."""

        async def test_async_cleanup():
            # Use async context manager
            async with self.agent_instance as agent:
                # Resources should be initialized
                self.assertIsNotNone(agent._conversation_memory)
                self.assertIsNotNone(agent._llm_resource_instance)

            # After context manager exit
            self.assertIsNone(self.agent_instance._conversation_memory)
            self.assertIsNone(self.agent_instance._llm_resource_instance)
            self.assertIsNone(self.agent_instance._llm_resource)

            # Verify metrics are updated
            metrics = self.agent_instance.get_metrics()
            self.assertEqual(metrics["current_step"], "cleaned_up")
            self.assertFalse(metrics["is_running"])

        # Run the async test
        asyncio.run(test_async_cleanup())

    def test_async_context_manager_exception_handling(self):
        """Test that async context manager handles exceptions properly."""

        async def test_async_exception():
            # Test that exceptions are not suppressed
            with self.assertRaises(ValueError):
                async with self.agent_instance as _:
                    # This should raise an exception
                    raise ValueError("Test async exception")

            # Verify cleanup still happened despite exception
            self.assertIsNone(self.agent_instance._conversation_memory)
            self.assertIsNone(self.agent_instance._llm_resource_instance)

        # Run the async test
        asyncio.run(test_async_exception())

    @unittest.skip("Async context manager methods not implemented yet")
    def test_async_context_manager_logging(self):
        """Test that async context manager logs initialization and cleanup."""

        async def test_async_logging():
            with self.assertLogs(level="INFO") as log_context:
                async with self.agent_instance as _:
                    pass

                # Check for initialization and cleanup log messages
                log_messages = [record.getMessage() for record in log_context.records]
                self.assertTrue(any("Agent resources initialized (async)" in msg for msg in log_messages))
                self.assertTrue(any("Agent resources cleaned up (async)" in msg for msg in log_messages))

        # Run the async test
        asyncio.run(test_async_logging())

    def test_async_context_manager_multiple_uses(self):
        """Test that async context manager can be used multiple times."""

        async def test_async_multiple():
            # First use
            async with self.agent_instance as agent:
                self.assertIsNotNone(agent._conversation_memory)
                self.assertIsNotNone(agent._llm_resource_instance)

            # Verify cleanup
            self.assertIsNone(self.agent_instance._conversation_memory)
            self.assertIsNone(self.agent_instance._llm_resource_instance)

            # Second use - should work again
            async with self.agent_instance as agent:
                self.assertIsNotNone(agent._conversation_memory)
                self.assertIsNotNone(agent._llm_resource_instance)

        # Run the async test
        asyncio.run(test_async_multiple())

    def test_async_context_manager_nested_usage(self):
        """Test nested async context manager usage."""

        async def test_async_nested():
            # Create another agent instance
            agent2 = AgentInstance(self.agent_type, {"name": "nested_async_agent", "config": {"llm_model": "test-model-2"}})

            # Nested usage
            async with self.agent_instance as agent1:
                async with agent2 as agent2_inst:
                    # Both agents should be initialized
                    self.assertIsNotNone(agent1._conversation_memory)
                    self.assertIsNotNone(agent2_inst._conversation_memory)
                    self.assertIsNotNone(agent1._llm_resource_instance)
                    self.assertIsNotNone(agent2_inst._llm_resource_instance)

            # Both should be cleaned up
            self.assertIsNone(self.agent_instance._conversation_memory)
            self.assertIsNone(agent2._conversation_memory)

        # Run the async test
        asyncio.run(test_async_nested())

    def test_async_vs_sync_context_manager_compatibility(self):
        """Test that async and sync context managers are compatible."""

        async def test_compatibility():
            # Test sync context manager
            with self.agent_instance as _:
                self.assertIsNotNone(self.agent_instance._conversation_memory)
                self.assertIsNotNone(self.agent_instance._llm_resource_instance)

            # Verify cleanup
            self.assertIsNone(self.agent_instance._conversation_memory)
            self.assertIsNone(self.agent_instance._llm_resource_instance)

            # Test async context manager
            async with self.agent_instance as _:
                self.assertIsNotNone(self.agent_instance._conversation_memory)
                self.assertIsNotNone(self.agent_instance._llm_resource_instance)

            # Verify cleanup
            self.assertIsNone(self.agent_instance._conversation_memory)
            self.assertIsNone(self.agent_instance._llm_resource_instance)

        # Run the async test
        asyncio.run(test_compatibility())


if __name__ == "__main__":
    unittest.main()
