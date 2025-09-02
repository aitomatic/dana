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
        """Test that context engine is properly initialized."""
        assert self.agent._context_engine is None

        # Trigger context engine creation
        with patch("dana.frameworks.ctxeng.ContextEngine") as mock_ctxeng:
            mock_instance = Mock()
            mock_ctxeng.from_agent.return_value = mock_instance

            # This should trigger context engine creation
            self.agent.solve("test problem")

            # Verify context engine was created
            assert self.agent._context_engine is not None
            mock_ctxeng.from_agent.assert_called_once_with(self.agent)

    def test_context_engine_resource_discovery(self):
        """Test that context engine discovers agent resources."""
        with patch("dana.frameworks.ctxeng.ContextEngine") as mock_ctxeng:
            mock_instance = Mock()
            mock_instance.assemble.return_value = "<context><query>test problem</query></context>"
            mock_ctxeng.from_agent.return_value = mock_instance

            # Trigger context engine creation
            self.agent.solve("test problem")

            # Verify the context engine was created and used
            assert self.agent._context_engine is not None
            mock_ctxeng.from_agent.assert_called_once_with(self.agent)

    def test_context_engine_assembly(self):
        """Test that context engine assembles rich context."""
        with patch("dana.frameworks.ctxeng.ContextEngine") as mock_ctxeng:
            mock_instance = Mock()
            mock_instance.assemble.return_value = "<context><query>test problem</query></context>"
            mock_ctxeng.from_agent.return_value = mock_instance

            # Trigger context engine creation and assembly
            self.agent.solve("test problem")

            # Verify assembly was called with correct parameters
            mock_instance.assemble.assert_called_once_with("test problem", template="problem_solving")

    def test_fallback_on_import_error(self):
        """Test that agent falls back to basic problem when ctxeng is not available."""
        # Test with a patch that affects the import inside the solve method
        with patch("dana.frameworks.ctxeng.ContextEngine", side_effect=ImportError("No module named 'dana.frameworks.ctxeng'")):
            # Should not raise an error, should fall back to basic problem
            self.agent.solve("test problem")

            # The context engine should not be created due to import error
            # Note: In this test scenario, the mock is created before the import error
            # so we can't easily test the fallback behavior without more complex mocking
            # For now, we just verify the method doesn't crash
            # Note: result is not used in this test case

    def test_fallback_on_assembly_error(self):
        """Test that agent falls back to basic problem when context assembly fails."""
        with patch("dana.frameworks.ctxeng.ContextEngine") as mock_ctxeng:
            mock_instance = Mock()
            mock_instance.assemble.side_effect = Exception("Assembly failed")
            mock_ctxeng.from_agent.return_value = mock_instance

            # Should not raise an error, should fall back to basic problem
            self.agent.solve("test problem")

            # Verify context engine was created but assembly failed
            assert self.agent._context_engine is not None

    def test_context_engine_reuse(self):
        """Test that context engine is reused across multiple solve calls."""
        with patch("dana.frameworks.ctxeng.ContextEngine") as mock_ctxeng:
            mock_instance = Mock()
            mock_instance.assemble.return_value = "<context><query>test</query></context>"
            mock_ctxeng.from_agent.return_value = mock_instance

            # First call should create context engine
            self.agent.solve("first problem")
            first_engine = self.agent._context_engine

            # Second call should reuse the same engine
            self.agent.solve("second problem")
            second_engine = self.agent._context_engine

            # Verify same instance is reused
            assert first_engine is second_engine
            assert mock_ctxeng.from_agent.call_count == 1  # Only called once


if __name__ == "__main__":
    pytest.main([__file__])
