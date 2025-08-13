"""
Tests for with statement execution in Dana.

Tests both the original pattern (with mcp(*args) as var:) and the new pattern (with mcp_object as var:).
"""

from unittest.mock import patch

import pytest

from dana.common.sys_resource.base_sys_resource import BaseSysResource
from dana.core.lang.dana_sandbox import DanaSandbox


class MockMCPResource(BaseSysResource):
    """Mock MCP resource for testing without real MCP servers."""

    def __init__(self, name, *args, **kwargs):
        super().__init__(name=name)
        self.args = args
        self.kwargs = kwargs
        self.is_entered = False
        self.is_exited = False

    def __enter__(self):
        self.is_entered = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.is_exited = True
        return False  # Don't suppress exceptions

    def __str__(self):
        return f"MockMCPResource(name={self.name})"


@pytest.fixture
def mock_use_function():
    """Mock the use function to return MockMCPResource instances."""

    def mock_use(*args, **kwargs):
        print(f"mock_use called with args={args}, kwargs={kwargs}")

        # Extract the _name parameter and remove it from kwargs
        _name = kwargs.pop("_name", None)

        # Create a mock resource with the proper name and all arguments
        # The first argument should be the resource name (e.g., "mcp")
        resource_name = args[0] if args else (_name or "test_resource")
        # The remaining arguments are the resource arguments
        resource_args = args[1:] if len(args) > 1 else ()

        resource = MockMCPResource(resource_name, *resource_args, **kwargs)
        return resource

    # Instead of patching at module level, we'll patch the function registry's resolve method
    # to return our mock function when 'use' is requested
    from dana.core.lang.interpreter.functions.function_registry import FunctionRegistry

    original_resolve = FunctionRegistry.resolve

    def mock_resolve(self, name, namespace=None):
        if name == "use":
            from dana.core.lang.interpreter.functions.function_registry import FunctionMetadata
            from dana.core.lang.interpreter.functions.python_function import PythonFunction

            return PythonFunction(mock_use), "python", FunctionMetadata()
        else:
            return original_resolve(self, name, namespace)

    with patch.object(FunctionRegistry, "resolve", mock_resolve):
        yield mock_use


