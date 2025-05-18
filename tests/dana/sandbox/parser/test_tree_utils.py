"""Tests for the tree traversal utilities."""

import pytest
from lark import Token, Tree

from opendxa.dana.sandbox.parser.tree_utils import (
    TreeTraverser,
    extract_token_value,
    unwrap_single_child_tree,
)


# Helper function to create tokens for testing with proper type hints
def create_token(type_name: str, value: str) -> Token:
    """Create a token with proper type annotations for testing."""
    # This is safe for testing but bypasses type checking issues
    return Token(type_name, value)  # type: ignore


class SimpleTransformer:
    """A simple transformer for testing."""

    def __init__(self):
        self.transform_count = 0

    def expr(self, items):
        """Transform an expression node."""
        self.transform_count += 1
        return f"transformed_expr({','.join(str(i) for i in items)})"

    def NUMBER(self, token):
        """Transform a NUMBER token."""
        self.transform_count += 1
        return int(token.value) * 2  # Double numbers as a test


class TestTreeTraverser:
    """Tests for the TreeTraverser class."""

    @pytest.fixture
    def traverser(self):
        """Create a TreeTraverser instance."""
        return TreeTraverser()

    @pytest.fixture
    def transformer_traverser(self):
        """Create a TreeTraverser with a transformer."""
        transformer = SimpleTransformer()
        return TreeTraverser(transformer), transformer

    def test_unwrap_token_numeric(self, traverser):
        """Test unwrapping tokens with numeric values."""
        assert traverser.unwrap_token(create_token("NUMBER", "42")) == 42
        assert traverser.unwrap_token(create_token("FLOAT", "3.14")) == 3.14

    def test_unwrap_token_boolean_none(self, traverser):
        """Test unwrapping tokens with boolean or None values."""
        assert traverser.unwrap_token(create_token("BOOL", "true")) is True
        assert traverser.unwrap_token(create_token("BOOL", "false")) is False
        assert traverser.unwrap_token(create_token("NONE", "none")) is None

    def test_unwrap_token_string(self, traverser):
        """Test unwrapping tokens with string values."""
        assert traverser.unwrap_token(create_token("STRING", "hello")) == "hello"

    def test_unwrap_single_child_tree_simple(self, traverser):
        """Test unwrapping a simple tree with one child."""
        tree = Tree("expr", [create_token("NUMBER", "42")])  # type: ignore
        assert traverser.unwrap_single_child_tree(tree) == create_token("NUMBER", "42")

    def test_unwrap_single_child_tree_nested(self, traverser):
        """Test unwrapping a nested tree with single children."""
        number_token = create_token("NUMBER", "42")
        inner = Tree("term", [number_token])  # type: ignore
        middle = Tree("expr", [inner])
        outer = Tree("statement", [middle])
        assert traverser.unwrap_single_child_tree(outer) == number_token

    def test_unwrap_single_child_tree_multiple_children(self, traverser):
        """Test unwrapping a tree with multiple children (should not unwrap)."""
        tree = Tree("expr", [create_token("NUMBER", "1"), create_token("NUMBER", "2")])  # type: ignore
        assert traverser.unwrap_single_child_tree(tree) == tree

    def test_extract_from_tree_matching(self, traverser):
        """Test extracting children from a tree with matching rule name."""
        token1 = create_token("NUMBER", "1")
        token2 = create_token("NUMBER", "2")
        tree = Tree("expr", [token1, token2])  # type: ignore
        children = traverser.extract_from_tree(tree, "expr")
        assert children == [token1, token2]

    def test_extract_from_tree_non_matching(self, traverser):
        """Test extracting children from a tree with non-matching rule name."""
        tree = Tree("expr", [create_token("NUMBER", "1"), create_token("NUMBER", "2")])  # type: ignore
        assert traverser.extract_from_tree(tree, "term") is None

    def test_extract_from_tree_non_tree(self, traverser):
        """Test extracting children from a non-tree."""
        assert traverser.extract_from_tree(create_token("NUMBER", "42"), "expr") is None

    def test_transform_tree_simple(self, transformer_traverser):
        """Test transforming a simple tree."""
        traverser, transformer = transformer_traverser
        token1 = create_token("NUMBER", "1")
        token2 = create_token("NUMBER", "2")
        tree = Tree("expr", [token1, token2])  # type: ignore

        result = traverser.transform_tree(tree)
        assert result == "transformed_expr(2,4)"  # Numbers doubled by transformer
        assert transformer.transform_count == 3  # expr + 2 NUMBER tokens

    def test_transform_tree_custom_transformer(self, traverser):
        """Test transforming with a custom transformer function."""
        tree = Tree("expr", [create_token("NUMBER", "1"), create_token("NUMBER", "2")])  # type: ignore

        # Define a custom transformer function
        def custom_transform(node):
            if isinstance(node, Tree) and node.data == "expr":
                return "custom_transform"
            return node

        result = traverser.transform_tree(tree, custom_transform)
        assert result == "custom_transform"

    def test_transform_tree_exclude_rules(self, transformer_traverser):
        """Test transforming with excluded rules."""
        traverser, transformer = transformer_traverser
        tree = Tree("expr", [create_token("NUMBER", "1"), create_token("NUMBER", "2")])  # type: ignore

        # Exclude the 'expr' rule from transformation
        result = traverser.transform_tree(tree, exclude_rules=["expr"])

        # expr should be skipped, but NUMBER tokens should be transformed
        assert isinstance(result, Tree)
        assert result.data == "expr"
        assert result.children == [2, 4]  # Numbers doubled by transformer
        assert transformer.transform_count == 2  # Only the 2 NUMBER tokens

    def test_transform_tree_max_depth(self, traverser):
        """Test transforming with a max depth limit."""
        number_token = create_token("NUMBER", "42")
        inner = Tree("term", [number_token])  # type: ignore
        middle = Tree("expr", [inner])
        outer = Tree("statement", [middle])

        # Set max_depth to 1 to prevent recursion
        result = traverser.transform_tree(outer, max_depth=1)

        # Should only transform the outer level
        assert isinstance(result, Tree)
        assert result.data == "statement"
        assert len(result.children) == 1
        assert result.children[0] == middle  # Child should be unchanged

    def test_transform_tree_cycle_detection(self, traverser):
        """Test that cycles are properly detected and handled."""
        # Create a cyclic tree structure
        tree = Tree("expr", [])
        tree.children.append(tree)  # Self-reference creates a cycle

        # Should not cause infinite recursion
        result = traverser.transform_tree(tree)

        # Result should be the tree itself due to cycle detection
        assert result is tree

    def test_find_children_by_rule(self, traverser):
        """Test finding all children with a specific rule name."""
        expr1 = Tree("expr", [create_token("NUMBER", "1")])  # type: ignore
        expr2 = Tree("expr", [create_token("NUMBER", "2")])  # type: ignore
        term = Tree("term", [expr2])
        statement = Tree("statement", [expr1, term])

        exprs = traverser.find_children_by_rule(statement, "expr")
        assert len(exprs) == 2
        assert exprs[0] == expr1
        assert exprs[1] == expr2

    def test_get_rule_name(self, traverser):
        """Test getting the rule name of a tree."""
        tree = Tree("expr", [])
        assert traverser.get_rule_name(tree) == "expr"
        assert traverser.get_rule_name(create_token("NUMBER", "42")) is None

    def test_get_token_type(self, traverser):
        """Test getting the token type of a token."""
        token = create_token("NUMBER", "42")
        assert traverser.get_token_type(token) == "NUMBER"
        assert traverser.get_token_type(Tree("expr", [])) is None


def test_standalone_unwrap_single_child_tree():
    """Test the standalone unwrap_single_child_tree function."""
    number_token = create_token("NUMBER", "42")
    inner = Tree("term", [number_token])  # type: ignore
    middle = Tree("expr", [inner])
    outer = Tree("statement", [middle])
    assert unwrap_single_child_tree(outer) == number_token


def test_standalone_extract_token_value():
    """Test the standalone extract_token_value function."""
    assert extract_token_value(create_token("NUMBER", "42")) == 42
    assert extract_token_value(create_token("FLOAT", "3.14")) == 3.14
    assert extract_token_value(create_token("BOOL", "true")) is True
    assert extract_token_value(create_token("BOOL", "false")) is False
    assert extract_token_value(create_token("NONE", "none")) is None
    assert extract_token_value(create_token("STRING", "hello")) == "hello"
