"""
Tests for system prompt enhancement with resources and conversation context.

This module tests the system prompt enhancement functionality that automatically
adds resource information and conversation context to LLM prompts.
"""

import pytest
from unittest.mock import Mock, patch
from dana.core.agent.solvers.base import BaseSolver
from dana.core.agent.agent_instance import AgentInstance


class MockSolver(BaseSolver):
    """Mock solver for testing BaseSolver functionality."""

    def __init__(self, agent=None):
        if agent is None:
            agent = self._create_mock_agent()
        super().__init__(agent)

    def _create_mock_agent(self):
        """Create a mock agent with LLM resource."""
        mock_agent = Mock(spec=AgentInstance)

        # Mock LLM resource
        mock_llm = Mock()
        mock_llm.query_sync.return_value = Mock()
        mock_agent.llm_resource = mock_llm

        return mock_agent

    def solve_sync(self, problem_or_workflow, artifacts=None, sandbox_context=None, **kwargs):
        """Mock solve_sync implementation."""
        return "Mock solver response"


class TestSystemPromptEnhancement:
    """Test system prompt enhancement with resources and conversation context."""

    def test_enhance_system_prompt_with_resources_basic(self):
        """Test basic resource enhancement."""
        solver = MockSolver()

        # Mock resource registry
        mock_resource = Mock()
        mock_resource.kind = "browser"

        mock_ri = Mock()
        mock_ri.get_available_resources.return_value = {"web_browser": mock_resource}
        mock_ri._instance_metadata = {"web_browser": {"name": "web_browser"}}

        with patch.object(solver, "_inject_dependencies", return_value=(None, mock_ri, None)):
            system_prompt = "You are a helpful assistant."
            result = solver._enhance_system_prompt_with_resources(system_prompt)

            # Should add resources to system prompt
            assert "web_browser" in result
            assert "browser" in result
            assert "Browse websites" in result
            assert "<available_resources>" in result

    def test_enhance_system_prompt_with_placeholders(self):
        """Test system prompt with {available_resources} placeholder."""
        solver = MockSolver()

        # Mock resource registry
        mock_resource = Mock()
        mock_resource.kind = "browser"

        mock_ri = Mock()
        mock_ri.get_available_resources.return_value = {"web_browser": mock_resource}
        mock_ri._instance_metadata = {"web_browser": {"name": "web_browser"}}

        with patch.object(solver, "_inject_dependencies", return_value=(None, mock_ri, None)):
            system_prompt = "You are a helpful assistant.\n<available_resources>\n{available_resources}\n</available_resources>"
            result = solver._enhance_system_prompt_with_resources(system_prompt)

            # Should replace placeholder with actual resources
            assert "{available_resources}" not in result
            assert "web_browser" in result
            assert "browser" in result

    def test_enhance_system_prompt_with_conversation_context_placeholder(self):
        """Test system prompt with {conversation_context} placeholder."""
        solver = MockSolver()

        # Mock resource registry
        mock_resource = Mock()
        mock_resource.kind = "browser"

        mock_ri = Mock()
        mock_ri.get_available_resources.return_value = {"web_browser": mock_resource}
        mock_ri._instance_metadata = {"web_browser": {"name": "web_browser"}}

        with patch.object(solver, "_inject_dependencies", return_value=(None, mock_ri, None)):
            system_prompt = "You are a helpful assistant.\n<context>\n{conversation_context}\n</context>"
            result = solver._enhance_system_prompt_with_resources(system_prompt)

            # Should add resources and preserve conversation context placeholder
            assert "{conversation_context}" in result
            assert "web_browser" in result
            assert "<available_resources>" in result

    def test_enhance_system_prompt_both_placeholders(self):
        """Test system prompt with both placeholders."""
        solver = MockSolver()

        # Mock resource registry
        mock_resource = Mock()
        mock_resource.kind = "browser"

        mock_ri = Mock()
        mock_ri.get_available_resources.return_value = {"web_browser": mock_resource}
        mock_ri._instance_metadata = {"web_browser": {"name": "web_browser"}}

        with patch.object(solver, "_inject_dependencies", return_value=(None, mock_ri, None)):
            system_prompt = """You are a helpful assistant.
<context>
{conversation_context}
</context>
<available_resources>
{available_resources}
</available_resources>"""
            result = solver._enhance_system_prompt_with_resources(system_prompt)

            # Should replace available_resources placeholder
            assert "{available_resources}" not in result
            assert "{conversation_context}" in result
            assert "web_browser" in result

    def test_enhance_system_prompt_no_resources(self):
        """Test behavior when no resources are available."""
        solver = MockSolver()

        # Mock empty resource registry
        mock_ri = Mock()
        mock_ri.get_available_resources.return_value = {}

        with patch.object(solver, "_inject_dependencies", return_value=(None, mock_ri, None)):
            system_prompt = "You are a helpful assistant."
            result = solver._enhance_system_prompt_with_resources(system_prompt)

            # Should return original prompt unchanged
            assert result == system_prompt

    def test_enhance_system_prompt_no_resource_registry(self):
        """Test behavior when resource registry is not available."""
        solver = MockSolver()

        # Mock no resource registry
        with patch.object(solver, "_inject_dependencies", return_value=(None, None, None)):
            system_prompt = "You are a helpful assistant."
            result = solver._enhance_system_prompt_with_resources(system_prompt)

            # Should return original prompt unchanged
            assert result == system_prompt

    def test_enhance_system_prompt_error_handling(self):
        """Test error handling in system prompt enhancement."""
        solver = MockSolver()

        # Mock resource registry that raises exception
        mock_ri = Mock()
        mock_ri.get_available_resources.side_effect = Exception("Registry error")

        with patch.object(solver, "_inject_dependencies", return_value=(None, mock_ri, None)):
            system_prompt = "You are a helpful assistant."
            result = solver._enhance_system_prompt_with_resources(system_prompt)

            # Should return original prompt on error
            assert result == system_prompt

    def test_enhance_system_prompt_multiple_resources(self):
        """Test enhancement with multiple resources."""
        solver = MockSolver()

        # Mock multiple resources
        mock_browser = Mock()
        mock_browser.kind = "browser"

        mock_database = Mock()
        mock_database.kind = "database"
        mock_database.description = "Database access"

        mock_ri = Mock()
        mock_ri.get_available_resources.return_value = {"web_browser": mock_browser, "database": mock_database}
        mock_ri._instance_metadata = {"web_browser": {"name": "web_browser"}, "database": {"name": "database"}}

        with patch.object(solver, "_inject_dependencies", return_value=(None, mock_ri, None)):
            system_prompt = "You are a helpful assistant."
            result = solver._enhance_system_prompt_with_resources(system_prompt)

            # Should include both resources
            assert "web_browser" in result
            assert "database" in result
            assert "browser" in result
            assert "Database access" in result


