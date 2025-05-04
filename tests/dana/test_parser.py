"""Unit tests for the DANA language parser."""

import unittest
import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from opendxa.dana.language.parser import parse
from opendxa.dana.language.ast import (
    Program,
    Assignment,
    Identifier,
    LiteralExpression,
    Literal
)
from opendxa.dana.exceptions import ParseError

class TestParser(unittest.TestCase):
    """Test cases for the Parser class."""

    def setUp(self):
        """Set up a fresh parser for each test."""
        self.parser = parse  # Changed to use parse function

    def test_parse_assignment(self):
        """Test parsing a simple assignment statement."""
        source = "temp.x = 42"
        program = self.parser(source)
        
        # Verify the structure of the parsed program
        self.assertIsInstance(program, Program)
        self.assertEqual(len(program.statements), 1)
        
        # Check the assignment statement
        stmt = program.statements[0]
        self.assertIsInstance(stmt, Assignment)
        self.assertIsInstance(stmt.target, Identifier)
        self.assertEqual(stmt.target.name, "temp.x")
        
        # Check the value expression
        self.assertIsInstance(stmt.value, LiteralExpression)
        self.assertIsInstance(stmt.value.literal, Literal)
        self.assertEqual(stmt.value.literal.value, 42)

    def test_parse_string_assignment(self):
        """Test parsing an assignment with a string literal."""
        source = 'temp.msg = "hello"'
        program = self.parser(source)
        
        stmt = program.statements[0]
        self.assertEqual(stmt.target.name, "temp.msg")
        self.assertEqual(stmt.value.literal.value, "hello")

    def test_parse_multiple_statements(self):
        """Test parsing multiple statements."""
        source = """
        temp.x = 10
        temp.y = 20
        """
        program = self.parser(source)
        
        self.assertEqual(len(program.statements), 2)
        self.assertEqual(program.statements[0].target.name, "temp.x")
        self.assertEqual(program.statements[0].value.literal.value, 10)
        self.assertEqual(program.statements[1].target.name, "temp.y")
        self.assertEqual(program.statements[1].value.literal.value, 20)

    def test_parse_invalid_syntax(self):
        """Test parsing invalid syntax."""
        with self.assertRaises(ParseError):
            self.parser("temp.x =")  # Missing value
        with self.assertRaises(ParseError):
            self.parser("= 42")      # Missing target
        with self.assertRaises(ParseError):
            self.parser("temp.x 42")  # Missing equals sign

if __name__ == '__main__':
    unittest.main() 