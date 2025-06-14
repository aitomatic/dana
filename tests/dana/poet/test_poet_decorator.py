"""
Tests for POET Decorator functionality
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from opendxa.dana.poet.decorator import poet, feedback, _execute_enhanced_function
from opendxa.dana.poet.types import POETConfig, POETResult, POETServiceError


class TestPOETDecorator:
    """Test POET decorator functionality"""

    def test_poet_decorator_creation(self):
        """Test @poet decorator creates enhanced function"""

        @poet()
        def simple_function(x: int) -> int:
            return x * 2

        # Check that function is wrapped
        assert hasattr(simple_function, "_poet_config")
        assert hasattr(simple_function, "_poet_original")
        assert hasattr(simple_function, "_poet_source")

        # Check configuration
        config = simple_function._poet_config
        assert isinstance(config, POETConfig)
        assert config.domain is None
        assert config.optimize_for is None

    def test_poet_decorator_with_params(self):
        """Test @poet decorator with parameters"""

        @poet(domain="ml_monitoring", optimize_for="accuracy", retries=5)
        def ml_function(data):
            return {"prediction": 0.8}

        config = ml_function._poet_config
        assert config.domain == "ml_monitoring"
        assert config.optimize_for == "accuracy"
        assert config.retries == 5

    def test_poet_decorator_preserves_metadata(self):
        """Test @poet decorator preserves function metadata"""

        @poet()
        def documented_function(x: int, y: str = "default") -> dict:
            """This function has documentation and type hints"""
            return {"x": x, "y": y}

        # Check original function is preserved
        original = documented_function._poet_original
        assert original.__name__ == "documented_function"
        assert original.__doc__ == "This function has documentation and type hints"

        # Check wrapper preserves name and doc
        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ == "This function has documentation and type hints"

    @patch("opendxa.dana.poet.decorator._get_or_create_enhanced_function")
    @patch("opendxa.dana.poet.decorator.get_default_client")
    def test_poet_function_execution(self, mock_get_client, mock_get_enhanced):
        """Test POET enhanced function execution"""

        # Mock the enhanced function
        mock_enhanced_func = Mock()
        mock_result = POETResult({"value": 42}, "test_func")
        mock_enhanced_func.return_value = mock_result
        mock_get_enhanced.return_value = mock_enhanced_func

        # Mock the client
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        @poet()
        def test_function(x: int) -> int:
            return x * 2

        # Call the enhanced function
        result = test_function(21)

        # Verify result
        assert isinstance(result, POETResult)
        assert result._poet["function_name"] == "test_func"

        # Verify enhanced function was called
        mock_enhanced_func.assert_called_once_with(21)

        # Verify transpilation was attempted
        mock_get_enhanced.assert_called_once()

    @patch("opendxa.dana.poet.decorator.get_default_client")
    def test_poet_function_fallback_on_error(self, mock_get_client):
        """Test POET falls back to original function on enhancement error"""

        # Mock client to raise error during transpilation
        mock_client = Mock()
        mock_client.transpile_function.side_effect = Exception("Transpilation failed")
        mock_get_client.return_value = mock_client

        @poet()
        def test_function(x: int) -> int:
            return x * 2

        # Call should fallback to original function
        result = test_function(21)

        assert isinstance(result, POETResult)
        assert result._poet["version"] == "original"
        assert result.unwrap() == 42  # Original function result

    def test_feedback_function_valid_result(self):
        """Test feedback function with valid POETResult"""

        with patch("opendxa.dana.poet.decorator.get_default_client") as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client

            result = POETResult({"value": 42}, "test_func")
            feedback_data = "The result was too low"

            feedback(result, feedback_data)

            mock_client.feedback.assert_called_once_with(result, feedback_data)

    def test_feedback_function_invalid_result(self):
        """Test feedback function raises error with invalid result"""

        with pytest.raises(Exception):  # Should raise some error for invalid input
            feedback("not a POETResult", "feedback")

    @patch("opendxa.dana.poet.decorator.get_default_client")
    def test_enhanced_function_caching(self, mock_get_client):
        """Test enhanced function caching mechanism"""

        mock_client = Mock()
        mock_transpiled = Mock()
        mock_transpiled.code = "def test_function_enhanced(x): return x * 3"
        mock_client.transpile_function.return_value = mock_transpiled
        mock_get_client.return_value = mock_client

        @poet()
        def test_function(x: int) -> int:
            return x * 2

        # First call should trigger transpilation
        with patch("builtins.exec") as mock_exec:
            # Mock the execution of enhanced code
            def mock_exec_func(code, namespace):
                namespace["test_function_enhanced"] = lambda x: POETResult(x * 3, "test_function")

            mock_exec.side_effect = mock_exec_func

            result1 = test_function(10)

            # Verify transpilation happened
            mock_client.transpile_function.assert_called_once()

        # Reset mock to verify caching
        mock_client.reset_mock()

        # Second call should use cache (no transpilation)
        with patch("builtins.exec") as mock_exec:

            def mock_exec_func(code, namespace):
                namespace["test_function_enhanced"] = lambda x: POETResult(x * 3, "test_function")

            mock_exec.side_effect = mock_exec_func

            result2 = test_function(10)

            # Verify no additional transpilation
            mock_client.transpile_function.assert_not_called()


class TestPOETExecutionFlow:
    """Test POET execution flow"""

    @patch("opendxa.dana.poet.decorator.get_default_client")
    def test_execute_enhanced_function_success(self, mock_get_client):
        """Test successful execution of enhanced function"""

        mock_client = Mock()
        mock_transpiled = Mock()
        mock_transpiled.code = """