class TestConversationContextFormatting:
    """Test conversation context formatting in system prompts."""

    def test_format_conversation_context_with_placeholder(self):
        """Test formatting conversation context with placeholder."""
        MockSolver()

        # Mock conversation context
        conversation_context = "User: Hello\nAssistant: Hi there!"

        system_prompt = "You are a helpful assistant.\n<context>\n{conversation_context}\n</context>"

        # Test the formatting logic
        if conversation_context and "{conversation_context}" in system_prompt:
            result = system_prompt.format(conversation_context=conversation_context)
        else:
            result = system_prompt

        # Should replace placeholder with actual context
        assert "{conversation_context}" not in result
        assert "User: Hello" in result
        assert "Assistant: Hi there!" in result

    def test_format_conversation_context_without_placeholder(self):
        """Test formatting conversation context without placeholder."""
        MockSolver()

        conversation_context = "User: Hello\nAssistant: Hi there!"
        system_prompt = "You are a helpful assistant."

        # Test the fallback logic
        if conversation_context and "{conversation_context}" in system_prompt:
            result = system_prompt.format(conversation_context=conversation_context)
        elif conversation_context:
            result = f"{system_prompt}\n\n{conversation_context}"
        else:
            result = system_prompt

        # Should append context
        assert "User: Hello" in result
        assert "Assistant: Hi there!" in result
        assert result.endswith("Assistant: Hi there!")

    def test_format_conversation_context_empty(self):
        """Test formatting with empty conversation context."""
        MockSolver()

        conversation_context = ""
        system_prompt = "You are a helpful assistant."

        # Test the logic
        if conversation_context and "{conversation_context}" in system_prompt:
            result = system_prompt.format(conversation_context=conversation_context)
        elif conversation_context:
            result = f"{system_prompt}\n\n{conversation_context}"
        else:
            result = system_prompt

        # Should return original prompt
        assert result == system_prompt


