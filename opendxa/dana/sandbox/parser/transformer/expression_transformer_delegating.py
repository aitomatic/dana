"""
Expression transformers for Dana language parsing.

This module provides expression transformers for the Dana language using the delegation pattern.
It delegates to specialized transformers for different expression types while maintaining
backward compatibility with the original interface.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any

from lark import Tree

from opendxa.dana.sandbox.parser.ast import (
    BinaryExpression,
    FunctionCall,
    Identifier,
    LiteralExpression,
)
from opendxa.dana.sandbox.parser.transformer.base_transformer import BaseTransformer
from opendxa.dana.sandbox.parser.transformer.expression.call_transformer import CallTransformer
from opendxa.dana.sandbox.parser.transformer.expression.collection_transformer import CollectionTransformer
from opendxa.dana.sandbox.parser.transformer.expression.literal_transformer import LiteralTransformer
from opendxa.dana.sandbox.parser.transformer.expression.operator_transformer import OperatorTransformer

ValidExprType = LiteralExpression | Identifier | BinaryExpression | FunctionCall


class ExpressionTransformer(BaseTransformer):
    """
    Transforms Lark parse trees for Dana expressions into AST nodes using delegation.

    This class maintains the original ExpressionTransformer interface while delegating
    to specialized transformers for different types of expressions. This improves
    maintainability and reduces complexity.
    """

    def __init__(self):
        """Initialize the expression transformer with specialized delegates."""
        super().__init__()

        # Create specialized transformers
        self._literal_transformer = LiteralTransformer()
        self._operator_transformer = OperatorTransformer()
        self._call_transformer = CallTransformer()
        self._collection_transformer = CollectionTransformer()

    def expression(self, items):
        """Main expression transformation entry point."""
        if not items:
            return None

        # Use TreeTraverser to unwrap single-child trees
        item = self.tree_traverser.unwrap_single_child_tree(items[0])

        # If it's a Tree, dispatch by rule name
        if isinstance(item, Tree):
            rule_name = getattr(item, "data", None)
            if isinstance(rule_name, str):
                # Try specialized transformers first
                for transformer in [
                    self._literal_transformer,
                    self._operator_transformer,
                    self._call_transformer,
                    self._collection_transformer,
                ]:
                    if hasattr(transformer, rule_name):
                        method = getattr(transformer, rule_name)
                        return method(item.children)

                # Fallback to general transformation
                method = getattr(self, rule_name, None)
                if method:
                    return method(item.children)

            # Fallback: General traverser with specialized transforms
            def custom_transformer(node: Any) -> Any:
                """Transform a tree node using the appropriate method."""
                if isinstance(node, Tree):
                    rule = getattr(node, "data", None)
                    if isinstance(rule, str):
                        # Try specialized transformers
                        for transformer in [
                            self._literal_transformer,
                            self._operator_transformer,
                            self._call_transformer,
                            self._collection_transformer,
                        ]:
                            if hasattr(transformer, rule):
                                method = getattr(transformer, rule)
                                return method(node.children)

                        # Try main transformer
                        transformer_method = getattr(self, rule, None)
                        if callable(transformer_method):
                            return transformer_method(node.children)
                return node

            return self.tree_traverser.walk_expression_tree(item, custom_transformer)

        # For non-Tree items, return as-is
        return item

    # Delegation methods for literals
    def literal(self, items):
        """Delegate to literal transformer."""
        return self._literal_transformer.literal(items)

    def atom(self, items):
        """Delegate to literal transformer."""
        return self._literal_transformer.atom(items)

    def string_literal(self, items):
        """Delegate to literal transformer."""
        return self._literal_transformer.string_literal(items)

    def identifier(self, items):
        """Delegate to literal transformer."""
        return self._literal_transformer.identifier(items)

    # Delegation methods for operators
    def or_expr(self, items):
        """Delegate to operator transformer."""
        return self._operator_transformer.or_expr(items)

    def and_expr(self, items):
        """Delegate to operator transformer."""
        return self._operator_transformer.and_expr(items)

    def pipe_expr(self, items):
        """Delegate to operator transformer."""
        return self._operator_transformer.pipe_expr(items)

    def not_expr(self, items):
        """Delegate to operator transformer."""
        return self._operator_transformer.not_expr(items)

    def comparison(self, items):
        """Delegate to operator transformer."""
        return self._operator_transformer.comparison(items)

    def sum_expr(self, items):
        """Delegate to operator transformer."""
        return self._operator_transformer.sum_expr(items)

    def term(self, items):
        """Delegate to operator transformer."""
        return self._operator_transformer.term(items)

    def factor(self, items):
        """Delegate to operator transformer."""
        return self._operator_transformer.factor(items)

    def power(self, items):
        """Delegate to operator transformer."""
        return self._operator_transformer.power(items)

    # Delegation methods for function calls and attribute access
    def trailer(self, items):
        """Delegate to call transformer, but need to handle expression resolution."""
        # The call transformer needs access to the main expression transformer
        # for processing arguments, so we need to patch it
        original_process_function_arguments = self._call_transformer._process_function_arguments

        def patched_process_function_arguments(arg_children):
            """Process function arguments using the main expression transformer."""
            args = []  # List of positional arguments
            kwargs = {}  # Dict of keyword arguments

            for arg_child in arg_children:
                # Check if this is a kw_arg tree
                if hasattr(arg_child, "data") and arg_child.data == "kw_arg":
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

        # Temporarily patch the method
        self._call_transformer._process_function_arguments = patched_process_function_arguments

        try:
            return self._call_transformer.trailer(items)
        finally:
            # Restore original method
            self._call_transformer._process_function_arguments = original_process_function_arguments

    def argument(self, items):
        """Delegate to call transformer."""
        return self._call_transformer.argument(items)

    def slice_or_index(self, items):
        """Delegate to call transformer for slice handling."""
        return self._call_transformer.slice_or_index(items)

    def slice_start_only(self, items):
        """Delegate to call transformer for slice_start_only handling."""
        return self._call_transformer.slice_start_only(items)

    def slice_stop_only(self, items):
        """Delegate to call transformer for slice_stop_only handling."""
        return self._call_transformer.slice_stop_only(items)

    def slice_start_stop(self, items):
        """Delegate to call transformer for slice_start_stop handling."""
        return self._call_transformer.slice_start_stop(items)

    def slice_start_stop_step(self, items):
        """Delegate to call transformer for slice_start_stop_step handling."""
        return self._call_transformer.slice_start_stop_step(items)

    def slice_all(self, items):
        """Delegate to call transformer for slice_all handling."""
        return self._call_transformer.slice_all(items)

    def slice_step_only(self, items):
        """Delegate to call transformer for slice_step_only handling."""
        return self._call_transformer.slice_step_only(items)

    def slice_expr(self, items):
        """Delegate to call transformer for slice_expr handling."""
        return self._call_transformer.slice_expr(items)

    def slice_list(self, items):
        """Delegate to call transformer for slice_list handling."""
        return self._call_transformer.slice_list(items)

    # Delegation methods for collections
    def tuple(self, items):
        """Delegate to collection transformer with expression resolution."""
        # Patch the collection transformer to use the main expression transformer

        def patched_tuple(items):
            flat_items = self._collection_transformer.flatten_items(items)
            tuple_items = []
            for item in flat_items:
                expr = self.expression([item])
                tuple_items.append(expr)

            from opendxa.dana.sandbox.parser.ast import TupleLiteral

            return TupleLiteral(items=tuple_items)

        return patched_tuple(items)

    def list(self, items):
        """Delegate to collection transformer with expression resolution."""
        flat_items = self._collection_transformer.flatten_items(items)
        list_items = []
        for item in flat_items:
            expr = self.expression([item])
            list_items.append(expr)

        from opendxa.dana.sandbox.parser.ast import ListLiteral

        return ListLiteral(items=list_items)

    def dict(self, items):
        """Delegate to collection transformer with expression resolution."""
        flat_items = self._collection_transformer.flatten_items(items)
        pairs = []
        for item in flat_items:
            if isinstance(item, tuple) and len(item) == 2:
                # Process both key and value
                key = self.expression([item[0]])
                value = self.expression([item[1]])
                pairs.append((key, value))
            elif hasattr(item, "data") and item.data == "key_value_pair":
                pair = self.key_value_pair(item.children)
                pairs.append(pair)

        from opendxa.dana.sandbox.parser.ast import DictLiteral

        return DictLiteral(items=pairs)

    def set(self, items):
        """Delegate to collection transformer with expression resolution."""
        flat_items = self._collection_transformer.flatten_items(items)
        set_items = []
        for item in flat_items:
            expr = self.expression([item])
            set_items.append(expr)

        from opendxa.dana.sandbox.parser.ast import SetLiteral

        return SetLiteral(items=set_items)

    def key_value_pair(self, items):
        """Delegate to collection transformer with expression resolution."""
        if len(items) >= 2:
            key = self.expression([items[0]])
            value = self.expression([items[1]])
            return (key, value)
        else:
            self.error(f"Invalid key-value pair: {items}")
            return (None, None)

    # Token delegation methods (delegate to appropriate transformers)
    def TRUE(self, token):
        """Delegate to literal transformer."""
        return self._literal_transformer.TRUE(token)

    def FALSE(self, token):
        """Delegate to literal transformer."""
        return self._literal_transformer.FALSE(token)

    def NONE(self, token):
        """Delegate to literal transformer."""
        return self._literal_transformer.NONE(token)

    def NUMBER(self, token):
        """Delegate to literal transformer."""
        return self._literal_transformer.NUMBER(token)

    def REGULAR_STRING(self, token):
        """Delegate to literal transformer."""
        return self._literal_transformer.REGULAR_STRING(token)

    def ADD(self, token):
        """Delegate to operator transformer."""
        return self._operator_transformer.ADD(token)

    def SUB(self, token):
        """Delegate to operator transformer."""
        return self._operator_transformer.SUB(token)

    def MUL(self, token):
        """Delegate to operator transformer."""
        return self._operator_transformer.MUL(token)

    def DIV(self, token):
        """Delegate to operator transformer."""
        return self._operator_transformer.DIV(token)

    def MOD(self, token):
        """Delegate to operator transformer."""
        return self._operator_transformer.MOD(token)

    def POW(self, token):
        """Delegate to operator transformer."""
        return self._operator_transformer.POW(token)

    # Support methods that need to be accessible from specialized transformers
    def _process_function_arguments(self, arg_children):
        """Process function call arguments, handling both positional and keyword arguments."""
        args = []  # List of positional arguments
        kwargs = {}  # Dict of keyword arguments

        for arg_child in arg_children:
            # Check if this is a kw_arg tree
            if hasattr(arg_child, "data") and arg_child.data == "kw_arg":
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
