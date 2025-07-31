"""
Tests for dual delivery mechanism with deliver and return statements.
"""

import pytest

from dana.core.lang.sandbox_context import SandboxContext
from dana.core.runtime.promise import Promise

try:
    from unittest.mock import AsyncMock, Mock
except ImportError:
    from unittest.mock import Mock

    # Fallback for older Python versions
    class AsyncMock:
        def __init__(self, return_value=None):
            self.return_value = return_value

        async def __call__(self, *args, **kwargs):
            return self.return_value


from dana.core.lang.ast import DeliverStatement, LiteralExpression, ReturnStatement
from dana.core.lang.interpreter.executor.control_flow.control_flow_utils import ControlFlowUtils
from dana.core.lang.interpreter.executor.control_flow.exceptions import ReturnException


class TestDeliverStatement:
    """Test eager execution with deliver statements."""

    @pytest.fixture
    def mock_executor(self):
        """Create a mock executor for testing."""
        executor = Mock()
        executor.execute_and_await = AsyncMock()
        return executor

    @pytest.fixture
    def control_flow_utils(self, mock_executor):
        """Create ControlFlowUtils with mock executor."""
        utils = ControlFlowUtils(parent_executor=mock_executor)
        return utils

    @pytest.fixture
    def context(self):
        """Create a test sandbox context."""
        return SandboxContext()

    @pytest.mark.asyncio
    async def test_deliver_with_value_eager_execution(self, control_flow_utils, context, mock_executor):
        """Test that deliver executes immediately and returns concrete value."""
        # Arrange
        mock_executor.execute_and_await.return_value = 42
        deliver_stmt = DeliverStatement(value=LiteralExpression(value=42))

        # Act & Assert
        with pytest.raises(ReturnException) as exc_info:
            await control_flow_utils.execute_deliver_statement(deliver_stmt, context)

        assert exc_info.value.value == 42
        mock_executor.execute_and_await.assert_called_once()

    @pytest.mark.asyncio
    async def test_deliver_with_no_value(self, control_flow_utils, context):
        """Test deliver statement with no value."""
        # Arrange
        deliver_stmt = DeliverStatement(value=None)

        # Act & Assert
        with pytest.raises(ReturnException) as exc_info:
            await control_flow_utils.execute_deliver_statement(deliver_stmt, context)

        assert exc_info.value.value is None

    @pytest.mark.asyncio
    async def test_deliver_executor_not_available(self, context):
        """Test error when parent executor not available."""
        # Arrange
        utils = ControlFlowUtils(parent_executor=None)
        deliver_stmt = DeliverStatement(value=LiteralExpression(value=42))

        # Act & Assert
        with pytest.raises(RuntimeError, match="Parent executor not available"):
            await utils.execute_deliver_statement(deliver_stmt, context)


class TestReturnStatement:
    """Test lazy execution with return statements."""

    @pytest.fixture
    def mock_executor(self):
        """Create a mock executor for testing."""
        executor = Mock()
        executor.parent = Mock()
        executor.parent.execute_sync_only = Mock(return_value=42)
        return executor

    @pytest.fixture
    def control_flow_utils(self, mock_executor):
        """Create ControlFlowUtils with mock executor."""
        return ControlFlowUtils(parent_executor=mock_executor)

    @pytest.fixture
    def context(self):
        """Create a test sandbox context."""
        return SandboxContext()

    @pytest.mark.asyncio
    async def test_return_creates_promise(self, control_flow_utils, context, mock_executor):
        """Test that return creates a Promise[T] wrapper."""
        # Arrange
        return_stmt = ReturnStatement(value=LiteralExpression(value=42))

        # Act & Assert
        with pytest.raises(ReturnException) as exc_info:
            await control_flow_utils.execute_return_statement(return_stmt, context)

        result = exc_info.value.value
        assert isinstance(result, Promise)
        assert result.value == 42

    @pytest.mark.asyncio
    async def test_return_promise_lazy_evaluation(self, control_flow_utils, context, mock_executor):
        """Test that promise evaluation is lazy."""
        # Arrange
        return_stmt = ReturnStatement(value=LiteralExpression(value=42))

        # Act
        with pytest.raises(ReturnException) as exc_info:
            await control_flow_utils.execute_return_statement(return_stmt, context)

        promise = exc_info.value.value

        # Assert - computation should not have been called yet
        mock_executor.parent.execute_sync_only.assert_not_called()

        # Resolve the promise
        result = promise.value

        # Now computation should have been called
        assert result == 42
        mock_executor.parent.execute_sync_only.assert_called_once()

    @pytest.mark.asyncio
    async def test_return_with_no_value(self, control_flow_utils, context):
        """Test return statement with no value."""
        # Arrange
        return_stmt = ReturnStatement(value=None)

        # Act & Assert
        with pytest.raises(ReturnException) as exc_info:
            await control_flow_utils.execute_return_statement(return_stmt, context)

        assert exc_info.value.value is None


