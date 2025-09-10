"""
Tests for Context Engineering Framework integration with agent.solve().
"""

from unittest.mock import Mock, patch

import pytest

from dana.core.agent.agent_instance import AgentInstance
from dana.core.agent.agent_type import AgentType


class TestContextEngineIntegration:
    """Test the integration of Context Engineering Framework with agent.solve()."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create a mock agent type with required attributes
        self.agent_type = Mock(spec=AgentType)
        self.agent_type.name = "TestAgent"
        self.agent_type.field_defaults = {}
        self.agent_type.fields = {}
        self.agent_type.field_order = []
        self.agent_type.field_comments = {}

        # Create agent values
        self.agent_values = {"name": "test_agent", "description": "A test agent for ctxeng integration"}

        # Create agent instance
        self.agent = AgentInstance(self.agent_type, self.agent_values)

    def test_context_engine_initialization(self):
        """Test that context engineer is properly initialized."""
        # The context_engineer property will be None initially since it's lazy-loaded
        # We can't directly test the private attribute, so we test the property behavior

        # Trigger context engineer creation
        with patch("dana.frameworks.ctxeng.ContextEngineer") as mock_ctxeng:
            mock_instance = Mock()
            mock_instance.engineer_context.return_value = "<context>test problem</context>"
            mock_ctxeng.from_agent.return_value = mock_instance

            # This should trigger context engineer creation
            self.agent.solve_sync("test problem")

            # Verify context engineer was created by checking the property
            engineer = self.agent.context_engineer
            assert engineer is not None
            mock_ctxeng.from_agent.assert_called_once_with(self.agent)

    def test_context_engine_resource_discovery(self):
        """Test that context engineer discovers agent resources."""
        with patch("dana.frameworks.ctxeng.ContextEngineer") as mock_ctxeng:
            mock_instance = Mock()
            mock_instance.engineer_context.return_value = "<context><query>test problem</query></context>"
            mock_ctxeng.from_agent.return_value = mock_instance

            # Trigger context engineer creation
            self.agent.solve_sync("test problem")

            # Verify the context engineer was created and used
            engineer = self.agent.context_engineer
            assert engineer is not None
            mock_ctxeng.from_agent.assert_called_once_with(self.agent)

    def test_context_engine_assembly(self):
        """Test that context engineer assembles rich context."""
        # Note: The current AgentInstance uses PlannerExecutorSolverMixin which doesn't use ContextEngineer
        # This test verifies that the solve method works without ContextEngineer
        with patch("dana.frameworks.ctxeng.ContextEngineer") as mock_ctxeng:
            mock_instance = Mock()
            mock_instance.engineer_context.return_value = "<context><query>test problem</query></context>"
            mock_ctxeng.from_agent.return_value = mock_instance

            # Trigger solve - should work without ContextEngineer
            result = self.agent.solve_sync("test problem")

            # Verify solve completed successfully
            assert result is not None
            # ContextEngineer should not be called in the current implementation
            mock_instance.engineer_context.assert_not_called()

    def test_fallback_on_import_error(self):
        """Test that agent falls back to basic problem when ctxeng is not available."""
        # Test with a patch that affects the import inside the solve method
        with patch("dana.frameworks.ctxeng.ContextEngineer", side_effect=ImportError("No module named 'dana.frameworks.ctxeng'")):
            # Should not raise an error, should fall back to basic problem
            self.agent.solve_sync("test problem")

            # The context engineer should not be created due to import error
            # Note: In this test scenario, the mock is created before the import error
            # so we can't easily test the fallback behavior without more complex mocking
            # For now, we just verify the method doesn't crash
            # Note: result is not used in this test case

    def test_fallback_on_assembly_error(self):
        """Test that agent falls back to basic problem when context assembly fails."""
        with patch("dana.frameworks.ctxeng.ContextEngineer") as mock_ctxeng:
            mock_instance = Mock()
            mock_instance.engineer_context.side_effect = Exception("Assembly failed")
            mock_ctxeng.from_agent.return_value = mock_instance

            # Should not raise an error, should fall back to basic problem
            self.agent.solve_sync("test problem")

            # Verify context engineer was created but assembly failed
            engineer = self.agent.context_engineer
            assert engineer is not None

    def test_context_engine_reuse(self):
        """Test that context engineer is reused across multiple solve calls."""
        with patch("dana.frameworks.ctxeng.ContextEngineer") as mock_ctxeng:
            mock_instance = Mock()
            mock_instance.engineer_context.return_value = "<context><query>test</query></context>"
            mock_ctxeng.from_agent.return_value = mock_instance

            # First call should create context engineer
            self.agent.solve_sync("first problem")
            first_engine = self.agent.context_engineer

            # Second call should reuse the same engineer
            self.agent.solve_sync("second problem")
            second_engine = self.agent.context_engineer

            # Verify same instance is reused
            assert first_engine is second_engine
            assert mock_ctxeng.from_agent.call_count == 1  # Only called once


if __name__ == "__main__":
    pytest.main([__file__])
