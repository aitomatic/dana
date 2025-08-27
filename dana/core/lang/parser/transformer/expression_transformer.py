"""
Expression transformer for the Dana language.

This module handles the transformation of parsed expressions into the appropriate
AST nodes for the Dana language interpreter.

Methods are organized by function:
- Binary and Unary Operations (or_expr, and_expr, comparison, etc.)
- Collection Literals (list, dict, set, tuple)
- Comprehensions (list_comprehension, dict_comprehension, etc.)
- Literal Values (literal, string_literal, etc.)
- Function Calls and Attribute Access
- Utility and Helper Methods

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any, cast

from lark import Token, Tree

from dana.core.lang.ast import (
    AttributeAccess,
    BinaryExpression,
    BinaryOperator,
    ConditionalExpression,
    DictComprehension,
    DictLiteral,
    Expression,
    FStringExpression,
    FunctionCall,
    Identifier,
    LambdaExpression,
    ListComprehension,
    ListLiteral,
    LiteralExpression,
    ObjectFunctionCall,
    PipelineExpression,
    PlaceholderExpression,
    SetComprehension,
    SetLiteral,
    SliceExpression,
    SubscriptExpression,
    TupleLiteral,
    UnaryExpression,
)
from dana.core.lang.parser.transformer.base_transformer import BaseTransformer
from dana.core.lang.parser.transformer.expression.expression_helpers import (
    OperatorHelper,
)

ValidExprType = LiteralExpression | Identifier | BinaryExpression | FunctionCall


class ExpressionTransformer(BaseTransformer):
    """Transform expression parse trees into AST Expression nodes."""

    def __init__(self, main_transformer=None):
        """Initialize the ExpressionTransformer.

        Args:
            main_transformer: Optional main transformer instance for coordination.
                            Can be None for standalone usage.
        """
        super().__init__()
        self.main_transformer = main_transformer
        self._in_declarative_function = False

    def set_declarative_function_context(self, in_declarative_function: bool):
        """Set whether we're currently in a declarative function context."""
        self._in_declarative_function = in_declarative_function

    def _filter_comments(self, items):
        """Filter out COMMENT tokens from a list of items."""
        filtered = []
        for item in items:
            # Skip COMMENT tokens - they should not appear in final collections
            if isinstance(item, Token) and item.type == "COMMENT":
                continue
            filtered.append(item)
        return filtered

    def expression(self, items):
        if not items:
            return None

        # Use TreeTraverser to unwrap single-child trees
        item = self.tree_traverser.unwrap_single_child_tree(items[0])

        # If it's a Tree, dispatch by rule name
        if isinstance(item, Tree):
            # For simple transformations, use a custom transformer
            # that handles the most common expression patterns
            rule_name = getattr(item, "data", None)
            if isinstance(rule_name, str):
                if rule_name in {
                    "key_value_pair",
                    "tuple",
                    "dict",
                    "list",
                    "true_lit",
                    "false_lit",
                    "none_lit",
                    "literal",
                    "sum_expr",
                    "product",
                    "term",
                    "comparison",
                    "and_expr",
                    "or_expr",
                    "conditional_expr",
                }:
                    # These rules have specialized transformers, dispatch directly
                    method = getattr(self, rule_name, None)
                    if method:
                        return method(item.children)

            # Fallback: General traverser with specialized transforms
            def custom_transformer(node: Any) -> Any:
                """Transform a tree node using the appropriate method."""
                if isinstance(node, Tree):
                    rule = getattr(node, "data", None)
                    if isinstance(rule, str):
                        transformer_method = getattr(self, rule, None)
                        if callable(transformer_method):
                            return transformer_method(node.children)
                return node

            # If there's no specific handler, try the tree traverser for recursion
            transformed = self.tree_traverser.transform_tree(item, custom_transformer)

            # If transformation succeeded, return the result
            if transformed is not item:
                return transformed

            # Fallback: recursively call expression on all children and return the last non-None result
            last_result = None
            for child in item.children:
                result = self.expression([child])
                if result is not None:
                    last_result = result
            if last_result is not None:
                return last_result
            raise TypeError(f"Unhandled tree in expression: {item.data} with children {item.children}")

        # If it's already an AST node, return as is
        if isinstance(
            item,
            LiteralExpression
            | Identifier
            | BinaryExpression
            | ConditionalExpression
            | FunctionCall
            | ObjectFunctionCall
            | TupleLiteral
            | DictLiteral
            | ListLiteral
            | SetLiteral
            | SubscriptExpression
            | AttributeAccess
            | FStringExpression
            | UnaryExpression
            | PlaceholderExpression
            | PipelineExpression
            | LambdaExpression
            | ListComprehension
            | SetComprehension
            | DictComprehension,
        ):
            return item
        # If it's a primitive or FStringExpression, wrap as LiteralExpression
        if isinstance(item, int | float | str | bool | type(None) | FStringExpression):
            return LiteralExpression(value=item)
        # If it's a Token, unwrap to primitive for LiteralExpression
        if isinstance(item, Token):
            if item.type == "NAME":
                return Identifier(name=item.value)
            # Use the tree traverser's unwrap_token for consistent token handling
            value = self.tree_traverser.unwrap_token(item)
            return LiteralExpression(value=value)

        # Handle NamedPipelineStage objects (already transformed)
        if hasattr(item, "__class__") and item.__class__.__name__ == "NamedPipelineStage":
            return item

        raise TypeError(f"Cannot transform expression: {item} ({type(item)})")

    def _extract_operator_string(self, op_token):
        """Extract operator string from a token or tree."""
        return OperatorHelper.extract_operator_string(op_token)

    def _op_tree_to_str(self, tree):
        # For ADD_OP and MUL_OP, the child is the actual operator token
        from lark import Token, Tree

        if isinstance(tree, Token):
            return tree.value
        if isinstance(tree, Tree):
            if tree.children and isinstance(tree.children[0], Token):
                return tree.children[0].value
        raise ValueError(f"Cannot extract operator string from: {tree}")

    def _left_associative_binop(self, items, operator_getter):
        """
        Helper for left-associative binary operations (e.g., a + b + c).
        Iterates over items, applying the operator from operator_getter to each pair.
        Used by or_expr, and_expr, comparison, sum_expr, and term.
        """
        return OperatorHelper.left_associative_binop(items, operator_getter)

    def _get_binary_operator(self, op_str):
        """
        Maps an operator string or token to the corresponding BinaryOperator enum value.
        Used by comparison, sum_expr, term, and factor.
        """
        op_map = {
            "+": BinaryOperator.ADD,
            "-": BinaryOperator.SUBTRACT,
            "*": BinaryOperator.MULTIPLY,
            "/": BinaryOperator.DIVIDE,
            "//": BinaryOperator.FLOOR_DIVIDE,
            "%": BinaryOperator.MODULO,
            "==": BinaryOperator.EQUALS,
            "!=": BinaryOperator.NOT_EQUALS,
            "<": BinaryOperator.LESS_THAN,
            ">": BinaryOperator.GREATER_THAN,
            "<=": BinaryOperator.LESS_EQUALS,
            ">=": BinaryOperator.GREATER_EQUALS,
            "and": BinaryOperator.AND,
            "or": BinaryOperator.OR,
            "in": BinaryOperator.IN,
            "not in": BinaryOperator.NOT_IN,
            "is": BinaryOperator.IS,
            "is not": BinaryOperator.IS_NOT,
            "^": BinaryOperator.POWER,
            "|": BinaryOperator.PIPE,
        }
        return op_map[op_str]

    # ================================================================
    # BINARY AND UNARY OPERATIONS
    # ================================================================

    def or_expr(self, items):
        # If items contains only operands, insert 'or' between each pair
        if all(not (isinstance(item, Tree) and hasattr(item, "data") and item.data.endswith("_op")) for item in items) and len(items) > 1:
            new_items = []
            for i, item in enumerate(items):
                new_items.append(item)
                if i < len(items) - 1:
                    new_items.append("or")
            items = new_items
        return self._left_associative_binop(items, lambda op: BinaryOperator.OR)

    def and_expr(self, items):
        # If items contains only operands, insert 'and' between each pair
        if all(not (isinstance(item, Tree) and hasattr(item, "data") and item.data.endswith("_op")) for item in items) and len(items) > 1:
            new_items = []
            for i, item in enumerate(items):
                new_items.append(item)
                if i < len(items) - 1:
                    new_items.append("and")
            items = new_items
        return self._left_associative_binop(items, lambda op: BinaryOperator.AND)

    def conditional_expr(self, items):
        """Transform conditional expression (ternary operator) into ConditionalExpression AST node."""
        from dana.core.lang.ast import ConditionalExpression

        if len(items) == 1:
            # No conditional, just return the or_expr
            return self.expression([items[0]])
        elif len(items) == 3 and items[1] is None and items[2] is None:
            # No conditional (optional parts are None), just return the or_expr
            return self.expression([items[0]])
        elif len(items) == 3 and items[1] is not None and items[2] is not None:
            # Conditional: value, condition, alternative (tokens filtered out)
            true_branch = self.expression([items[0]])
            condition = self.expression([items[1]])
            false_branch = self.expression([items[2]])

            location = getattr(true_branch, "location", None) or getattr(condition, "location", None)

            return ConditionalExpression(condition=condition, true_branch=true_branch, false_branch=false_branch, location=location)
        elif len(items) == 5:
            # Full conditional: value "if" condition "else" alternative
            true_branch = self.expression([items[0]])
            condition = self.expression([items[2]])
            false_branch = self.expression([items[4]])

            location = getattr(true_branch, "location", None) or getattr(condition, "location", None)

            return ConditionalExpression(condition=condition, true_branch=true_branch, false_branch=false_branch, location=location)
        else:
            raise ValueError(f"Unexpected number of items in conditional_expr: {len(items)} - {[type(item).__name__ for item in items]}")

    def placeholder_expression(self, items):
        """Transform placeholder expression into PlaceholderExpression AST node."""
        return PlaceholderExpression()

    def pipe_expr(self, items):
        """Transform pipe expressions into PipelineExpression AST node.

        pipe_expr: or_expr (PIPE or_expr)*

        This method collects all expressions separated by PIPE tokens and creates
        a PipelineExpression with the stages list. Only creates PipelineExpression
        if there are actual PIPE tokens (at least one | operator).

        Rejects pipe expressions in non-declarative function contexts.
        Only allows pipe expressions in declarative function definitions.
        """
        stages = []
        has_pipe = False

        # Check if we have any PIPE tokens
        for item in items:
            if isinstance(item, Token) and item.type == "PIPE":
                has_pipe = True
                break
            elif str(item) == "|":
                has_pipe = True
                break

        # Filter out PIPE tokens and collect only the expressions
        for item in items:
            if isinstance(item, Token) and item.type == "PIPE":
                continue
            elif str(item) == "|":
                continue
            else:
                # This is an expression, process it
                expr = self.expression([item])
                stages.append(expr)

        # If no PIPE tokens, return the single expression directly
        if not has_pipe and len(stages) == 1:
            return stages[0]

        # Enforce declarative function context restriction
        if not self._is_in_declarative_function_context():
            raise SyntaxError(
                "Pipe expressions (|) are only allowed in declarative function definitions. "
                "Use 'def function_name() = expr1 | expr2' syntax instead of assignment."
            )

        # Otherwise, create PipelineExpression
        return PipelineExpression(stages=stages)

    def _is_in_declarative_function_context(self):
        """Check if we're currently parsing a declarative function definition."""
        return self._in_declarative_function

    def _is_literal_expression(self, expr):
        """Check if an expression is a literal value that should be rejected in pipe contexts."""
        from dana.core.lang.ast import LiteralExpression

        # Direct literal expressions
        if isinstance(expr, LiteralExpression):
            return True

        # Check for common literal patterns
        if hasattr(expr, "value"):
            # String literals, numbers, booleans, etc.
            if isinstance(expr.value, str | int | float | bool | type(None)):
                return True

        # Check for string literals with specific attributes
        if hasattr(expr, "type") and expr.type in ["REGULAR_STRING", "SINGLE_QUOTED_STRING", "F_STRING_TOKEN"]:
            return True

        return False

    def not_expr(self, items):
        """
        Transform a not_expr rule into an AST UnaryExpression with 'not' operator.
        Grammar: not_expr: "not" not_expr | comparison

        For "not [expr]" form, creates a UnaryExpression.
        For regular comparison case, passes through.
        """
        from lark import Token

        if len(items) == 1:
            return self.expression([items[0]])

        # "not" operator at the beginning - match it as a string or token
        is_not_op = False

        # Check various forms of 'not' in the parse tree
        if isinstance(items[0], str) and items[0] == "not":
            is_not_op = True
        elif isinstance(items[0], Token) and items[0].value == "not":
            is_not_op = True
        elif hasattr(items[0], "type") and getattr(items[0], "type", None) == "NOT_OP":
            is_not_op = True

        if is_not_op:
            # Use a UnaryExpression node for 'not'
            operand = None
            if len(items) > 1:
                operand = self.expression([items[1]])
            else:
                # Fallback for unexpected structure
                operand = LiteralExpression(value=None)

            # Explicitly cast to Expression
            from dana.core.lang.ast import Expression

            operand_expr = cast(Expression, operand)
            return UnaryExpression(operator="not", operand=operand_expr)

        # Fallback for unexpected case
        return self.expression([items[0]])

    def comparison(self, items):
        return self._left_associative_binop(items, self._get_binary_operator)

    def sum_expr(self, items):
        result = self._left_associative_binop(items, self._get_binary_operator)
        return result

    def term(self, items):
        result = self._left_associative_binop(items, self._get_binary_operator)
        return result

    def factor(self, items):
        """
        Transform a factor rule into an AST expression.

        Grammar: factor: (ADD | SUB) factor | atom trailer*
        """
        # Single item case - just pass through
        if len(items) == 1:
            return self.expression([items[0]])

        # Multiple items - need to determine if it's unary operator or atom with trailers
        first_item = items[0]
        from lark import Token

        # Check if first item is actually a unary operator (+ or -)
        is_unary_operator = False
        if isinstance(first_item, Token):
            if first_item.type in ("ADD", "SUB") or first_item.value in ("+", "-"):
                is_unary_operator = True
        elif hasattr(first_item, "data") and first_item.data in ("ADD", "SUB"):
            is_unary_operator = True
        elif isinstance(first_item, BinaryOperator) and first_item in (BinaryOperator.ADD, BinaryOperator.SUBTRACT):
            is_unary_operator = True

        if is_unary_operator:
            # Case 1: (ADD | SUB) factor - unary operator
            op_token = first_item
            if len(items) < 2:
                raise ValueError(f"Factor with operator {op_token} has no operand")

            right = self.expression([items[1]])
            right_expr = cast(Expression, right)

            # Extract operator string
            if isinstance(op_token, Token):
                op_str = op_token.value
            elif isinstance(op_token, BinaryOperator):
                if op_token == BinaryOperator.ADD:
                    op_str = "+"
                elif op_token == BinaryOperator.SUBTRACT:
                    op_str = "-"
                else:
                    op_str = str(op_token.value)
            else:
                op_str = str(op_token)

            return UnaryExpression(operator=op_str, operand=right_expr)
        else:
            # Case 2: atom trailer* - atom with trailers
            # Delegate to atom method which handles trailers
            return self.atom(items)

    def power(self, items):
        """
        Transform a power rule into an AST expression.

        New grammar structure: power: factor (POWER_OP power)?
        This makes power right-associative, as in 2**3**4 = 2**(3**4)
        """
        if len(items) == 1:
            # Just a single factor, no power operation
            return self.expression([items[0]])

        # We have a power operation with a right operand
        base = self.expression([items[0]])  # Base/left operand

        # Process the POWER_OP and its right operand
        from lark import Token

        # Check for POWER_OP token or "**" string in the middle element
        if len(items) >= 3 and (
            (isinstance(items[1], Token) and items[1].type == "POWER_OP")
            or items[1] == "**"
            or (hasattr(items[1], "value") and items[1].value == "**")
        ):
            # Found a power operator, right operand is already processed recursively
            # due to the grammar rule being recursive: (POWER_OP power)?
            right = self.expression([items[2]])

            # Cast operands to appropriate types to satisfy type checking
            left_expr = cast(LiteralExpression | Identifier | BinaryExpression | FunctionCall, base)
            right_expr = cast(LiteralExpression | Identifier | BinaryExpression | FunctionCall, right)

            return BinaryExpression(left=left_expr, operator=BinaryOperator.POWER, right=right_expr)

        # Shouldn't reach here with the new grammar rule, but just in case
        return base

    def atom(self, items):
        if not items:
            return None

        # Get the base atom (first item)
        base = self.unwrap_single_child_tree(items[0])

        # If there are trailers, process them using the trailer method
        if len(items) > 1:
            # Create a list with base + trailers and delegate to trailer method
            trailer_items = [base] + items[1:]
            return self.trailer(trailer_items)

        # No trailers, just process the base atom
        item = base
        from lark import Token, Tree

        # Handle Token
        if isinstance(item, Token):
            return self._atom_from_token(item)
        # Handle Tree
        if isinstance(item, Tree):
            if item.data == "literal" and item.children:
                return self.atom(item.children)
            if item.data == "true_lit":
                return LiteralExpression(value=True, location=self.create_location(item))
            if item.data == "false_lit":
                return LiteralExpression(value=False, location=self.create_location(item))
            if item.data == "none_lit":
                return LiteralExpression(value=None, location=self.create_location(item))
            if item.data == "collection" and len(item.children) == 1:
                child = item.children[0]
                from dana.core.lang.ast import DictLiteral, SetLiteral, TupleLiteral

                if isinstance(child, DictLiteral | TupleLiteral | SetLiteral):
                    return child
            # Otherwise, flatten all children and recurse
            for child in item.children:
                result = self.atom([child])
                if isinstance(result, LiteralExpression):
                    return result
            raise TypeError(f"Unhandled tree in atom: {item.data} with children {item.children}")
        # If it's already a primitive, wrap as LiteralExpression
        if isinstance(item, int | float | str | bool | type(None)):
            result = LiteralExpression(value=item)
            return result
        return item

    def _atom_from_token(self, token):
        value = token.value
        location = self.create_location(token)  # Create location from token

        # Handle NUMBER tokens specifically
        if hasattr(token, "type") and token.type == "NUMBER":
            try:
                if "." in value:
                    return LiteralExpression(value=float(value), location=location)
                else:
                    return LiteralExpression(value=int(value), location=location)
            except (ValueError, TypeError):
                # Fallback if conversion fails
                pass

        # Handle boolean and None tokens
        if hasattr(token, "type"):
            if token.type == "TRUE" or value in ["True", "true", "TRUE"]:
                return LiteralExpression(value=True, location=location)
            elif token.type == "FALSE" or value in ["False", "false", "FALSE"]:
                return LiteralExpression(value=False, location=location)
            elif token.type == "NONE" or value in ["None", "none", "NONE"]:
                return LiteralExpression(value=None, location=location)

        # String literal: strip quotes
        if (
            value
            and isinstance(value, str)
            and (
                (value.startswith('"') and value.endswith('"'))
                or (value.startswith("'") and value.endswith("'"))
                or (value.startswith('"""') and value.endswith('"""'))
                or (value.startswith("'''") and value.endswith("'''"))
            )
        ):
            # Remove triple quotes first
            if value.startswith('"""') and value.endswith('"""'):
                value = value[3:-3]
            elif value.startswith("'''") and value.endswith("'''"):
                value = value[3:-3]
            else:
                value = value[1:-1]
            return LiteralExpression(value=value, location=location)

        # Fallback: try to convert numeric strings to int or float
        try:
            # Try int first (for simple digits)
            if value.isdigit() or (value.startswith("-") and value[1:].isdigit()):
                value = int(value)
            else:
                # Try float
                value = float(value)
        except (ValueError, TypeError):
            # Not numeric, keep as string for identifiers
            pass

        return LiteralExpression(value=value, location=location)

    # ================================================================
    # LITERAL VALUES
    # ================================================================

    def literal(self, items):
        # Unwrap and convert all literal tokens/trees to primitives
        return self.atom(items)

    def identifier(self, items):
        # Should be handled by VariableTransformer, but fallback here
        if len(items) == 1 and isinstance(items[0], Token):
            return Identifier(name=items[0].value, location=self.create_location(items[0]))
        raise TypeError(f"Cannot transform identifier: {items}")

    def argument(self, items):
        """Transform an argument rule into an expression or keyword argument pair."""
        # items[0] is either a kw_arg tree or an expression
        arg_item = items[0]

        # If it's a kw_arg tree, return it as-is for now
        # The function call handler will process it properly
        if hasattr(arg_item, "data") and arg_item.data == "kw_arg":
            return arg_item

        # Otherwise, transform it as a regular expression
        return self.expression([arg_item])

    def _process_function_arguments(self, arg_children):
        """Process function call arguments, handling both positional and keyword arguments."""
        args = []  # List of positional arguments
        kwargs = {}  # Dict of keyword arguments

        for arg_child in arg_children:
            # Skip None values (from optional COMMENT tokens)
            if arg_child is None:
                continue
            # Check if this is a kw_arg tree
            elif hasattr(arg_child, "data") and arg_child.data == "kw_arg":
                # Extract keyword argument name and value
                name = arg_child.children[0].value
                value = self.expression([arg_child.children[1]])
                kwargs[name] = value
            else:
                # Regular positional argument
                expr = self.expression([arg_child])
                args.append(expr)

        # Build the final args dict
        result = {"__positional": args}
        result.update(kwargs)
        return result

    # ================================================================
    # COLLECTION LITERALS
    # ================================================================

    def tuple(self, items):
        from dana.core.lang.ast import Expression, TupleLiteral

        flat_items = self.flatten_items(items)
        # Filter out COMMENT tokens before processing
        filtered_items = self._filter_comments(flat_items)
        # Ensure each item is properly cast to Expression type
        tuple_items: list[Expression] = []
        for item in filtered_items:
            expr = self.expression([item])
            tuple_items.append(cast(Expression, expr))

        return TupleLiteral(items=tuple_items)

    def list(self, items):
        """
        Transform a list literal or list comprehension into an AST node.
        """
        from dana.core.lang.ast import Expression

        # Check if this is a list comprehension (items[0] would be a Tree with data="list_comprehension")
        if items and hasattr(items[0], "data") and items[0].data == "list_comprehension":
            # This is a list comprehension, delegate to the list_comprehension method
            return self.list_comprehension([items[0]])

        # Check if items[0] is already a ListComprehension (from previous processing)
        if items and hasattr(items[0], "__class__") and items[0].__class__.__name__ == "ListComprehension":
            return items[0]

        # This is a regular list literal
        flat_items = self.flatten_items(items)
        # Filter out COMMENT tokens before processing
        filtered_items = self._filter_comments(flat_items)
        # Ensure each item is properly cast to Expression type
        list_items: list[Expression] = []
        for item in filtered_items:
            expr = self.expression([item])
            list_items.append(cast(Expression, expr))

        return ListLiteral(items=list_items)

    def dict(self, items):
        """
        Transform a dict literal or dict comprehension into an AST node.
        """
        from dana.core.lang.ast import DictLiteral

        # Check if this is a dict comprehension by looking for comprehension patterns
        if items and self._is_dict_comprehension(items):
            return self._create_dict_comprehension(items)

        # This is a regular dict literal
        flat_items = self.flatten_items(items)
        # Filter out COMMENT tokens before processing
        filtered_items = self._filter_comments(flat_items)
        pairs = []
        for item in filtered_items:
            # Check if this individual item is a dict comprehension
            if hasattr(item, "__class__") and item.__class__.__name__ == "DictComprehension":
                # If we have a single dict comprehension, return it directly
                if len(filtered_items) == 1:
                    return item
                # Otherwise, this shouldn't happen - a dict literal can't contain a comprehension
                raise ValueError("Dict literal cannot contain dict comprehension as an item")
            elif isinstance(item, tuple) and len(item) == 2:
                pairs.append(item)
            elif hasattr(item, "data") and item.data == "key_value_pair":
                pair = self.key_value_pair(item.children)
                pairs.append(pair)
            # Skip comment tokens - they are handled at the grammar level but ignored during transformation
            elif hasattr(item, "type") and item.type == "COMMENT":
                continue
        result = DictLiteral(items=pairs)
        return result

    def dict_items(self, items):
        """Transform dict_items rule (list of dict_element)."""
        return self.flatten_items(items)

    def dict_element(self, items):
        """Transform dict_element rule (either key_value_pair or COMMENT)."""
        if not items:
            return None

        item = items[0]

        # If it's a comment token, skip it (comments are ignored during transformation)
        if hasattr(item, "type") and item.type == "COMMENT":
            return None

        # Otherwise, it should be a key_value_pair
        return item

    def set(self, items):
        """
        Transform a set literal or set comprehension into an AST node.
        """
        from dana.core.lang.ast import Expression, SetLiteral

        # Check if this is a set comprehension by looking for comprehension patterns
        if items and self._is_set_comprehension(items):
            return self._create_set_comprehension(items)

        # This is a regular set literal
        flat_items = self.flatten_items(items)
        # Filter out COMMENT tokens before processing
        filtered_items = self._filter_comments(flat_items)
        # Ensure each item is properly cast to Expression type
        set_items: list[Expression] = []
        for item in filtered_items:
            # Check if this individual item is a set comprehension
            if hasattr(item, "__class__") and item.__class__.__name__ == "SetComprehension":
                # If we have a single set comprehension, return it directly
                if len(filtered_items) == 1:
                    return item
                # Otherwise, this shouldn't happen - a set literal can't contain a comprehension
                raise ValueError("Set literal cannot contain set comprehension as an item")
            expr = self.expression([item])
            set_items.append(cast(Expression, expr))

        return SetLiteral(items=set_items)

    def TRUE(self, items=None):
        return LiteralExpression(value=True)

    def FALSE(self, items=None):
        return LiteralExpression(value=False)

    def NONE(self, items=None):
        return LiteralExpression(value=None)

    def trailer(self, items):
        """
        Handles function calls, attribute access, and indexing after an atom.

        This method now uses the TrailerProcessor to handle method chaining with
        improved separation of concerns, error handling, and performance monitoring.

        METHOD CHAINING SUPPORT:
        -----------------------
        The TrailerProcessor implements sequential trailer processing to properly
        support method chaining. For example:

        df.groupby(df.index).mean() becomes:
        1. df (base)
        2. .groupby(df.index) -> ObjectFunctionCall
        3. .mean() -> ObjectFunctionCall on result of step 2

        Args:
            items: List containing base expression and trailer elements from parse tree

        Returns:
            AST node (ObjectFunctionCall, FunctionCall, AttributeAccess, or SubscriptExpression)

        Raises:
            SandboxError: If trailer processing fails or chain is too long
        """
        from dana.core.lang.parser.transformer.trailer_processor import TrailerProcessor

        # Initialize trailer processor if not already done
        if not hasattr(self, "_trailer_processor"):
            self._trailer_processor = TrailerProcessor(self)

        base = items[0]
        trailers = items[1:]

        # Use the trailer processor to handle the chain
        return self._trailer_processor.process_trailers(base, trailers)

    def _get_full_attribute_name(self, attr):
        # Recursively extract full dotted name from AttributeAccess chain
        parts = []
        while isinstance(attr, AttributeAccess):
            parts.append(attr.attribute)
            attr = attr.object
        if isinstance(attr, Identifier):
            parts.append(attr.name)
        else:
            parts.append(str(attr))
        return ".".join(reversed(parts))

    def key_value_pair(self, items):
        # Filter out COMMENT tokens before processing
        filtered_items = self._filter_comments(items)
        # Always return a (key, value) tuple
        if len(filtered_items) >= 2:
            key = self.expression([filtered_items[0]])
            value = self.expression([filtered_items[1]])
            return (key, value)
        else:
            # Handle error case with insufficient items after filtering
            return (None, None)

    def expr(self, items):
        # Delegate to the main expression handler
        return self.expression(items)

    def string(self, items):
        # Handles REGULAR_STRING, fstring, raw_string, multiline_string
        item = items[0]
        from lark import Token, Tree

        if isinstance(item, Token):
            if item.type == "REGULAR_STRING":
                value = item.value[1:-1]  # Strip quotes
                return LiteralExpression(value)
            elif item.type == "F_STRING_TOKEN":
                # Pass to the fstring_transformer
                from dana.core.lang.parser.transformer.fstring_transformer import (
                    FStringTransformer,
                )

                fstring_transformer = FStringTransformer()
                return fstring_transformer.fstring([item])
            elif item.type == "RAW_STRING":
                # Handle raw string
                value = item.value[2:-1]  # Strip r" and "
                return LiteralExpression(value)
            elif item.type == "MULTILINE_STRING":
                # Handle multiline string
                if item.value.startswith('"""') and item.value.endswith('"""'):
                    value = item.value[3:-3]
                elif item.value.startswith("'''") and item.value.endswith("'''"):
                    value = item.value[3:-3]
                else:
                    value = item.value
                return LiteralExpression(value)
        elif isinstance(item, Tree):
            if item.data == "raw_string":
                # raw_string: "r" REGULAR_STRING
                string_token = item.children[1]
                value = string_token.value[1:-1]
                return LiteralExpression(value)
            elif item.data == "multiline_string":
                # multiline_string: TRIPLE_QUOTED_STRING
                string_token = item.children[0]
                # Strip triple quotes
                value = string_token.value[3:-3]
                return LiteralExpression(value)
            elif item.data == "fstring":
                # Handle fstring: f_prefix fstring_content
                # For now, treat as a regular string but prepare for embedded expressions

                # Extract f_prefix (already processed) and fstring_content
                content_node = item.children[1]

                if isinstance(content_node, Token) and content_node.type == "REGULAR_STRING":
                    # Simple case: f"..." with no embedded expressions
                    value = content_node.value[1:-1]  # Strip quotes
                    return LiteralExpression(value)

                # Process complex fstring with potential embedded expressions
                content_parts = []
                # Skip the opening and closing quotes in content_node.children
                for child in content_node.children[1:-1]:
                    if isinstance(child, Token) and child.type == "fstring_text":
                        # Regular text
                        content_parts.append(LiteralExpression(child.value))
                    elif isinstance(child, Tree) and child.data == "fstring_expr":
                        # Embedded expression {expr}
                        expr_node = child.children[1]  # Skip the { and }
                        expr = self.expression([expr_node])
                        content_parts.append(expr)
                    elif isinstance(child, Token) and child.type == "ESCAPED_BRACE":
                        # Escaped braces {{ or }}
                        content_parts.append(LiteralExpression(child.value[0]))  # Just add one brace

                # Return specialized FStringExpression node
                return FStringExpression(parts=content_parts)

        self.error(f"Unknown string type: {item}")
        return LiteralExpression("")

    # Add support for the new grammar rules
    def product(self, items):
        """Transform a product rule (term with multiplication, division, etc)."""
        if len(items) == 1:
            return self.expression([items[0]])

        # Build a binary expression tree for the product
        return self._left_associative_binop(items, self._get_binary_operator)

    def POW(self, token):
        """Handle the power operator token."""
        return BinaryOperator.POWER

    def ADD(self, token):
        """Handle the addition operator token."""
        return BinaryOperator.ADD

    def SUB(self, token):
        """Handle the subtraction operator token."""
        return BinaryOperator.SUBTRACT

    def MUL(self, token):
        """Handle the multiplication operator token."""
        return BinaryOperator.MULTIPLY

    def DIV(self, token):
        """Handle the division operator token."""
        return BinaryOperator.DIVIDE

    def FDIV(self, token):
        """Handle the floor division operator token."""
        return BinaryOperator.FLOOR_DIVIDE

    def MOD(self, token):
        """Handle the modulo operator token."""
        return BinaryOperator.MODULO

    def string_literal(self, items):
        """
        Handles string_literal rule from the grammar, which includes REGULAR_STRING, F_STRING_TOKEN, RAW_STRING, etc.
        This rule directly maps to grammar's string_literal rule.
        """
        if not items:
            return LiteralExpression("")

        item = items[0]
        from lark import Token

        if isinstance(item, Token):
            # F-string handling
            if item.type == "F_STRING_TOKEN":
                # Pass to the FStringTransformer
                from dana.core.lang.parser.transformer.fstring_transformer import (
                    FStringTransformer,
                )

                fstring_transformer = FStringTransformer()
                return fstring_transformer.fstring([item])
            # Regular string
            elif item.type == "REGULAR_STRING":
                value = item.value[1:-1]  # Strip quotes
                return LiteralExpression(value)
            # Single-quoted string
            elif item.type == "SINGLE_QUOTED_STRING":
                value = item.value[1:-1]  # Strip single quotes
                return LiteralExpression(value)
            # Raw string
            elif item.type == "RAW_STRING":
                # Extract the raw string content (removing r" prefix and " suffix)
                if item.value.startswith('r"') and item.value.endswith('"'):
                    value = item.value[2:-1]
                elif item.value.startswith("r'") and item.value.endswith("'"):
                    value = item.value[2:-1]
                else:
                    value = item.value
                return LiteralExpression(value)
            # Multiline string
            elif item.type == "MULTILINE_STRING":
                if item.value.startswith('"""') and item.value.endswith('"""'):
                    value = item.value[3:-3]
                elif item.value.startswith("'''") and item.value.endswith("'''"):
                    value = item.value[3:-3]
                else:
                    value = item.value
                return LiteralExpression(value)

        # If we reach here, it's an unexpected string type
        self.error(f"Unexpected string literal type: {type(item)}")
        return LiteralExpression("")

    def slice_or_index(self, items):
        """Handle slice_or_index rule - returns either a slice_expr or expr."""
        return items[0]  # Return the slice_expr or expr directly

    def slice_start_only(self, items):
        """Transform [start:] slice pattern."""
        return SliceExpression(start=items[0], stop=None, step=None)

    def slice_stop_only(self, items):
        """Transform [:stop] slice pattern."""
        return SliceExpression(start=None, stop=items[0], step=None)

    def slice_start_stop(self, items):
        """Transform [start:stop] slice pattern."""
        return SliceExpression(start=items[0], stop=items[1], step=None)

    def slice_start_stop_step(self, items):
        """Transform [start:stop:step] slice pattern."""
        return SliceExpression(start=items[0], stop=items[1], step=items[2])

    def slice_all(self, items):
        """Transform [:] slice pattern."""
        return SliceExpression(start=None, stop=None, step=None)

    def slice_step_only(self, items):
        """Transform [::step] slice pattern."""
        return SliceExpression(start=None, stop=None, step=items[0])

    def slice_expr(self, items):
        """Handle slice_expr containing one of the specific slice patterns."""
        # This method receives the result from one of the specific slice pattern methods
        return items[0]

    def slice_list(self, items):
        """Handle slice_list - returns either a single slice/index or a SliceTuple for multi-dimensional slicing."""
        if len(items) == 1:
            # Single dimension - return the slice/index directly
            return items[0]
        else:
            # Multi-dimensional - return a SliceTuple
            from dana.core.lang.ast import SliceTuple

            return SliceTuple(slices=items)

    # ===== FUNCTION COMPOSITION EXPRESSIONS =====
    def function_composition_expr(self, items):
        """Transform function_composition_expr rule."""
        # Grammar: function_composition_expr: function_pipe_expr
        return items[0]

    def function_pipe_expr(self, items):
        """Transform function_pipe_expr rule."""
        # Grammar: function_pipe_expr: pipeline_stage (PIPE pipeline_stage)*
        if len(items) == 1:
            return items[0]
        else:
            # Multiple expressions with PIPE operators
            result = items[0]
            for i in range(1, len(items), 2):
                if i + 1 < len(items):
                    operator = BinaryOperator.PIPE
                    right = items[i + 1]
                    result = BinaryExpression(left=result, operator=operator, right=right)
            return result

    def pipeline_stage(self, items):
        """Transform pipeline_stage rule."""
        # Grammar: pipeline_stage: function_expr ["as" NAME]
        if len(items) == 1:
            # No "as" clause - just return the expression
            return items[0]
        else:
            # Has "as" clause - create NamedPipelineStage
            from dana.core.lang.ast import NamedPipelineStage

            expression = items[0]
            # Handle the case where items[1] might be None or not have a value attribute
            if hasattr(items[1], "value"):
                name = items[1].value
            elif isinstance(items[1], str):
                name = items[1]
            else:
                # Fallback - try to get the name from the token
                name = str(items[1]) if items[1] is not None else None

            # Only create NamedPipelineStage if we have a valid name
            if name:
                return NamedPipelineStage(expression=expression, name=name)
            else:
                # If no valid name, just return the expression
                return expression

    def function_expr(self, items):
        """Transform function_expr rule."""
        # Grammar: function_expr: function_name | function_call | function_list_literal
        return items[0]

    def function_name(self, items):
        """Transform function_name rule."""
        # Grammar: function_name: NAME
        return Identifier(items[0].value)

    def function_call(self, items):
        """Transform function_call rule."""
        # Grammar: function_call: NAME "(" [arguments] ")"
        name = items[0].value
        if len(items) > 1 and items[1] is not None:
            # Process arguments through the proper method
            # items[1] is a Tree with argument children
            arguments = self._process_function_arguments(items[1].children)
        else:
            # No arguments - create empty args dict
            arguments = {"__positional": []}

        # Check if this function call contains a placeholder expression
        # If so, treat it as a single-stage pipeline (placeholders are only valid in pipelines)
        if self._contains_placeholder(arguments):
            # PHASE B CHANGE: Don't create PipelineExpression for function calls with placeholders
            # Let them be handled as regular FunctionCall nodes, which will trigger PartialFunction logic
            # from dana.core.lang.ast import PipelineExpression
            # return PipelineExpression(stages=[FunctionCall(name=name, args=arguments)])
            pass

        return FunctionCall(name=name, args=arguments)

    def function_list_literal(self, items):
        """Transform function_list_literal rule."""
        # Grammar: function_list_literal: "[" [function_expr ("," function_expr)*] "]"
        if len(items) == 0:
            return ListLiteral(items=[])
        else:
            return ListLiteral(items=items)

    def _contains_placeholder(self, arguments):
        """Check if function call arguments contain a placeholder expression."""
        if not isinstance(arguments, dict):
            return False

        # Check positional arguments
        if "__positional" in arguments:
            for arg in arguments["__positional"]:
                if self._is_placeholder_expression(arg):
                    return True

        # Check keyword arguments
        for key, arg in arguments.items():
            if key != "__positional" and self._is_placeholder_expression(arg):
                return True

        return False

    def _is_placeholder_expression(self, expr):
        """Check if an expression is a placeholder expression."""
        from dana.core.lang.ast import PlaceholderExpression

        return isinstance(expr, PlaceholderExpression)

    def lambda_expr(self, items):
        """Transform a lambda expression using the specialized lambda transformer."""
        from dana.core.lang.parser.transformer.expression.lambda_transformer import LambdaTransformer

        lambda_transformer = LambdaTransformer(main_transformer=self.main_transformer)
        return lambda_transformer.lambda_expr(items)

    def lambda_receiver(self, items):
        """Transform a lambda receiver using the specialized lambda transformer."""
        from dana.core.lang.parser.transformer.expression.lambda_transformer import LambdaTransformer

        lambda_transformer = LambdaTransformer(main_transformer=self.main_transformer)
        return lambda_transformer.lambda_receiver(items)

    def lambda_params(self, items):
        """Transform lambda parameters using the specialized lambda transformer."""
        from dana.core.lang.parser.transformer.expression.lambda_transformer import LambdaTransformer

        lambda_transformer = LambdaTransformer(main_transformer=self.main_transformer)
        return lambda_transformer.lambda_params(items)

    # ================================================================
    # COMPREHENSIONS
    # ================================================================

    def list_comprehension(self, items):
        """Transform list comprehension parse tree to AST node."""
        from dana.core.lang.ast import ListComprehension

        if not items or len(items) < 1:
            return None

        # items[0] could be either a Tree (comprehension_body) or a list (if comprehension_body was already processed)
        comprehension_body = items[0]

        if isinstance(comprehension_body, list):
            # comprehension_body was already processed and returned a list
            body_children = comprehension_body
        elif hasattr(comprehension_body, "data") and comprehension_body.data == "comprehension_body":
            # comprehension_body is a Tree
            body_children = comprehension_body.children
        else:
            return None

        if len(body_children) < 3:
            return None

        # Extract components: expression, target, iterable, optional condition
        expression = self.main_transformer.transform(body_children[0]) if self.main_transformer else body_children[0]
        target = body_children[1].value if hasattr(body_children[1], "value") else str(body_children[1])
        iterable = self.main_transformer.transform(body_children[2]) if self.main_transformer else body_children[2]

        # Check for optional condition
        condition = None
        if len(body_children) > 3 and body_children[3]:
            condition = self.main_transformer.transform(body_children[3]) if self.main_transformer else body_children[3]

        return ListComprehension(expression=expression, target=target, iterable=iterable, condition=condition)

    def set_comprehension(self, items):
        """Transform set comprehension parse tree to AST node."""
        from dana.core.lang.ast import SetComprehension

        if not items or len(items) < 1:
            return None

        # items[0] could be either a Tree (comprehension_body) or a list (if comprehension_body was already processed)
        comprehension_body = items[0]

        if isinstance(comprehension_body, list):
            # comprehension_body was already processed and returned a list
            body_children = comprehension_body
        elif hasattr(comprehension_body, "data") and comprehension_body.data == "comprehension_body":
            # comprehension_body is a Tree
            body_children = comprehension_body.children
        else:
            return None

        if len(body_children) < 3:
            return None

        # Extract components: expression, target, iterable, optional condition
        expression = self.main_transformer.transform(body_children[0]) if self.main_transformer else body_children[0]
        target = body_children[1].value if hasattr(body_children[1], "value") else str(body_children[1])
        iterable = self.main_transformer.transform(body_children[2]) if self.main_transformer else body_children[2]

        # Check for optional condition
        condition = None
        if len(body_children) > 3 and body_children[3]:
            condition = self.main_transformer.transform(body_children[3]) if self.main_transformer else body_children[3]

        return SetComprehension(expression=expression, target=target, iterable=iterable, condition=condition)

    def dict_comprehension(self, items):
        """Transform dict comprehension parse tree to AST node."""
        from dana.core.lang.ast import DictComprehension

        if not items or len(items) < 1:
            return None

        # items[0] should be the result from dict_comprehension_body
        comprehension_body = items[0]

        if isinstance(comprehension_body, list):
            # comprehension_body was already processed and returned a list
            body_children = comprehension_body
        elif hasattr(comprehension_body, "data") and comprehension_body.data == "dict_comprehension_body":
            # comprehension_body is a Tree
            body_children = comprehension_body.children
        else:
            return None

        # The dict_comprehension_body method passes through the processed tokens
        # Structure: [key_expr, value_expr, target, iterable, condition]
        if len(body_children) < 4:  # Need at least key, value, target, iterable
            return None

        # Extract components from the simplified structure
        key_expr = body_children[0]
        value_expr = body_children[1]
        target = body_children[2].value if hasattr(body_children[2], "value") else str(body_children[2])
        iterable = body_children[3]

        # Check for optional condition (5th element)
        condition = None
        if len(body_children) > 4 and body_children[4]:
            condition = body_children[4]

        result = DictComprehension(key_expr=key_expr, value_expr=value_expr, target=target, iterable=iterable, condition=condition)
        return result

    def dict_comprehension_body(self, items):
        """Transform dict comprehension body - just pass through to parent."""
        return items

    def comprehension_body(self, items):
        """Transform comprehension body - just pass through to parent."""
        return items

    def for_targets(self, items):
        """Transform for loop targets (single variable or tuple unpacking)."""
        # Handle the new grammar: NAME ("," NAME)* | "(" for_target_list ")"

        # Check if we have exactly one item that's a list (parenthesized form)
        if len(items) == 1 and isinstance(items[0], list):
            # This is the result from "(" for_target_list ")" - parentheses are consumed by grammar
            target_list = items[0]
            if all(isinstance(name, str) for name in target_list):
                # for_target_list returns processed names
                return ", ".join(target_list)
            else:
                # Handle unexpected format
                return str(target_list)

        # Handle the direct form: NAME ("," NAME)*
        # All items should be NAME tokens or comma tokens
        names = []
        for item in items:
            if hasattr(item, "value") and item.value != ",":
                names.append(item.value)
            elif hasattr(item, "value") and item.value == ",":
                # Skip comma tokens
                continue
            elif isinstance(item, str) and item != ",":
                names.append(item)

        if len(names) == 1:
            # Single variable: just return the name
            return names[0]
        else:
            # Multiple variables: return comma-separated string
            return ", ".join(names)

    def for_target_list(self, items):
        """Transform for target list (comma-separated names)."""
        # Extract tokens and return list of name strings
        names = []
        for item in items:
            if hasattr(item, "value") and item.value != ",":
                names.append(item.value)
            elif isinstance(item, str) and item != ",":
                names.append(item)
        return names

    def comprehension_if(self, items):
        """Transform comprehension condition - just pass through to parent."""
        return items[0] if items else None

    def _is_set_comprehension(self, items):
        """Check if the items represent a set comprehension pattern."""
        # Look for pattern: expr for var in iterable [if condition]
        if not items:
            return False

        flat_items = self.flatten_items(items)
        if len(flat_items) < 3:
            return False

        # Check if we have the pattern: expr, 'for', var, 'in', iterable, [optional 'if', condition]
        for item in flat_items:
            if hasattr(item, "value") and item.value == "for":
                # Found 'for' keyword, this looks like a comprehension
                return True
        return False

    def _is_dict_comprehension(self, items):
        """Check if the items represent a dict comprehension pattern."""
        # Look for pattern: key_expr : value_expr for var in iterable [if condition]
        if not items:
            return False

        flat_items = self.flatten_items(items)
        if len(flat_items) < 5:  # Need at least: key, :, value, for, var, in, iterable
            return False

        # Check if we have the pattern with 'for' keyword and ':'
        has_for = False
        has_colon = False
        for item in flat_items:
            if hasattr(item, "value") and item.value == "for":
                has_for = True
            elif hasattr(item, "type") and item.type == "COLON":
                has_colon = True

        return has_for and has_colon

    def _create_set_comprehension(self, items):
        """Create a SetComprehension AST node from parsed items."""
        from dana.core.lang.ast import SetComprehension

        flat_items = self.flatten_items(items)

        # Parse the comprehension pattern: expr for var in iterable [if condition]
        expression = None
        target = None
        iterable = None
        condition = None

        i = 0
        # Get expression (everything before 'for')
        while i < len(flat_items) and not (hasattr(flat_items[i], "value") and flat_items[i].value == "for"):
            if expression is None:
                expression = self.main_transformer.transform(flat_items[i]) if self.main_transformer else flat_items[i]
            i += 1

        # Skip 'for'
        i += 1

        # Get target variable
        if i < len(flat_items):
            target = flat_items[i].value if hasattr(flat_items[i], "value") else str(flat_items[i])
            i += 1

        # Skip 'in'
        if i < len(flat_items) and hasattr(flat_items[i], "value") and flat_items[i].value == "in":
            i += 1

        # Get iterable (everything before 'if' or end)
        while i < len(flat_items) and not (hasattr(flat_items[i], "value") and flat_items[i].value == "if"):
            if iterable is None:
                iterable = self.main_transformer.transform(flat_items[i]) if self.main_transformer else flat_items[i]
            i += 1

        # Get condition if present
        if i < len(flat_items) and hasattr(flat_items[i], "value") and flat_items[i].value == "if":
            i += 1
            if i < len(flat_items):
                condition = self.main_transformer.transform(flat_items[i]) if self.main_transformer else flat_items[i]

        return SetComprehension(expression=expression, target=target, iterable=iterable, condition=condition)

    def _create_dict_comprehension(self, items):
        """Create a DictComprehension AST node from parsed items."""
        from dana.core.lang.ast import DictComprehension

        flat_items = self.flatten_items(items)

        # Parse the comprehension pattern: key_expr : value_expr for var in iterable [if condition]
        key_expr = None
        value_expr = None
        target = None
        iterable = None
        condition = None

        i = 0
        # Get key expression (everything before ':')
        while i < len(flat_items) and not (hasattr(flat_items[i], "type") and flat_items[i].type == "COLON"):
            if key_expr is None:
                key_expr = self.main_transformer.transform(flat_items[i]) if self.main_transformer else flat_items[i]
            i += 1

        # Skip ':'
        i += 1

        # Get value expression (everything before 'for')
        while i < len(flat_items) and not (hasattr(flat_items[i], "value") and flat_items[i].value == "for"):
            if value_expr is None:
                value_expr = self.main_transformer.transform(flat_items[i]) if self.main_transformer else flat_items[i]
            i += 1

        # Skip 'for'
        i += 1

        # Get target variable
        if i < len(flat_items):
            target = flat_items[i].value if hasattr(flat_items[i], "value") else str(flat_items[i])
            i += 1

        # Skip 'in'
        if i < len(flat_items) and hasattr(flat_items[i], "value") and flat_items[i].value == "in":
            i += 1

        # Get iterable (everything before 'if' or end)
        while i < len(flat_items) and not (hasattr(flat_items[i], "value") and flat_items[i].value == "if"):
            if iterable is None:
                iterable = self.main_transformer.transform(flat_items[i]) if self.main_transformer else flat_items[i]
            i += 1

        # Get condition if present
        if i < len(flat_items) and hasattr(flat_items[i], "value") and flat_items[i].value == "if":
            i += 1
            if i < len(flat_items):
                condition = self.main_transformer.transform(flat_items[i]) if self.main_transformer else flat_items[i]

        return DictComprehension(key_expr=key_expr, value_expr=value_expr, target=target, iterable=iterable, condition=condition)


# File updated to resolve GitHub CI syntax error - 2025-06-09