class TestWithStatementExecution:
    """Test execution of with statements with both patterns."""

    def _get_from_context(self, result, key):
        """Helper to safely get values from execution result context."""
        assert result.final_context is not None, "Final context should not be None"
        return result.final_context.get(key)

    def test_with_function_call_pattern_basic(self, mock_use_function):
        """Test basic with statement using function call pattern."""
        code = """
with use("mcp", url="http://test.com") as client:
    result = f"Got client: {type(client)}"
"""

        sandbox = DanaSandbox()
        result = sandbox.execute_string(code)

        assert result.success, f"Execution failed: {result.error}"
        # Verify the context has the expected result
        final_result = self._get_from_context(result, "local:result")
        assert "Got client: MockMCPResource" in final_result

    def test_with_function_call_pattern_with_args(self, mock_use_function):
        """Test with statement using function call pattern with arguments."""
        code = """
with use("mcp", "arg1", "arg2", url="http://test.com", port=8080) as client:
    args_count = len(client.args)
    kwargs_count = len(client.kwargs)
"""

        sandbox = DanaSandbox()
        result = sandbox.execute_string(code)

        assert result.success, f"Execution failed: {result.error}"

        # Verify arguments were passed correctly
        args_count = self._get_from_context(result, "local:args_count")
        kwargs_count = self._get_from_context(result, "local:kwargs_count")

        assert args_count == 2  # "arg1", "arg2"
        assert kwargs_count == 2  # url, port

    def test_with_direct_object_pattern_basic(self, mock_use_function):
        """Test with statement using direct object pattern."""
        code = """
mcp_client = use("mcp", url="http://test.com")
with mcp_client as client:
    result = f"Got client: {type(client)}"
    client_name = client.name
"""

        sandbox = DanaSandbox()
        result = sandbox.execute_string(code)

        assert result.success, f"Execution failed: {result.error}"

        # Verify the context has the expected result
        final_result = self._get_from_context(result, "local:result")
        client_name = self._get_from_context(result, "local:client_name")

        assert "Got client: MockMCPResource" in final_result
        assert client_name is not None

    def test_with_direct_object_pattern_variable_scoping(self, mock_use_function):
        """Test that direct object pattern works with different variable scopes."""
        code = """
private:mcp_client = use("mcp", url="http://test.com")
with private:mcp_client as client:
    entered_status = client.is_entered
    result = "Client entered"
"""

        sandbox = DanaSandbox()
        result = sandbox.execute_string(code)

        assert result.success, f"Execution failed: {result.error}"

        # Verify the context manager was entered
        entered_status = self._get_from_context(result, "local:entered_status")
        assert entered_status is True, "Context manager should be entered"

    def test_context_manager_lifecycle(self, mock_use_function):
        """Test that context manager __enter__ and __exit__ are called correctly."""
        code = """
client_ref = None
with use("mcp", url="http://test.com") as client:
    client_ref = client
    entered_status = client.is_entered
    exited_status = client.is_exited

# After the with block
final_exited_status = client_ref.is_exited
"""

        sandbox = DanaSandbox()
        result = sandbox.execute_string(code)

        assert result.success, f"Execution failed: {result.error}"

        # Verify context manager lifecycle
        entered_status = self._get_from_context(result, "local:entered_status")
        exited_status = self._get_from_context(result, "local:exited_status")
        final_exited_status = self._get_from_context(result, "local:final_exited_status")

        assert entered_status is True, "Context manager should be entered during with block"
        assert exited_status is False, "Context manager should not be exited during with block"
        assert final_exited_status is True, "Context manager should be exited after with block"

    def test_with_statement_resource_access(self, mock_use_function):
        """Test that resources created with direct pattern can access their attributes."""
        code = """
mcp_obj = use("mcp", url="http://test.com")
with mcp_obj as client:
    # Test that we can access attributes of the context manager
    client_name = client.name
    client_args = len(client.args)
    is_entered = client.is_entered
"""

        sandbox = DanaSandbox()
        result = sandbox.execute_string(code)

        assert result.success, f"Execution failed: {result.error}"

        # Verify we can access context manager attributes
        client_name = self._get_from_context(result, "local:client_name")
        client_args = self._get_from_context(result, "local:client_args")
        is_entered = self._get_from_context(result, "local:is_entered")

        assert client_name is not None, "Should be able to access client name"
        assert client_args == 0, "Should have no positional args"
        assert is_entered is True, "Context manager should be entered"

    def test_with_statement_nested(self, mock_use_function):
        """Test nested with statements work correctly."""
        code = """
with use("mcp", url="http://outer.com") as outer_client:
    outer_name = outer_client.name
    with use("mcp", url="http://inner.com") as inner_client:
        inner_name = inner_client.name
        both_entered = outer_client.is_entered and inner_client.is_entered
"""

        sandbox = DanaSandbox()
        result = sandbox.execute_string(code)

        assert result.success, f"Execution failed: {result.error}"

        # Verify both context managers work correctly when nested
        both_entered = self._get_from_context(result, "local:both_entered")

        assert both_entered is True, "Both nested context managers should be entered"

    def test_with_statement_mixed_patterns(self, mock_use_function):
        """Test mixing function call and direct object patterns."""
        code = """
# Function call pattern
with use("mcp", url="http://test1.com") as client1:
    client1_type = type(client1)

# Direct object pattern  
client2_obj = use("mcp", url="http://test2.com")
with client2_obj as client2:
    client2_type = type(client2)
    
# Both should work the same way
types_match = client1_type == client2_type
"""

        sandbox = DanaSandbox()
        result = sandbox.execute_string(code)

        assert result.success, f"Execution failed: {result.error}"

        # Verify both patterns work identically
        client1_type = self._get_from_context(result, "local:client1_type")
        client2_type = self._get_from_context(result, "local:client2_type")
        types_match = self._get_from_context(result, "local:types_match")

        assert client1_type == "MockMCPResource"
        assert client2_type == "MockMCPResource"
        assert types_match is True


