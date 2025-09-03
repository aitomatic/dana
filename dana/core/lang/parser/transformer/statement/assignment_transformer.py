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

from typing import Any

from dana.core.lang.ast import (
    CompoundAssignment,
    Identifier,
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
        Transform a unified assignment rule into an Assignment node.
        Grammar: assignment: target [":" basic_type] "=" expr [COMMENT] | compound_assignment
        """
        # The unified assignment rule can be either a regular assignment or a compound assignment
        # We need to determine which one based on the structure of the items

        # If we have only 1 item and it's already a CompoundAssignment, return it directly
        if len(items) == 1 and hasattr(items[0], "__class__") and items[0].__class__.__name__ == "CompoundAssignment":
            return items[0]

        # Check for compound assignment (3 items: target, operator, value)
        if (
            len(items) == 3
            and hasattr(items[1], "value")
            and items[1].value in ["+=", "-=", "*=", "/=", "%=", "//=", "**=", "&=", "|=", "^=", "<<=", ">>="]
        ):
            return self.compound_assignment(items)

        # Check for typed assignment: target, type_hint, value, [comment]
        # Look for TypeHint in the items - could be at index 1 (4 items) or index 2 (with different grammar structure)
        type_hint_index = None
        for i, item in enumerate(items):
            if item is not None and hasattr(item, "__class__") and item.__class__.__name__ == "TypeHint":
                type_hint_index = i
                break

        if type_hint_index is not None:
            # Found a type hint, this is a typed assignment
            target_tree = items[0]
            type_hint = items[type_hint_index]
            # Find the value - should be after the type hint
            value_tree = None
            for i in range(type_hint_index + 1, len(items)):
                if items[i] is not None and not (hasattr(items[i], "type") and items[i].type == "COMMENT"):
                    value_tree = items[i]
                    break
            return AssignmentHelper.create_assignment(
                target_tree, value_tree, self.expression_transformer, VariableTransformer(), type_hint
            )

        # Regular assignment without type hint: target "=" expr
        if len(items) >= 2:
            target_tree = items[0]
            # Find the value - it could be at index 1 (no type hint) or index 2 (with type hint that's None)
            value_tree = None
            for i in range(1, len(items)):
                if items[i] is not None and not (hasattr(items[i], "type") and items[i].type == "COMMENT"):
                    value_tree = items[i]
                    break

            return AssignmentHelper.create_assignment(target_tree, value_tree, self.expression_transformer, VariableTransformer(), None)

        # Fallback for unexpected structure
        raise ValueError(f"Unexpected assignment structure with {len(items)} items: {items}")

    def compound_assignment(self, items):
        """Transform a compound assignment rule into a CompoundAssignment node."""
        # Grammar: compound_assignment: target compound_op expr
        target_tree = items[0]
        operator_token = items[1]  # This will be the token from compound_op
        value_tree = items[2]

        # Transform the target using the same logic as simple assignment
        from lark import Tree

        # Handle different types of assignment targets
        if isinstance(target_tree, Tree) and hasattr(target_tree, "data"):
            # Check if this is a complex target (atom with trailers)
            if target_tree.data == "target":
                # target -> atom
                atom_tree = target_tree.children[0]
                if isinstance(atom_tree, Tree) and atom_tree.data == "atom":
                    # Check if atom has trailers (indicating subscript or attribute access)
                    if len(atom_tree.children) > 1:
                        # Complex target: use expression transformer to handle subscript/attribute access
                        target = self.expression_transformer.expression([target_tree])
                    else:
                        # Simple target: use variable transformer
                        target = VariableTransformer().variable([target_tree])
                else:
                    # Fallback to variable transformer
                    target = VariableTransformer().variable([target_tree])
            else:
                # Not a target rule, try expression transformer first
                try:
                    target = self.expression_transformer.expression([target_tree])
                except Exception:
                    # Fallback to variable transformer
                    target = VariableTransformer().variable([target_tree])
        else:
            # Simple case: use variable transformer
            target = VariableTransformer().variable([target_tree])

        # Validate target type
        from dana.core.lang.ast import AttributeAccess, SubscriptExpression

        if not isinstance(target, Identifier | SubscriptExpression | AttributeAccess):
            raise TypeError(f"Compound assignment target must be Identifier, SubscriptExpression, or AttributeAccess, got {type(target)}")

        # Transform the value expression
        value = self.expression_transformer.expression([value_tree])

        # Get the operator string
        operator_str = str(operator_token)

        return CompoundAssignment(target=target, operator=operator_str, value=value)

    def compound_op(self, items):
        """Return the compound operator token."""
        # Grammar: compound_op: PLUS_EQUALS | MINUS_EQUALS | MULT_EQUALS | DIV_EQUALS
        return items[0].value  # Return the string value of the token

    def declarative_function_assignment(self, items):
        """Transform a declarative function assignment rule into a DeclarativeFunctionDefinition node."""
        # Grammar: declarative_function_assignment: "def" NAME "(" [parameters] ")" ["->" basic_type] "=" function_composition_expr
        from dana.core.lang.ast import DeclarativeFunctionDefinition

        # Extract components from the parse tree
        name_token = items[0]  # NAME token
        parameters = items[1] if len(items) > 1 and items[1] is not None else []
        return_type = items[2] if len(items) > 2 and items[2] is not None else None
        composition = items[-1]  # The function composition expression after "="

        # Create the function name identifier
        name = Identifier(name_token.value)

        # Transform parameters if they exist
        if parameters and isinstance(parameters, list | tuple):
            params = []
            for param in parameters:
                if hasattr(param, "name") and hasattr(param, "type_hint"):
                    # Already a Parameter object
                    params.append(param)
                else:
                    # Transform from parse tree
                    params.append(self._transform_parameter(param))
            parameters = params
        else:
            parameters = []

        # Transform return type if it exists
        if return_type and hasattr(return_type, "name"):
            # Already a TypeHint object
            pass
        elif return_type:
            # Transform from parse tree
            return_type = self._transform_type_hint(return_type)

        # Transform the function composition expression
        composition = self._transform_function_composition(composition)

        # Reset the declarative function context after processing
        if hasattr(self, "expression_transformer") and self.expression_transformer is not None:
            self.expression_transformer.set_declarative_function_context(False)

        # Create the DeclarativeFunctionDefinition node
        return DeclarativeFunctionDefinition(
            name=name,
            parameters=parameters,
            composition=composition,
            return_type=return_type,
            docstring=None,  # Will be extracted later if needed
            location=self.create_location(name_token),
        )

    def _transform_function_composition(self, composition_tree):
        """Transform a function composition expression tree into an Expression."""
        # The composition_tree should be one of the function composition expression types
        # We can use the existing expression transformer since function composition expressions
        # are valid expressions, but we need to validate that they're actually function compositions

        # Transform using the expression transformer
        # Note: Grammar now restricts to function composition expressions only
        if not hasattr(self, "expression_transformer") or self.expression_transformer is None:
            raise AttributeError("The 'expression_transformer' attribute is not initialized.")

        # Set declarative function context to allow pipe expressions and placeholders
        self.expression_transformer.set_declarative_function_context(True)

        composition = self.expression_transformer.expression([composition_tree])

        # Don't reset the context here - let the caller handle it
        # The context needs to be maintained during the entire transformation
        return composition

    def _transform_parameter(self, param_tree):
        """Transform a parameter parse tree into a Parameter object."""
        from dana.core.lang.ast import Parameter

        if isinstance(param_tree, str):
            return Parameter(param_tree)
        elif hasattr(param_tree, "name"):
            # Already a Parameter object
            return param_tree
        else:
            # Parse tree - extract name and type hint
            name = param_tree.children[0].value if param_tree.children else "param"
            type_hint = None
            if len(param_tree.children) > 1:
                type_hint = self._transform_type_hint(param_tree.children[1])
            return Parameter(name, type_hint)

    def _transform_type_hint(self, type_tree):
        """Transform a type hint parse tree into a TypeHint object."""
        from dana.core.lang.ast import TypeHint

        if isinstance(type_tree, str):
            return TypeHint(type_tree)
        elif hasattr(type_tree, "name"):
            # Already a TypeHint object
            return type_tree
        else:
            # Parse tree - extract type name
            type_name = type_tree.children[0].value if type_tree.children else "any"
            return TypeHint(type_name)

    def return_object_stmt(self, items):
        """Transform a return_object_stmt rule into the appropriate object-returning statement."""
        # Grammar: return_object_stmt: use_stmt | agent_stmt
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

        # Grammar: typed_parameter: NAME [":" basic_type] ["=" expr] [COMMENT]
        name_item = items[0]
        param_name = name_item.value if hasattr(name_item, "value") else str(name_item)

        type_hint = None
        default_value = None

        # Check for type hint and default value, filtering out comment tokens and None values
        for item in items[1:]:
            # Skip comment tokens and None values (from optional COMMENT rules)
            if item is None:
                continue
            elif hasattr(item, "type") and item.type == "COMMENT":
                continue
            elif hasattr(item, "name"):  # Already transformed TypeHint object
                type_hint = item
            elif hasattr(item, "data") and item.data == "basic_type":
                # Raw basic_type tree that needs transformation
                type_hint = self.basic_type(item.children)
            else:
                # Assume it's a default value expression
                default_value = self.expression_transformer.expression([item])
                if isinstance(default_value, tuple):
                    raise TypeError(f"Parameter default value cannot be a tuple: {default_value}")

        return Parameter(name=param_name, type_hint=type_hint, default_value=default_value)
