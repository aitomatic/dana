"""Pipeline integration for lambda expressions."""

from typing import Any
from collections.abc import Callable
from dana.core.lang.ast import LambdaExpression
from dana.core.lang.sandbox_context import SandboxContext
from dana.common.exceptions import SandboxError


class LambdaPipelineFunction:
    """Wrapper for lambda expressions used in pipeline operations."""

    def __init__(self, lambda_expr: LambdaExpression, context: SandboxContext):
        """Initialize lambda pipeline function.

        Args:
            lambda_expr: The lambda expression
            context: The execution context where lambda was defined
        """
        self.lambda_expr = lambda_expr
        self.context = context
        self._cached_function = None

    def __call__(self, *args, **kwargs) -> Any:
        """Execute the lambda in pipeline context.

        Args:
            *args: Arguments passed from pipeline
            **kwargs: Keyword arguments passed from pipeline

        Returns:
            Result of lambda execution
        """
        if self._cached_function is None:
            # Create the lambda function using the expression executor
            self._cached_function = self._create_lambda_function()

        return self._cached_function(*args, **kwargs)

    def _create_lambda_function(self) -> Callable:
        """Create a callable function from the lambda expression.

        Returns:
            A callable function
        """
        # Import here to avoid circular imports
        from dana.core.lang.interpreter.executor.expression_executor import ExpressionExecutor

        # Create an expression executor to handle lambda creation
        class MockParentExecutor:
            def execute(self, node, context):
                from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter

                interpreter = DanaInterpreter()
                return interpreter.evaluate_expression(node, context)

        parent = MockParentExecutor()
        executor = ExpressionExecutor(parent)

        # Execute the lambda expression to get the function
        return executor.execute_lambda_expression(self.lambda_expr, self.context)

    def supports_pipeline_composition(self) -> bool:
        """Check if this lambda supports pipeline composition.

        Returns:
            True if lambda can be used in pipelines
        """
        # All lambdas support pipeline composition
        return True

    def get_parameter_count(self) -> int:
        """Get the number of parameters the lambda expects.

        Returns:
            Number of parameters (excluding receiver)
        """
        return len(self.lambda_expr.parameters)

    def has_receiver(self) -> bool:
        """Check if lambda has a receiver.

        Returns:
            True if lambda has a receiver
        """
        return self.lambda_expr.receiver is not None

    def __repr__(self) -> str:
        """String representation of lambda pipeline function."""
        params = ", ".join(p.name for p in self.lambda_expr.parameters)
        if self.lambda_expr.receiver:
            return f"LambdaPipelineFunction(({self.lambda_expr.receiver.name}: {self.lambda_expr.receiver.type_hint.name}) {params} :: ...)"
        else:
            return f"LambdaPipelineFunction({params} :: ...)"


class LambdaPipelineIntegrator:
    """Integrates lambda expressions with pipeline operations."""

    @staticmethod
    def can_resolve_as_pipeline_function(expr: Any) -> bool:
        """Check if an expression can be resolved as a pipeline function.

        Args:
            expr: The expression to check

        Returns:
            True if it's a lambda expression suitable for pipelines
        """
        return isinstance(expr, LambdaExpression)

    @staticmethod
    def resolve_lambda_to_pipeline_function(lambda_expr: LambdaExpression, context: SandboxContext) -> LambdaPipelineFunction:
        """Resolve a lambda expression to a pipeline function.

        Args:
            lambda_expr: The lambda expression
            context: The execution context

        Returns:
            A pipeline function wrapper for the lambda
        """
        if not isinstance(lambda_expr, LambdaExpression):
            raise SandboxError(f"Expected LambdaExpression, got {type(lambda_expr)}")

        return LambdaPipelineFunction(lambda_expr, context)

    @staticmethod
    def validate_lambda_for_pipeline(lambda_expr: LambdaExpression) -> bool:
        """Validate that a lambda is suitable for pipeline use.

        Args:
            lambda_expr: The lambda expression to validate

        Returns:
            True if lambda is valid for pipeline use
        """
        # Check that lambda has proper structure
        if not hasattr(lambda_expr, "body") or lambda_expr.body is None:
            return False

        # Check parameter count - pipelines typically expect single input
        # But lambdas with multiple parameters can still be used if curried
        if len(lambda_expr.parameters) > 3:  # Arbitrary limit for pipeline sanity
            return False

        # Receiver lambdas need special handling in pipelines
        if lambda_expr.receiver:
            # Receiver lambdas should have at least one additional parameter
            return len(lambda_expr.parameters) >= 1

        return True

    @staticmethod
    def create_pipeline_lambda_adapter(lambda_expr: LambdaExpression, context: SandboxContext) -> Callable:
        """Create an adapter function for lambdas in pipelines.

        This handles the common case where a lambda needs to be adapted
        for pipeline use (e.g., handling partial application).

        Args:
            lambda_expr: The lambda expression
            context: The execution context

        Returns:
            An adapted function suitable for pipeline composition
        """
        pipeline_func = LambdaPipelineIntegrator.resolve_lambda_to_pipeline_function(lambda_expr, context)

        # If lambda has receiver, create an adapter that handles receiver binding
        if lambda_expr.receiver:

            def receiver_adapter(receiver_obj, *args, **kwargs):
                # Bind receiver and call lambda
                return pipeline_func(receiver_obj, *args, **kwargs)

            return receiver_adapter
        else:
            # Direct pipeline function
            return pipeline_func


def enhance_pipe_operation_with_lambdas():
    """Enhance the pipe operation handler to support lambda expressions.

    This function patches the existing pipe operation handler to recognize
    and properly handle lambda expressions in pipeline contexts.
    """
    try:
        from dana.core.lang.interpreter.executor.expression.pipe_operation_handler import PipeOperationHandler

        # Store original method
        original_resolve_to_function = PipeOperationHandler._resolve_to_function

        def enhanced_resolve_to_function(self, expr: Any, context: SandboxContext) -> Any:
            """Enhanced version that handles lambda expressions."""
            # Check if it's a lambda expression
            if LambdaPipelineIntegrator.can_resolve_as_pipeline_function(expr):
                return LambdaPipelineIntegrator.resolve_lambda_to_pipeline_function(expr, context)

            # Fall back to original implementation
            return original_resolve_to_function(self, expr, context)

        # Patch the method
        PipeOperationHandler._resolve_to_function = enhanced_resolve_to_function

    except ImportError:
        # Pipe operation handler not available
        pass
