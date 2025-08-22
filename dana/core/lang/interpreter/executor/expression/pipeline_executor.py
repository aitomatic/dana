"""
Pipeline executor for Dana with support for named parameter capture.

This module provides pipeline execution with support for:
1. Implicit first-argument mode (default)
2. Explicit placeholder mode ($$)
3. Named parameter capture mode (as param)

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any

from dana.common.exceptions import SandboxError
from dana.core.lang.ast import (
    BinaryExpression,
    BinaryOperator,
    FunctionCall,
    Identifier,
    NamedPipelineStage,
    PlaceholderExpression,
)
from dana.core.lang.sandbox_context import SandboxContext


class PipelineExecutor:
    """Pipeline executor with support for named parameter capture."""

    def __init__(self, parent_executor=None):
        """Initialize the pipeline executor."""
        self.parent_executor = parent_executor

    def execute_pipeline(self, pipeline_expr: BinaryExpression, context: SandboxContext, *args, **kwargs) -> Any:
        """Execute a pipeline expression with support for named parameter capture.

        Args:
            pipeline_expr: The pipeline expression to execute
            context: The execution context
            *args: Initial arguments for the pipeline
            **kwargs: Initial keyword arguments for the pipeline

        Returns:
            The final result of the pipeline execution (may be an EagerPromise object)
        """
        # Extract pipeline stages from the binary expression tree
        stages = self._extract_pipeline_stages(pipeline_expr)

        # Execute the pipeline with named parameter support
        return self._execute_pipeline_stages(stages, context, *args, **kwargs)

    def _extract_pipeline_stages(self, pipeline_expr: BinaryExpression) -> list[NamedPipelineStage]:
        """Extract pipeline stages from a binary expression tree.

        Args:
            pipeline_expr: The pipeline expression to extract stages from

        Returns:
            List of pipeline stages
        """
        stages = []

        # Recursively extract stages from the left side
        if isinstance(pipeline_expr.left, BinaryExpression) and pipeline_expr.left.operator == BinaryOperator.PIPE:
            stages.extend(self._extract_pipeline_stages(pipeline_expr.left))
        else:
            # Convert to NamedPipelineStage if not already
            if isinstance(pipeline_expr.left, NamedPipelineStage):
                stages.append(pipeline_expr.left)
            else:
                stages.append(NamedPipelineStage(expression=pipeline_expr.left))

        # Add the right stage
        if isinstance(pipeline_expr.right, NamedPipelineStage):
            stages.append(pipeline_expr.right)
        else:
            stages.append(NamedPipelineStage(expression=pipeline_expr.right))

        return stages

    def _execute_pipeline_stages(self, stages: list[NamedPipelineStage], context: SandboxContext, *args, **kwargs) -> Any:
        """Execute pipeline stages with named parameter capture support.

        Args:
            stages: List of pipeline stages to execute
            context: The execution context
            *args: Initial arguments
            **kwargs: Initial keyword arguments

        Returns:
            The final result of the pipeline (may be an EagerPromise object)
        """
        # Initialize pipeline context for named captures
        pipeline_context: dict[str, Any] = {}

        # Start with the initial value (first argument)
        current_value = args[0] if args else None
        # current_value may be an EagerPromise object - this is handled by Promise transparency

        # Execute each stage in sequence
        for stage in stages:
            # Execute the stage - the result may be an EagerPromise object
            current_value = self._execute_single_stage(stage, current_value, pipeline_context, context)

            # Capture the result if this stage has a name
            if stage.name:
                # current_value may be an EagerPromise object - this is handled by Promise transparency
                pipeline_context[stage.name] = current_value

        # Return the final result - may be an EagerPromise object
        return current_value

    def _execute_single_stage(
        self, stage: NamedPipelineStage, current_value: Any, pipeline_context: dict[str, Any], context: SandboxContext
    ) -> Any:
        """Execute a single pipeline stage.

        Args:
            stage: The pipeline stage to execute
            current_value: The current value from previous stages (may be an EagerPromise object)
            pipeline_context: Dictionary of named captures
            context: The execution context

        Returns:
            The result of executing this stage (may be an EagerPromise object)
        """
        expression = stage.expression

        # Handle different expression types
        if isinstance(expression, FunctionCall):
            return self._execute_function_call_stage(expression, current_value, pipeline_context, context)
        elif isinstance(expression, Identifier):
            return self._execute_identifier_stage(expression, current_value, pipeline_context, context)
        elif isinstance(expression, BinaryExpression) and expression.operator == BinaryOperator.PIPE:
            # Nested pipeline - execute recursively
            return self.execute_pipeline(expression, context, current_value)
        else:
            # For other expression types, evaluate normally
            if self.parent_executor:
                result = self.parent_executor.execute(expression, context)
                # The result may be an EagerPromise object - this is handled by Promise transparency
                return result
            else:
                raise SandboxError(f"Cannot execute pipeline stage: {type(expression)}")

    def _execute_function_call_stage(
        self, func_call: FunctionCall, current_value: Any, pipeline_context: dict[str, Any], context: SandboxContext
    ) -> Any:
        """Execute a function call stage with parameter resolution and Promise transparency.

        Args:
            func_call: The function call to execute
            current_value: The current pipeline value (may be an EagerPromise object)
            pipeline_context: Dictionary of named captures
            context: The execution context

        Returns:
            The result of the function call (may be an EagerPromise object)
        """
        # Resolve the function
        func = self._resolve_function(func_call.name, context)

        if not callable(func):
            raise SandboxError(f"'{func_call.name}' is not callable")

        # Process arguments with placeholder and named variable substitution
        args = []
        kwargs = {}

        if isinstance(func_call.args, dict):
            # Handle positional arguments
            if "__positional" in func_call.args:
                for arg_expr in func_call.args["__positional"]:
                    resolved_arg = self._resolve_argument(arg_expr, current_value, pipeline_context, context)
                    args.append(resolved_arg)

            # Handle keyword arguments
            for key, arg_expr in func_call.args.items():
                if key != "__positional":
                    resolved_arg = self._resolve_argument(arg_expr, current_value, pipeline_context, context)
                    kwargs[key] = resolved_arg

        # Check if we need implicit first-argument insertion
        has_placeholder = self._contains_placeholder_or_named_variable(func_call.args.get("__positional", []), pipeline_context)

        if not has_placeholder:
            # No placeholders or named variables found, insert current_value as first argument
            # current_value may be an EagerPromise object - this is handled by Promise transparency
            args.insert(0, current_value)

        # Execute the function - the result may be an EagerPromise object
        # Promise transparency will handle resolution when the result is accessed
        return self._call_function(func, context, *args, **kwargs)

    def _execute_identifier_stage(
        self, identifier: Identifier, current_value: Any, pipeline_context: dict[str, Any], context: SandboxContext
    ) -> Any:
        """Execute an identifier stage (function name).

        Args:
            identifier: The function identifier
            current_value: The current pipeline value (may be an EagerPromise object)
            pipeline_context: Dictionary of named captures
            context: The execution context

        Returns:
            The result of calling the function (may be an EagerPromise object)
        """
        func = self._resolve_function(identifier, context)

        if not callable(func):
            raise SandboxError(f"'{identifier.name}' is not callable")

        # Call the function with the current value
        # current_value may be an EagerPromise object - this is handled by Promise transparency
        result = self._call_function(func, context, current_value)
        # The result may be an EagerPromise object - this is handled by Promise transparency
        return result

    def _resolve_argument(self, arg_expr: Any, current_value: Any, pipeline_context: dict[str, Any], context: SandboxContext) -> Any:
        """Resolve an argument expression with placeholder and named variable substitution.

        Args:
            arg_expr: The argument expression
            current_value: The current pipeline value (may be an EagerPromise object)
            pipeline_context: Dictionary of named captures
            context: The execution context

        Returns:
            The resolved argument value (may be an EagerPromise object)
        """
        if isinstance(arg_expr, PlaceholderExpression):
            # $$ placeholder - substitute current pipeline value
            # current_value may be an EagerPromise object - this is handled by Promise transparency
            return current_value
        elif isinstance(arg_expr, Identifier):
            # Check if this is a named variable from pipeline context
            if arg_expr.name in pipeline_context:
                # The value in pipeline_context may be an EagerPromise object - this is handled by Promise transparency
                return pipeline_context[arg_expr.name]
            else:
                # Regular identifier - evaluate normally
                if self.parent_executor:
                    result = self.parent_executor.execute(arg_expr, context)
                    # The result may be an EagerPromise object - this is handled by Promise transparency
                    return result
                else:
                    raise SandboxError(f"Cannot resolve identifier: {arg_expr.name}")
        elif hasattr(arg_expr, "__class__") and arg_expr.__class__.__name__ == "LiteralExpression":
            # Handle literal expressions directly
            return arg_expr.value
        else:
            # Other expression types - evaluate normally using parent executor
            if self.parent_executor:
                result = self.parent_executor.execute(arg_expr, context)
                # The result may be an EagerPromise object - this is handled by Promise transparency
                return result
            else:
                # Try to get parent executor from context
                if hasattr(context, "_interpreter") and hasattr(context._interpreter, "_expression_executor"):
                    result = context._interpreter._expression_executor.execute(arg_expr, context)
                    # The result may be an EagerPromise object - this is handled by Promise transparency
                    return result
                else:
                    raise SandboxError(f"Cannot resolve argument: {type(arg_expr)} - no parent executor available")

    def _resolve_function(self, func_name: Any, context: SandboxContext) -> Any:
        """Resolve a function name to a callable.

        Args:
            func_name: The function name or expression
            context: The execution context

        Returns:
            The resolved function
        """
        if isinstance(func_name, str):
            # Try to get from context
            try:
                func = context.get(f"local:{func_name}")
                if callable(func):
                    return func
            except (KeyError, AttributeError):
                pass

            # Try function registry
            if hasattr(context, "_interpreter") and hasattr(context._interpreter, "function_registry"):
                registry = context._interpreter.function_registry
                if registry.has(func_name):
                    resolved_func, func_type, metadata = registry.resolve_with_type(func_name)
                    return resolved_func

            raise SandboxError(f"Function '{func_name}' not found")
        elif isinstance(func_name, Identifier):
            return self._resolve_function(func_name.name, context)
        else:
            # For other types, try to evaluate
            if self.parent_executor:
                return self.parent_executor.execute(func_name, context)
            else:
                raise SandboxError(f"Cannot resolve function: {type(func_name)}")

    def _contains_placeholder_or_named_variable(self, args: list[Any], pipeline_context: dict[str, Any]) -> bool:
        """Check if arguments contain placeholders or named variables.

        Args:
            args: List of arguments to check
            pipeline_context: Dictionary of named captures

        Returns:
            True if any placeholder or named variable is found
        """
        for arg in args:
            if isinstance(arg, PlaceholderExpression):
                return True
            elif isinstance(arg, Identifier) and arg.name in pipeline_context:
                return True
        return False

    def _call_function(self, func: Any, context: SandboxContext, *args, **kwargs) -> Any:
        """Call a function with proper context handling and Promise transparency.

        Args:
            func: The function to call
            context: The execution context
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            The result of the function call (may be an EagerPromise object)
        """
        # Handle SandboxFunction objects (including DanaFunction)
        if hasattr(func, "execute") and callable(func.execute):
            result = func.execute(context, *args, **kwargs)
            # The result may be an EagerPromise object - this is expected behavior
            # The Promise transparency will handle resolution when the result is accessed
            return result

        # Handle regular callables
        if callable(func):
            try:
                # Try calling with context first
                result = func(context, *args, **kwargs)
                # The result may be an EagerPromise object - this is expected behavior
                return result
            except TypeError:
                # If that fails, try without context
                result = func(*args, **kwargs)
                # The result may be an EagerPromise object - this is expected behavior
                return result

        raise SandboxError(f"Cannot call non-callable object: {type(func)}")
