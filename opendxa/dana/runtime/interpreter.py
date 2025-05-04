"""DANA Runtime: Executes parsed AST nodes."""

from typing import TYPE_CHECKING, Any, Optional

from opendxa.dana.exceptions import InterpretError, StateError
from opendxa.dana.language.ast import Assignment, Expression, LiteralExpression, LogStatement, Program, Statement
from opendxa.dana.language.parser import ParseResult
from opendxa.dana.state.context import RuntimeContext

# Conditional import for type hinting only
if TYPE_CHECKING:
    # No RuntimeContext import needed here anymore
    pass


class Interpreter:
    """Interprets and executes DANA AST nodes."""

    def __init__(self, context: Optional[RuntimeContext] = None):
        """Initializes the interpreter with a runtime context."""
        self.context = context if context is not None else RuntimeContext()

    def execute_program(self, parse_result: ParseResult) -> None:
        """Executes a DANA program, node by node.

        Args:
            parse_result: Result of parsing the program, containing:
                - program: The Program to execute
                - error: Any ParseError encountered during parsing
        """
        if not isinstance(parse_result.program, Program):
            raise InterpretError(f"Expected a Program node, got {type(parse_result.program).__name__}")

        try:
            # Execute the partial program
            for statement in parse_result.program.statements:
                self.execute_statement(statement)

            # If there was a parse error, display it after executing valid statements
            if parse_result.error:
                print(f"DANA Error: {parse_result.error}")

        except (InterpretError, StateError) as e:
            # TODO: Enhance error reporting with line numbers if AST nodes store them
            print(f"Runtime Error: {e}")
            # Decide whether to stop execution or continue
            raise  # Re-raise for now
        except Exception as e:
            print(f"Unexpected Runtime Error: {e}")
            raise  # Re-raise unexpected errors

    def execute_statement(self, statement: Statement) -> None:
        """Executes a single statement node by dispatching to visitor methods."""
        if isinstance(statement, Assignment):
            self.visit_Assignment(statement)
        elif isinstance(statement, LogStatement):
            self.visit_LogStatement(statement)
        else:
            raise InterpretError(f"Unsupported statement type for execution: {type(statement).__name__}")

    def visit_Assignment(self, node: Assignment) -> None:
        """Handles execution of an Assignment statement."""
        value_to_assign = self._evaluate_expression(node.value)
        target_key = node.target.name
        # print(f"DEBUG: Assigning {target_key} = {repr(value_to_assign)}") # Optional debug
        self.context.set(target_key, value_to_assign)

    def visit_LogStatement(self, node: LogStatement) -> None:
        """Handles execution of a LogStatement."""
        # In Iteration 1, message is always a LiteralExpression with a string
        if isinstance(node.message, LiteralExpression) and isinstance(node.message.literal.value, str):
            message_to_log = node.message.literal.value
            print(f"[DANA Log] {message_to_log}")
        else:
            # Should not happen with current parser, but good practice
            raise TypeError("Log statement currently only supports string literals.")

    def _evaluate_expression(self, expression: Expression) -> Any:
        """Evaluates an expression node and returns its value."""
        if isinstance(expression, LiteralExpression):
            # For Iteration 1, the only expression is a LiteralExpression
            return expression.literal.value
        # Add other expression types (VariableReference, BinaryOp, FunctionCall) later
        # elif isinstance(expression, VariableReference):
        #     return self.context.get(expression.name)
        else:
            raise InterpretError(f"Unsupported expression type for evaluation: {type(expression).__name__}")
