"""DANA Runtime Interpreter.

This module provides the main Interpreter implementation for executing DANA programs.
It uses a modular architecture with specialized components for different aspects of execution.
"""

import logging
from typing import Any, Dict, Optional

from opendxa.common.mixins.loggable import Loggable
from opendxa.dana.common.exceptions import SandboxError
from dana.parser.dana_parser import ParseResult
from opendxa.dana.sandbox.executor.context_manager import ContextManager
from opendxa.dana.sandbox.executor.expression_evaluator import ExpressionEvaluator
from opendxa.dana.sandbox.executor.llm_integration import LLMIntegration
from opendxa.dana.sandbox.executor.statement_executor import StatementExecutor
from opendxa.dana.sandbox.hooks import HookRegistry, HookType
from opendxa.dana.sandbox.log_manager import LogLevel
from opendxa.dana.sandbox.sandbox_context import SandboxContext

# Map DANA LogLevel to Python logging levels
LEVEL_MAP = {LogLevel.DEBUG: logging.DEBUG, LogLevel.INFO: logging.INFO, LogLevel.WARN: logging.WARNING, LogLevel.ERROR: logging.ERROR}


class Interpreter(Loggable):
    """Interpreter for executing DANA programs."""

    def __init__(self, context: Optional[SandboxContext] = None):
        """Initialize the interpreter.

        Args:
            context: Optional runtime context to use
        """
        super().__init__()
        self.context = context or SandboxContext()
        self.context_manager = ContextManager(self.context)
        self.expression_evaluator = ExpressionEvaluator(self.context_manager)
        self.llm_integration = LLMIntegration(self.context_manager)
        self.statement_executor = StatementExecutor(self.context_manager, self.expression_evaluator, self.llm_integration)

        # Initialize system state
        self.context.set("system.id", self.statement_executor._execution_id)

    def evaluate_expression(self, expression: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        """Evaluate an expression.

        Args:
            expression: The expression to evaluate
            context: Optional local context

        Returns:
            The result of evaluating the expression
        """
        return self.expression_evaluator.evaluate(expression, context)

    def execute_program(self, parse_result: ParseResult) -> Any:
        """Execute a DANA program.

        Args:
            parse_result: The parse result containing the program to execute

        Returns:
            The result of executing the program

        Raises:
            RuntimeError: If the program execution fails
        """
        # Initialize hook context
        hook_context = {
            "program": parse_result.program,
            "context": self.context,
        }

        # Execute before program hooks
        if HookRegistry.has_hooks(HookType.BEFORE_PROGRAM):
            self.debug("Executing BEFORE_PROGRAM hooks")
            HookRegistry.execute(HookType.BEFORE_PROGRAM, hook_context)

        try:
            # Execute all statements in the program
            last_result = None
            for i, statement in enumerate(parse_result.program.statements):
                # Execute the statement (statement hooks are now handled inside the executor)
                self.debug(f"Executing statement {i+1}/{len(parse_result.program.statements)}: {type(statement).__name__}")

                # Handle statement execution with better error messages
                try:
                    result = self.statement_executor.execute(statement)
                    last_result = result
                except Exception as e:
                    if "Undefined variable" in str(e) or "Variable" in str(e):
                        # Use consistent error message format
                        error_msg = str(e)
                        if "must be accessed with a scope prefix" not in error_msg:
                            # If it's a bare variable reference, suggest the correct format
                            var_name = error_msg.split("'")[1] if "'" in error_msg else ""
                            if var_name and "." not in var_name:
                                raise SandboxError(
                                    f"Variable '{var_name}' must be accessed with a scope prefix: "
                                    f"private.{var_name}, public.{var_name}, or system.{var_name}"
                                )
                    raise e

                # For single-statement programs, ensure we return the statement's value
                if len(parse_result.program.statements) == 1:
                    # Store in context directly for REPL to retrieve
                    if last_result is not None:
                        self.context.set(StatementExecutor.LAST_VALUE, last_result)

            # If there are any parse errors, stop at the first one
            if parse_result.errors:
                self.error(f"Encountered parse error: {parse_result.errors[0]}")
                raise parse_result.errors[0]

            # Execute after program hooks
            if HookRegistry.has_hooks(HookType.AFTER_PROGRAM):
                self.debug("Executing AFTER_PROGRAM hooks")
                HookRegistry.execute(HookType.AFTER_PROGRAM, hook_context)

            self.debug("Program execution completed successfully")
            return last_result

        except Exception as e:
            # Log the error
            self.debug(f"Program execution failed: {e}")

            # Execute error hooks
            if HookRegistry.has_hooks(HookType.ON_ERROR):
                self.debug("Executing ON_ERROR hooks")
                error_context = {**hook_context, "error": e}
                HookRegistry.execute(HookType.ON_ERROR, error_context)

            raise e

    @classmethod
    def new(cls, context: SandboxContext) -> "Interpreter":
        """Create a new instance of the Interpreter.

        Args:
            context: The runtime context for the interpreter.

        Returns:
            An instance of the Interpreter.
        """
        return cls(context)
