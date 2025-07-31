"""Type inference and validation for lambda expressions."""

from typing import Any
from dana.core.lang.ast import LambdaExpression, Parameter
from dana.core.lang.parser.utils.type_checker import DanaType, TypeEnvironment


class LambdaTypeInferencer:
    """Handles type inference for lambda expressions."""

    def __init__(self, type_environment: TypeEnvironment):
        """Initialize the lambda type inferencer.

        Args:
            type_environment: The current type checking environment
        """
        self.type_environment = type_environment

    def infer_lambda_type(self, lambda_expr: LambdaExpression, context_type: DanaType | None = None) -> DanaType:
        """Infer the complete type of a lambda expression.

        Args:
            lambda_expr: The lambda expression to analyze
            context_type: Optional context type hint from usage

        Returns:
            The inferred function type
        """
        # Create a new scope for type inference
        self.type_environment.push_scope()

        try:
            # Infer receiver type
            receiver_type = self._infer_receiver_type(lambda_expr.receiver, context_type)

            # Infer parameter types
            param_types = self._infer_parameter_types(lambda_expr.parameters, context_type)

            # Bind types to local scope for body analysis
            if receiver_type and lambda_expr.receiver:
                self.type_environment.set(lambda_expr.receiver.name, receiver_type)

            for param, param_type in zip(lambda_expr.parameters, param_types, strict=False):
                self.type_environment.set(param.name, param_type)

            # Infer return type from body
            from dana.core.lang.parser.utils.type_checker import TypeChecker

            type_checker = TypeChecker()
            type_checker.environment = self.type_environment
            return_type = type_checker.check_expression(lambda_expr.body)

            # Create function type representation
            return self._create_function_type(receiver_type, param_types, return_type)

        finally:
            self.type_environment.pop_scope()

    def _infer_receiver_type(self, receiver: Parameter | None, context_type: DanaType | None) -> DanaType | None:
        """Infer the type of a lambda receiver.

        Args:
            receiver: The receiver parameter (if any)
            context_type: Context type hint from usage

        Returns:
            The inferred receiver type or None
        """
        if not receiver:
            return None

        # If receiver has explicit type hint, use it
        if receiver.type_hint:
            return DanaType.from_type_hint(receiver.type_hint)

        # Try to infer from context
        if context_type and context_type.name.startswith("function"):
            # Simplified approach: returning a generic type ('any') for the receiver
            # A full implementation would parse function signatures to extract the receiver type
            return DanaType("any")

        # Default to any if no information available
        return DanaType("any")

    def _infer_parameter_types(self, parameters: list[Parameter], context_type: DanaType | None) -> list[DanaType]:
        """Infer types for lambda parameters.

        Args:
            parameters: List of lambda parameters
            context_type: Context type hint from usage

        Returns:
            List of inferred parameter types
        """
        param_types = []

        for param in parameters:
            if param.type_hint:
                # Use explicit type hint
                param_types.append(DanaType.from_type_hint(param.type_hint))
            else:
                # Try to infer from context or default to any
                param_types.append(DanaType("any"))

        return param_types

    def _create_function_type(self, receiver_type: DanaType | None, param_types: list[DanaType], return_type: DanaType) -> DanaType:
        """Create a function type representation.

        Args:
            receiver_type: Type of receiver (if any)
            param_types: Types of parameters
            return_type: Return type

        Returns:
            A DanaType representing the function
        """
        # Create a function type string representation
        # Format: function(receiver_type?)(param_types...) -> return_type
        param_type_str = ", ".join(ptype.name for ptype in param_types)

        if receiver_type:
            func_type_str = f"function({receiver_type.name})({param_type_str}) -> {return_type.name}"
        else:
            func_type_str = f"function({param_type_str}) -> {return_type.name}"

        return DanaType(func_type_str)

    def validate_receiver_type(self, receiver_type: DanaType, expected_types: list[str]) -> bool:
        """Validate that a receiver type is compatible with expected types.

        Args:
            receiver_type: The actual receiver type
            expected_types: List of expected type names (for union types)

        Returns:
            True if compatible, False otherwise
        """
        if not expected_types:
            return True

        # Check if receiver type matches any of the expected types
        return receiver_type.name in expected_types or "any" in expected_types

    def infer_from_usage_context(self, lambda_expr: LambdaExpression, usage_context: str) -> DanaType:
        """Infer lambda type from its usage context.

        Args:
            lambda_expr: The lambda expression
            usage_context: Context where lambda is used (e.g., "pipeline", "assignment")

        Returns:
            The inferred type based on usage
        """
        if usage_context == "pipeline":
            # In pipeline context, lambdas typically transform data
            return DanaType("function(any) -> any")
        elif usage_context == "assignment":
            # In assignment context, use standard inference
            return self.infer_lambda_type(lambda_expr)
        else:
            # Default inference
            return self.infer_lambda_type(lambda_expr)


class LambdaTypeValidator:
    """Validates lambda type compatibility and constraints."""

    @staticmethod
    def validate_parameter_compatibility(lambda_params: list[Parameter], call_args: list[Any]) -> bool:
        """Validate that call arguments are compatible with lambda parameters.

        Args:
            lambda_params: Lambda parameter definitions
            call_args: Arguments passed to lambda call

        Returns:
            True if compatible, False otherwise
        """
        # Check parameter count
        if len(call_args) > len(lambda_params):
            return False  # Too many arguments

        # Check type compatibility for each argument
        for i, arg in enumerate(call_args):
            if i < len(lambda_params):
                param = lambda_params[i]
                if param.type_hint:
                    expected_type = DanaType.from_type_hint(param.type_hint)
                    actual_type = LambdaTypeValidator._infer_value_type(arg)
                    if not LambdaTypeValidator._is_type_compatible(actual_type, expected_type):
                        return False

        return True

    @staticmethod
    def _infer_value_type(value: Any) -> DanaType:
        """Infer the type of a runtime value.

        Args:
            value: The runtime value

        Returns:
            The inferred DanaType
        """
        if isinstance(value, bool):
            return DanaType("bool")
        elif isinstance(value, int):
            return DanaType("int")
        elif isinstance(value, float):
            return DanaType("float")
        elif isinstance(value, str):
            return DanaType("string")
        elif isinstance(value, list):
            return DanaType("list")
        elif isinstance(value, dict):
            return DanaType("dict")
        elif value is None:
            return DanaType("null")
        else:
            return DanaType("any")

    @staticmethod
    def _is_type_compatible(actual: DanaType, expected: DanaType) -> bool:
        """Check if actual type is compatible with expected type.

        Args:
            actual: The actual type
            expected: The expected type

        Returns:
            True if compatible, False otherwise
        """
        # Exact match
        if actual == expected:
            return True

        # Any type is compatible with everything
        if expected.name == "any" or actual.name == "any":
            return True

        # Int is compatible with float
        if actual.name == "int" and expected.name == "float":
            return True

        # Additional compatibility rules can be added here
        return False
