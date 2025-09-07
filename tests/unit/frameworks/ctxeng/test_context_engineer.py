"""Tests for ContextEngineer functionality."""

from unittest.mock import Mock

import pytest

from dana.frameworks.ctxeng import ContextEngineer


class TestContextEngineer:
    """Test ContextEngineer functionality."""

    @pytest.fixture
    def context_engineer(self):
        """Create a ContextEngineer instance."""
        return ContextEngineer()

    @pytest.fixture
    def context_engineer_with_config(self):
        """Create a ContextEngineer instance with custom config."""
        return ContextEngineer(format_type="text", max_tokens=2000, relevance_threshold=0.8)

    def test_initialization(self, context_engineer):
        """Test ContextEngineer initialization."""
        assert context_engineer.format_type == "xml"
        assert context_engineer.max_tokens == 1500
        assert context_engineer.relevance_threshold == 0.7
        assert hasattr(context_engineer, "_template_manager")

    def test_initialization_with_config(self, context_engineer_with_config):
        """Test ContextEngineer initialization with custom config."""
        assert context_engineer_with_config.format_type == "text"
        assert context_engineer_with_config.max_tokens == 2000
        assert context_engineer_with_config.relevance_threshold == 0.8

    def test_engineer_context(self, context_engineer):
        """Test basic context engineering."""
        result = context_engineer.engineer_context("test query", {"key": "value"})

        assert isinstance(result, str)
        assert len(result) > 0
        assert "test query" in result

    def test_engineer_context_with_template(self, context_engineer):
        """Test context engineering with specific template."""
        result = context_engineer.engineer_context("solve this", template="problem_solving")

        assert isinstance(result, str)
        assert len(result) > 0
        assert "solve this" in result

    def test_get_available_templates(self, context_engineer):
        """Test getting available templates."""
        templates = context_engineer.get_available_templates()

        assert isinstance(templates, list)
        assert len(templates) > 0
        assert "problem_solving" in templates
        assert "conversation" in templates
        assert "analysis" in templates
        assert "general" in templates

    def test_get_template_info(self, context_engineer):
        """Test getting template information."""
        info = context_engineer.get_template_info("problem_solving")

        assert isinstance(info, dict)
        assert info["name"] == "problem_solving"
        assert info["format"] == "xml"
        assert "required_context" in info
        assert "optional_context" in info

    def test_from_agent_factory(self):
        """Test from_agent factory method."""
        mock_agent = Mock()
        engineer = ContextEngineer.from_agent(mock_agent)
        assert isinstance(engineer, ContextEngineer)

    def test_template_detection(self, context_engineer):
        """Test automatic template detection."""
        # Test problem solving detection
        result = context_engineer.engineer_context("solve this problem")
        assert isinstance(result, str)

        # Test conversation detection
        result = context_engineer.engineer_context("chat with me")
        assert isinstance(result, str)

        # Test analysis detection
        result = context_engineer.engineer_context("analyze this data")
        assert isinstance(result, str)


if __name__ == "__main__":
    pytest.main([__file__])
