"""Base transformer class for Dana language parsing."""

from typing import Any

from lark import Token, Transformer, Tree

from dana.common.mixins.loggable import Loggable
from dana.core.lang.ast import ASTNode, Location
from dana.core.lang.parser.utils.parsing_utils import create_literal, parse_literal
from dana.core.lang.parser.utils.scope_utils import insert_local_scope
from dana.core.lang.parser.utils.transformer_utils import flatten_items as utils_flatten_items
from dana.core.lang.parser.utils.transformer_utils import get_leaf_node as utils_get_leaf_node
from dana.core.lang.parser.utils.transformer_utils import unwrap_single_child_tree as utils_unwrap_single
from dana.core.lang.parser.utils.tree_utils import TreeTraverser


class BaseTransformer(Loggable, Transformer):
    """Base class for Dana AST transformers.

    Provides common utility methods for transforming Lark parse trees into Dana AST nodes.
    """

    def __init__(self):
        """Initialize the transformer with tree traversal utilities."""
        super().__init__()
        # Create a TreeTraverser instance for tree traversal operations
        self.tree_traverser = TreeTraverser(transformer=self)
        self.current_filename = None  # Track current filename for error reporting

    def set_filename(self, filename: str | None) -> None:
        """Set the current filename for location tracking."""
        self.current_filename = filename

    def _parse_literal(self, text):
        """Parse a simple literal value from text or Token."""
        return parse_literal(text)

    def _create_literal(self, token):
        """Create a LiteralExpression node from a token."""
        return create_literal(token)

    def _insert_local_scope(self, parts: list[str] | str) -> Any:
        """Insert local scope prefix to parts if not already present."""
        return insert_local_scope(parts)

    @staticmethod
    def get_leaf_node(item: Tree | Token | ASTNode) -> Token | ASTNode:
        """Recursively unwrap a Tree until an AST node or token is reached."""
        return utils_get_leaf_node(item)

    def flatten_items(self, items):
        """
        Recursively flatten lists and Tree nodes, returning a flat list of AST nodes or tokens.
        Useful for collection and statement flattening.
        """
        return utils_flatten_items(items)

    def unwrap_single_child_tree(self, item, stop_at=None):
        """
        Recursively unwrap single-child Tree nodes, stopping at rule names in stop_at.
        If stop_at is None, unwrap all single-child Trees.

        This method delegates to the transformer_utils implementation for consistency.
        """
        return utils_unwrap_single(item, stop_at)

    def get_location(self, item: Any) -> tuple[int, int] | None:
        """Get line and column from a token or tree."""
        if hasattr(item, "line") and hasattr(item, "column"):
            return item.line, item.column
        if isinstance(item, list | tuple):
            for child in item:
                loc = self.get_location(child)
                if loc is not None:
                    return loc
        elif isinstance(item, Tree) and hasattr(item, "children"):
            for child in item.children:
                loc = self.get_location(child)
                if loc is not None:
                    return loc
        return None

    def create_location(self, item: Any) -> Location | None:
        """Create a Location object from a token or tree."""
        loc = self.get_location(item)
        if loc:
            line, column = loc
            # Use the current filename if available, otherwise empty string
            source = self.current_filename if self.current_filename else ""
            return Location(line=line, column=column, source=source)
        return None
