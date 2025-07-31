"""Lambda receiver support for struct methods."""

from typing import Any

from dana.common.exceptions import SandboxError
from dana.core.lang.ast import LambdaExpression, Parameter
from dana.core.lang.interpreter.struct_system import MethodRegistry
from dana.core.lang.sandbox_context import SandboxContext


class LambdaReceiver:
    """Handles lambda expressions with struct receivers."""

    def __init__(self, lambda_expr: LambdaExpression):
        """Initialize lambda receiver handler.

        Args:
            lambda_expr: The lambda expression with receiver
        """
        self.lambda_expr = lambda_expr
        self.receiver = lambda_expr.receiver
        self.parameters = lambda_expr.parameters
        self.body = lambda_expr.body

    def validate_receiver(self) -> bool:
        """Validate that the receiver is properly defined.

        Returns:
            True if receiver is valid, False otherwise
        """
        if not self.receiver:
            return False

        if not isinstance(self.receiver, Parameter):
            return False

        if not self.receiver.type_hint:
            return False

        return True

    def get_receiver_types(self) -> list[str]:
        """Extract receiver type names, handling union types.

        Returns:
            List of type names the receiver can handle
        """
        if not self.receiver or not self.receiver.type_hint:
            return []

        type_hint_name = self.receiver.type_hint.name

        # Handle union types (e.g., "Point | Circle | Rectangle")
        if " | " in type_hint_name:
            return [t.strip() for t in type_hint_name.split(" | ")]
        else:
            return [type_hint_name]

    def create_method_function(self):
        """Create a method function that can be registered with the MethodRegistry.

        Returns:
            A callable function that implements the lambda as a struct method
        """

        def method_function(receiver_instance: Any, *args, **kwargs):
            """Method function created from lambda with receiver."""
            # Import here to avoid circular imports
            from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter

            # Validate receiver type at runtime
            if not self._validate_receiver_instance(receiver_instance):
                receiver_types = self.get_receiver_types()
                raise SandboxError(
                    f"Invalid receiver type for lambda method. Expected one of {receiver_types}, got {type(receiver_instance)}"
                )

            # Create execution context for the lambda
            # TODO: This should be passed from the caller
            context = SandboxContext()

            # Create a copy of the context for method execution
            method_context = context.copy()

            # Bind receiver to the receiver parameter
            method_context.set(self.receiver.name, receiver_instance)

            # Bind regular parameters
            for i, param in enumerate(self.parameters):
                if i < len(args):
                    method_context.set(param.name, args[i])
                elif param.name in kwargs:
                    method_context.set(param.name, kwargs[param.name])

            # Execute the lambda body
            interpreter = DanaInterpreter()
            try:
                return interpreter.evaluate_expression(self.body, method_context)
            except Exception as e:
                raise SandboxError(f"Error executing lambda method: {e}")

        # Store lambda metadata on the function
        method_function._dana_lambda_receiver = self.receiver
        method_function._dana_lambda_parameters = self.parameters
        method_function._dana_lambda_body = self.body

        return method_function

    def _validate_receiver_instance(self, instance: Any) -> bool:
        """Validate that an instance matches the receiver type.

        Args:
            instance: The runtime instance to validate

        Returns:
            True if instance is compatible with receiver type
        """
        receiver_types = self.get_receiver_types()

        # Check if instance is a struct with matching type
        if hasattr(instance, "__struct_type__"):
            struct_type = instance.__struct_type__
            return struct_type.name in receiver_types

        # For non-struct types, check Python type compatibility
        # This is a simplified check - a full implementation would have proper type mapping
        instance_type = type(instance).__name__
        return instance_type in receiver_types or "any" in receiver_types

    def register_as_method(self, method_name: str) -> None:
        """Register this lambda as a struct method.

        Args:
            method_name: Name to register the method under
        """
        if not self.validate_receiver():
            raise ValueError("Cannot register lambda without valid receiver")

        receiver_types = self.get_receiver_types()
        method_function = self.create_method_function()

        # Register with the method registry
        MethodRegistry.register_method(receiver_types, method_name, method_function)


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
        return MethodRegistry.has_method(struct_type.name, method_name)

    @staticmethod
    def dispatch_method_call(obj: Any, method_name: str, *args, **kwargs) -> Any:
        """Dispatch a method call to a lambda with receiver.

        Args:
            obj: The object the method is being called on
            method_name: The method name
            *args: Method arguments
            **kwargs: Method keyword arguments

        Returns:
            The result of the method call
        """
        if not hasattr(obj, "__struct_type__"):
            raise SandboxError(f"Object {obj} is not a struct instance")

        struct_type = obj.__struct_type__
        method_function = MethodRegistry.get_method(struct_type.name, method_name)

        if method_function is None:
            raise AttributeError(f"No lambda method '{method_name}' found for type '{struct_type.name}'")

        # Call the method function with the object as the first argument
        return method_function(obj, *args, **kwargs)


def register_lambda_method(lambda_expr: LambdaExpression, method_name: str) -> None:
    """Convenience function to register a lambda expression as a struct method.

    Args:
        lambda_expr: The lambda expression with receiver
        method_name: Name to register the method under
    """
    receiver_handler = LambdaReceiver(lambda_expr)
    receiver_handler.register_as_method(method_name)
