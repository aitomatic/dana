"""Base transformer class for DANA language parsing."""

from typing import Any, Union

from lark import Token, Tree

from opendxa.common.mixins.loggable import Loggable
from opendxa.dana.common.exceptions import ParseError
from opendxa.dana.sandbox.parser.ast import ASTNode, LiteralExpression
from opendxa.dana.sandbox.parser.utils.tree_utils import TreeTraverser
from opendxa.dana.sandbox.parser.utils.tree_utils import unwrap_single_child_tree as utils_unwrap


class BaseTransformer(Loggable):
    """Base class for DANA AST transformers.

    Provides common utility methods for transforming Lark parse trees into DANA AST nodes.
    """

    def __init__(self):
        """Initialize the transformer with tree traversal utilities."""
        super().__init__()
        # Create a TreeTraverser instance for tree traversal operations
        self.tree_traverser = TreeTraverser(transformer=self)

    def _parse_literal(self, text):
        """Parse a simple literal value from text or Token."""
        from lark import Token

        # Unwrap Token to its value
        if isinstance(text, Token):
            text = text.value
        if isinstance(text, str):
            text = text.strip()

        # Try numbers first
        try:
            if isinstance(text, str) and "." in text:
                return LiteralExpression(value=float(text))
            elif isinstance(text, str):
                return LiteralExpression(value=int(text))
            elif isinstance(text, (int, float)):
                return LiteralExpression(value=text)
        except ValueError:
            pass

        # Try boolean
        if isinstance(text, str):
            if text.lower() == "true":
                return LiteralExpression(value=True)
            elif text.lower() == "false":
                return LiteralExpression(value=False)

        # Try string (with quotes)
        if isinstance(text, str) and ((text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'"))):
            return LiteralExpression(value=text[1:-1])

        # Default to string
        return LiteralExpression(value=text)

    def _create_literal(self, token):
        """Create a LiteralExpression node from a token."""
        token_type = token.type
        value = token.value

        if token_type == "STRING":
            # Remove quotes (either single or double)
            if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            return LiteralExpression(value=value)
        elif token_type == "NUMBER":
            # Check if it's an integer or float
            if "." in value:
                return LiteralExpression(value=float(value))
            else:
                return LiteralExpression(value=int(value))
        elif token_type == "BOOL":
            return LiteralExpression(value=value.lower() == "true")
        elif value == "null":
            return LiteralExpression(value=None)

        # Fallback
        return LiteralExpression(value=value)

    def _insert_local_scope(self, parts: Union[list[str], str]) -> Any:
        """Insert local scope prefix to parts if not already present."""
        if isinstance(parts, str):
            if "." in parts:
                raise ParseError(f"Local variable must be a simple name: {parts}")
            return f"local.{parts}"
        elif isinstance(parts, list):
            if len(parts) == 0:
                raise ParseError("No local variable name provided")
            elif len(parts) > 1:
                # For nested identifiers, keep as is
                return parts
            else:
                parts.insert(0, "local")
                return parts
        else:
            raise ParseError(f"Invalid type for local variable: {type(parts)}")

    @staticmethod
    def get_leaf_node(item: Union[Tree, Token, ASTNode]) -> Union[Token, ASTNode]:
        """Recursively unwrap a Tree until an AST node or token is reached."""
        while hasattr(item, "children") and len(item.children) == 1:
            item = item.children[0]
        return item  # type: ignore

    def flatten_items(self, items):
        """
        Recursively flatten lists and Tree nodes, returning a flat list of AST nodes or tokens.
        Useful for collection and statement flattening.
        """
        from lark import Tree

        flat = []
        for item in items:
            if isinstance(item, list):
                flat.extend(self.flatten_items(item))
            elif isinstance(item, Tree) and hasattr(item, "children"):
                flat.extend(self.flatten_items(item.children))
            elif item is not None:
                flat.append(item)
        return flat

    def unwrap_single_child_tree(self, item, stop_at=None):
        """
        Recursively unwrap single-child Tree nodes, stopping at rule names in stop_at.
        If stop_at is None, unwrap all single-child Trees.

        This method now delegates to the tree_utils implementation for consistency.
        """
        from lark import Tree

        # For backward compatibility, handle stop_at parameter
        if stop_at:
            stop_at = stop_at or set()
            # Use the old implementation if stop_at is provided
            while isinstance(item, Tree) and len(item.children) == 1 and getattr(item, "data", None) not in stop_at:
                item = item.children[0]
            return item
        else:
            # Use the new implementation from tree_utils
            return utils_unwrap(item)
