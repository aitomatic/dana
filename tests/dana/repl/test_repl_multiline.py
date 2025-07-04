"""Test the multiline input support in the Dana REPL.

This module contains unit tests for the multiline input handling logic
in the Dana REPL implementation.
"""

import unittest

import pytest

from dana.core.repl.repl.input.completeness_checker import InputCompleteChecker


@pytest.mark.unit
class TestReplMultiline(unittest.TestCase):
    """Test the multiline input handling in the Dana REPL."""

    def setUp(self):
        """Set up the test case."""
        self.checker = InputCompleteChecker()

    def test_complete_simple_statement(self):
        """Test that a simple complete statement is recognized."""
        code = "temp.x = 42"
        self.assertTrue(self.checker.is_complete(code))

    def test_incomplete_assignment(self):
        """Test that an incomplete assignment is recognized."""
        code = "temp.x = "
        self.assertFalse(self.checker.is_complete(code))

    def test_complete_if_statement(self):
        """Test that a complete if statement is still not considered input-complete (needs explicit ending)."""
        code = 'if temp.x > 10:\n    log.info("Greater than 10")'
        # With explicit ending, even syntactically complete multiline blocks
        # are not considered input-complete
        self.assertFalse(self.checker.is_complete(code))

    def test_incomplete_if_statement_without_body(self):
        """Test that an if statement without a body is recognized as incomplete."""
        code = "if temp.x > 10:"
        self.assertFalse(self.checker.is_complete(code))

    def test_incomplete_if_statement_without_indented_body(self):
        """Test that an if statement without an indented body is recognized as incomplete."""
        code = "if temp.x > 10:"
        self.assertFalse(self.checker.is_complete(code))

        # Even with body, multiline code is not considered input-complete
        code = 'if temp.x > 10:\nlog.info("Greater than 10")'
        self.assertFalse(self.checker.is_complete(code))

    def test_complete_if_else_statement(self):
        """Test that even complete if-else statements require explicit ending."""
        code = 'if temp.x > 10:\n    log.info("Greater than 10")\nelse:\n    log.info("Less than or equal to 10")'
        # With explicit ending, multiline blocks are not auto-completed
        self.assertFalse(self.checker.is_complete(code))

    def test_incomplete_if_else_statement(self):
        """Test that an incomplete if-else statement is recognized."""
        code = 'if temp.x > 10:\n    log.info("Greater than 10")\nelse:'
        self.assertFalse(self.checker.is_complete(code))

    def test_complete_while_loop(self):
        """Test that complete while loops require explicit ending."""
        code = 'while temp.x < 10:\n    temp.x = temp.x + 1\n    log.info("Incrementing")'
        # With explicit ending, multiline blocks are not auto-completed
        self.assertFalse(self.checker.is_complete(code))

    def test_incomplete_while_loop(self):
        """Test that an incomplete while loop is recognized."""
        code = "while temp.x < 10:"
        self.assertFalse(self.checker.is_complete(code))

    def test_balanced_parentheses(self):
        """Test that balanced parentheses are recognized as complete."""
        code = 'log.info("Value: " + str(temp.x * (2 + 3)))'
        self.assertTrue(self.checker.is_complete(code))

    def test_unbalanced_parentheses(self):
        """Test that unbalanced parentheses are recognized as incomplete."""
        code = 'log.info("Value: " + str(temp.x * (2 + 3)'
        self.assertFalse(self.checker.is_complete(code))

    def test_nested_blocks(self):
        """Test that nested blocks require explicit ending."""
        code = 'if temp.x > 10:\n    if temp.y > 20:\n        log.info("Both conditions met")\n    else:\n        log.info("Only first condition met")'
        # With explicit ending, even nested multiline blocks are not auto-completed
        self.assertFalse(self.checker.is_complete(code))

    def test_complex_multiline_statement(self):
        """Test that complex multiline statements require explicit ending."""
        code = """if temp.counter < 10:
    temp.counter = temp.counter + 1
    log.info("Counter: {temp.counter}")
    if temp.counter % 2 == 0:
        log.info("Even number")
    else:
        log.info("Odd number")
else:
    log.info("Counter reached limit")
    temp.counter = 0"""
        # With explicit ending, complex multiline blocks are not auto-completed
        self.assertFalse(self.checker.is_complete(code))

    def test_obviously_incomplete_detection(self):
        """Test the obviously incomplete detection logic."""
        # Test the obviously incomplete detection
        self.assertTrue(self.checker.is_obviously_incomplete("if local:a == 365:"))
        self.assertFalse(self.checker.is_obviously_incomplete("print(hello)"))
        self.assertFalse(self.checker.is_obviously_incomplete("local:x = 42"))

    def test_orphaned_else_detection(self):
        """Test orphaned else statement detection."""
        from dana.core.repl.repl.input.input_processor import InputProcessor

        processor = InputProcessor()

        # Test orphaned else detection
        self.assertTrue(processor.is_orphaned_else_statement("else:"))
        self.assertTrue(processor.is_orphaned_else_statement("elif x > 10:"))
        self.assertFalse(processor.is_orphaned_else_statement("if x > 10:"))


if __name__ == "__main__":
    unittest.main()
