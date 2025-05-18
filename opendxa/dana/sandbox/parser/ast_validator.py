"""AST validation utilities for DANA parser.

This module provides utilities for validating that ASTs produced by the parser
do not contain any remaining Lark Tree nodes that should have been transformed.
"""

from typing import List, Optional, Tuple, TypeVar, cast

from lark import Tree

from opendxa.common.mixins.loggable import Loggable
from opendxa.dana.sandbox.parser.ast import Program

# Type variable for generic AST node
AstNodeT = TypeVar("AstNodeT")


class AstValidator(Loggable):
    """Mixin for validating ASTs produced by the parser.

    This mixin can be used to add strict AST validation to the parser
    without modifying the existing implementation.
    """

    def validate_ast(self, ast: AstNodeT, strict: bool = False, max_nodes: int = 5) -> Tuple[bool, List[Tuple[List[str], Tree]]]:
        """
        Validate that an AST does not contain any remaining Lark Tree nodes.

        Args:
            ast: The AST to validate
            strict: If True, raise an exception if Tree nodes are found
            max_nodes: Maximum number of Tree nodes to report in warnings

        Returns:
            Tuple containing:
                - bool: True if the AST is valid (no Tree nodes), False otherwise
                - List: List of (path, tree_node) tuples for found Tree nodes

        Raises:
            TypeError: If strict=True and Tree nodes are found
        """
        from opendxa.dana.sandbox.parser.dana_parser import find_tree_nodes, strip_lark_trees

        tree_nodes = find_tree_nodes(ast)

        if tree_nodes:
            # Log warning about the found Tree nodes
            self.warning(f"Found {len(tree_nodes)} Lark Tree nodes in the AST after transformation:")
            for i, (path, tree) in enumerate(tree_nodes[:max_nodes]):
                path_str = "".join(path)
                self.warning(f"  {i+1}. Tree node at 'ast{path_str}' with data='{tree.data}'")

            if len(tree_nodes) > max_nodes:
                self.warning(f"  ... and {len(tree_nodes) - max_nodes} more Tree nodes")

            if strict:
                strip_lark_trees(ast)  # This will raise a TypeError

            return False, tree_nodes

        return True, []

    def transform_and_validate(self, parse_tree: Tree, transformer: Optional[object] = None, strict: bool = False) -> Program:
        """
        Transform a parse tree into an AST and validate it.

        This is a generic implementation that can be used by any parser.

        Args:
            parse_tree: The parse tree to transform
            transformer: The transformer to use (if None, uses self.transformer)
            strict: If True, raise an exception if Tree nodes are found

        Returns:
            The transformed and validated AST

        Raises:
            TypeError: If strict=True and Tree nodes are found
        """
        # Use the provided transformer or self.transformer
        actual_transformer = transformer or getattr(self, "transformer", None)
        if not actual_transformer:
            raise ValueError("No transformer available. Provide a transformer or ensure self.transformer exists.")

        # Transform the parse tree into AST nodes
        self.debug("Transforming parse tree to AST")
        ast = cast(Program, actual_transformer.transform(parse_tree))

        # Additional steps that might be performed by the parser
        if hasattr(self, "program_text"):
            ast.source_text = self.program_text

        self.debug(f"Successfully parsed program with {len(ast.statements)} statements")

        # Validate the AST
        is_valid, tree_nodes = self.validate_ast(ast, strict=strict)

        return ast


# Standalone functions for use without the mixin


def validate_ast(ast: AstNodeT, strict: bool = False) -> bool:
    """
    Utility function to validate an AST is free of Lark Tree nodes.

    Args:
        ast: The AST to validate
        strict: If True, raises an exception if Tree nodes are found
               If False, returns False if Tree nodes are found

    Returns:
        bool: True if the AST is valid (no Tree nodes), False otherwise
              (only when strict=False)

    Raises:
        TypeError: If strict=True and Tree nodes are found
    """
    from opendxa.dana.sandbox.parser.dana_parser import find_tree_nodes, strip_lark_trees

    tree_nodes = find_tree_nodes(ast)
    if tree_nodes:
        if strict:
            strip_lark_trees(ast)  # This will raise a TypeError
        return False
    return True
