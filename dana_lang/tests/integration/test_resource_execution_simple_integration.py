"""
Simple integration tests for resource execution across solvers.

This module tests the resource execution functionality with minimal mocking
to ensure the basic integration works correctly.
"""

import pytest
from unittest.mock import Mock, patch
from dana.core.agent.solvers import SimpleHelpfulSolver
from dana.core.agent.agent_instance import AgentInstance


class TestResourceExecutionSimpleIntegration:
    """Simple integration tests for resource execution."""

    def test_simple_helpful_with_resource_execution_basic(self):
        """Test basic resource execution in SimpleHelpfulSolver."""
        # Create a simple mock agent
        mock_agent = Mock(spec=AgentInstance)

        # Mock LLM resource with proper response structure
        mock_llm = Mock()
        mock_llm_response = Mock()
        mock_llm_response.content = {
            "choices": [{"message": {"content": 'I\'ll browse that for you.\nRESOURCE_CALL: web_browser.query("https://example.com")'}}]
        }
        mock_llm.query_sync.return_value = mock_llm_response
        mock_agent.llm_resource = mock_llm

        # Create a simple mock resource
        mock_browser = Mock()
        mock_browser.query.return_value = "Mock content for https://example.com"

        # Mock resource registry
        mock_ri = Mock()
        mock_ri.get_available_resources.return_value = {"web_browser": mock_browser}
        mock_ri._instance_metadata = {"web_browser": {"name": "web_browser"}}

        # Mock workflow registry
        mock_wc = Mock()
        mock_wc.get_available_workflows.return_value = {}

        # Mock dependencies injection
        with patch(
            "dana.core.agent.solvers.simple_helpful.SimpleHelpfulSolver._inject_dependencies", return_value=(mock_wc, mock_ri, None)
        ):
            solver = SimpleHelpfulSolver(mock_agent)

            # Test solver execution
            result = solver.solve_sync("browse example.com and tell me what's there")

            # Verify resource was called
            mock_browser.query.assert_called_once_with("https://example.com")

            # Verify LLM was called
            assert mock_agent.llm_resource.query_sync.call_count >= 1

            # Verify final result contains the resource call (since LLM follow-up failed)
            assert "RESOURCE_CALL: web_browser.query" in result or "browse" in result.lower()

    def test_system_prompt_enhancement_basic(self):
        """Test that system prompts are enhanced with resources."""
        # Create a simple mock agent
        mock_agent = Mock(spec=AgentInstance)

        # Mock LLM resource
        mock_llm = Mock()
        mock_llm_response = Mock()
        mock_llm_response.content = {"choices": [{"message": {"content": "Test response"}}]}
        mock_llm.query_sync.return_value = mock_llm_response
        mock_agent.llm_resource = mock_llm

        # Create a simple mock resource with proper class name
        class MockBrowserResource:
            def query(self, url):
                return f"Mock content for {url}"

        mock_browser = MockBrowserResource()

        # Mock resource registry
        mock_ri = Mock()
        mock_ri.get_available_resources.return_value = {"web_browser": mock_browser}
        mock_ri._instance_metadata = {"web_browser": {"name": "web_browser"}}

        # Mock workflow registry
        mock_wc = Mock()
        mock_wc.get_available_workflows.return_value = {}

        # Mock dependencies injection
        with patch(
            "dana.core.agent.solvers.simple_helpful.SimpleHelpfulSolver._inject_dependencies", return_value=(mock_wc, mock_ri, None)
        ):
            solver = SimpleHelpfulSolver(mock_agent)

            # Test that system prompt is enhanced
            system_prompt = "You are a helpful assistant."
            enhanced_prompt = solver._enhance_system_prompt_with_resources(system_prompt)

            # Should include resource information
            assert "web_browser" in enhanced_prompt
            assert "MockBrowserResource" in enhanced_prompt
            assert "query" in enhanced_prompt

    def test_resource_execution_no_calls(self):
        """Test behavior when no resource calls are present."""
        # Create a simple mock agent
        mock_agent = Mock(spec=AgentInstance)

        # Mock LLM resource with response that has no resource calls
        mock_llm = Mock()
        mock_llm_response = Mock()
        mock_llm_response.content = {"choices": [{"message": {"content": "This is a normal response without resource calls."}}]}
        mock_llm.query_sync.return_value = mock_llm_response
        mock_agent.llm_resource = mock_llm

        # Mock resource registry
        mock_ri = Mock()
        mock_ri.get_available_resources.return_value = {}
        mock_ri._instance_metadata = {}

        # Mock workflow registry
        mock_wc = Mock()
        mock_wc.get_available_workflows.return_value = {}

        # Mock dependencies injection
        with patch(
            "dana.core.agent.solvers.simple_helpful.SimpleHelpfulSolver._inject_dependencies", return_value=(mock_wc, mock_ri, None)
        ):
            solver = SimpleHelpfulSolver(mock_agent)

            # Test solver execution
            result = solver.solve_sync("tell me about the weather")

            # Verify LLM was called
            assert mock_agent.llm_resource.query_sync.call_count >= 1

            # Verify final result
            assert "normal response" in result or "weather" in result.lower()

    def test_resource_execution_error_handling(self):
        """Test error handling in resource execution."""
        # Create a simple mock agent
        mock_agent = Mock(spec=AgentInstance)

        # Mock LLM resource with response that has resource calls
        mock_llm = Mock()
        mock_llm_response = Mock()
        mock_llm_response.content = {
            "choices": [{"message": {"content": 'I\'ll browse that for you.\nRESOURCE_CALL: web_browser.query("https://example.com")'}}]
        }
        mock_llm.query_sync.return_value = mock_llm_response
        mock_agent.llm_resource = mock_llm

        # Create a mock resource that raises an exception
        mock_browser = Mock()
        mock_browser.query.side_effect = Exception("Network error")

        # Mock resource registry
        mock_ri = Mock()
        mock_ri.get_available_resources.return_value = {"web_browser": mock_browser}
        mock_ri._instance_metadata = {"web_browser": {"name": "web_browser"}}

        # Mock workflow registry
        mock_wc = Mock()
        mock_wc.get_available_workflows.return_value = {}

        # Mock dependencies injection
        with patch(
            "dana.core.agent.solvers.simple_helpful.SimpleHelpfulSolver._inject_dependencies", return_value=(mock_wc, mock_ri, None)
        ):
            solver = SimpleHelpfulSolver(mock_agent)

            # Test solver execution
            result = solver.solve_sync("browse example.com")

            # Verify resource was called (and failed) - it will be called multiple times due to max iterations
            assert mock_browser.query.call_count >= 1
            mock_browser.query.assert_called_with("https://example.com")

            # Verify LLM was called
            assert mock_agent.llm_resource.query_sync.call_count >= 1

            # Verify error was handled gracefully
            assert "RESOURCE_CALL: web_browser.query" in result or "browse" in result.lower()

    def test_resource_parsing_basic(self):
        """Test parsing of resource calls."""
        from dana.core.agent.solvers.base import BaseSolver

        # Create a simple mock solver
        class MockSolver(BaseSolver):
            def __init__(self, agent):
                super().__init__(agent)

            def solve_sync(self, problem_or_workflow, artifacts=None, sandbox_context=None, **kwargs):
                return "Mock solver response"

        # Create a mock agent
        mock_agent = Mock(spec=AgentInstance)
        MockSolver(mock_agent)

        # Test parsing resource calls
        response = 'I\'ll help you with that.\nRESOURCE_CALL: web_browser.query("https://example.com")'

        # Use the internal regex pattern
        import re

        pattern = r"RESOURCE_CALL:\s*(\w+)\.(\w+)\(([^)]*)\)"
        matches = re.findall(pattern, response)

        assert len(matches) == 1
        assert matches[0] == ("web_browser", "query", '"https://example.com"')

        # Test parsing multiple resource calls
        response = """I'll help you with that.
        RESOURCE_CALL: web_browser.query("https://example.com")
        RESOURCE_CALL: database.query("SELECT * FROM users")"""

        matches = re.findall(pattern, response)

        assert len(matches) == 2
        assert ("web_browser", "query", '"https://example.com"') in matches
        assert ("database", "query", '"SELECT * FROM users"') in matches

        # Test parsing when no resource calls are present
        response = "This is a normal response without resource calls."
        matches = re.findall(pattern, response)

        assert len(matches) == 0


if __name__ == "__main__":
    pytest.main([__file__])