class TestResourceFormatting:
    """Test resource formatting for LLM consumption."""

    def test_format_resources_from_registry_basic(self):
        """Test basic resource formatting."""
        solver = MockSolver()

        # Mock browser resource
        mock_browser = Mock()
        mock_browser.kind = "browser"

        mock_ri = Mock()
        mock_ri._instance_metadata = {"web_browser": {"name": "web_browser"}}

        resources = {"web_browser": mock_browser}
        result = solver._format_resources_from_registry(resources, mock_ri)

        # Should format browser resource correctly
        assert "web_browser" in result
        assert "browser" in result
        assert "Browse websites" in result
        assert "query(url)" in result
        assert "web_browser.query" in result

    def test_format_resources_from_registry_multiple_resources(self):
        """Test formatting multiple resources."""
        solver = MockSolver()

        # Mock multiple resources
        mock_browser = Mock()
        mock_browser.kind = "browser"

        mock_database = Mock()
        mock_database.kind = "database"
        mock_database.description = "Database access"

        mock_ri = Mock()
        mock_ri._instance_metadata = {"web_browser": {"name": "web_browser"}, "database": {"name": "database"}}

        resources = {"web_browser": mock_browser, "database": mock_database}
        result = solver._format_resources_from_registry(resources, mock_ri)

        # Should format both resources
        assert "web_browser" in result
        assert "database" in result
        assert "Database access" in result
        assert "browser" in result

    def test_format_resources_from_registry_metadata_handling(self):
        """Test handling of resource metadata."""
        solver = MockSolver()

        # Mock resource with friendly name
        mock_resource = Mock()
        mock_resource.kind = "browser"

        mock_ri = Mock()
        mock_ri._instance_metadata = {"BrowserResource_123": {"name": "web_browser"}}

        resources = {"BrowserResource_123": mock_resource}
        result = solver._format_resources_from_registry(resources, mock_ri)

        # Should use friendly name from metadata
        assert "web_browser" in result
        assert "BrowserResource_123" not in result

    def test_format_resources_from_registry_fallback_to_instance_id(self):
        """Test fallback to instance_id when no metadata."""
        solver = MockSolver()

        # Mock resource without metadata
        mock_resource = Mock()
        mock_resource.kind = "browser"

        mock_ri = Mock()
        mock_ri._instance_metadata = {}

        resources = {"web_browser": mock_resource}
        result = solver._format_resources_from_registry(resources, mock_ri)

        # Should use instance_id as fallback
        assert "web_browser" in result

    def test_format_resources_from_registry_error_handling(self):
        """Test error handling in resource formatting."""
        solver = MockSolver()

        # Mock resource that raises exception during formatting
        mock_resource = Mock()
        mock_resource.kind = "browser"
        mock_resource.__str__ = Mock(side_effect=Exception("Formatting error"))

        mock_ri = Mock()
        mock_ri._instance_metadata = {"web_browser": {"name": "web_browser"}}

        resources = {"web_browser": mock_resource}
        result = solver._format_resources_from_registry(resources, mock_ri)

        # Should return error message or handle gracefully
        assert "Error" in result or "web_browser" in result


class TestGetAvailableResourcesText:
    """Test getting formatted available resources text."""

    def test_get_available_resources_text_basic(self):
        """Test basic resource text retrieval."""
        solver = MockSolver()

        # Mock resource registry
        mock_resource = Mock()
        mock_resource.kind = "browser"

        mock_ri = Mock()
        mock_ri.get_available_resources.return_value = {"web_browser": mock_resource}
        mock_ri._instance_metadata = {"web_browser": {"name": "web_browser"}}

        with patch.object(solver, "_inject_dependencies", return_value=(None, mock_ri, None)):
            result = solver._get_available_resources_text()

            # Should return formatted resources
            assert "web_browser" in result
            assert "browser" in result
            assert "Browse websites" in result

    def test_get_available_resources_text_no_resources(self):
        """Test behavior when no resources are available."""
        solver = MockSolver()

        # Mock empty resource registry
        mock_ri = Mock()
        mock_ri.get_available_resources.return_value = {}

        with patch.object(solver, "_inject_dependencies", return_value=(None, mock_ri, None)):
            result = solver._get_available_resources_text()

            # Should return no resources message
            assert result == "No resources available"

    def test_get_available_resources_text_no_registry(self):
        """Test behavior when resource registry is not available."""
        solver = MockSolver()

        # Mock no resource registry
        with patch.object(solver, "_inject_dependencies", return_value=(None, None, None)):
            result = solver._get_available_resources_text()

            # Should return no resources message
            assert result == "No resources available"

    def test_get_available_resources_text_error_handling(self):
        """Test error handling in resource text retrieval."""
        solver = MockSolver()

        # Mock resource registry that raises exception
        mock_ri = Mock()
        mock_ri.get_available_resources.side_effect = Exception("Registry error")

        with patch.object(solver, "_inject_dependencies", return_value=(None, mock_ri, None)):
            result = solver._get_available_resources_text()

            # Should return error message
            assert "Error" in result


if __name__ == "__main__":
    pytest.main([__file__])
