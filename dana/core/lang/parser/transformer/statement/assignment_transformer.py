"""
Assignment transformer for Dana language parsing.

This module handles all assignment-related transformations, including:
- Simple assignments (variable = expression)
- Typed assignments (variable: type = expression)
- Function call assignments (variable = use(...))
- Type hint processing

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any, cast

from dana.core.lang.ast import (
    AgentPoolStatement,
    AgentStatement,
    Assignment,
    Identifier,
    UseStatement,
)
from dana.core.lang.parser.transformer.base_transformer import BaseTransformer
from dana.core.lang.parser.transformer.statement.statement_helpers import AssignmentHelper
from dana.core.lang.parser.transformer.variable_transformer import VariableTransformer

# Allowed types for Assignment.value
AllowedAssignmentValue = Any  # Using Any for now to avoid circular imports - will be properly typed later


class AssignmentTransformer(BaseTransformer):
    """
    Handles assignment statement transformations for the Dana language.
    Converts assignment parse trees into Assignment AST nodes with proper type hints and validation.
    """

    def __init__(self, main_transformer):
        """Initialize with reference to main transformer for shared utilities."""
        super().__init__()
        self.main_transformer = main_transformer
        self.expression_transformer = main_transformer.expression_transformer

    # === Assignment Statement Methods ===

    def assignment(self, items):
        """
        Transform an assignment rule into an Assignment node.
        Grammar: assignment: typed_assignment | simple_assignment

        This rule is just a choice, so return the result of whichever was chosen.
        """
        return items[0]

    def typed_assignment(self, items):
        """Transform a typed assignment rule into an Assignment node with type hint."""
        # Grammar: typed_assignment: variable ":" basic_type "=" expr
        target_tree = items[0]
        type_hint = items[1]  # Should be a TypeHint from basic_type
        value_tree = items[2]

        return AssignmentHelper.create_assignment(target_tree, value_tree, self.expression_transformer, VariableTransformer(), type_hint)

    def simple_assignment(self, items):
        """Transform a simple assignment rule into an Assignment node without type hint."""
        # Grammar: simple_assignment: variable "=" expr
        target_tree = items[0]
        value_tree = items[1]

        return AssignmentHelper.create_assignment(target_tree, value_tree, self.expression_transformer, VariableTransformer())

    def function_call_assignment(self, items):
        """Transform a function_call_assignment rule into an Assignment node with object-returning statement."""
        # Grammar: function_call_assignment: target "=" return_object_stmt
        target_tree = items[0]
        return_object_tree = items[1]

        # Get target identifier
        target = VariableTransformer().variable([target_tree])
        if not isinstance(target, Identifier):
            raise TypeError(f"Assignment target must be Identifier, got {type(target)}")

        # Transform the return_object_stmt (which should be UseStatement, AgentStatement, or AgentPoolStatement)
        # The return_object_tree should already be transformed by return_object_stmt method
        if isinstance(return_object_tree, UseStatement | AgentStatement | AgentPoolStatement):
            if hasattr(return_object_tree, "target") and return_object_tree.target is None:
                # If the target is not set, set it to the target of the assignment
                return_object_tree.target = target
            value_expr = cast(AllowedAssignmentValue, return_object_tree)
        else:
            # Fallback transformation if needed
            value_expr = cast(AllowedAssignmentValue, return_object_tree)

        return Assignment(target=target, value=value_expr)

    def return_object_stmt(self, items):
        """Transform a return_object_stmt rule into the appropriate object-returning statement."""
        # Grammar: return_object_stmt: use_stmt | agent_stmt | agent_pool_stmt
        # items[0] should be the result of the chosen statement transformation

        # The statement should already be transformed into the appropriate AST node
        if len(items) > 0 and items[0] is not None:
            return items[0]

        # Fallback - this shouldn't happen in normal cases
        raise ValueError("return_object_stmt received empty or None items")

    # === Type Hint Processing ===

    def basic_type(self, items):
        """Transform a basic_type rule into a TypeHint node."""
        return AssignmentHelper.create_type_hint(items)

    def typed_parameter(self, items):
        """Transform a typed parameter rule into a Parameter object."""
        from dana.core.lang.ast import Parameter

        # Grammar: typed_parameter: NAME [":" basic_type] ["=" expr]
        name_item = items[0]
        param_name = name_item.value if hasattr(name_item, "value") else str(name_item)

        type_hint = None
        default_value = None

        # Check for type hint and default value
        for item in items[1:]:
            if hasattr(item, "name"):  # TypeHint object
                type_hint = item
            else:
                # Assume it's a default value expression
                default_value = self.expression_transformer.expression([item])
                if isinstance(default_value, tuple):
                    raise TypeError(f"Parameter default value cannot be a tuple: {default_value}")

        return Parameter(name=param_name, type_hint=type_hint, default_value=default_value)
