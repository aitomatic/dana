"""
Tests for the ResourceHandlingMixin.

This module tests the resource handling functionality that was extracted from BaseSolver
into a separate mixin for better code organization.
"""

import pytest
from unittest.mock import Mock, patch

from dana.core.agent.solvers.mixins.resource_handling import ResourceHandlingMixin
from dana.core.agent.solvers.base import BaseSolver


class TestResourceHandlingMixin:
    """Test the ResourceHandlingMixin functionality."""

    def create_mock_agent(self):
        """Create a mock agent for testing."""
        mock_agent = Mock()
        mock_agent.llm_resource = None
        return mock_agent

    def create_test_solver(self):
        """Create a test solver that combines BaseSolver and ResourceHandlingMixin."""

        class TestSolver(BaseSolver, ResourceHandlingMixin):
            def solve_sync(self, problem_or_workflow, artifacts=None, sandbox_context=None, **kwargs):
                return {"result": "test"}

        return TestSolver(self.create_mock_agent())

    def create_mock_resource_registry(self):
        """Create a mock resource registry for testing."""
        mock_registry = Mock()
        mock_resource = Mock()
        mock_resource.query.return_value = {
            "url": "https://example.com",
            "status_code": 200,
            "success": True,
            "content": "<html><body>Test content</body></html>",
        }

        mock_registry.get_available_resources.return_value = {"web_browser": mock_resource}

        # Add metadata for friendly name lookup
        mock_registry._instance_metadata = {"web_browser": {"name": "web_browser"}}

        return mock_registry, mock_resource

    def test_extract_post_processing_prompt(self):
        """Test extraction of POST_PROCESSING_PROMPT from LLM response."""
        mixin = ResourceHandlingMixin()

        # Test with valid POST_PROCESSING_PROMPT
        response = 'Some text\nPOST_PROCESSING_PROMPT: "Extract headlines and format as list"\nMore text'
        prompt = mixin._extract_post_processing_prompt(response)
        assert prompt == "Extract headlines and format as list"

        # Test with no POST_PROCESSING_PROMPT
        response = "Some text without POST_PROCESSING_PROMPT"
        prompt = mixin._extract_post_processing_prompt(response)
        assert prompt is None

        # Test with malformed POST_PROCESSING_PROMPT
        response = 'POST_PROCESSING_PROMPT: "Unclosed quote'
        prompt = mixin._extract_post_processing_prompt(response)
        assert prompt is None

    def test_get_smart_truncation_limit(self):
        """Test smart truncation limit calculation."""
        mixin = ResourceHandlingMixin()

        limit = mixin._get_smart_truncation_limit()
        assert limit == 15000  # Should return the default value

    def test_format_resources_from_registry(self):
        """Test formatting resources from registry."""
        mixin = ResourceHandlingMixin()

        # Create mock resource
        mock_resource = Mock()
        mock_resource.__class__.__name__ = "BrowserResource"

        # Mock dir() to return some methods
        with patch(
            "builtins.dir",
            return_value=["query", "browse", "get_content", "method1", "method2", "method3", "method4", "method5", "method6"],
        ):
            resources = {"web_browser": mock_resource}
            mock_ri = Mock()
            mock_ri._instance_metadata = {"web_browser": {"name": "web_browser"}}

            result = mixin._format_resources_from_registry(resources, mock_ri)

            assert "web_browser (BrowserResource):" in result
            assert "query, browse, get_content, method1, method2" in result
            assert "(and 4 more)" in result  # Should truncate after 5 methods

    def test_get_available_resources_text(self):
        """Test getting available resources text."""
        solver = self.create_test_solver()

        # Mock _inject_dependencies to return a resource registry
        mock_ri, mock_resource = self.create_mock_resource_registry()

        with patch.object(solver, "_inject_dependencies", return_value=(None, mock_ri, None)):
            result = solver._get_available_resources_text()

            assert "web_browser" in result
            # The class name will be Mock in tests, not BrowserResource
            assert "Mock" in result or "BrowserResource" in result

    def test_enhance_system_prompt_with_resources(self):
        """Test enhancing system prompt with resources."""
        mixin = ResourceHandlingMixin()

        with patch.object(mixin, "_get_available_resources_text", return_value="- web_browser: query, browse"):
            result = mixin._enhance_system_prompt_with_resources("Original prompt")

            assert "Original prompt" in result
            assert "<available_resources>" in result
            assert "web_browser: query, browse" in result

    def test_process_resource_calls_legacy(self):
        """Test the legacy _process_resource_calls method."""
        mixin = ResourceHandlingMixin()

        # Test with no resource calls
        response = "No resource calls here"
        result = mixin._process_resource_calls(response)
        assert result == response

        # Test with resource calls
        response = 'RESOURCE_CALL: web_browser.query("https://example.com")'
        with patch.object(mixin, "_execute_resource_calls", return_value="Processed response"):
            result = mixin._process_resource_calls(response)
            assert result == "Processed response"

    def test_execute_resource_calls_basic(self):
        """Test basic resource call execution."""
        solver = self.create_test_solver()

        # Mock _inject_dependencies
        mock_ri, mock_resource = self.create_mock_resource_registry()

        with patch.object(solver, "_inject_dependencies", return_value=(None, mock_ri, None)):
            response = 'RESOURCE_CALL: web_browser.query("https://example.com")'
            result = solver._execute_resource_calls(response)

            # Should execute the resource call and replace it in the response
            assert "Resource calls executed successfully:" in result
            assert "web_browser.query:" in result
            assert "https://example.com" in result

    def test_execute_resource_calls_no_matches(self):
        """Test resource call execution with no matches."""
        mixin = ResourceHandlingMixin()

        response = "No resource calls in this response"
        result = mixin._execute_resource_calls(response)

        assert result == response

    def test_execute_resource_calls_resource_not_found(self):
        """Test resource call execution when resource is not found."""
        solver = self.create_test_solver()

        # Mock registry with no resources
        mock_ri = Mock()
        mock_ri.get_available_resources.return_value = {}

        with patch.object(solver, "_inject_dependencies", return_value=(None, mock_ri, None)):
            response = 'RESOURCE_CALL: nonexistent.query("test")'
            result = solver._execute_resource_calls(response)

            # When no resources are available, the original response should be returned
            assert result == response

    def test_execute_resources_iteratively_basic(self):
        """Test iterative resource execution."""
        solver = self.create_test_solver()

        # Mock _inject_dependencies
        mock_ri, mock_resource = self.create_mock_resource_registry()

        with patch.object(solver, "_inject_dependencies", return_value=(None, mock_ri, None)):
            response = 'RESOURCE_CALL: web_browser.query("https://example.com")'
            system_prompt = "Test system prompt"

            with patch.object(solver, "_process_with_standard_flow", return_value="Processed response"):
                result = solver._execute_resources_iteratively(response, system_prompt)

                assert result == "Processed response"

    def test_execute_resources_iteratively_with_post_processing(self):
        """Test iterative resource execution with POST_PROCESSING_PROMPT."""
        solver = self.create_test_solver()

        # Mock _inject_dependencies
        mock_ri, mock_resource = self.create_mock_resource_registry()

        with patch.object(solver, "_inject_dependencies", return_value=(None, mock_ri, None)):
            response = '''RESOURCE_CALL: web_browser.query("https://example.com")
POST_PROCESSING_PROMPT: "Extract headlines and format as list"'''
            system_prompt = "Test system prompt"

            with (
                patch.object(solver, "_process_with_post_processing_prompt", return_value="Processed content"),
                patch.object(solver, "_continue_conversation_with_processed_content", return_value="Final response"),
            ):
                result = solver._execute_resources_iteratively(response, system_prompt)

                assert result == "Final response"

    def test_process_with_post_processing_prompt(self):
        """Test processing with POST_PROCESSING_PROMPT."""
        ResourceHandlingMixin()

        # Mock LLM response
        mock_agent = self.create_mock_agent()
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "Processed headlines:\n- Headline 1\n- Headline 2"
        mock_llm.query_sync.return_value = mock_response
        mock_agent.llm_resource = mock_llm

        # Create a mock solver with the agent
        class MockSolver(ResourceHandlingMixin):
            def __init__(self, agent):
                self.agent = agent

            def _query_llm_with_prteng(self, prompt, system_prompt, max_turns=1):
                return mock_llm.query_sync(Mock()).content

        solver = MockSolver(mock_agent)

        resource_results = [
            {
                "resource_name": "web_browser",
                "result_str": "<html><h1>Headline 1</h1><h2>Headline 2</h2></html>",
                "url": "https://example.com",
            }
        ]

        result = solver._process_with_post_processing_prompt(
            "Original response", resource_results, "Extract headlines and format as list", "System prompt", 1
        )

        assert "Processed headlines:" in result
        assert "Headline 1" in result
        assert "Headline 2" in result

    def test_process_with_standard_flow(self):
        """Test processing with standard flow."""
        ResourceHandlingMixin()

        # Mock LLM response
        mock_agent = self.create_mock_agent()
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "Here's the information from the website: Test content"
        mock_llm.query_sync.return_value = mock_response
        mock_agent.llm_resource = mock_llm

        # Create a mock solver with the agent
        class MockSolver(ResourceHandlingMixin):
            def __init__(self, agent):
                self.agent = agent

            def _query_llm_with_prteng(self, prompt, system_prompt):
                return mock_llm.query_sync(Mock()).content

        solver = MockSolver(mock_agent)

        resource_results = [
            {"resource_name": "web_browser", "result_str": "<html><body>Test content</body></html>", "url": "https://example.com"}
        ]

        result = solver._process_with_standard_flow("Original response", resource_results, "System prompt", 1)

        assert "Here's the information from the website:" in result
        assert "Test content" in result

    def test_continue_conversation_with_processed_content(self):
        """Test continuing conversation with processed content."""
        ResourceHandlingMixin()

        # Mock LLM response
        mock_agent = self.create_mock_agent()
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "Based on the processed content, here's what I found: Summary of information"
        mock_llm.query_sync.return_value = mock_response
        mock_agent.llm_resource = mock_llm

        # Create a mock solver with the agent
        class MockSolver(ResourceHandlingMixin):
            def __init__(self, agent):
                self.agent = agent

            def _query_llm_with_prteng(self, prompt, system_prompt):
                return mock_llm.query_sync(Mock()).content

        solver = MockSolver(mock_agent)

        result = solver._continue_conversation_with_processed_content("Original response", "Processed content summary", "System prompt", 1)

        assert "Based on the processed content" in result
        assert "Summary of information" in result

    def test_execute_resources_iteratively_max_iterations(self):
        """Test that iterative execution respects max iterations."""
        solver = self.create_test_solver()

        # Mock _inject_dependencies to return None (no resources)
        with patch.object(solver, "_inject_dependencies", return_value=(None, None, None)):
            response = 'RESOURCE_CALL: web_browser.query("https://example.com")'
            system_prompt = "Test system prompt"

            result = solver._execute_resources_iteratively(response, system_prompt)

            # Should return the original response when no resources are available
            assert result == response

    def test_execute_resources_iteratively_no_resource_calls(self):
        """Test iterative execution with no resource calls."""
        mixin = ResourceHandlingMixin()

        response = "No resource calls here"
        system_prompt = "Test system prompt"

        result = mixin._execute_resources_iteratively(response, system_prompt)

        assert result == response

    def test_resource_call_parsing(self):
        """Test parsing of different resource call formats."""
        solver = self.create_test_solver()

        # Mock _inject_dependencies
        mock_ri, mock_resource = self.create_mock_resource_registry()

        with patch.object(solver, "_inject_dependencies", return_value=(None, mock_ri, None)):
            # Test with quoted string argument
            response = 'RESOURCE_CALL: web_browser.query("https://example.com")'
            result = solver._execute_resource_calls(response)
            assert "Resource calls executed successfully:" in result
            assert "web_browser.query:" in result

            # Test with unquoted string argument
            response = "RESOURCE_CALL: web_browser.query(https://example.com)"
            result = solver._execute_resource_calls(response)
            assert "Resource calls executed successfully:" in result
            assert "web_browser.query:" in result

            # Test with boolean argument
            response = "RESOURCE_CALL: web_browser.query(true)"
            result = solver._execute_resource_calls(response)
            assert "Resource calls executed successfully:" in result
            assert "web_browser.query:" in result

            # Test with numeric argument
            response = "RESOURCE_CALL: web_browser.query(123)"
            result = solver._execute_resource_calls(response)
            assert "Resource calls executed successfully:" in result
            assert "web_browser.query:" in result

    def test_error_handling_in_resource_execution(self):
        """Test error handling during resource execution."""
        solver = self.create_test_solver()

        # Mock registry with a resource that raises an exception
        mock_ri = Mock()
        mock_resource = Mock()
        mock_resource.query.side_effect = Exception("Resource execution failed")
        mock_ri.get_available_resources.return_value = {"web_browser": mock_resource}
        mock_ri._instance_metadata = {"web_browser": {"name": "web_browser"}}

        with patch.object(solver, "_inject_dependencies", return_value=(None, mock_ri, None)):
            response = 'RESOURCE_CALL: web_browser.query("https://example.com")'
            result = solver._execute_resource_calls(response)

            # When resource execution fails, the original response should be returned
            assert result == response

    def test_friendly_name_lookup(self):
        """Test resource lookup by friendly name."""
        solver = self.create_test_solver()

        # Mock registry with friendly name metadata
        mock_ri = Mock()
        mock_resource = Mock()
        mock_resource.query.return_value = {"content": "Test content"}
        mock_ri.get_available_resources.return_value = {"browser_instance_123": mock_resource}
        mock_ri._instance_metadata = {"browser_instance_123": {"name": "web_browser"}}

        with patch.object(solver, "_inject_dependencies", return_value=(None, mock_ri, None)):
            response = 'RESOURCE_CALL: web_browser.query("https://example.com")'
            result = solver._execute_resource_calls(response)

            assert "Resource calls executed successfully:" in result
            assert "web_browser.query:" in result

    def test_url_extraction_for_resource_context(self):
        """Test URL extraction for resource context formatting."""
        solver = self.create_test_solver()

        # Mock _inject_dependencies
        mock_ri, mock_resource = self.create_mock_resource_registry()

        with patch.object(solver, "_inject_dependencies", return_value=(None, mock_ri, None)):
            response = 'RESOURCE_CALL: web_browser.query("https://example.com")'

            with patch.object(solver, "_process_with_standard_flow") as mock_process:
                mock_process.return_value = "Processed response"

                solver._execute_resources_iteratively(response, "System prompt")

                # Check that the resource results include the URL
                call_args = mock_process.call_args[0]
                resource_results = call_args[1]
                assert resource_results[0]["url"] == "https://example.com"


