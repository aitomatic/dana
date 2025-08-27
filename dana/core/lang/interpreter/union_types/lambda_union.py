"""Union type support for lambda expressions."""

from typing import Any

from dana.common.exceptions import SandboxError
from dana.core.lang.ast import LambdaExpression, TypeHint
from dana.core.lang.sandbox_context import SandboxContext
from dana.core.lang.type_system.constants import COMMON_TYPE_NAMES, PYTHON_TO_DANA_TYPE_MAPPING
from dana.registry import FUNCTION_REGISTRY, TYPE_REGISTRY


class UnionTypeHandler:
    """Handles union types in lambda receiver declarations."""

    @staticmethod
    def parse_union_type(type_hint: TypeHint) -> list[str]:
        """Parse a union type hint into individual type names.

        Args:
            type_hint: The type hint to parse (e.g., "Point | Circle | Rectangle")

        Returns:
            List of individual type names
        """
        if not type_hint or not type_hint.name:
            return []

        type_name = type_hint.name.strip()

        # Handle union types with "|" separator
        if " | " in type_name:
            return [t.strip() for t in type_name.split(" | ")]
        elif "|" in type_name:
            return [t.strip() for t in type_name.split("|")]
        else:
            # Single type
            return [type_name]

    @staticmethod
    def validate_union_types(type_names: list[str]) -> bool:
        """Validate that all types in a union are valid struct types.

        Args:
            type_names: List of type names to validate

        Returns:
            True if all types are valid
        """
        for type_name in type_names:
            # Check if it's a basic type
            if type_name in COMMON_TYPE_NAMES:
                continue

            # Check if it's a registered struct type
            if TYPE_REGISTRY.exists(type_name):
                continue

            # For now, allow unknown types (they might be defined later)
            # In a full implementation, we'd have stricter validation

        return True

    @staticmethod
    def is_union_type(type_hint: TypeHint | None) -> bool:
        """Check if a type hint represents a union type.

        Args:
            type_hint: The type hint to check

        Returns:
            True if it's a union type
        """
        if not type_hint or not type_hint.name:
            return False

        return " | " in type_hint.name or "|" in type_hint.name


class LambdaUnionReceiver:
    """Handles lambda expressions with union type receivers."""

    def __init__(self, lambda_expr: LambdaExpression):
        """Initialize lambda union receiver handler.

        Args:
            lambda_expr: The lambda expression with union receiver
        """
        self.lambda_expr = lambda_expr
        self.receiver = lambda_expr.receiver
        self.parameters = lambda_expr.parameters
        self.body = lambda_expr.body
        self.union_types = self._extract_union_types()

    def _extract_union_types(self) -> list[str]:
        """Extract union type names from the receiver.

        Returns:
            List of type names in the union
        """
        if not self.receiver or not self.receiver.type_hint:
            return []

        return UnionTypeHandler.parse_union_type(self.receiver.type_hint)

    def validate_union_receiver(self) -> bool:
        """Validate that the union receiver is properly defined.

        Returns:
            True if the union receiver is valid
        """
        if not self.receiver:
            return False

        if not UnionTypeHandler.is_union_type(self.receiver.type_hint):
            return False

        union_types = self.union_types
        if not union_types:
            return False

        return UnionTypeHandler.validate_union_types(union_types)

    def create_union_method_function(self):
        """Create a method function that handles union type dispatch.

        Returns:
            A callable function that dispatches based on runtime type
        """

        def union_method_function(receiver_instance: Any, *args, **kwargs):
            """Method function with union type dispatch."""
            # Determine the runtime type of the receiver
            runtime_type = self._get_runtime_type(receiver_instance)

            # Validate that the runtime type matches one of the union types
            if runtime_type not in self.union_types:
                raise SandboxError(f"Runtime type '{runtime_type}' does not match union types {self.union_types}")

            # Execute the lambda with the receiver bound
            return self._execute_lambda_with_receiver(receiver_instance, *args, **kwargs)

        # Store metadata
        union_method_function._dana_lambda_union_receiver = self.receiver
        union_method_function._dana_lambda_union_types = self.union_types
        union_method_function._dana_lambda_parameters = self.parameters
        union_method_function._dana_lambda_body = self.body

        return union_method_function

    def _get_runtime_type(self, instance: Any) -> str:
        """Get the runtime type name of an instance.

        Args:
            instance: The instance to check

        Returns:
            The type name
        """
        # Check if it's a struct instance
        if hasattr(instance, "__struct_type__"):
            return instance.__struct_type__.name

        # Map Python types to Dana type names
        type_mapping = PYTHON_TO_DANA_TYPE_MAPPING.copy()

        python_type = type(instance)
        return type_mapping.get(python_type, python_type.__name__)

    def _execute_lambda_with_receiver(self, receiver_instance: Any, *args, **kwargs) -> Any:
        """Execute the lambda with the receiver bound.

        Args:
            receiver_instance: The receiver instance
            *args: Additional arguments
            **kwargs: Keyword arguments

        Returns:
            Result of lambda execution
        """
        # Import here to avoid circular imports
        from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter

        # Create execution context
        context = SandboxContext()
        lambda_context = context.copy()

        # Bind receiver
        lambda_context.set(self.receiver.name, receiver_instance)

        # Bind parameters
        for i, param in enumerate(self.parameters):
            if i < len(args):
                lambda_context.set(param.name, args[i])
            elif param.name in kwargs:
                lambda_context.set(param.name, kwargs[param.name])

        # Execute lambda body
        interpreter = DanaInterpreter()
        try:
            return interpreter.evaluate_expression(self.body, lambda_context)
        except Exception as e:
            raise SandboxError(f"Error executing union lambda: {e}")

    def register_union_method(self, method_name: str) -> None:
        """Register this lambda as a method for all union types.

        Args:
            method_name: Name to register the method under
        """
        if not self.validate_union_receiver():
            raise ValueError("Cannot register lambda without valid union receiver")

        union_method_function = self.create_union_method_function()

        # Register for all types in the union
        FUNCTION_REGISTRY.register_struct_function(self.union_types, method_name, union_method_function)


