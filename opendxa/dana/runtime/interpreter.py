"""DANA Runtime Interpreter.

This module provides the main Interpreter implementation for executing DANA programs.
It uses a modular architecture with specialized components for different aspects of execution.
"""

import logging
from typing import Any, Dict, Optional

from opendxa.common.mixins.loggable import Loggable
from opendxa.common.utils.logging.dxa_logger import DXA_LOGGER
from opendxa.dana.exceptions import InterpretError, RuntimeError
from opendxa.dana.language.ast import LogLevel, Program
from opendxa.dana.language.parser import ParseResult
from opendxa.dana.runtime.context import RuntimeContext
from opendxa.dana.runtime.executor.context_manager import ContextManager
from opendxa.dana.runtime.executor.error_utils import format_error_location
from opendxa.dana.runtime.executor.expression_evaluator import ExpressionEvaluator
from opendxa.dana.runtime.executor.llm_integration import LLMIntegration
from opendxa.dana.runtime.executor.statement_executor import StatementExecutor
from opendxa.dana.runtime.hooks import HookType, execute_hook, has_hooks

# Map DANA LogLevel to Python logging levels
LEVEL_MAP = {LogLevel.DEBUG: logging.DEBUG, LogLevel.INFO: logging.INFO, LogLevel.WARN: logging.WARNING, LogLevel.ERROR: logging.ERROR}

# Re-export for backward compatibility
__all__ = ["Interpreter", "create_interpreter", "format_error_location"]


class Interpreter(Loggable):
    """Interpreter for executing DANA programs.

    This class coordinates the execution of DANA programs using specialized components
    for different aspects of execution.
    """

    def __init__(self, context: RuntimeContext):
        """Initialize the interpreter with a runtime context.

        Args:
            context: The runtime context for state management
        """
        # Initialize Loggable
        super().__init__()

        # Create the execution components
        self.context_manager = ContextManager(context)
        self.expression_evaluator = ExpressionEvaluator(self.context_manager)
        self.llm_integration = LLMIntegration(self.context_manager)
        self.statement_executor = StatementExecutor(self.context_manager, self.expression_evaluator, self.llm_integration)

        # Store a direct reference to the context for backward compatibility
        self.context = context

        # Initialize system state
        self.context.set("system.id", self.statement_executor._execution_id)

    def execute_program(self, parse_result: ParseResult) -> None:
        """Execute a DANA program.

        Args:
            parse_result: Result of parsing the program

        Raises:
            InterpretError: If a program is not provided
            Various exceptions: For errors during execution
        """
        if not isinstance(parse_result.program, Program):
            raise InterpretError(f"Expected a Program node, got {type(parse_result.program).__name__}")

        # Log execution start
        self.debug(f"Executing program with {len(parse_result.program.statements)} statements")

        # Create hook context for program hooks
        hook_context = {"interpreter": self, "context": self.context, "program": parse_result.program, "errors": parse_result.errors}

        # Execute before program hooks
        if has_hooks(HookType.BEFORE_PROGRAM):
            self.debug("Executing BEFORE_PROGRAM hooks")
            execute_hook(HookType.BEFORE_PROGRAM, hook_context)

        try:
            # Execute all statements in the program
            for i, statement in enumerate(parse_result.program.statements):
                # Execute the statement (statement hooks are now handled inside the executor)
                self.debug(f"Executing statement {i+1}/{len(parse_result.program.statements)}: {type(statement).__name__}")
                self.statement_executor.execute(statement)

            # If there are any parse errors, stop at the first one
            if parse_result.errors:
                self.error(f"Encountered parse error: {parse_result.errors[0]}")
                raise parse_result.errors[0]

            # Execute after program hooks
            if has_hooks(HookType.AFTER_PROGRAM):
                self.debug("Executing AFTER_PROGRAM hooks")
                execute_hook(HookType.AFTER_PROGRAM, hook_context)

            self.debug("Program execution completed successfully")

        except Exception as e:
            # Log the error
            self.error(f"Program execution failed: {e}")

            # Execute error hooks
            if has_hooks(HookType.ON_ERROR):
                self.debug("Executing ON_ERROR hooks")
                error_context = {**hook_context, "error": e}
                execute_hook(HookType.ON_ERROR, error_context)

            raise e

    def evaluate_expression(self, node: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        """Evaluate an expression node.

        Args:
            node: The expression node to evaluate
            context: Optional local context for variable resolution

        Returns:
            The result of the expression
        """
        return self.expression_evaluator.evaluate(node, context)

    # Backward compatibility methods

    def visit_node(self, node: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        """Backward compatibility method for visiting nodes.

        Args:
            node: The node to visit
            context: Optional local context

        Returns:
            The result of visiting the node
        """
        from opendxa.dana.language.ast import (
            Assignment,
            BinaryExpression,
            Conditional,
            FStringExpression,
            FunctionCall,
            Identifier,
            Literal,
            LiteralExpression,
            LogLevelSetStatement,
            LogStatement,
            PrintStatement,
            Program,
            ReasonStatement,
            WhileLoop,
        )

        # Handle statements
        if isinstance(node, (Assignment, LogStatement, LogLevelSetStatement, PrintStatement, Conditional, WhileLoop, ReasonStatement)):
            return self.statement_executor.execute(node, context)

        # Handle expressions
        elif isinstance(node, (BinaryExpression, LiteralExpression, Identifier, Literal, FStringExpression)):
            return self.expression_evaluator.evaluate(node, context)

        # Handle function calls
        elif isinstance(node, FunctionCall):
            return self.statement_executor.execute_function_call(node, context)

        # Handle programs
        elif isinstance(node, Program):
            # Create a parse result for the program
            parse_result = ParseResult(program=node)
            return self.execute_program(parse_result)

        # Unknown node type
        else:
            raise RuntimeError(f"Unsupported node type: {type(node).__name__}")

    # Backward compatibility method for REPL functionality

    def _visit_reason_statement_sync(self, node: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        """Method for synchronously visiting reason statements.

        Used by the REPL implementation to handle reason statements in async contexts.

        Args:
            node: The reason statement node
            context: Optional local context

        Returns:
            The result of the reasoning
        """
        if hasattr(self.statement_executor, "_execute_reason_statement_sync"):
            return self.statement_executor._execute_reason_statement_sync(node, context)
        else:
            # Fallback to asynchronous version
            return self.statement_executor.execute_reason_statement(node, context)

    def set_log_level(self, level: LogLevel) -> None:
        """Set the log level for the interpreter.

        Args:
            level: The log level to set
        """
        DXA_LOGGER.setLevel(LEVEL_MAP[level], scope="opendxa.dana")
        self.context.set("system.log_level", level.value)
        self.debug(f"Set log level to {level.value}")


# Factory function for creating interpreters
def create_interpreter(context: RuntimeContext) -> Interpreter:
    """Create a new interpreter with the given context."""
    return Interpreter(context)