class TestBaseSolverWithResourceHandlingMixin:
    """Test BaseSolver with ResourceHandlingMixin integration."""

    def create_mock_agent(self):
        """Create a mock agent for testing."""
        mock_agent = Mock()
        mock_agent.llm_resource = None
        return mock_agent

    def create_test_solver(self):
        """Create a test solver that combines BaseSolver and ResourceHandlingMixin."""

        class TestSolver(BaseSolver, ResourceHandlingMixin):
            def solve_sync(self, problem_or_workflow, artifacts=None, sandbox_context=None, **kwargs):
                return {"result": "test"}

        return TestSolver(self.create_mock_agent())

    def test_base_solver_inherits_resource_handling(self):
        """Test that BaseSolver inherits ResourceHandlingMixin methods."""
        solver = self.create_test_solver()

        # Check that resource handling methods are available
        assert hasattr(solver, "_execute_resource_calls")
        assert hasattr(solver, "_execute_resources_iteratively")
        assert hasattr(solver, "_extract_post_processing_prompt")
        assert hasattr(solver, "_get_smart_truncation_limit")
        assert hasattr(solver, "_process_with_post_processing_prompt")
        assert hasattr(solver, "_process_with_standard_flow")
        assert hasattr(solver, "_continue_conversation_with_processed_content")
        assert hasattr(solver, "_get_available_resources_text")
        assert hasattr(solver, "_enhance_system_prompt_with_resources")
        assert hasattr(solver, "_format_resources_from_registry")
        assert hasattr(solver, "_process_resource_calls")

    def test_base_solver_resource_handling_integration(self):
        """Test that BaseSolver can use resource handling methods."""
        solver = self.create_test_solver()

        # Test that we can call resource handling methods
        response = 'RESOURCE_CALL: web_browser.query("https://example.com")'

        # Mock the dependencies
        mock_ri = Mock()
        mock_resource = Mock()
        mock_resource.query.return_value = {"content": "Test content"}
        mock_ri.get_available_resources.return_value = {"web_browser": mock_resource}
        mock_ri._instance_metadata = {"web_browser": {"name": "web_browser"}}

        with patch.object(solver, "_inject_dependencies", return_value=(None, mock_ri, None)):
            result = solver._execute_resource_calls(response)

            assert "Resource calls executed successfully:" in result
            assert "web_browser.query:" in result

    def test_base_solver_llm_query_with_resource_handling(self):
        """Test that BaseSolver's LLM query method works with resource handling."""
        mock_agent = self.create_mock_agent()
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = 'RESOURCE_CALL: web_browser.query("https://example.com")'
        mock_llm.query_sync.return_value = mock_response
        mock_agent.llm_resource = mock_llm

        solver = self.create_test_solver()
        solver.agent = mock_agent

        # Mock the resource execution
        with patch.object(solver, "_execute_resources_iteratively", return_value="Processed with resources"):
            result = solver._query_llm_with_prteng("Test prompt", "System prompt")

            assert result == "Processed with resources"


if __name__ == "__main__":
    pytest.main([__file__])
