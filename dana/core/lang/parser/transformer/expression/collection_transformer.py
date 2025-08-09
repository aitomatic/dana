"""
Collection transformer for Dana language parsing.

This module handles collection literals including:
- Lists ([1, 2, 3])
- Dictionaries ({"key": value})
- Sets ({1, 2, 3})
- Tuples ((1, 2, 3))
- Key-value pairs for dictionaries

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import cast

from lark import Token

from dana.core.lang.ast import (
    DictLiteral,
    Expression,
    ListLiteral,
    SetLiteral,
    TupleLiteral,
)
from dana.core.lang.parser.transformer.base_transformer import BaseTransformer


class CollectionTransformer(BaseTransformer):
    """Transformer for collection literals."""

    def _filter_comments(self, items):
        """Filter out COMMENT tokens from a list of items."""
        filtered = []
        for item in items:
            # Skip COMMENT tokens - they should not appear in final collections
            if isinstance(item, Token) and item.type == "COMMENT":
                continue
            filtered.append(item)
        return filtered

    def tuple(self, items):
        """Transform a tuple literal into a TupleLiteral AST node."""
        flat_items = self.flatten_items(items)
        # Ensure each item is properly cast to Expression type
        tuple_items: list[Expression] = []
        for item in flat_items:
            # Note: This requires the main expression transformer
            # We'll handle this in the integration phase
            tuple_items.append(cast(Expression, item))

        return TupleLiteral(items=tuple_items)

    def list(self, items):
        """Transform a list literal into a ListLiteral AST node."""
        flat_items = self.flatten_items(items)
        # Ensure each item is properly cast to Expression type
        list_items: list[Expression] = []
        for item in flat_items:
            # Note: This requires the main expression transformer
            # We'll handle this in the integration phase
            list_items.append(cast(Expression, item))

        return ListLiteral(items=list_items)

    def dict(self, items):
        """Transform a dictionary literal into a DictLiteral AST node."""
        flat_items = self.flatten_items(items)
        pairs = []
        for item in flat_items:
            if isinstance(item, tuple) and len(item) == 2:
                pairs.append(item)
            elif hasattr(item, "data") and item.data == "key_value_pair":
                pair = self.key_value_pair(item.children)
                pairs.append(pair)

        return DictLiteral(items=pairs)

    def set(self, items):
        """Transform a set literal into a SetLiteral AST node."""
        flat_items = self.flatten_items(items)
        # Ensure each item is properly cast to Expression type
        set_items: list[Expression] = []
        for item in flat_items:
            # Note: This requires the main expression transformer
            # We'll handle this in the integration phase
            set_items.append(cast(Expression, item))

        return SetLiteral(items=set_items)

    def key_value_pair(self, items):
        """Transform a key-value pair into a tuple of (key, value)."""
        # Filter out comments first
        filtered_items = self._filter_comments(items)
        # Always return a (key, value) tuple
        if len(filtered_items) >= 2:
            key = filtered_items[0]
            value = filtered_items[1]
            # Note: Both key and value require the main expression transformer
            # We'll handle this in the integration phase
            return (key, value)
        else:
            self.error(f"Invalid key-value pair: {filtered_items}")
            return (None, None)

    def list_items(self, items):
        """Transform list items rule."""
        flat_items = self.flatten_items(items)
        return self._filter_comments(flat_items)

    def dict_items(self, items):
        """Transform dict items rule."""
        flat_items = self.flatten_items(items)
        return self._filter_comments(flat_items)