class TestPromiseTransparency:
    """Test that Promise[T] appears completely transparent as T."""

    @pytest.fixture
    def context(self):
        """Create a test sandbox context."""
        return SandboxContext()

    def test_promise_arithmetic_operations(self, context):
        """Test that Promise[T] supports arithmetic operations transparently."""
        # Create promises
        promise_5 = Promise(lambda: 5, context)
        promise_3 = Promise(lambda: 3, context)

        # Test arithmetic operations
        assert promise_5 + promise_3 == 8
        assert promise_5 - promise_3 == 2
        assert promise_5 * promise_3 == 15
        assert promise_5 / promise_3 == 5 / 3

    def test_promise_comparison_operations(self, context):
        """Test that Promise[T] supports comparison operations transparently."""
        promise_5 = Promise(lambda: 5, context)
        promise_3 = Promise(lambda: 3, context)

        assert promise_5 > promise_3
        assert promise_3 < promise_5
        assert promise_5 >= promise_3
        assert promise_3 <= promise_5
        assert promise_5 == 5
        assert promise_3 != 5

    def test_promise_string_operations(self, context):
        """Test that Promise[T] supports string operations transparently."""
        promise_str = Promise(lambda: "hello", context)

        assert str(promise_str) == "hello"
        assert len(promise_str) == 5
        assert "ell" in promise_str
        assert promise_str + " world" == "hello world"

    def test_promise_collection_operations(self, context):
        """Test that Promise[T] supports collection operations transparently."""
        promise_list = Promise(lambda: [1, 2, 3], context)
        promise_dict = Promise(lambda: {"a": 1, "b": 2}, context)

        # List operations
        assert len(promise_list) == 3
        assert promise_list[0] == 1
        assert 2 in promise_list

        # Dict operations
        assert len(promise_dict) == 2
        assert promise_dict["a"] == 1
        assert "b" in promise_dict

    def test_promise_function_call(self, context):
        """Test that Promise[T] supports function calls transparently."""

        def test_func(x, y):
            return x + y

        promise_func = Promise(lambda: test_func, context)
        result = promise_func(3, 4)
        assert result == 7

    def test_promise_attribute_access(self, context):
        """Test that Promise[T] supports attribute access transparently."""

        class TestObj:
            def __init__(self):
                self.value = 42

            def method(self):
                return self.value * 2

        promise_obj = Promise(lambda: TestObj(), context)

        assert promise_obj.value == 42
        assert promise_obj.method() == 84


class TestPromiseParallelization:
    """Test automatic parallelization of multiple promise access."""

    @pytest.fixture
    def context(self):
        """Create a test sandbox context."""
        return SandboxContext()

    def test_multiple_promise_access_patterns(self, context):
        """Test that multiple promises are detected and resolved in parallel."""
        call_count = 0

        def slow_computation(value):
            nonlocal call_count
            call_count += 1
            return value * 2

        # Create multiple promises
        promise_a = Promise(lambda: slow_computation(5), context)
        promise_b = Promise(lambda: slow_computation(10), context)
        promise_c = Promise(lambda: slow_computation(15), context)

        # Access multiple promises in same expression
        result = promise_a + promise_b + promise_c

        # All computations should have been called
        assert result == 60  # (5*2) + (10*2) + (15*2)
        assert call_count == 3


class TestPromiseErrorHandling:
    """Test comprehensive error handling with stack trace preservation."""

    @pytest.fixture
    def context(self):
        """Create a test sandbox context."""
        return SandboxContext()

    def test_promise_error_preservation(self, context):
        """Test that errors in promise resolution are properly preserved."""

        def failing_computation():
            raise ValueError("Test error")

        promise = Promise(failing_computation, context)

        with pytest.raises(Exception) as exc_info:
            _ = promise + 1  # Force resolution

        # Should preserve original error information
        assert "Test error" in str(exc_info.value)

    def test_promise_creation_location_tracking(self, context):
        """Test that promise creation location is tracked."""
        promise = Promise(lambda: 42, context)

        # Creation location should be tracked
        assert promise._creation_location != "unknown location"
        assert "test_dual_delivery.py" in promise._creation_location


if __name__ == "__main__":
    pytest.main([__file__])
