"""
Function error handling utilities for Dana language function execution.

This module provides comprehensive error handling and recovery mechanisms
for function execution in the Dana language interpreter.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import logging
from typing import TYPE_CHECKING, Any

from dana.common.exceptions import FunctionRegistryError, SandboxError
from dana.common.runtime_scopes import RuntimeScopes
from dana.core.lang.ast import FunctionCall

if TYPE_CHECKING:
    from dana.core.lang.interpreter.executor.function_executor import FunctionExecutor


class FunctionExecutionErrorHandler:
    """Centralized error handling for function execution.

    This class encapsulates all error handling logic for function execution,
    including exception mapping, error recovery, and message formatting.
    """

    def __init__(self, executor: "FunctionExecutor"):
        """Initialize error handler.

        Args:
            executor: The function executor instance
        """
        self.executor = executor
        self.logger = logging.getLogger(__name__)

    def handle_function_call_error(self, error: Exception, node: FunctionCall, context: Any) -> Any:
        """Handle function call errors with recovery attempts.

        Args:
            error: The original error
            node: The function call node
            context: The execution context

        Returns:
            The function execution result if recovery succeeds

        Raises:
            SandboxError: If recovery fails
        """
        # Try recovery strategies in order of preference
        recovery_strategies = [
            PositionalErrorRecoveryStrategy(self.executor),
            # Future: Add more recovery strategies here
        ]

        for strategy in recovery_strategies:
            if strategy.can_handle(error, {}):  # Empty kwargs for now
                try:
                    # The result may be an EagerPromise object - this is expected behavior
                    # Promise transparency will handle resolution when the result is accessed
                    return strategy.recover(error, node, None, context, [], {}, node.name, self.executor)
                except Exception:
                    # Strategy failed, try next one
                    continue

        # No recovery possible, raise enhanced error
        raise self._create_enhanced_sandbox_error(error, node, node.name)

    def _is_positional_argument_error(self, error: Exception) -> bool:
        """Check if the error is related to positional arguments.

        Args:
            error: The exception to check

        Returns:
            True if this is a positional argument error
        """
        error_msg = str(error).lower()
        positional_indicators = ["takes", "positional argument", "too many positional arguments", "missing", "required positional argument"]
        return any(indicator in error_msg for indicator in positional_indicators)

    def _handle_registry_error(self, error: FunctionRegistryError, node: FunctionCall) -> Any:
        """Handle function registry errors.

        Args:
            error: The registry error
            node: The function call node

        Returns:
            Error response
        """
        return self.executor._create_error_response(f"Function '{node.name}' not found in registry", original_error=error)

    def _convert_to_user_friendly_name(self, function_name: str) -> str:
        """Convert internal dot notation to user-friendly colon notation for display.

        Args:
            function_name: Internal function name (e.g., 'local:fact')

        Returns:
            User-friendly function name (e.g., 'local:fact')
        """
        # Check if this looks like a scoped function name
        if "." in function_name:
            parts = function_name.split(".", 1)
            if len(parts) == 2 and parts[0] in RuntimeScopes.ALL:
                scope, func_name = parts
                return f"{scope}:{func_name}"

        # Return as-is if not a scoped function
        return function_name

    def format_error_message(self, error: Exception, function_name: str, context: str = "") -> str:
        """Format a comprehensive error message.

        Args:
            error: The exception
            function_name: Name of the function that failed
            context: Additional context information

        Returns:
            Formatted error message
        """
        # Convert internal dot notation to user-friendly colon notation
        user_friendly_name = self._convert_to_user_friendly_name(function_name)

        base_msg = f"Function '{user_friendly_name}' execution failed: {str(error)}"
        if context:
            base_msg += f" (Context: {context})"
        return base_msg

    def handle_registry_execution_error(
        self,
        error: Exception,
        node: FunctionCall,
        registry: Any,
        context: Any,
        evaluated_args: list[Any],
        evaluated_kwargs: dict[str, Any],
        func_name: str,
    ) -> Any:
        """Handle registry execution errors with recovery attempts.

        Args:
            error: The original error
            node: The function call node
            registry: The function registry
            context: The execution context
            evaluated_args: Evaluated positional arguments
            evaluated_kwargs: Evaluated keyword arguments
            func_name: The base function name

        Returns:
            The function execution result if recovery succeeds

        Raises:
            SandboxError: If recovery fails
        """
        # Try recovery strategies in order of preference
        recovery_strategies = [
            PositionalErrorRecoveryStrategy(self.executor),
            # Future: Add more recovery strategies here
        ]

        for strategy in recovery_strategies:
            if strategy.can_handle(error, evaluated_kwargs):
                try:
                    return strategy.recover(error, node, registry, context, evaluated_args, evaluated_kwargs, func_name, self.executor)
                except Exception:
                    # Strategy failed, try next one
                    continue

        # No recovery possible, raise enhanced error
        raise self._create_enhanced_sandbox_error(error, node, func_name)

    def _create_enhanced_sandbox_error(self, error: Exception, node: FunctionCall, func_name: str) -> SandboxError:
        """Create an enhanced SandboxError with context information.

        Args:
            error: The original error
            node: The function call node
            func_name: The function name

        Returns:
            Enhanced SandboxError
        """
        enhanced_msg = self.format_error_message(error, func_name, f"function call at {getattr(node, 'location', 'unknown location')}")
        sandbox_error = SandboxError(enhanced_msg)
        sandbox_error.__cause__ = error
        return sandbox_error


class PositionalErrorRecoveryStrategy:
    """Strategy for recovering from positional argument errors.

    This class implements recovery mechanisms when function calls fail
    due to positional argument mismatches.
    """

    def __init__(self, executor: "FunctionExecutor"):
        """Initialize recovery strategy.

        Args:
            executor: The function executor instance
        """
        self.executor = executor
        self.logger = logging.getLogger(__name__)

    def can_handle(self, error: Exception, kwargs: dict) -> bool:
        """Check if this strategy can handle the given error.

        Args:
            error: The error to check
            kwargs: The keyword arguments from the function call

        Returns:
            True if this strategy can handle the error
        """
        # Check if this is a positional argument error
        return self._is_positional_argument_error(error)

    def recover(
        self,
        error: Exception,
        node: FunctionCall,
        registry: Any,
        context: Any,
        evaluated_args: list,
        evaluated_kwargs: dict,
        func_name: str,
        executor: "FunctionExecutor",
    ) -> Any:
        """Attempt to recover from a positional argument error.

        Args:
            error: The original error
            node: The function call node
            registry: The function registry
            context: The execution context
            evaluated_args: Evaluated positional arguments
            evaluated_kwargs: Evaluated keyword arguments
            func_name: The function name
            executor: The function executor

        Returns:
            Result of recovery attempt (may be an EagerPromise object)

        Raises:
            Exception: If recovery fails
        """
        self.logger.debug(f"Attempting positional error recovery for '{func_name}': {error}")

        # Strategy 1: Try converting positional args to keyword args
        try:
            return self._try_keyword_conversion(node, context)
        except Exception as recovery_error:
            self.logger.debug(f"Keyword conversion failed: {recovery_error}")

        # Strategy 2: Try with fewer arguments
        try:
            return self._try_reduced_args(node, context)
        except Exception as recovery_error:
            self.logger.debug(f"Reduced args failed: {recovery_error}")

        # Recovery failed, raise original error
        self.logger.debug(f"All recovery strategies failed for '{func_name}'")
        raise error

    def _is_positional_argument_error(self, error: Exception) -> bool:
        """Check if the error is related to positional arguments.

        Args:
            error: The error to check

        Returns:
            True if this is a positional argument error
        """
        error_str = str(error).lower()
        return any(keyword in error_str for keyword in ["positional", "argument", "missing", "required", "unexpected"])

    def attempt_recovery(self, error: Exception, node: FunctionCall, context: Any) -> Any:
        """Attempt to recover from a positional argument error.

        Args:
            error: The original error
            node: The function call node
            context: The execution context

        Returns:
            Result of recovery attempt or raises original error
        """
        self.logger.debug(f"Attempting positional error recovery for '{node.name}': {error}")

        # Strategy 1: Try converting positional args to keyword args
        try:
            return self._try_keyword_conversion(node, context)
        except Exception as recovery_error:
            self.logger.debug(f"Keyword conversion failed: {recovery_error}")

        # Strategy 2: Try with fewer arguments
        try:
            return self._try_reduced_args(node, context)
        except Exception as recovery_error:
            self.logger.debug(f"Reduced args failed: {recovery_error}")

        # Recovery failed, raise original error
        self.logger.debug(f"All recovery strategies failed for '{node.name}'")
        raise error

    def _try_keyword_conversion(self, node: FunctionCall, context: Any) -> Any:
        """Try converting positional arguments to keyword arguments.

        Args:
            node: The function call node
            context: The execution context

        Returns:
            Result of function call with keyword arguments (may be an EagerPromise object)
        """
        # This is a simplified implementation
        # In practice, you'd need function signature inspection
        converted_kwargs = {}

        # Convert numeric keys to common parameter names
        for key, value in node.args.items():
            if key.isdigit():
                param_names = ["arg1", "arg2", "arg3", "data", "value", "input"]
                if int(key) < len(param_names):
                    converted_kwargs[param_names[int(key)]] = value
                else:
                    converted_kwargs[f"arg{int(key) + 1}"] = value
            else:
                converted_kwargs[key] = value

        # Create a new node with converted arguments
        converted_node = FunctionCall(name=node.name, args=converted_kwargs, location=node.location)

        # The result may be an EagerPromise object - this is expected behavior
        # Promise transparency will handle resolution when the result is accessed
        return self.executor.execute_function_call(converted_node, context)

    def _try_reduced_args(self, node: FunctionCall, context: Any) -> Any:
        """Try executing with a reduced set of arguments.

        Args:
            node: The function call node
            context: The execution context

        Returns:
            Result of function call with reduced arguments (may be an EagerPromise object)
        """
        if not node.args:
            raise ValueError("No arguments to reduce")

        # Try removing the last argument
        reduced_args = dict(node.args)

        # Find the highest numeric key and remove it
        numeric_keys = [k for k in reduced_args.keys() if k.isdigit()]
        if numeric_keys:
            max_key = max(numeric_keys, key=int)
            del reduced_args[max_key]

        # Create a new node with reduced arguments
        reduced_node = FunctionCall(name=node.name, args=reduced_args, location=node.location)

        # The result may be an EagerPromise object - this is expected behavior
        # Promise transparency will handle resolution when the result is accessed
        return self.executor.execute_function_call(reduced_node, context)
