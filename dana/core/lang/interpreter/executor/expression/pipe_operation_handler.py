"""
Clean pipe operation handler for Dana function composition.

This module provides pure function composition using the pipe operator.
Supports the two-statement approach:
1. pipeline = f1 | f2 | [f3, f4]  (pure composition)
2. result = pipeline(data)        (pure application)

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any

from dana.common.exceptions import SandboxError
from dana.common.mixins.loggable import Loggable
from dana.core.lang.ast import AttributeAccess, BinaryExpression, BinaryOperator, FunctionCall, Identifier, ListLiteral, NamedPipelineStage
from dana.core.lang.interpreter.functions.composed_function import ComposedFunction
from dana.core.lang.interpreter.functions.sandbox_function import SandboxFunction
from dana.core.lang.sandbox_context import SandboxContext


class ParallelFunction(SandboxFunction):
    """Function that executes multiple functions with the same input and returns a list of results.

    Note: Despite the name 'Parallel', this currently executes functions sequentially.
    The name reflects the conceptual parallel application of multiple functions to the same data.
    """

    def __init__(self, functions: list[Any], context: SandboxContext | None = None):
        """Initialize a parallel function.

        Args:
            functions: List of functions to execute with the same input
            context: The execution context (optional)
        """
        super().__init__()
        self.functions = functions
        self.context = context

    def execute(self, context: SandboxContext, *args, **kwargs) -> list[Any]:
        """Execute all functions with the same input and return list of results."""
        results = []

        # In a pipeline context, the first argument is the intermediate result from the left function
        # We should pass this single value to each function in the parallel list
        if len(args) == 1 and len(kwargs) == 0:
            # Single argument case - this is likely the intermediate result from a pipeline
            input_value = args[0]
            for func in self.functions:
                result = self._call_function(func, context, input_value)
                results.append(result)
        else:
            # Multiple arguments case - pass all arguments to each function
            for func in self.functions:
                result = self._call_function(func, context, *args, **kwargs)
                results.append(result)

        # Auto-resolve any promises in the results
        from dana.core.concurrency.promise_utils import resolve_if_promise

        resolved_results = []
        for result in results:
            resolved_results.append(resolve_if_promise(result))

        return resolved_results

    def restore_context(self, context: SandboxContext, original_context: SandboxContext) -> None:
        """Restore context after function execution (required by SandboxFunction)."""
        # For parallel functions, we don't need special context restoration
        pass

    def _call_function(self, func: Any, context: SandboxContext, *args, **kwargs) -> Any:
        """Call a function with proper context handling."""
        # Handle SandboxFunction objects (including composed functions)
        if isinstance(func, SandboxFunction):
            # Ensure the context has an interpreter for DanaFunction execution
            if not hasattr(context, "_interpreter") or context._interpreter is None:
                # Try to get interpreter from the function's context if available
                if hasattr(func, "context") and func.context is not None:
                    if hasattr(func.context, "_interpreter") and func.context._interpreter is not None:
                        context._interpreter = func.context._interpreter
            return func.execute(context, *args, **kwargs)

        # Handle direct callables
        if callable(func):
            try:
                # Try calling without context first (most common case)
                return func(*args, **kwargs)
            except TypeError:
                # If that fails, try with context (for functions that expect context)
                try:
                    return func(context, *args, **kwargs)
                except Exception as e:
                    raise SandboxError(f"Error calling function {func}: {e}")
        else:
            raise SandboxError(f"Cannot call non-callable object: {type(func)}")

    def __str__(self) -> str:
        return f"ParallelFunction({self.functions})"

    def __repr__(self) -> str:
        return f"ParallelFunction(functions={self.functions})"


class NamedPipelineComposedFunction(SandboxFunction):
    """A composed function that supports named parameter capture in pipelines."""

    def __init__(self, pipeline_expr: BinaryExpression, context: SandboxContext | None = None):
        """Initialize a named pipeline composed function.

        Args:
            pipeline_expr: The pipeline expression to execute
            context: Optional sandbox context
        """
        super().__init__(context)
        self.pipeline_expr = pipeline_expr
        self._pipeline_executor = None

    def execute(self, context: SandboxContext, *args, **kwargs) -> Any:
        """Execute the pipeline with named parameter capture support.

        Args:
            context: The execution context
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            The result of the pipeline execution
        """
        # Lazy initialize the pipeline executor with parent executor
        if self._pipeline_executor is None:
            from dana.core.lang.interpreter.executor.expression.pipeline_executor import PipelineExecutor

            # Get the parent executor from the context's interpreter
            parent_executor = None
            if hasattr(context, "_interpreter") and hasattr(context._interpreter, "_expression_executor"):
                parent_executor = context._interpreter._expression_executor
            self._pipeline_executor = PipelineExecutor(parent_executor=parent_executor)

        return self._pipeline_executor.execute_pipeline(self.pipeline_expr, context, *args, **kwargs)

    def restore_context(self, context: SandboxContext, original_context: SandboxContext) -> None:
        """Restore context after function execution (required by SandboxFunction)."""
        # No special context restoration needed
        pass

    def __repr__(self) -> str:
        return f"NamedPipelineComposedFunction({self.pipeline_expr})"


class PipeOperationHandler(Loggable):
    """Clean pipe operation handler for pure function composition."""

    def __init__(self, parent_executor: Any = None):
        """Initialize the pipe operation handler."""
        super().__init__()
        self.parent_executor = parent_executor

    def execute_pipe(self, left: Any, right: Any, context: SandboxContext) -> Any:
        """Execute a pipe operation for pure function composition.

        Supports only function-to-function composition:
        - f1 | f2 -> ComposedFunction

        Does NOT support data pipelines like: data | function
        """
        try:
            # Check if this is a declarative function composition with named stages
            if self._has_named_stages(left) or self._has_named_stages(right):
                # Use the new named pipeline composed function
                pipeline_expr = self._create_pipeline_expression(left, right)
                return NamedPipelineComposedFunction(pipeline_expr, context=context)

            # Handle NamedPipelineStage objects without names (convert to regular expressions)
            left_expr = self._unwrap_named_stage(left)
            right_expr = self._unwrap_named_stage(right)

            # Resolve both operands to functions
            left_func = self._resolve_to_function(left_expr, context)
            right_func = self._resolve_to_function(right_expr, context)

            # Create composed function using Dana's existing infrastructure
            return ComposedFunction(left_func, right_func, context=context)

        except Exception as e:
            if isinstance(e, SandboxError):
                raise
            raise SandboxError(f"Error in pipe composition: {e}")

    def _unwrap_named_stage(self, expr: Any) -> Any:
        """Unwrap a NamedPipelineStage to get the underlying expression.

        Args:
            expr: The expression to unwrap

        Returns:
            The unwrapped expression
        """
        if isinstance(expr, NamedPipelineStage):
            return expr.expression
        elif isinstance(expr, BinaryExpression) and expr.operator == BinaryOperator.PIPE:
            return BinaryExpression(
                left=self._unwrap_named_stage(expr.left), operator=expr.operator, right=self._unwrap_named_stage(expr.right)
            )
        return expr

    def _has_named_stages(self, expr: Any) -> bool:
        """Check if an expression contains named pipeline stages.

        Args:
            expr: The expression to check

        Returns:
            True if the expression contains named stages
        """
        if isinstance(expr, NamedPipelineStage):
            return expr.name is not None
        elif isinstance(expr, BinaryExpression) and expr.operator == BinaryOperator.PIPE:
            return self._has_named_stages(expr.left) or self._has_named_stages(expr.right)
        return False

    def _create_pipeline_expression(self, left: Any, right: Any) -> BinaryExpression:
        """Create a pipeline expression from left and right operands.

        Args:
            left: The left operand
            right: The right operand

        Returns:
            A BinaryExpression representing the pipeline
        """
        # If left is already a pipeline, extend it
        if isinstance(left, BinaryExpression) and left.operator == BinaryOperator.PIPE:
            return BinaryExpression(left=left, operator=BinaryOperator.PIPE, right=right)
        else:
            # Create a new pipeline
            return BinaryExpression(left=left, operator=BinaryOperator.PIPE, right=right)

    def _resolve_to_function(self, expr: Any, context: SandboxContext) -> Any:
        """Resolve an expression to a function.

        Handles:
        - Identifiers: resolve from context/registry
        - BinaryExpressions: evaluate recursively
        - FunctionCall: evaluate to get the function
        - ListLiteral: create ParallelFunction for parallel composition
        - Functions: return as-is
        """
        # Handle identifiers
        if isinstance(expr, Identifier):
            return self._resolve_identifier(expr, context)

        # Handle binary expressions (nested compositions)
        if isinstance(expr, BinaryExpression) and expr.operator == BinaryOperator.PIPE:
            return self.execute_pipe(expr.left, expr.right, context)

        # Handle function calls (evaluate to get the function)
        if isinstance(expr, FunctionCall):
            return self._resolve_function_call(expr, context)

        # Handle list literals (parallel function composition)
        if isinstance(expr, ListLiteral):
            return self._resolve_list_literal(expr, context)

        # Handle lambda expressions
        if hasattr(expr, "__class__") and expr.__class__.__name__ == "LambdaExpression":
            return self._resolve_lambda_expression(expr, context)

        # Handle already composed functions and SandboxFunctions
        if isinstance(expr, SandboxFunction | ParallelFunction):
            return expr

        # Handle direct callables
        if callable(expr):
            # Wrap callables in a SandboxFunction-compatible wrapper
            from dana.core.lang.interpreter.functions.composed_function import ComposedFunction

            return ComposedFunction._wrap_callable(expr, str(expr), context)

        # Strict validation: reject non-callable objects early
        raise SandboxError(
            f"Cannot use non-function '{expr}' of type {type(expr).__name__} in pipe composition. Only functions are allowed."
        )

    def _resolve_function_call(self, func_call: FunctionCall, context: SandboxContext) -> Any:
        """Resolve a function call to a function (partial application)."""
        # Handle AttributeAccess for method calls
        if isinstance(func_call.name, AttributeAccess):
            # Resolve the object and get the method
            if self.parent_executor is None:
                # Handle case where parent_executor is not available
                # Try to resolve the object directly from context
                if isinstance(func_call.name.object, Identifier):
                    obj = context.get(func_call.name.object.name)
                    if obj is None:
                        raise SandboxError(f"Object '{func_call.name.object.name}' not found in context")
                else:
                    raise SandboxError("Cannot resolve attribute access without parent executor")
            else:
                obj = self.parent_executor.execute(func_call.name.object, context)

            method_name = func_call.name.attribute
            if hasattr(obj, method_name):
                func = getattr(obj, method_name)
                if callable(func):
                    return func
                else:
                    raise SandboxError(f"'{method_name}' is not a callable method on {type(obj).__name__}")
            else:
                raise SandboxError(f"Object {type(obj).__name__} has no method '{method_name}'")

        # Handle string function names
        func_name = func_call.name if isinstance(func_call.name, str) else func_call.name.name
        func = self._resolve_identifier(Identifier(func_name), context)

        # If the function call has arguments, create a partial function
        if func_call.args and (func_call.args.get("__positional") or any(k != "__positional" for k in func_call.args.keys())):
            # Create a partial function that remembers the arguments
            return self._create_partial_function(func, func_call, context)

        return func

    def _resolve_list_literal(self, list_literal: ListLiteral, context: SandboxContext) -> Any:
        """Resolve a list literal to a ParallelFunction for parallel composition."""
        functions = []

        for item in list_literal.items:
            # Resolve each item to a function
            func = self._resolve_to_function(item, context)
            functions.append(func)

        # Create a ParallelFunction that will execute all functions with the same input
        return ParallelFunction(functions, context=context)

    def _resolve_lambda_expression(self, lambda_expr: Any, context: SandboxContext) -> Any:
        """Resolve a lambda expression to a pipeline-compatible function."""
        try:
            from dana.core.lang.interpreter.pipeline.lambda_pipeline import LambdaPipelineIntegrator

            # Validate lambda for pipeline use
            if not LambdaPipelineIntegrator.validate_lambda_for_pipeline(lambda_expr):
                raise SandboxError("Lambda expression is not suitable for pipeline use")

            # Create pipeline function wrapper
            return LambdaPipelineIntegrator.resolve_lambda_to_pipeline_function(lambda_expr, context)

        except ImportError:
            # Fall back to basic lambda execution if pipeline integration not available
            if self.parent_executor and hasattr(self.parent_executor, "execute_lambda_expression"):
                lambda_func = self.parent_executor.execute_lambda_expression(lambda_expr, context)
                if callable(lambda_func):
                    return lambda_func

            raise SandboxError("Lambda expressions not supported in pipeline operations")

    def _create_partial_function(self, func: Any, func_call: FunctionCall, context: SandboxContext) -> Any:
        """Create a partial function that remembers the original arguments.

        This handles both implicit and explicit pipeline modes:
        - Implicit mode: If no placeholders, insert pipeline value as first argument
        - Explicit mode: If placeholders ($$), substitute them with pipeline value
        """
        from dana.core.lang.ast import PlaceholderExpression
        from dana.core.lang.interpreter.functions.sandbox_function import SandboxFunction

        class PartialFunction(SandboxFunction):
            def __init__(self, base_func, original_args, parent_executor, exec_context):
                super().__init__(exec_context)
                self.base_func = base_func
                self.original_args = original_args
                self.parent_executor = parent_executor
                self.exec_context = exec_context

            def prepare_context(self, context: SandboxContext, args: list, kwargs: dict) -> SandboxContext:
                """Prepare context for partial function execution."""
                return context

            def restore_context(self, context: SandboxContext, original_context: SandboxContext) -> None:
                """Restore context after partial function execution."""
                pass

            def execute(self, context: SandboxContext, pipeline_value: Any) -> Any:
                """Execute the partial function with the pipeline value."""
                # Process arguments with placeholder substitution (same logic as _execute_function_call_stage)
                args = []
                kwargs = {}

                if isinstance(self.original_args, dict):
                    # Handle positional arguments
                    if "__positional" in self.original_args:
                        for arg_expr in self.original_args["__positional"]:
                            if isinstance(arg_expr, PlaceholderExpression):
                                args.append(pipeline_value)
                            else:
                                evaluated = self.parent_executor.execute(arg_expr, context)
                                args.append(evaluated)

                    # Handle keyword arguments
                    for key, arg_expr in self.original_args.items():
                        if key != "__positional":
                            if isinstance(arg_expr, PlaceholderExpression):
                                kwargs[key] = pipeline_value
                            else:
                                kwargs[key] = self.parent_executor.execute(arg_expr, context)
                else:
                    # Fallback for other argument formats
                    args = [pipeline_value]

                # Check if we need implicit first-argument insertion
                has_placeholder = any(isinstance(arg, PlaceholderExpression) for arg in self.original_args.get("__positional", []))

                if not has_placeholder:
                    # No placeholders found, insert pipeline_value as first argument (implicit mode)
                    args.insert(0, pipeline_value)

                # Execute the function with proper context handling
                if isinstance(self.base_func, SandboxFunction):
                    return self.base_func.execute(context, *args, **kwargs)
                else:
                    return self.base_func(*args, **kwargs)

        return PartialFunction(func, func_call.args, self.parent_executor, context)

    def _resolve_identifier(self, identifier: Identifier, context: SandboxContext) -> Any:
        """Resolve an identifier to a function from context or registry."""
        resolved_value = None

        # Try context first
        try:
            resolved_value = context.get(identifier.name)
            if resolved_value is not None:
                # Validate that the resolved value is callable
                if not callable(resolved_value):
                    raise SandboxError(
                        f"Cannot use non-function '{identifier.name}' (value: {resolved_value}) of type {type(resolved_value).__name__} in pipe composition. Only functions are allowed."
                    )
                # Wrap callables in a SandboxFunction-compatible wrapper
                from dana.core.lang.interpreter.functions.composed_function import ComposedFunction

                temp_composed = ComposedFunction(None, None, context)
                return temp_composed._wrap_callable(resolved_value, identifier.name, context)
        except (KeyError, AttributeError):
            pass

        # Try function registry if available
        if (
            self.parent_executor
            and hasattr(self.parent_executor, "parent")
            and hasattr(self.parent_executor.parent, "_function_executor")
            and hasattr(self.parent_executor.parent._function_executor, "function_registry")
        ):
            registry = self.parent_executor.parent._function_executor.function_registry
            if registry.has(identifier.name):
                resolved_func, func_type, metadata = registry.resolve_with_type(identifier.name)
                # Registry should only contain callable functions, but validate to be safe
                if not callable(resolved_func):
                    raise SandboxError(f"Registry contains non-callable for '{identifier.name}': {type(resolved_func).__name__}")
                return resolved_func

        # If not found, raise error
        raise SandboxError(f"Function '{identifier.name}' not found")
