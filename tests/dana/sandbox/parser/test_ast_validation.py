"""Tests for AST validation after transformation.

This module demonstrates a more principled approach to AST validation,
ensuring that no Lark Tree nodes remain in the transformed AST.
"""

from typing import Any, List

import pytest
from lark import Tree

from opendxa.dana.sandbox.parser.ast import Assignment, Identifier, LiteralExpression, Program
from opendxa.dana.sandbox.parser.dana_parser import DanaParser, find_tree_nodes
from opendxa.dana.sandbox.parser.strict_dana_parser import StrictDanaParser, create_parser


# Safer version of strip_lark_trees that avoids infinite recursion
def safe_strip_lark_trees(node, visited=None, max_depth=100):
    """Recursively walk the AST and raise if any Lark Tree nodes are found."""
    if visited is None:
        visited = set()

    # Avoid infinite recursion by tracking visited objects
    obj_id = id(node)
    if obj_id in visited or max_depth <= 0:
        return node
    visited.add(obj_id)

    if isinstance(node, Tree):
        raise TypeError(f"Lark Tree node found in AST after transformation: {node.data}")
    elif isinstance(node, list):
        for item in node:
            safe_strip_lark_trees(item, visited, max_depth - 1)
    elif isinstance(node, dict):
        for v in node.values():
            safe_strip_lark_trees(v, visited, max_depth - 1)
    elif hasattr(node, "__dict__"):
        for k, v in vars(node).items():
            # Skip private attributes to avoid potential cycles in test objects
            if not k.startswith("_"):
                safe_strip_lark_trees(v, visited, max_depth - 1)
    # else: primitive, fine
    return node


# Special class for testing purposes only - inserts a Tree node
class MalformedLiteral(LiteralExpression):
    """A modified LiteralExpression that contains a Tree node for testing validation."""

    def __init__(self, tree_node: Tree):
        """Initialize with a Tree node as a public attribute."""
        super().__init__(value="tree_container")
        self.tree_node = tree_node  # Public attribute with a Tree node

    def __repr__(self):
        """String representation for debug purposes."""
        return f"MalformedLiteral(tree_node={self.tree_node})"


# Helper class for testing - creates a mocked AST with Tree nodes for validation testing
class TestASTFactory:
    """Factory for creating AST structures with embedded Lark Tree nodes for testing."""

    @staticmethod
    def create_tree_node(data: str, children: List[Any]) -> Tree:
        """Create a Lark Tree node for testing."""
        return Tree(data, children)

    @staticmethod
    def create_program_with_tree() -> Program:
        """Create a Program with a Tree node embedded in a custom Expression."""
        # Create a tree node
        tree = Tree("test", ["value"])

        # Put it in our custom literal that holds a Tree node
        malformed_literal = MalformedLiteral(tree)

        # Create a proper AST structure that incorporates our malformed literal
        target = Identifier(name="local.x")
        assignment = Assignment(target=target, value=malformed_literal)
        return Program(statements=[assignment])


class TestAstValidation:
    """Tests for ensuring AST is free of Lark Tree nodes after transformation."""

    @pytest.fixture
    def parser(self):
        """Create a fresh parser instance for each test."""
        return DanaParser()

    @pytest.fixture
    def strict_parser(self):
        """Create a fresh strict parser instance for each test."""
        return StrictDanaParser(strict_validation=True)

    def test_basic_ast_validation(self, parser):
        """Test that basic ASTs are properly transformed with no Lark nodes."""
        programs = [
            "private:x = 5",
            "if 1 > 2:\n    private:x = 3",
            "def test(x, y):\n    return x + y",
            "while True:\n    break",
            "for i in [1, 2, 3]:\n    private:x = i",
        ]

        for program in programs:
            ast = parser.parse(program)

            # Verify that find_tree_nodes finds no Lark Tree nodes
            tree_nodes = find_tree_nodes(ast)
            assert len(tree_nodes) == 0, f"Found {len(tree_nodes)} Lark Tree nodes in: {program}"

            # Verify that our safe version of strip_lark_trees doesn't raise an exception
            try:
                safe_strip_lark_trees(ast)
            except TypeError as e:
                pytest.fail(f"safe_strip_lark_trees raised an exception for program '{program}': {e}")

    def test_strip_lark_trees_functionality(self):
        """Test that strip_lark_trees correctly identifies Tree nodes."""
        # Create a test program with an embedded Tree node
        ast = TestASTFactory.create_program_with_tree()

        # Verify that our safe version of strip_lark_trees raises an exception
        with pytest.raises(TypeError) as exc_info:
            safe_strip_lark_trees(ast)

        # The exception should mention 'test' which is the data attribute of our Tree
        assert "test" in str(exc_info.value)

        # find_tree_nodes should find our Tree node
        tree_nodes = find_tree_nodes(ast)
        assert len(tree_nodes) == 1
        assert tree_nodes[0][1].data == "test"

    def test_strict_parser_validation(self, strict_parser):
        """Test that the StrictDanaParser correctly validates ASTs."""
        # Valid program should parse successfully
        valid_program = "private:x = 5"
        ast = strict_parser.parse(valid_program)
        assert isinstance(ast, Program)

        # Create a Program with a Tree node embedded for testing
        program_with_tree = TestASTFactory.create_program_with_tree()

        # The strict parser should raise an exception when validating this AST
        with pytest.raises(TypeError) as exc_info:
            strict_parser.validate_ast(program_with_tree, strict=True)

        # The exception should mention 'test'
        assert "test" in str(exc_info.value)

    def test_strict_parser_temporarily_disable(self):
        """Test that we can temporarily disable strict validation."""
        # Create a strict parser
        parser = StrictDanaParser(strict_validation=True)

        # Create a valid program
        valid_program = "private:x = 5"

        # Should parse successfully
        ast1 = parser.parse(valid_program)
        assert isinstance(ast1, Program)

        # Create a program with a Tree node embedded for testing
        program_with_tree = TestASTFactory.create_program_with_tree()

        # The parser should raise an exception in strict mode
        with pytest.raises(TypeError):
            # This will validate and raise an exception because of the Tree node
            parser.validate_ast(program_with_tree, strict=True)

        # But should not raise an exception if we temporarily disable strict mode
        result, nodes = parser.validate_ast(program_with_tree, strict=False)
        assert result is False
        assert len(nodes) == 1

    def test_parser_factory_function(self):
        """Test the create_parser factory function."""
        # Create a regular parser
        regular_parser = create_parser(strict=False)
        assert isinstance(regular_parser, DanaParser)
        assert not isinstance(regular_parser, StrictDanaParser)

        # Create a strict parser
        strict_parser = create_parser(strict=True)
        assert isinstance(strict_parser, StrictDanaParser)

        # Both should parse valid programs
        valid_program = "private:x = 5"
        assert isinstance(regular_parser.parse(valid_program), Program)
        assert isinstance(strict_parser.parse(valid_program), Program)


def validate_ast(ast, strict=False):
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
    tree_nodes = find_tree_nodes(ast)
    if tree_nodes:
        if strict:
            safe_strip_lark_trees(ast)  # Use our safer version
        return False
    return True
