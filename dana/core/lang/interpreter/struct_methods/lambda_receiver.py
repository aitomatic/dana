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
from dana.core.lang.interpreter.struct_system import universal_method_registry
from dana.core.lang.sandbox_context import SandboxContext


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

        # Register with the universal method registry for structs
        for receiver_type in receiver_types:
            universal_method_registry.register_struct_method(receiver_type, method_name, method_function)


class LambdaMethodDispatcher:
    """Dispatches method calls to lambdas with receivers."""

    @staticmethod
    def can_handle_method_call(obj: Any, method_name: str) -> bool:
        """Check if a method call can be handled by a lambda with receiver.

        Args:
            obj: The object the method is being called on
            method_name: The method name

        Returns:
            True if a lambda method exists for this object type and method name
        """
        if not hasattr(obj, "__struct_type__"):
            return False

        struct_type = obj.__struct_type__
        return universal_method_registry.has_struct_method(struct_type.name, method_name)

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
        method_function = universal_method_registry.get_struct_method(struct_type.name, method_name)

        if method_function is None:
            raise AttributeError(f"No lambda method '{method_name}' found for type '{struct_type.name}'")

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