def original_func_enhanced(x):
    from opendxa.dana.poet.types import POETResult
    return POETResult(x * 2, "original_func", "v1")
"""
        mock_client.transpile_function.return_value = mock_transpiled
        mock_get_client.return_value = mock_client

        def original_func(x):
            return x * 2

        config = POETConfig()
        source_code = "def original_func(x): return x * 2"

        result = _execute_enhanced_function(original_func, config, source_code, 5)

        assert isinstance(result, POETResult)
        assert result._poet["function_name"] == "original_func"

    @patch("opendxa.dana.poet.decorator.get_default_client")
    def test_execute_enhanced_function_fallback(self, mock_get_client):
        """Test fallback to original function on enhancement failure"""

        mock_client = Mock()
        mock_client.transpile_function.side_effect = Exception("Enhancement failed")
        mock_get_client.return_value = mock_client

        def original_func(x):
            return x * 2

        config = POETConfig()
        source_code = "def original_func(x): return x * 2"

        result = _execute_enhanced_function(original_func, config, source_code, 5)

        assert isinstance(result, POETResult)
        assert result._poet["version"] == "original"
        assert result.unwrap() == 10  # Original function result


class TestPOETIntegration:
    """Test POET integration scenarios"""

    def test_end_to_end_local_mode(self):
        """Test end-to-end POET usage in local mode"""

        # This is more of an integration test that would require
        # actual LLM and transpiler components to be working
        # For now, we'll mock the heavy components

        with patch("opendxa.dana.poet.decorator.get_default_client") as mock_get_client:
            mock_client = Mock()

            # Mock successful transpilation
            mock_transpiled = Mock()
            mock_transpiled.code = """
def simple_add_enhanced(a, b):
    from opendxa.dana.poet.types import POETResult
    # Enhanced with P->O->E phases
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise ValueError("Inputs must be numbers")
    result = a + b
    return POETResult(result, "simple_add", "v1")
"""
            mock_client.transpile_function.return_value = mock_transpiled
            mock_get_client.return_value = mock_client

            @poet()
            def simple_add(a: int, b: int) -> int:
                return a + b

            # Test function call
            result = simple_add(2, 3)

            assert isinstance(result, POETResult)
            assert result._poet["function_name"] == "simple_add"

            # Test feedback
            mock_client.feedback = Mock()
            feedback(result, "Good calculation")
            mock_client.feedback.assert_called_once_with(result, "Good calculation")

    def test_multiple_poet_functions(self):
        """Test multiple POET functions work independently"""

        with patch("opendxa.dana.poet.decorator.get_default_client") as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client

            # Mock transpilation for both functions
            def mock_transpile(code, config, context=None):
                mock_result = Mock()
                if "multiply" in code:
                    mock_result.code = "def multiply_enhanced(x, y): return POETResult(x * y, 'multiply')"
                else:
                    mock_result.code = "def divide_enhanced(x, y): return POETResult(x / y, 'divide')"
                return mock_result

            mock_client.transpile_function.side_effect = mock_transpile

            @poet(domain="math")
            def multiply(x: float, y: float) -> float:
                return x * y

            @poet(domain="math", optimize_for="accuracy")
            def divide(x: float, y: float) -> float:
                return x / y

            # Check configurations are independent
            assert multiply._poet_config.domain == "math"
            assert multiply._poet_config.optimize_for is None

            assert divide._poet_config.domain == "math"
            assert divide._poet_config.optimize_for == "accuracy"

            # Both should trigger transpilation independently
            with patch("builtins.exec"):
                multiply(4, 5)
                divide(10, 2)

            assert mock_client.transpile_function.call_count == 2
