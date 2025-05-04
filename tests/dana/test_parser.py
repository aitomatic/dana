"""Unit tests for the DANA language parser."""

import os
import sys
import unittest
from typing import cast

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dana.language.ast import Assignment, Identifier, Literal, LiteralExpression, LogStatement, Program

from opendxa.dana.language.parser import ParseResult, parse


class TestParser(unittest.TestCase):
    """Test cases for the Parser class."""

    def setUp(self):
        """Set up a fresh parser for each test."""
        self.parser = parse  # Changed to use parse function

    def test_parse_assignment(self):
        """Test parsing a simple assignment statement."""
        source = "temp.x = 42"
        parse_result = self.parser(source)

        # Verify the structure of the parsed program
        self.assertIsInstance(parse_result, ParseResult)
        self.assertIsInstance(parse_result.program, Program)
        self.assertEqual(len(parse_result.program.statements), 1)
        self.assertIsNone(parse_result.error)

        # Check the assignment statement
        stmt = parse_result.program.statements[0]
        self.assertIsInstance(stmt, Assignment)
        assignment = cast(Assignment, stmt)
        self.assertIsInstance(assignment.target, Identifier)
        self.assertEqual(assignment.target.name, "temp.x")

        # Check the value expression
        self.assertIsInstance(assignment.value, LiteralExpression)
        self.assertIsInstance(assignment.value.literal, Literal)
        self.assertEqual(assignment.value.literal.value, 42)

    def test_parse_string_assignment(self):
        """Test parsing an assignment with a string literal."""
        source = 'temp.msg = "hello"'
        parse_result = self.parser(source)

        stmt = parse_result.program.statements[0]
        self.assertIsInstance(stmt, Assignment)
        assignment = cast(Assignment, stmt)
        self.assertEqual(assignment.target.name, "temp.msg")
        self.assertEqual(assignment.value.literal.value, "hello")

    def test_parse_log_statement(self):
        """Test parsing a log statement."""
        source = 'log("test message")'
        parse_result = self.parser(source)

        stmt = parse_result.program.statements[0]
        self.assertIsInstance(stmt, LogStatement)
        log_stmt = cast(LogStatement, stmt)
        self.assertIsInstance(log_stmt.message, LiteralExpression)
        self.assertEqual(log_stmt.message.literal.value, "test message")

    def test_parse_multiple_statements(self):
        """Test parsing multiple statements."""
        source = """
        temp.x = 10
        log("test")
        temp.y = 20
        """
        parse_result = self.parser(source)

        self.assertEqual(len(parse_result.program.statements), 3)

        # Check first assignment
        stmt1 = parse_result.program.statements[0]
        self.assertIsInstance(stmt1, Assignment)
        assignment1 = cast(Assignment, stmt1)
        self.assertEqual(assignment1.target.name, "temp.x")
        self.assertEqual(assignment1.value.literal.value, 10)

        # Check log statement
        stmt2 = parse_result.program.statements[1]
        self.assertIsInstance(stmt2, LogStatement)
        log_stmt = cast(LogStatement, stmt2)
        self.assertEqual(log_stmt.message.literal.value, "test")

        # Check second assignment
        stmt3 = parse_result.program.statements[2]
        self.assertIsInstance(stmt3, Assignment)
        assignment3 = cast(Assignment, stmt3)
        self.assertEqual(assignment3.target.name, "temp.y")
        self.assertEqual(assignment3.value.literal.value, 20)

    def test_parse_invalid_syntax(self):
        """Test parsing invalid syntax."""
        # Test missing value
        parse_result = self.parser("temp.x =")
        self.assertIsNotNone(parse_result.error)
        self.assertEqual(len(parse_result.program.statements), 0)

        # Test missing target
        parse_result = self.parser("= 42")
        self.assertIsNotNone(parse_result.error)
        self.assertEqual(len(parse_result.program.statements), 0)

        # Test missing equals sign
        parse_result = self.parser("temp.x 42")
        self.assertIsNotNone(parse_result.error)
        self.assertEqual(len(parse_result.program.statements), 0)


if __name__ == "__main__":
    unittest.main()
