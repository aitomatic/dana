"""
Lambda method receiver system for Dana structs.

This module provides the infrastructure for registering lambda expressions
as methods on struct types, enabling functional-style method definitions.
"""

from collections.abc import Callable
from typing import Any

from dana.common.exceptions import SandboxError
from dana.core.lang.ast import LambdaExpression
from dana.core.lang.interpreter.functions.dana_function import DanaFunction
from dana.core.lang.sandbox_context import SandboxContext
from dana.registry import FUNCTION_REGISTRY


class LambdaReceiver:
    """Handles lambda expressions with explicit receivers for struct methods."""

    def __init__(self, lambda_expr: LambdaExpression):
        """Initialize with a lambda expression.

        Args:
            lambda_expr: The lambda expression to handle
        """
        self.lambda_expr = lambda_expr
        self.receiver_types = self._extract_receiver_types()

    def _extract_receiver_types(self) -> list[str]:
        """Extract receiver types from the lambda expression.

        Returns:
            List of receiver type names
        """
        # This is a simplified implementation
        # In a full implementation, this would parse the lambda signature
        # to extract the receiver type from the first parameter

        # For now, we'll assume the receiver type is specified in the lambda
        # This would need to be enhanced based on the actual lambda parsing
        return ["any"]  # Default to accepting any struct type

    def validate_receiver(self) -> bool:
        """Validate that the lambda has a proper receiver.

        Returns:
            True if the lambda has a valid receiver
        """
        # This would validate the lambda signature
        # For now, we'll assume any lambda with parameters is valid
        return len(self.lambda_expr.parameters) > 0

    def get_receiver_types(self) -> list[str]:
        """Get the receiver types for this lambda.

        Returns:
            List of receiver type names
        """
        return self.receiver_types

    def create_method_function(self) -> Callable:
        """Create a method function from the lambda expression.

        Returns:
            A callable method function
        """

        # This would create a proper method function from the lambda
        # For now, we'll return a placeholder
        def method_function(receiver: Any, *args, **kwargs) -> Any:
            # This would execute the lambda with the receiver as first argument
            # For now, we'll return a placeholder
            return f"Method called on {type(receiver).__name__} with args: {args}, kwargs: {kwargs}"

        return method_function

    def is_compatible_with(self, instance: Any) -> bool:
        """Check if this lambda is compatible with a given instance.

        Args:
            instance: The instance to check compatibility with

        Returns:
            True if the lambda can be called on this instance
        """
        if hasattr(instance, "__struct_type__"):
            struct_type = instance.__struct_type__
            return struct_type.name in self.receiver_types

        # For non-struct types, check Python type compatibility
        # This is a simplified check - a full implementation would have proper type mapping
        instance_type = type(instance).__name__
        return instance_type in self.receiver_types or "any" in self.receiver_types

    def register_as_method(self, method_name: str) -> None:
        """Register this lambda as a struct method.

        Args:
            method_name: Name to register the method under
        """
        if not self.validate_receiver():
            raise ValueError("Cannot register lambda without valid receiver")

        receiver_types = self.get_receiver_types()
        method_function = self.create_method_function()

        # Register with the unified method registry for structs
        FUNCTION_REGISTRY.register_method_for_types(receiver_types, method_name, method_function)


