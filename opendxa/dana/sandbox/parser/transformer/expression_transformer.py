"""
Copyright © 2025 Aitomatic, Inc.

This source code is licensed under the license found in the LICENSE file in the root directory of this source tree

Expression transformers for DANA language parsing.
"""

from typing import Union, cast

from lark import Token, Tree

from opendxa.dana.sandbox.parser.ast import (
    AttributeAccess,
    BinaryExpression,
    BinaryOperator,
    DictLiteral,
    Expression,
    FStringExpression,
    FunctionCall,
    Identifier,
    LiteralExpression,
    SetLiteral,
    SubscriptExpression,
    TupleLiteral,
    UnaryExpression,
)
from opendxa.dana.sandbox.parser.transformer.base_transformer import BaseTransformer

ValidExprType = Union[LiteralExpression, Identifier, BinaryExpression, FunctionCall]


class ExpressionTransformer(BaseTransformer):
    """
    Transforms Lark parse trees for DANA expressions into AST nodes.

    Handles all expression grammar rules, including operator precedence, literals, collections,
    function calls, attribute access, and constants. Methods are grouped by grammar hierarchy for clarity.
    """

    def expression(self, items):
        if not items:
            return None
        item = items[0]
        # Recursively unwrap single-child Trees, but do not unwrap comp_op
        while isinstance(item, Tree) and len(item.children) == 1 and getattr(item, "data", None) != "comp_op":
            item = item.children[0]
        # If it's a Tree, dispatch by rule name
        if isinstance(item, Tree):
            if item.data == "key_value_pair":
                return self.key_value_pair(item.children)
            if item.data == "tuple":
                return self.tuple(item.children)
            if item.data == "dict":
                return self.dict(item.children)
            if item.data == "list":
                return self.list(item.children)
            if item.data == "true_lit":
                return LiteralExpression(value=True)
            if item.data == "false_lit":
                return LiteralExpression(value=False)
            if item.data == "none_lit":
                return LiteralExpression(value=None)
            if item.data == "literal":
                if len(item.children) == 1:
                    return self.expression([item.children[0]])
                else:
                    return LiteralExpression(value=None)
            # Always dispatch to the corresponding method for these rules
            if item.data == "sum_expr":
                return self.sum_expr(item.children)
            if item.data == "term":
                return self.term(item.children)
            if item.data == "comparison":
                return self.comparison(item.children)
            if item.data == "and_expr":
                return self.and_expr(item.children)
            if item.data == "or_expr":
                return self.or_expr(item.children)
            method = getattr(self, item.data, None)
            if method:
                return method(item.children)
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
            (
                LiteralExpression,
                Identifier,
                BinaryExpression,
                FunctionCall,
                TupleLiteral,
                DictLiteral,
                SetLiteral,
                SubscriptExpression,
                AttributeAccess,
                FStringExpression,
                UnaryExpression,
            ),
        ):
            return item
        # If it's a primitive or FStringExpression, wrap as LiteralExpression
        if isinstance(item, (int, float, str, bool, type(None), FStringExpression)):
            return LiteralExpression(value=item)
        # If it's a Token, unwrap to primitive for LiteralExpression
        if isinstance(item, Token):
            if item.type == "NAME":
                return Identifier(name=item.value)
            value = item.value
            try:
                if "." in value:
                    value = float(value)
                else:
                    value = int(value)
            except (ValueError, TypeError):
                if value.lower() == "true":
                    value = True
                elif value.lower() == "false":
                    value = False
                elif value.lower() == "none":
                    value = None
            return LiteralExpression(value=value)
        raise TypeError(f"Cannot transform expression: {item} ({type(item)})")

    def _extract_operator_string(self, op_token):
        """
        Extract the operator string from a parse tree node, token, or string.
        Handles comp_op, *_op, ADD_OP, MUL_OP, direct tokens, and plain strings.
        Also handles BinaryOperator enum values.
        """
        from lark import Token, Tree

        if isinstance(op_token, Token):
            return op_token.value
        if isinstance(op_token, str):
            return op_token
        if isinstance(op_token, BinaryOperator):
            return op_token.value  # Return the value of the enum
        if isinstance(op_token, Tree):
            if getattr(op_token, "data", None) == "comp_op":
                op_str = " ".join(child.value for child in op_token.children if isinstance(child, Token))
                return op_str
            elif op_token.children and isinstance(op_token.children[0], Token):
                return op_token.children[0].value
        raise ValueError(f"Cannot extract operator string from: {op_token}")

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
        if not items:
            raise ValueError("No items for binary operation")
        result = items[0]
        i = 1
        while i < len(items):
            op_token = items[i]
            from lark import Tree

            if isinstance(op_token, Tree) and hasattr(op_token, "data") and op_token.data.endswith("_op") and not op_token.children:
                raise ValueError(f"Malformed parse tree: operator node '{op_token.data}' has no children at index {i} in items: {items}")
            op_str = self._extract_operator_string(op_token)
            op = operator_getter(op_str)
            right = items[i + 1]
            left = result
            result = BinaryExpression(left, op, right)
            i += 2
        return result

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
            "^": BinaryOperator.POWER,
        }
        return op_map[op_str]

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
            from opendxa.dana.sandbox.parser.ast import Expression

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
        # Unary plus/minus or pass-through
        if len(items) == 1:
            return self.expression([items[0]])
        op_token = items[0]
        right = self.expression([items[1]])

        # Explicitly cast right to Expression
        right_expr = cast(Expression, right)
        # Ensure operator is a string for UnaryExpression
        from lark import Token

        if isinstance(op_token, Token):
            op_str = op_token.value
        else:
            op_str = str(op_token)
        return UnaryExpression(operator=op_str, operand=right_expr)

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
            return BinaryExpression(left=base, operator=BinaryOperator.POWER, right=right)

        # Shouldn't reach here with the new grammar rule, but just in case
        return base

    def atom(self, items):
        if not items:
            return None
        # Handle function call on Identifier (including dotted)
        if len(items) >= 2:
            base = self.unwrap_single_child_tree(items[0])
            trailer = items[1]
            from lark import Tree

            from opendxa.dana.sandbox.parser.ast import FunctionCall, Identifier

            if isinstance(base, Identifier) and isinstance(trailer, Tree) and getattr(trailer, "data", None) == "arguments":
                name = base.name
                args = trailer.children if hasattr(trailer, "children") else []
                if not isinstance(args, dict):
                    args = {"__positional": args}
                return FunctionCall(name=name, args=args, location=getattr(base, "location", None))
        item = self.unwrap_single_child_tree(items[0])
        from lark import Token, Tree

        # Handle Token
        if isinstance(item, Token):
            return self._atom_from_token(item)
        # Handle Tree
        if isinstance(item, Tree):
            if item.data == "literal" and item.children:
                return self.atom(item.children)
            if item.data == "true_lit":
                return LiteralExpression(value=True)
            if item.data == "false_lit":
                return LiteralExpression(value=False)
            if item.data == "none_lit":
                return LiteralExpression(value=None)
            if item.data == "collection" and len(item.children) == 1:
                child = item.children[0]
                from opendxa.dana.sandbox.parser.ast import DictLiteral, SetLiteral, TupleLiteral

                if isinstance(child, (DictLiteral, TupleLiteral, SetLiteral)):
                    return child
            # Otherwise, flatten all children and recurse
            for child in item.children:
                result = self.atom([child])
                if isinstance(result, LiteralExpression):
                    return result
            raise TypeError(f"Unhandled tree in atom: {item.data} with children {item.children}")
        # If it's already a primitive, wrap as LiteralExpression
        if isinstance(item, (int, float, str, bool, type(None))):
            result = LiteralExpression(value=item)
            return result
        return item

    def _atom_from_token(self, token):
        value = token.value
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
            return LiteralExpression(value=value)
        # Try to convert to int, float, bool, or None
        if value.isdigit():
            value = int(value)
        else:
            try:
                value = float(value)
            except Exception:
                if value == "True":
                    value = True
                elif value == "False":
                    value = False
                elif value == "None":
                    value = None
        return LiteralExpression(value=value)

    def literal(self, items):
        # Unwrap and convert all literal tokens/trees to primitives
        return self.atom(items)

    def identifier(self, items):
        # Should be handled by VariableTransformer, but fallback here
        if len(items) == 1 and isinstance(items[0], Token):
            return Identifier(name=items[0].value)
        raise TypeError(f"Cannot transform identifier: {items}")

    def tuple(self, items):
        from opendxa.dana.sandbox.parser.ast import TupleLiteral

        flat_items = self.flatten_items(items)
        return TupleLiteral(items=[self.expression([item]) for item in flat_items])

    def list(self, items):
        flat_items = self.flatten_items(items)
        return LiteralExpression(value=[self.expression([item]) for item in flat_items])

    def dict(self, items):
        flat_items = self.flatten_items(items)
        pairs = []
        for item in flat_items:
            if isinstance(item, tuple) and len(item) == 2:
                pairs.append(item)
            elif hasattr(item, "data") and item.data == "key_value_pair":
                pair = self.key_value_pair(item.children)
                pairs.append(pair)
        from opendxa.dana.sandbox.parser.ast import DictLiteral

        return DictLiteral(items=pairs)

    def set(self, items):
        flat_items = self.flatten_items(items)
        from opendxa.dana.sandbox.parser.ast import SetLiteral

        return SetLiteral(items=[self.expression([item]) for item in flat_items])

    def TRUE(self, items=None):
        return LiteralExpression(value=True)

    def FALSE(self, items=None):
        return LiteralExpression(value=False)

    def NONE(self, items=None):
        return LiteralExpression(value=None)

    def trailer(self, items):
        """
        Handles function calls, attribute access, and indexing after an atom.
        If the base is an Identifier (including dotted), and the trailer is a function call, produce a FunctionCall node.
        """
        base = items[0]
        trailers = items[1:]
        for t in trailers:
            # Function call: ( ... )
            if hasattr(t, "data") and t.data == "arguments":
                from opendxa.dana.sandbox.parser.ast import FunctionCall

                name = getattr(base, "name", None)
                if not isinstance(name, str):
                    name = str(base)
                args = t.children if hasattr(t, "children") else []
                if not isinstance(args, dict):
                    args = {"__positional": args}
                return FunctionCall(name=name, args=args, location=getattr(base, "location", None))
            # Attribute access: .NAME
            elif hasattr(t, "type") and t.type == "NAME":
                from opendxa.dana.sandbox.parser.ast import Identifier

                name = getattr(base, "name", None)
                if not isinstance(name, str):
                    name = str(base)
                name = f"{name}.{t.value}"
                base = Identifier(name=name, location=getattr(base, "location", None))
            # Indexing: [ ... ]
            elif hasattr(t, "data") and t.data == "expr":
                from opendxa.dana.sandbox.parserx.parser.ast import SubscriptExpression

                base = SubscriptExpression(
                    object=base, index=t.children[0] if hasattr(t, "children") else t, location=getattr(base, "location", None)
                )
        return base

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
        # Always return a (key, value) tuple
        key = self.expression([items[0]])
        value = self.expression([items[1]])
        return (key, value)

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
                parts = []

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
        return BinaryOperator.DIVIDE  # For now, just map to regular division

    def MOD(self, token):
        """Handle the modulo operator token."""
        return BinaryOperator.MODULO