class UnionLambdaDispatcher:
    """Dispatches method calls to lambdas with union receivers."""

    @staticmethod
    def can_handle_union_method_call(obj: Any, method_name: str) -> bool:
        """Check if a method call can be handled by a union lambda.

        Args:
            obj: The object the method is being called on
            method_name: The method name

        Returns:
            True if a union lambda method exists
        """
        if not hasattr(obj, "__struct_type__"):
            return False

        struct_type = obj.__struct_type__
        method = FUNCTION_REGISTRY.lookup_struct_function(struct_type.name, method_name)

        # Check if the method has union receiver metadata
        return method is not None and hasattr(method, "_dana_lambda_union_types") and struct_type.name in method._dana_lambda_union_types

    @staticmethod
    def dispatch_union_method_call(obj: Any, method_name: str, *args, **kwargs) -> Any:
        """Dispatch a method call to a union lambda.

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
        method_function = FUNCTION_REGISTRY.lookup_struct_function(struct_type.name, method_name)

        if method_function is None:
            raise AttributeError(f"No union lambda method '{method_name}' found for type '{struct_type.name}'")

        # Validate that this is indeed a union method
        if not hasattr(method_function, "_dana_lambda_union_types"):
            raise SandboxError(f"Method '{method_name}' is not a union lambda method")

        union_types = method_function._dana_lambda_union_types
        if struct_type.name not in union_types:
            raise SandboxError(f"Type '{struct_type.name}' is not in union types {union_types} for method '{method_name}'")

        # Call the union method function
        return method_function(obj, *args, **kwargs)


def create_union_lambda_method(lambda_expr: LambdaExpression, method_name: str) -> None:
    """Convenience function to create and register a union lambda method.

    Args:
        lambda_expr: The lambda expression with union receiver
        method_name: Name to register the method under
    """
    union_handler = LambdaUnionReceiver(lambda_expr)
    union_handler.register_union_method(method_name)


def enhance_lambda_receiver_with_unions():
    """Enhance lambda receiver support to handle union types.

    This function patches existing lambda receiver functionality to support union types.
    """
    try:
        from dana.core.lang.interpreter.struct_functions.lambda_receiver import LambdaReceiver

        def enhanced_get_receiver_types(self) -> list[str]:
            """Enhanced version that handles union types."""
            if not self.receiver or not self.receiver.type_hint:
                return []

            # Use union type handler
            return UnionTypeHandler.parse_union_type(self.receiver.type_hint)

        # Patch the method
        LambdaReceiver.get_receiver_types = enhanced_get_receiver_types

    except ImportError:
        # Lambda receiver support not available
        pass