class LambdaMethodDispatcher:
    """Dispatches method calls to lambdas with receivers."""

    @staticmethod
    def can_handle_method_call(obj: Any, method_name: str) -> bool:
        """Check if this dispatcher can handle a method call.

        Args:
            obj: The object the method is being called on
            method_name: The method name

        Returns:
            True if this dispatcher can handle the method call
        """
        if not hasattr(obj, "__struct_type__"):
            return False

        struct_type = obj.__struct_type__
        
        # Check direct method first
        if FUNCTION_REGISTRY.has_struct_function(struct_type.name, method_name):
            return True

        # Check delegation
        delegation_result = LambdaMethodDispatcher._can_handle_delegated_method_call(obj, method_name)
        return delegation_result

    @staticmethod
    def _can_handle_delegated_method_call(obj: Any, method_name: str) -> bool:
        """Check if a method call can be handled through delegation.

        Args:
            obj: The object the method is being called on
            method_name: The method name

        Returns:
            True if a delegated method exists
        """
        # Use the struct instance delegation logic
        if hasattr(obj, "_find_delegated_method_access"):
            delegation_result = obj._find_delegated_method_access(method_name)
            if delegation_result is not None:
                delegated_object, _ = delegation_result
                # Check if the delegated object can handle the method through registry
                if hasattr(delegated_object, "__struct_type__"):
                    delegated_struct_type = delegated_object.__struct_type__
                    return FUNCTION_REGISTRY.has_struct_function(delegated_struct_type.name, method_name)
                # For non-struct objects, check if method exists and is callable
                return hasattr(delegated_object, method_name) and callable(getattr(delegated_object, method_name))
        return False

    @staticmethod
    def dispatch_method_call(obj: Any, method_name: str, *args, context: SandboxContext | None = None, **kwargs) -> Any:
        """Dispatch a method call to a lambda with receiver.

        Args:
            obj: The object the method is being called on
            method_name: The method name
            *args: Method arguments
            context: Optional SandboxContext to use for execution
            **kwargs: Method keyword arguments

        Returns:
            The result of the method call
        """
        if not hasattr(obj, "__struct_type__"):
            raise SandboxError(f"Object {obj} is not a struct instance")

        struct_type = obj.__struct_type__
        method_function = FUNCTION_REGISTRY.lookup_struct_function(struct_type.name, method_name)

        # Try direct method first
        if method_function is not None:
            return LambdaMethodDispatcher._execute_method_function(method_function, obj, args, context, kwargs)

        # Try delegation
        if hasattr(obj, "_find_delegated_method_access"):
            delegation_result = obj._find_delegated_method_access(method_name)
            if delegation_result is not None:
                delegated_object, delegated_method_name = delegation_result

                # Check if delegated object is a struct with registered methods
                if hasattr(delegated_object, "__struct_type__"):
                    delegated_struct_type = delegated_object.__struct_type__
                    delegated_method_function = FUNCTION_REGISTRY.lookup_struct_function(delegated_struct_type.name, delegated_method_name)
                    if delegated_method_function is not None:
                        return LambdaMethodDispatcher._execute_method_function(
                            delegated_method_function, delegated_object, args, context, kwargs
                        )

                # Fall back to direct method call on delegated object
                method = getattr(delegated_object, delegated_method_name)
                if callable(method):
                    return method(*args, **kwargs)

        raise AttributeError(f"No lambda method '{method_name}' found for type '{struct_type.name}' or through delegation")

    @staticmethod
    def _execute_method_function(method_function: Any, obj: Any, args: tuple, context: SandboxContext | None, kwargs: dict) -> Any:
        """Execute a method function with proper context handling.

        Args:
            method_function: The method function to execute
            obj: The object the method is being called on
            args: Method arguments
            context: Optional SandboxContext to use for execution
            kwargs: Method keyword arguments

        Returns:
            The result of the method call
        """
        # Check if this is a DanaFunction that needs to be called via execute()
        if isinstance(method_function, DanaFunction):
            # Use provided context or create a new one
            if context is None:
                context = SandboxContext()
            elif not isinstance(context, SandboxContext):
                # If context is not a SandboxContext, create a child context
                context = context.create_child_context() if hasattr(context, "create_child_context") else SandboxContext()

            # Call the method function with the object as the first argument
            return method_function.execute(context, obj, *args, **kwargs)
        else:
            # For non-DanaFunction methods, call directly
            return method_function(obj, *args, **kwargs)


def register_lambda_method(lambda_expr: LambdaExpression, method_name: str) -> None:
    """Convenience function to register a lambda expression as a struct method.

    Args:
        lambda_expr: The lambda expression with receiver
        method_name: Name to register the method under
    """
    receiver_handler = LambdaReceiver(lambda_expr)
    receiver_handler.register_as_method(method_name)