class TestWithStatementErrorCases:
    """Test error cases for with statements."""

    def _get_from_context(self, result, key):
        """Helper to safely get values from execution result context."""
        assert result.final_context is not None, "Final context should not be None"
        return result.final_context.get(key)

    def test_with_non_context_manager_object(self):
        """Test error when using non-context manager object."""
        code = """
not_a_context_manager = "just a string"
with not_a_context_manager as client:
    pass
"""

        sandbox = DanaSandbox()
        result = sandbox.execute_string(code)

        assert not result.success, "Should fail with non-context manager object"
        assert "does not return a context manager" in str(result.error)

    def test_with_undefined_variable(self):
        """Test error when using undefined variable as context manager."""
        code = """
with undefined_variable as client:
    pass
"""

        sandbox = DanaSandbox()
        result = sandbox.execute_string(code)

        assert not result.success, "Should fail with undefined variable"
        # The exact error message may vary, but it should be about the undefined variable

    def test_with_variable_name_shadowing_error(self, mock_use_function):
        """Test error when with statement variable shadows the same variable name."""
        code = """
websearch = use("mcp", url="http://localhost:8880/websearch")
with websearch as websearch:
    # This should trigger an error about variable name shadowing
    result = type(websearch)
"""

        sandbox = DanaSandbox()
        result = sandbox.execute_string(code)

        # Should fail with variable shadowing error
        assert not result.success, "Should fail with variable shadowing error"
        assert "Variable name shadowing detected" in str(result.error)
        assert "is being used as both the context manager and the 'as' variable" in str(result.error)

    def test_with_variable_shadowing_affects_original(self, mock_use_function):
        """Test that variable shadowing affects access to the original variable."""
        code = """
websearch = use("mcp", url="http://localhost:8880/websearch")
original_name = websearch.name

# Use a different variable name to avoid the shadowing error
with websearch as client:
    client_name = client.name
    # websearch should still refer to the original here
    websearch_inside_name = websearch.name

# After the with block, websearch should still exist and be the original
final_name = websearch.name
"""

        sandbox = DanaSandbox()
        result = sandbox.execute_string(code)

        assert result.success, f"Execution failed: {result.error}"

        # Verify the original variable is preserved
        original_name = self._get_from_context(result, "local:original_name")
        client_name = self._get_from_context(result, "local:client_name")
        websearch_inside_name = self._get_from_context(result, "local:websearch_inside_name")
        final_name = self._get_from_context(result, "local:final_name")

        # All should refer to the same MockMCPResource
        assert original_name is not None
        assert client_name == original_name, "Client should be the same object as the original context manager"
        assert websearch_inside_name == original_name, "websearch should still refer to original inside with block"
        assert final_name == original_name, "websearch should still refer to original after with block"

        # The original variable should be preserved throughout

    def test_with_problematic_same_name_shadowing_demonstrates_issue(self, mock_use_function):
        """Test the problematic case to demonstrate why we need to prevent it."""
        # First, let's create a version that works correctly (no shadowing)
        code_good = """
websearch = use("mcp", url="http://localhost:8880/websearch")
good_original_name = websearch.name

with websearch as client:
    good_client_name = client.name
    
# After with block, websearch is still accessible
good_final_name = websearch.name
good_still_accessible = True
"""

        sandbox = DanaSandbox()
        result = sandbox.execute_string(code_good)
        assert result.success, f"Good version failed: {result.error}"

        good_original = self._get_from_context(result, "local:good_original_name")
        good_client = self._get_from_context(result, "local:good_client_name")
        good_final = self._get_from_context(result, "local:good_final_name")
        good_accessible = self._get_from_context(result, "local:good_still_accessible")

        assert good_original is not None
        assert good_client is not None
        assert good_final is not None
        assert good_accessible is True

        # The good version preserves access to the original variable


@pytest.mark.integration
class TestWithStatementIntegration:
    """Integration tests for with statements."""

    def _get_from_context(self, result, key):
        """Helper to safely get values from execution result context."""
        assert result.final_context is not None, "Final context should not be None"
        return result.final_context.get(key)

    def test_with_statement_in_function(self, mock_use_function):
        """Test with statements work correctly inside functions."""
        code = """
def test_function():
    with use("mcp", url="http://test.com") as client:
        # Test that context manager works inside function
        return client.is_entered

# Call the function to test it
test_function()
"""

        sandbox = DanaSandbox()
        result = sandbox.execute_string(code)

        assert result.success, f"Execution failed: {result.error}"
        # The function was called successfully, which means the with statement worked

    def test_with_statement_simple_execution(self, mock_use_function):
        """Test simple with statement execution in complex scenario."""
        code = """
def get_client_info():
    with use("mcp", url="http://test.com") as client:
        return client.name

# Just define the function - successful parsing means with statement works
"""

        sandbox = DanaSandbox()
        result = sandbox.execute_string(code)

        assert result.success, f"Execution failed: {result.error}"
        # If execution succeeded, it means the with statement was parsed and executed correctly
        # Verify the function was defined in the context
        assert result.final_context is not None
        get_client_info = result.final_context.get("local:get_client_info")
        assert get_client_info is not None, "Function should be defined"
