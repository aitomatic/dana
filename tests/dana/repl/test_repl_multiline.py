"""Test the multiline input support in the DANA REPL.

This module contains unit tests for the multiline input handling logic
in the DANA REPL implementation.
"""

import unittest

import pytest

from dana.repl.dana_repl_app import InputCompleteChecker


@pytest.mark.unit
class TestReplMultiline(unittest.TestCase):
    """Test the multiline input handling in the DANA REPL."""

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
        """Test that a complete if statement is recognized."""
        code = 'if temp.x > 10:\n    log.info("Greater than 10")'
        self.assertTrue(self.checker.is_complete(code))

    def test_incomplete_if_statement_without_body(self):
        """Test that an if statement without a body is recognized as incomplete."""
        code = "if temp.x > 10:"
        self.assertFalse(self.checker.is_complete(code))

    def test_incomplete_if_statement_without_indented_body(self):
        """Test that an if statement without an indented body is recognized as incomplete."""
        code = 'if temp.x > 10:\nlog.info("Greater than 10")'
        self.assertFalse(self.checker.is_complete(code))

    def test_complete_if_else_statement(self):
        """Test that a complete if-else statement is recognized."""
        code = 'if temp.x > 10:\n    log.info("Greater than 10")\nelse:\n    log.info("Less than or equal to 10")'
        self.assertTrue(self.checker.is_complete(code))

    def test_incomplete_if_else_statement(self):
        """Test that an incomplete if-else statement is recognized."""
        code = 'if temp.x > 10:\n    log.info("Greater than 10")\nelse:'
        self.assertFalse(self.checker.is_complete(code))

    def test_complete_while_loop(self):
        """Test that a complete while loop is recognized."""
        code = 'while temp.x < 10:\n    temp.x = temp.x + 1\n    log.info("Incrementing")'
        self.assertTrue(self.checker.is_complete(code))

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
        """Test that nested blocks are recognized correctly."""
        code = 'if temp.x > 10:\n    if temp.y > 20:\n        log.info("Both conditions met")\n    else:\n        log.info("Only first condition met")'
        self.assertTrue(self.checker.is_complete(code))

    def test_complex_multiline_statement(self):
        """Test a complex multiline statement."""
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
        self.assertTrue(self.checker.is_complete(code))


if __name__ == "__main__":
    unittest.main()
