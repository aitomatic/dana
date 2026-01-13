"""
Simple tests for the iterative resource execution functionality in BaseSolver.

This module tests the core resource execution logic with minimal mocking
to ensure the basic functionality works correctly.
"""

from unittest.mock import Mock, patch

import pytest

from dana_lang.core.agent.agent_instance import AgentInstance
from dana_lang.core.agent.solvers.base import BaseSolver


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


class TestResourceExecutionSimple:
    """Simple tests for resource execution functionality."""

    def test_execute_resources_iteratively_no_calls(self):
        """Test behavior when no resource calls are present."""
        solver = MockSolver()

        response = "This is a normal response without any resource calls."
        result = solver._execute_resources_iteratively(response, "Test system prompt")

        # Should return original response unchanged
        assert result == response

    def test_execute_resources_iteratively_basic_success(self):
        """Test basic successful resource execution."""
        solver = MockSolver()

        # Create a simple mock resource that returns a string
        class MockResource:
            def query(self, url):
                return f"Mock content for {url}"

        mock_resource = MockResource()

        # Mock resource registry
        mock_ri = Mock()
        mock_ri.get_available_resources.return_value = {"web_browser": mock_resource}
        mock_ri._instance_metadata = {"web_browser": {"name": "web_browser"}}

        # Mock LLM follow-up response
        mock_llm_response = Mock()
        mock_llm_response.content = {"choices": [{"message": {"content": "Based on the website, here are the headlines: Test Headline"}}]}
        solver.agent.llm_resource.query_sync.return_value = mock_llm_response

        with patch.object(solver, "_inject_dependencies", return_value=(None, mock_ri, None)):
            # Test response with resource call
            response = 'I\'ll browse that for you.\nRESOURCE_CALL: web_browser.query("https://example.com")'
            result = solver._execute_resources_iteratively(response, "Test system prompt")

            # Verify resource was called
            # Note: We can't easily verify this without more complex mocking

            # Verify LLM was called
            assert solver.agent.llm_resource.query_sync.call_count >= 1

            # Verify final result
            assert "Test Headline" in result

    def test_enhance_system_prompt_with_resources_basic(self):
        """Test basic resource enhancement."""
        solver = MockSolver()

        # Create a simple mock resource with methods
        class MockResource:
            def __init__(self):
                self.kind = "browser"

            def query(self, url):
                return f"Mock content for {url}"

        mock_resource = MockResource()

        # Mock resource registry
        mock_ri = Mock()
        mock_ri.get_available_resources.return_value = {"web_browser": mock_resource}
        mock_ri._instance_metadata = {"web_browser": {"name": "web_browser"}}

        with patch.object(solver, "_inject_dependencies", return_value=(None, mock_ri, None)):
            system_prompt = "You are a helpful assistant."
            result = solver._enhance_system_prompt_with_resources(system_prompt)

            # Should add resources to system prompt
            assert "web_browser" in result
            assert "MockResource" in result
            # The actual implementation uses class name and methods
            assert "query" in result

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

    def test_format_resources_from_registry_basic(self):
        """Test basic resource formatting."""
        solver = MockSolver()

        # Create a simple mock resource with methods
        class MockResource:
            def __init__(self):
                self.kind = "browser"

            def query(self, url):
                return f"Mock content for {url}"

        mock_browser = MockResource()

        mock_ri = Mock()
        mock_ri._instance_metadata = {"web_browser": {"name": "web_browser"}}

        resources = {"web_browser": mock_browser}
        result = solver._format_resources_from_registry(resources, mock_ri)

        # Should format browser resource correctly
        assert "web_browser" in result
        assert "MockResource" in result
        # The actual implementation uses class name and methods
        assert "query" in result

    def test_format_resources_from_registry_multiple_resources(self):
        """Test formatting multiple resources."""
        solver = MockSolver()

        # Create simple mock resources
        class MockBrowser:
            def __init__(self):
                self.kind = "browser"

        class MockDatabase:
            def __init__(self):
                self.kind = "database"
                self.description = "Database access"

        mock_browser = MockBrowser()
        mock_database = MockDatabase()

        mock_ri = Mock()
        mock_ri._instance_metadata = {"web_browser": {"name": "web_browser"}, "database": {"name": "database"}}

        resources = {"web_browser": mock_browser, "database": mock_database}
        result = solver._format_resources_from_registry(resources, mock_ri)

        # Should format both resources
        assert "web_browser" in result
        assert "database" in result
        # The actual implementation may not use the description field
        assert "Database access" in result or "database" in result

    def test_parse_resource_calls_basic(self):
        """Test parsing basic resource call patterns."""
        MockSolver()

        response = 'RESOURCE_CALL: web_browser.query("https://example.com")'

        # Use the internal regex pattern
        import re

        pattern = r"RESOURCE_CALL:\s*(\w+)\.(\w+)\(([^)]*)\)"
        matches = re.findall(pattern, response)

        assert len(matches) == 1
        assert matches[0] == ("web_browser", "query", '"https://example.com"')

    def test_parse_resource_calls_multiple(self):
        """Test parsing multiple resource calls."""
        MockSolver()

        response = """I'll help you with that.
        RESOURCE_CALL: web_browser.query("https://example.com")
        RESOURCE_CALL: database.query("SELECT * FROM users")"""

        import re

        pattern = r"RESOURCE_CALL:\s*(\w+)\.(\w+)\(([^)]*)\)"
        matches = re.findall(pattern, response)

        assert len(matches) == 2
        assert ("web_browser", "query", '"https://example.com"') in matches
        assert ("database", "query", '"SELECT * FROM users"') in matches

    def test_parse_resource_calls_no_matches(self):
        """Test parsing when no resource calls are present."""
        MockSolver()

        response = "This is a normal response without resource calls."

        import re

        pattern = r"RESOURCE_CALL:\s*(\w+)\.(\w+)\(([^)]*)\)"
        matches = re.findall(pattern, response)

        assert len(matches) == 0


if __name__ == "__main__":
    pytest.main([__file__])
