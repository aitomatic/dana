"""Expression transformers for DANA language parsing."""

from typing import Union, cast

from lark import Token, Tree

from opendxa.dana.parser.ast import (
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
from opendxa.dana.parser.transformers.base_transformer import BaseTransformer

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
        Extract the operator string from a parse tree node or token.
        Handles comp_op, *_op, and direct tokens.
        """
        from lark import Token, Tree

        if isinstance(op_token, Tree):
            if getattr(op_token, "data", None) == "comp_op":
                return " ".join(child.value for child in op_token.children if isinstance(child, Token))
            elif op_token.children and isinstance(op_token.children[0], Token):
                return op_token.children[0].value
            elif hasattr(op_token, "data") and op_token.data.endswith("_op"):
                return self._op_tree_to_str(op_token)
            else:
                raise TypeError(f"Unexpected op_token tree: {op_token}")
        else:
            return op_token

    def _op_tree_to_str(self, tree):
        op_map = {
            "add_op": "+",
            "mul_op": "*",
            "sub_op": "-",
            "div_op": "/",
            "mod_op": "%",
            "floordiv_op": "//",
            "pow_op": "**",
            "and_op": "and",
            "or_op": "or",
            "eq_op": "==",
            "neq_op": "!=",
            "lt_op": "<",
            "gt_op": ">",
            "le_op": "<=",
            "ge_op": ">=",
        }
        return op_map.get(tree.data, tree.data)

    def _left_associative_binop(self, items, operator_getter):
        """
        Helper for left-associative binary operations (e.g., a + b + c).
        Iterates over items, applying the operator from operator_getter to each pair.
        Used by or_expr, and_expr, comparison, sum_expr, and term.
        """
        # Defensive: filter out empty operator nodes (e.g., Tree with no children)
        filtered_items = []
        for item in items:
            if isinstance(item, Tree) and not item.children:
                # If this is an operator node, keep it for operator extraction
                if hasattr(item, "data") and item.data.endswith("_op"):
                    filtered_items.append(item)
                # Otherwise, skip
                continue
            filtered_items.append(item)
        items = filtered_items
        if not items:
            return None
        if len(items) == 1:
            return self.expression([items[0]])
        if len(items) % 2 == 0:
            raise ValueError(f"Malformed parse tree for binary operation: items={items} (length={len(items)})")
        left = self.expression([items[0]])
        i = 1
        while i < len(items):
            op_token = items[i]
            right = self.expression([items[i + 1]])
            op_str = self._extract_operator_string(op_token)
            valid_types = (LiteralExpression, Identifier, BinaryExpression, FunctionCall)
            invalid_ast_types = (TupleLiteral, DictLiteral, SetLiteral, SubscriptExpression, AttributeAccess, FStringExpression)
            if not isinstance(left, valid_types):
                if isinstance(left, (int, float, str, bool, type(None))):
                    left = LiteralExpression(value=left)
                elif isinstance(left, invalid_ast_types):
                    raise TypeError(f"Invalid left operand AST node for BinaryExpression: {type(left)}")
                else:
                    raise TypeError(f"Invalid left operand type for BinaryExpression: {type(left)}")
            if not isinstance(right, valid_types):
                if isinstance(right, (int, float, str, bool, type(None))):
                    right = LiteralExpression(value=right)
                elif isinstance(right, invalid_ast_types):
                    raise TypeError(f"Invalid right operand AST node for BinaryExpression: {type(right)}")
                else:
                    raise TypeError(f"Invalid right operand type for BinaryExpression: {type(right)}")
            left_casted = cast(ValidExprType, left)
            right_casted = cast(ValidExprType, right)
            op = operator_getter(op_str)
            left = BinaryExpression(left=left_casted, operator=op, right=right_casted)
            i += 2
        return left

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
            "//": BinaryOperator.FLOORDIV if hasattr(BinaryOperator, "FLOORDIV") else BinaryOperator.DIVIDE,
            "<": BinaryOperator.LESS_THAN,
            ">": BinaryOperator.GREATER_THAN,
            "<=": BinaryOperator.LESS_EQUALS,
            ">=": BinaryOperator.GREATER_EQUALS,
            "==": BinaryOperator.EQUALS,
            "!=": BinaryOperator.NOT_EQUALS,
            "and": BinaryOperator.AND,
            "or": BinaryOperator.OR,
            "**": BinaryOperator.POWER,
        }
        return op_map.get(op_str, BinaryOperator.EQUALS)  # Default to equals if unknown

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
        if len(items) == 1:
            return self.expression([items[0]])
        # Use a UnaryExpression node for 'not'
        right = self.expression([items[1]])
        from typing import cast

        # Explicitly cast right to Expression
        right_expr = cast(Expression, right)
        return UnaryExpression(operator="not", operand=right_expr)

    def comparison(self, items):
        return self._left_associative_binop(items, self._get_binary_operator)

    def sum_expr(self, items):
        return self._left_associative_binop(items, self._get_binary_operator)

    def term(self, items):
        return self._left_associative_binop(items, self._get_binary_operator)

    def factor(self, items):
        # Unary plus/minus or pass-through
        if len(items) == 1:
            return self.expression([items[0]])
        op_token = items[0]
        right = self.expression([items[1]])
        from typing import cast

        # Explicitly cast right to Expression
        right_expr = cast(Expression, right)
        return UnaryExpression(
            operator=self._get_binary_operator(op_token.value if isinstance(op_token, Token) else op_token), operand=right_expr
        )

    def power(self, items):
        base = self.expression([items[0]])
        # items[1] is None if no exponentiation
        if len(items) > 1 and items[1] is not None:
            exponent = self.expression([items[1]])
            return BinaryExpression(left=base, operator=BinaryOperator.POWER, right=exponent)  # type: ignore
        return base

    def atom(self, items):
        if not items:
            return None
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
                from opendxa.dana.parser.ast import DictLiteral, SetLiteral, TupleLiteral

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
            return LiteralExpression(value=item)
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
        from opendxa.dana.parser.ast import TupleLiteral

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
        from opendxa.dana.parser.ast import DictLiteral

        return DictLiteral(items=pairs)

    def set(self, items):
        flat_items = self.flatten_items(items)
        from opendxa.dana.parser.ast import SetLiteral

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

        In grammar terms, a 'trailer' is a construct that follows an atom (primary expression) and modifies or extends it.
        In DANA (and Python-like languages), a trailer can be:
            - a function call: ( ... )
            - an index: [ ... ]
            - an attribute access: .NAME
        Multiple trailers can be chained, and each is applied in sequence to the result of the previous one.

        Examples:
            foo(1, 2)         -> FunctionCall(name='foo', args={...})
            foo.bar           -> AttributeAccess(object=foo, attribute='bar')
            foo[0]            -> SubscriptExpression(object=foo, index=0)
            foo.bar(1)[2]     -> SubscriptExpression(
                                    object=FunctionCall(
                                        name='bar',
                                        args={...},
                                        # called on AttributeAccess(object=foo, attribute='bar')
                                    ),
                                    index=2
                                )
        The method processes each trailer (call, attribute, or index) in order, so chained calls like foo.bar()[0] are handled correctly.
        """
        base = items[0]
        from typing import cast

        for trailer_item in items[1:]:
            if isinstance(trailer_item, Tree):
                if trailer_item.data == "arguments":
                    # Function call
                    args = [self.expression([arg]) for arg in trailer_item.children]
                    base = FunctionCall(name=base.name if hasattr(base, "name") else str(base), args={"__positional": args})
                elif trailer_item.data == "expr":
                    # Indexing
                    index = self.expression([trailer_item.children[0]])
                    index_expr = cast(Expression, index)
                    base = SubscriptExpression(object=base, index=index_expr)
                elif trailer_item.data == "NAME":
                    # Attribute access
                    base = AttributeAccess(object=base, attribute=trailer_item.children[0].value)
            elif isinstance(trailer_item, Token):
                # Attribute access
                base = AttributeAccess(object=base, attribute=trailer_item.value)
        return base

    def key_value_pair(self, items):
        # Always return a (key, value) tuple
        key = self.expression([items[0]])
        value = self.expression([items[1]])
        return (key, value)

    def expr(self, items):
        # Delegate to the main expression handler
        return self.expression(items)
