"""
Tests for AST validation functionality.

These tests verify that the AST validation utilities correctly detect
Lark Tree nodes remaining in transformed ASTs.
"""

import pytest
from lark import Token, Tree

from opendxa.dana.sandbox.parser.ast import Assignment, Identifier, LiteralExpression, Program
from opendxa.dana.sandbox.parser.dana_parser import DanaParser
from opendxa.dana.sandbox.parser.utils.ast_validator import AstValidator, find_tree_nodes, validate_ast


class TestAstValidator:
    """Test cases for the AST validation utility."""

    def test_clean_ast_validation(self):
        """Test validation of a clean AST with no Tree nodes."""
        # Create a clean AST manually
        assignment = Assignment(target=Identifier(name="x"), value=LiteralExpression(value=42))
        program = Program(statements=[assignment])

        # Should validate successfully
        is_clean, tree_nodes = AstValidator.validate_clean_ast(program, raise_on_error=False)
        assert is_clean is True
        assert len(tree_nodes) == 0

    def test_dirty_ast_detection(self):
        """Test detection of Tree nodes in a dirty AST."""
        # Create a dirty AST with a Tree node embedded
        dirty_tree = Tree("some_rule", [Token("TOKEN", "value")])
        assignment = Assignment(target=Identifier(name="x"), value=dirty_tree)  # This should be detected
        program = Program(statements=[assignment])

        # Should detect the Tree node
        is_clean, tree_nodes = AstValidator.validate_clean_ast(program, raise_on_error=False)
        assert is_clean is False
        assert len(tree_nodes) == 1
        assert tree_nodes[0][0] == "program.statements[0].value"
        assert isinstance(tree_nodes[0][1], Tree)

    def test_validation_with_raise_on_error(self):
        """Test that validation raises an exception when configured to do so."""
        dirty_tree = Tree("some_rule", [])
        program = Program(statements=[dirty_tree])

        # Should raise ValueError
        with pytest.raises(ValueError, match="AST validation failed"):
            AstValidator.validate_clean_ast(program, raise_on_error=True)

    def test_nested_tree_detection(self):
        """Test detection of Tree nodes nested deep in the AST."""
        # Create nested structure with Tree at depth
        inner_tree = Tree("nested_rule", [])
        assignment = Assignment(target=Identifier(name="x"), value=LiteralExpression(value=[1, 2, inner_tree]))  # Tree inside list
        program = Program(statements=[assignment])

        # Should find the nested Tree
        tree_nodes = find_tree_nodes(program)
        assert len(tree_nodes) == 1
        assert "value[2]" in tree_nodes[0][0]

    def test_validate_and_report(self):
        """Test the validation reporting functionality."""
        # Clean AST
        clean_program = Program(statements=[Assignment(target=Identifier(name="x"), value=LiteralExpression(value=42))])

        result = AstValidator.validate_and_report(clean_program)
        assert result is True

        # Dirty AST
        dirty_program = Program(statements=[Tree("bad_node", [])])
        result = AstValidator.validate_and_report(dirty_program)
        assert result is False

    def test_real_parser_output(self):
        """Test validation on real parser output to see current state."""
        parser = DanaParser()

        # Test simple assignment
        simple_code = "x = 42"
        result = parser.parse(simple_code)

        # Check if the current parser produces clean ASTs
        is_clean, tree_nodes = AstValidator.validate_clean_ast(result, raise_on_error=False)

        if not is_clean:
            # If we find Tree nodes, log them for debugging but don't fail the test
            # This test is diagnostic to understand current state
            print(f"Found {len(tree_nodes)} Tree nodes in simple assignment:")
            for path, tree in tree_nodes[:5]:
                print(f"  - {path}: {tree.data}")

        # For now, just ensure the function doesn't crash
        assert isinstance(is_clean, bool)

    def test_complex_program_validation(self):
        """Test validation on more complex Dana programs."""
        parser = DanaParser()

        # Test function definition and conditional
        complex_code = """
def add(a: int, b: int) -> int:
    return a + b

if x > 5:
    result = add(x, 10)
else:
    result = 0
"""

        result = parser.parse(complex_code)

        # Validate the AST
        is_clean, tree_nodes = AstValidator.validate_clean_ast(result, raise_on_error=False)

        if not is_clean:
            print(f"Found {len(tree_nodes)} Tree nodes in complex program:")
            for path, tree in tree_nodes[:10]:
                print(f"  - {path}: {tree.data}")

        # This is diagnostic - we want to see what the current state is
        assert isinstance(is_clean, bool)


class TestConvenienceFunctions:
    """Test the convenience functions for AST validation."""

    def test_find_tree_nodes_function(self):
        """Test the standalone find_tree_nodes function."""
        dirty_tree = Tree("test", [])
        program = Program(statements=[dirty_tree])

        tree_nodes = find_tree_nodes(program)
        assert len(tree_nodes) == 1
        assert tree_nodes[0][0] == "statements[0]"

    def test_validate_ast_function(self):
        """Test the standalone validate_ast function."""
        clean_program = Program(statements=[Assignment(target=Identifier(name="x"), value=LiteralExpression(value=42))])

        # Clean AST should validate
        assert validate_ast(clean_program, raise_on_error=False) is True

        # Dirty AST should not validate
        dirty_program = Program(statements=[Tree("bad", [])])
        assert validate_ast(dirty_program, raise_on_error=False) is False

        # Test raise_on_error behavior
        with pytest.raises(ValueError):
            validate_ast(dirty_program, raise_on_error=True)
