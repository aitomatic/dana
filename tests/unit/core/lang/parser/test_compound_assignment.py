"""
Test compound assignment operators in Dana.

This module tests the parsing and basic execution of compound
assignment operators (+=, -=, *=, /=).

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import pytest

from dana.core.lang.ast import (
    AttributeAccess,
    CompoundAssignment,
    Identifier,
    SubscriptExpression,
)
from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter
from dana.core.lang.parser import DanaParser
from dana.core.lang.sandbox_context import SandboxContext


class TestCompoundAssignmentParsing:
    """Test parsing of compound assignment operators."""

    def test_parse_simple_compound_assignments(self):
        """Test parsing simple compound assignments."""
        parser = DanaParser()
        
        # Test += operator
        ast = parser.parse("x += 5")
        assert len(ast.statements) == 1
        stmt = ast.statements[0]
        assert isinstance(stmt, CompoundAssignment)
        assert isinstance(stmt.target, Identifier)
        assert stmt.target.name == "x"
        assert stmt.operator == "+="
        
        # Test -= operator
        ast = parser.parse("y -= 3")
        stmt = ast.statements[0]
        assert isinstance(stmt, CompoundAssignment)
        assert stmt.operator == "-="
        
        # Test *= operator
        ast = parser.parse("z *= 2")
        stmt = ast.statements[0]
        assert isinstance(stmt, CompoundAssignment)
        assert stmt.operator == "*="
        
        # Test /= operator
        ast = parser.parse("w /= 4")
        stmt = ast.statements[0]
        assert isinstance(stmt, CompoundAssignment)
        assert stmt.operator == "/="

    def test_parse_compound_assignments_with_scopes(self):
        """Test parsing compound assignments with scope prefixes."""
        parser = DanaParser()
        
        # Test with private scope
        ast = parser.parse("private:counter += 1")
        stmt = ast.statements[0]
        assert isinstance(stmt, CompoundAssignment)
        assert isinstance(stmt.target, Identifier)
        assert stmt.target.name == "private:counter"

    def test_parse_compound_assignments_complex_targets(self):
        """Test parsing compound assignments with complex targets."""
        parser = DanaParser()
        
        # Test with subscript
        ast = parser.parse("arr[0] += 10")
        stmt = ast.statements[0]
        assert isinstance(stmt, CompoundAssignment)
        assert isinstance(stmt.target, SubscriptExpression)
        
        # Test with attribute access
        ast = parser.parse("obj.value -= 5")
        stmt = ast.statements[0]
        assert isinstance(stmt, CompoundAssignment)
        assert isinstance(stmt.target, AttributeAccess)


class TestCompoundAssignmentExecution:
    """Test execution of compound assignment operators."""

    def test_execute_simple_compound_assignments(self):
        """Test executing simple compound assignments."""
        interpreter = DanaInterpreter()
        parser = DanaParser()
        
        # Test += operator
        context = SandboxContext()
        program = parser.parse("""
x = 10
x += 5
x
""")
        result = interpreter.execute_program(program, context)
        assert result == 15
        
        # Test -= operator
        context = SandboxContext()
        program = parser.parse("""
y = 20
y -= 8
y
""")
        result = interpreter.execute_program(program, context)
        assert result == 12
        
        # Test *= operator
        context = SandboxContext()
        program = parser.parse("""
z = 6
z *= 3
z
""")
        result = interpreter.execute_program(program, context)
        assert result == 18
        
        # Test /= operator
        context = SandboxContext()
        program = parser.parse("""
w = 20
w /= 4
w
""")
        result = interpreter.execute_program(program, context)
        assert result == 5.0

    def test_execute_compound_assignments_with_expressions(self):
        """Test compound assignments with complex expressions."""
        interpreter = DanaInterpreter()
        parser = DanaParser()
        
        # Test with expression on RHS
        context = SandboxContext()
        program = parser.parse("""
x = 10
y = 3
x += y * 2
x
""")
        result = interpreter.execute_program(program, context)
        assert result == 16


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 