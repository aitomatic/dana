"""
Copyright © 2025 Aitomatic, Inc.

This source code is licensed under the license found in the LICENSE file in the root directory of this source tree

Expression evaluator for the DANA interpreter.

This module provides the ExpressionEvaluator class, which is responsible for
evaluating expressions in DANA programs.
"""

import re
from typing import Any, Dict, Optional

from opendxa.dana.common.error_utils import ErrorUtils
from opendxa.dana.common.exceptions import SandboxError, StateError
from opendxa.dana.sandbox.interpreter.executor.base_executor import BaseExecutor
from opendxa.dana.sandbox.interpreter.executor.context_manager import ContextManager
from opendxa.dana.sandbox.interpreter.functions.python_function import PythonRegistry
from opendxa.dana.sandbox.parser.ast import (
    BinaryExpression,
    BinaryOperator,
    FStringExpression,
    FunctionCall,
    Identifier,
    LiteralExpression,
    UnaryExpression,
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
        self.debug(f"[EVAL] Node type: {type(node)}, value: {getattr(node, 'value', None)}")
        try:
            if isinstance(node, BinaryExpression):
                return self.evaluate_binary_expression(node, context)
            elif isinstance(node, UnaryExpression):
                return self.evaluate_unary_expression(node, context)
            elif isinstance(node, LiteralExpression):
                return self.evaluate_literal_expression(node, context)
            elif isinstance(node, Identifier):
                return self.evaluate_identifier(node, context)
            elif isinstance(node, FStringExpression):
                return self.evaluate_fstring_expression(node, context)
            elif isinstance(node, FunctionCall):
                return self.evaluate_function_call(node, context)
            elif hasattr(node, "__class__") and node.__class__.__name__ == "AttributeAccess":
                return self.evaluate_attribute_access(node, context)
            elif hasattr(node, "__class__") and node.__class__.__name__ == "SubscriptExpression":
                return self.evaluate_subscript_expression(node, context)
            elif hasattr(node, "__class__") and node.__class__.__name__ == "DictLiteral":
                return self.evaluate_dict_literal(node, context)
            elif hasattr(node, "__class__") and node.__class__.__name__ == "TupleLiteral":
                return self.evaluate_tuple_literal(node, context)
            elif hasattr(node, "__class__") and node.__class__.__name__ == "SetLiteral":
                return self.evaluate_set_literal(node, context)
            else:
                error_msg = f"Unsupported expression type: {type(node).__name__}"
                raise SandboxError(error_msg)
        except Exception as e:
            error, passthrough = ErrorUtils.handle_execution_error(e, node, "evaluating expression")
            if passthrough:
                raise error
            else:
                raise SandboxError(f"Failed to evaluate expression: {e}")

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
        self.debug(f"[EVAL_BIN_START] node: {node}, operator: {node.operator}")
        self.debug(
            f"[EVAL_BIN] operator={node.operator}, left={getattr(node.left, 'value', node.left)}, right={getattr(node.right, 'value', node.right)}"
        )
        try:
            # Evaluate left operand
            if isinstance(node.left, Identifier):
                try:
                    left = self.context_manager.get_from_context(node.left.name, context)
                    self.debug(f"Evaluated {node.left.name} = {left}")
                except Exception as e:
                    self.debug(f"Error evaluating left operand: {e}")
                    if "." in node.left.name:
                        raise ErrorUtils.create_state_error(f"Variable '{node.left.name}' not found", node)
                    else:
                        raise ErrorUtils.create_state_error(
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
                    right = self.context_manager.get_from_context(node.right.name, context)
                    self.debug(f"Evaluated {node.right.name} = {right}")
                except Exception as e:
                    self.debug(f"Error evaluating right operand: {e}")
                    if "." in node.right.name:
                        raise ErrorUtils.create_state_error(f"Variable '{node.right.name}' not found", node)
                    else:
                        raise ErrorUtils.create_state_error(
                            f"Variable '{node.right.name}' must be accessed with a scope prefix: "
                            f"private.{node.right.name}, public.{node.right.name}, or system.{node.right.name}",
                            node,
                        )
            else:
                right = self.evaluate(node.right, context)
                self.debug(f"Evaluated right operand: {right}")

            # Process the operation based on operator type
            try:
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
                    self.debug(f"[EVAL_BIN] About to check division: left={left}, right={right}")
                    self.debug(f"[EVAL_BIN] DIVIDE branch: left={left}, right={right}")
                    if right == 0:
                        self.debug("[EVAL_BIN] Division by zero detected, raising error.")
                        raise ErrorUtils.create_state_error("Math Error: Division by zero is not allowed.", node)
                    return left / right
                elif node.operator == BinaryOperator.MODULO:
                    if right == 0:
                        raise ErrorUtils.create_state_error("Math Error: Division by zero is not allowed.", node)
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
                elif node.operator == BinaryOperator.POWER:
                    # DANA '^' means exponentiation, not bitwise XOR
                    return left**right
                else:
                    # Unsupported operator
                    raise ErrorUtils.create_state_error(f"Unsupported binary operator: {node.operator.value}", node)
            except Exception as e:
                self.debug(f"Error in binary operation: {e}")
                self.debug(f"Left operand type: {type(left)}, value: {left}")
                self.debug(f"Right operand type: {type(right)}, value: {right}")
                self.debug(f"Operator: {node.operator}")
                raise

        except Exception as e:
            # Re-raise with more context
            if isinstance(e, StateError):
                raise e
            else:
                raise ErrorUtils.create_runtime_error(f"Error evaluating expression: {e}", node)

    def evaluate_unary_expression(self, node, context=None):
        """Evaluate a unary expression (e.g., -x, +x, not x)."""
        operand = self.evaluate(node.operand, context)
        if node.operator == "-":
            return -operand
        elif node.operator == "+":
            return +operand
        elif node.operator == "not":
            return not operand
        else:
            raise SandboxError(f"Unsupported unary operator: {node.operator}")

    def evaluate_literal_expression(self, node: LiteralExpression, context: Optional[Dict[str, Any]] = None) -> Any:
        """Evaluate a literal expression.

        Args:
            node: The literal expression to evaluate
            context: Optional local context (unused)

        Returns:
            The literal value
        """
        if isinstance(node.value, FStringExpression):
            return self.evaluate_fstring_expression(node.value, context)
        return node.value

    def evaluate_identifier(self, node: Identifier, context: Optional[Dict[str, Any]] = None) -> Any:
        """Evaluate an identifier.

        Args:
            node: The identifier to evaluate
            context: Optional local context for variable resolution

        Returns:
            The value of the identifier

        Raises:
            StateError: If the identifier is not found
        """
        try:
            # Get the value from the context manager
            return self.context_manager.get_from_context(node.name, context)
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
            raise ErrorUtils.create_state_error(error_msg, node)

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
                value = self.context_manager.get_from_context(var_ref, context)
                # Replace the variable reference with its value
                result = result.replace(f"{{{var_ref}}}", str(value))
            except StateError:
                # If the variable doesn't exist, leave the reference as is
                self.warning(f"Variable '{var_ref}' not found in f-string")

        return result

    def evaluate_function_call(self, node: FunctionCall, context: Optional[Dict[str, Any]] = None) -> Any:
        """Evaluate a function call expression."""
        # Evaluate arguments
        evaluated_args = {k: self.evaluate(v, context) for k, v in node.args.items()}
        # Call the function from the registry
        return PythonRegistry.call(node.name, evaluated_args)

    def evaluate_attribute_access(self, node, context=None):
        obj = self.evaluate(node.object, context)
        attr = node.attribute
        # Support dict and object attribute access
        if isinstance(obj, dict):
            return obj.get(attr)
        return getattr(obj, attr, None)

    def evaluate_subscript_expression(self, node, context=None):
        obj = self.evaluate(node.object, context)
        idx = self.evaluate(node.index, context)
        return obj[idx]

    def evaluate_dict_literal(self, node, context=None):
        # Evaluate all key-value pairs in the dict literal
        return {self.evaluate(k, context): self.evaluate(v, context) for k, v in node.items}

    def evaluate_tuple_literal(self, node, context=None):
        # Evaluate all items in the tuple literal
        return tuple(self.evaluate(item, context) for item in node.items)

    def evaluate_set_literal(self, node, context=None):
        # Evaluate all items in the set literal
        return set(self.evaluate(item, context) for item in node.items)
