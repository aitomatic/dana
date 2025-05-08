"""Expression evaluator for the DANA interpreter.

This module provides the ExpressionEvaluator class, which is responsible for
evaluating expressions in DANA programs.
"""

import re
from typing import Any, Dict, Optional

from opendxa.dana.exceptions import RuntimeError, StateError
from opendxa.dana.language.ast import (
    BinaryExpression,
    BinaryOperator,
    FStringExpression,
    Identifier,
    Literal,
    LiteralExpression,
)
from opendxa.dana.runtime.executor.base_executor import BaseExecutor
from opendxa.dana.runtime.executor.context_manager import ContextManager
from opendxa.dana.runtime.executor.error_utils import (
    create_runtime_error,
    create_state_error,
    handle_execution_error,
)


class ExpressionEvaluator(BaseExecutor):
    """Evaluates expressions in DANA programs.

    Responsibilities:
    - Evaluate binary expressions
    - Evaluate identifier references
    - Evaluate literal expressions
    - Evaluate f-string expressions
    """

    def __init__(self, context_manager: ContextManager):
        """Initialize the expression evaluator.

        Args:
            context_manager: The context manager for variable resolution
        """
        super().__init__()
        self.context_manager = context_manager

    def evaluate(self, node: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        """Evaluate an expression node.

        Args:
            node: The expression node to evaluate
            context: Optional local context for variable resolution

        Returns:
            The result of evaluating the expression

        Raises:
            RuntimeError: If the expression cannot be evaluated
        """
        try:
            if isinstance(node, BinaryExpression):
                return self.evaluate_binary_expression(node, context)
            elif isinstance(node, LiteralExpression):
                return self.evaluate_literal_expression(node, context)
            elif isinstance(node, Identifier):
                return self.evaluate_identifier(node, context)
            elif isinstance(node, Literal):
                return self.evaluate_literal(node, context)
            elif isinstance(node, FStringExpression):
                return self.evaluate_fstring_expression(node, context)
            else:
                error_msg = f"Unsupported expression type: {type(node).__name__}"
                raise RuntimeError(error_msg)
        except Exception as e:
            error, passthrough = handle_execution_error(e, node, "evaluating expression")
            if passthrough:
                raise error
            else:
                raise RuntimeError(f"Failed to evaluate expression: {e}")

    def evaluate_binary_expression(self, node: BinaryExpression, context: Optional[Dict[str, Any]] = None) -> Any:
        """Evaluate a binary expression.

        Args:
            node: The binary expression to evaluate
            context: Optional local context for variable resolution

        Returns:
            The result of evaluating the expression

        Raises:
            StateError: If the expression contains invalid operations
        """
        try:
            self.debug(f"Evaluating binary expression with operator: {node.operator}")

            # Evaluate left operand
            if isinstance(node.left, Identifier):
                try:
                    left = self.context_manager.get_variable(node.left.name, context)
                    self.debug(f"Evaluated {node.left.name} = {left}")
                except Exception as e:
                    self.debug(f"Error evaluating left operand: {e}")
                    if "." in node.left.name:
                        raise create_state_error(f"Variable '{node.left.name}' not found", node)
                    else:
                        raise create_state_error(
                            f"Variable '{node.left.name}' must be accessed with a scope prefix: "
                            f"private.{node.left.name}, public.{node.left.name}, or system.{node.left.name}",
                            node,
                        )
            else:
                left = self.evaluate(node.left, context)
                self.debug(f"Evaluated left operand: {left}")

            # Evaluate right operand
            if isinstance(node.right, Identifier):
                try:
                    right = self.context_manager.get_variable(node.right.name, context)
                    self.debug(f"Evaluated {node.right.name} = {right}")
                except Exception as e:
                    self.debug(f"Error evaluating right operand: {e}")
                    if "." in node.right.name:
                        raise create_state_error(f"Variable '{node.right.name}' not found", node)
                    else:
                        raise create_state_error(
                            f"Variable '{node.right.name}' must be accessed with a scope prefix: "
                            f"private.{node.right.name}, public.{node.right.name}, or system.{node.right.name}",
                            node,
                        )
            else:
                right = self.evaluate(node.right, context)
                self.debug(f"Evaluated right operand: {right}")

            # Process the operation based on operator type
            if node.operator == BinaryOperator.ADD:
                # String concatenation
                if isinstance(left, str) or isinstance(right, str):
                    return str(left) + str(right)
                return left + right
            elif node.operator == BinaryOperator.SUBTRACT:
                return left - right
            elif node.operator == BinaryOperator.MULTIPLY:
                return left * right
            elif node.operator == BinaryOperator.DIVIDE:
                if right == 0:
                    raise create_state_error("Division by zero", node)
                return left / right
            elif node.operator == BinaryOperator.MODULO:
                if right == 0:
                    raise create_state_error("Modulo by zero", node)
                return left % right
            elif node.operator == BinaryOperator.EQUALS:
                return left == right
            elif node.operator == BinaryOperator.NOT_EQUALS:
                return left != right
            elif node.operator == BinaryOperator.LESS_THAN:
                return left < right
            elif node.operator == BinaryOperator.GREATER_THAN:
                return left > right
            elif node.operator == BinaryOperator.LESS_EQUALS:
                return left <= right
            elif node.operator == BinaryOperator.GREATER_EQUALS:
                return left >= right
            elif node.operator == BinaryOperator.AND:
                return left and right
            elif node.operator == BinaryOperator.OR:
                return left or right
            elif node.operator == BinaryOperator.IN:
                return left in right
            else:
                # Unsupported operator
                raise create_state_error(f"Unsupported binary operator: {node.operator.value}", node)

        except Exception as e:
            # Re-raise with more context
            if isinstance(e, StateError):
                raise e
            else:
                raise create_runtime_error(f"Error evaluating expression: {e}", node)

    def evaluate_literal_expression(self, node: LiteralExpression, context: Optional[Dict[str, Any]] = None) -> Any:
        """Evaluate a literal expression.

        Args:
            node: The literal expression to evaluate
            context: Optional local context (unused)

        Returns:
            The literal value
        """
        if isinstance(node.literal.value, FStringExpression):
            return self.evaluate_fstring_expression(node.literal.value, context)
        return node.literal.value

    def evaluate_identifier(self, node: Identifier, context: Optional[Dict[str, Any]] = None) -> Any:
        """Evaluate an identifier.

        Args:
            node: The identifier to evaluate
            context: Optional local context for variable resolution

        Returns:
            The value of the identifier

        Raises:
            StateError: If the identifier is not defined
        """
        try:
            self.debug(f"Evaluating identifier: {node.name}")

            # Direct dictionary access for scoped variables
            if "." in node.name:
                parts = node.name.split(".", 1)
                scope, var_name = parts

                # Most reliable direct state dictionary access
                if scope in ["private", "public", "system"] and scope in self.context_manager.context._state:
                    state_dict = self.context_manager.context._state[scope]
                    if var_name in state_dict:
                        value = state_dict[var_name]
                        self.debug(f"Direct state access for '{node.name}' = {value}")
                        return value

            # Standard variable lookup
            try:
                value = self.context_manager.get_variable(node.name, context)
                self.debug(f"Standard lookup for '{node.name}' = {value}")
                return value
            except Exception as e:
                self.debug(f"Error in get_variable for '{node.name}': {e}")
                raise

        except StateError:
            # Standard error for undefined variables
            if "." in node.name:
                error_msg = f"Variable '{node.name}' not found"
            else:
                error_msg = (
                    f"Variable '{node.name}' must be accessed with a scope prefix: "
                    f"private.{node.name}, public.{node.name}, or system.{node.name}"
                )
            self.debug(f"Variable not found: {node.name}")
            raise create_state_error(error_msg, node)

    def evaluate_literal(self, node: Literal, context: Optional[Dict[str, Any]] = None) -> Any:
        """Evaluate a literal.

        Args:
            node: The literal to evaluate
            context: Optional local context (unused)

        Returns:
            The literal value
        """
        if isinstance(node.value, FStringExpression):
            return self.evaluate_fstring_expression(node.value, context)
        return node.value

    def evaluate_fstring_expression(self, node: FStringExpression, context: Optional[Dict[str, Any]] = None) -> str:
        """Evaluate an f-string expression.

        Args:
            node: The f-string expression to evaluate
            context: Optional local context for variable resolution

        Returns:
            The evaluated string with substitutions
        """
        # Special handling for placeholder f-strings
        if len(node.parts) == 1 and isinstance(node.parts[0], str) and node.parts[0].startswith("F-STRING-PLACEHOLDER:"):
            content = node.parts[0].replace("F-STRING-PLACEHOLDER:", "")
            return self._evaluate_placeholder_fstring(content, context)

        # Standard evaluation for normal AST f-strings
        result = ""
        for part in node.parts:
            if isinstance(part, str):
                result += part
            else:
                value = self.evaluate(part, context)
                result += str(value)
        return result

    def _evaluate_placeholder_fstring(self, content: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Evaluate a placeholder f-string.

        This handles f-strings that were parsed as placeholders rather than AST nodes.

        Args:
            content: The content of the f-string
            context: Optional local context for variable resolution

        Returns:
            The evaluated string with substitutions
        """
        # Find all variable references in the form {scope.name} or {name}
        var_pattern = r"\{([^{}]+)\}"
        var_matches = re.findall(var_pattern, content)

        # Replace each variable reference with its value
        result = content
        for var_ref in var_matches:
            try:
                # Try to evaluate the variable
                value = self.context_manager.get_variable(var_ref, context)
                # Replace the variable reference with its value
                result = result.replace(f"{{{var_ref}}}", str(value))
            except StateError:
                # If the variable doesn't exist, leave the reference as is
                self.warning(f"Variable '{var_ref}' not found in f-string")

        return result
