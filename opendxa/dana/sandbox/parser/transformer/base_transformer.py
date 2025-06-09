"""Base transformer class for Dana language parsing."""

from typing import Any, Union

from lark import Token, Tree

from opendxa.common.mixins.loggable import Loggable
from opendxa.dana.sandbox.parser.ast import ASTNode, LiteralExpression
from opendxa.dana.sandbox.parser.utils.tree_utils import TreeTraverser
from opendxa.dana.sandbox.parser.utils.tree_utils import unwrap_single_child_tree as utils_unwrap
from opendxa.dana.sandbox.parser.utils.scope_utils import insert_local_scope
from opendxa.dana.sandbox.parser.utils.parsing_utils import parse_literal, create_literal
from opendxa.dana.sandbox.parser.utils.transformer_utils import (
    get_leaf_node as utils_get_leaf_node, 
    flatten_items as utils_flatten_items, 
    unwrap_single_child_tree as utils_unwrap_single
)


class BaseTransformer(Loggable):
    """Base class for Dana AST transformers.

    Provides common utility methods for transforming Lark parse trees into Dana AST nodes.
    """

    def __init__(self):
        """Initialize the transformer with tree traversal utilities."""
        super().__init__()
        # Create a TreeTraverser instance for tree traversal operations
        self.tree_traverser = TreeTraverser(transformer=self)

    def _parse_literal(self, text):
        """Parse a simple literal value from text or Token."""
        return parse_literal(text)

    def _create_literal(self, token):
        """Create a LiteralExpression node from a token."""
        return create_literal(token)

    def _insert_local_scope(self, parts: Union[list[str], str]) -> Any:
        """Insert local scope prefix to parts if not already present."""
        return insert_local_scope(parts)

    @staticmethod
    def get_leaf_node(item: Union[Tree, Token, ASTNode]) -> Union[Token, ASTNode]:
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

        This method now delegates to the transformer_utils implementation for consistency.
        """
        # For backward compatibility, handle stop_at parameter
        if stop_at:
            return utils_unwrap_single(item, stop_at)
        else:
            # Use the tree_utils implementation when no stop_at is provided
            return utils_unwrap(item)
