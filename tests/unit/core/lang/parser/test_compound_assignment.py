"""
Test compound assignment operators in Dana.

This module tests the parsing, transformation, and execution of compound
assignment operators (+=, -=, *=, /=).

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import pytest

from dana.core.lang.ast import CompoundAssignment, Identifier, AttributeAccess, SubscriptExpression
from dana.core.lang.interpreter import DanaInterpreter
from dana.core.lang.parser import DanaParser
from dana.core.lang.sandbox_context import SandboxContext
from dana.common.exceptions import SandboxError


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
        
        # Test with public scope
        ast = parser.parse("public:total *= 2")
        stmt = ast.statements[0]
        assert isinstance(stmt, CompoundAssignment)
        assert stmt.target.name == "public:total"

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
        
        # Test with nested attribute access
        ast = parser.parse("obj.nested.prop *= 3")
        stmt = ast.statements[0]
        assert isinstance(stmt, CompoundAssignment)
        assert isinstance(stmt.target, AttributeAccess)


class TestCompoundAssignmentExecution:
    """Test execution of compound assignment operators."""

    def test_execute_simple_compound_assignments(self):
        """Test executing simple compound assignments."""
        interpreter = DanaInterpreter()
        
        # Test += operator
        result = interpreter.run("""
x = 10
x += 5
x
""")
        assert result == 15
        
        # Test -= operator
        result = interpreter.run("""
y = 20
y -= 8
y
""")
        assert result == 12
        
        # Test *= operator
        result = interpreter.run("""
z = 6
z *= 3
z
""")
        assert result == 18
        
        # Test /= operator
        result = interpreter.run("""
w = 20
w /= 4
w
""")
        assert result == 5.0

    def test_execute_compound_assignments_with_expressions(self):
        """Test compound assignments with complex expressions."""
        interpreter = DanaInterpreter()
        
        # Test with expression on RHS
        result = interpreter.run("""
x = 10
y = 3
x += y * 2
x
""")
        assert result == 16
        
        # Test chained operations
        result = interpreter.run("""
a = 100
b = 20
c = 5
a -= b + c
a
""")
        assert result == 75

    def test_execute_compound_assignments_with_lists(self):
        """Test compound assignments with list elements."""
        interpreter = DanaInterpreter()
        
        result = interpreter.run("""
nums = [1, 2, 3, 4]
nums[0] += 10
nums[2] *= 3
nums
""")
        assert result == [11, 2, 9, 4]

    def test_execute_compound_assignments_with_dicts(self):
        """Test compound assignments with dictionary values."""
        interpreter = DanaInterpreter()
        
        result = interpreter.run("""
scores = {"alice": 100, "bob": 80}
scores["alice"] += 20
scores["bob"] -= 10
scores
""")
        assert result == {"alice": 120, "bob": 70}

    def test_execute_compound_assignments_with_strings(self):
        """Test compound assignments with string concatenation."""
        interpreter = DanaInterpreter()
        
        result = interpreter.run("""
msg = "Hello"
msg += " World"
msg
""")
        assert result == "Hello World"

    def test_compound_assignment_errors(self):
        """Test error handling in compound assignments."""
        interpreter = DanaInterpreter()
        
        # Test undefined variable
        with pytest.raises(SandboxError, match="Undefined variable"):
            interpreter.run("undefined_var += 5")
        
        # Test type mismatch
        with pytest.raises(SandboxError):
            interpreter.run("""
s = "hello"
s -= 5
""")
        
        # Test invalid index
        with pytest.raises(SandboxError):
            interpreter.run("""
arr = [1, 2, 3]
arr[10] += 1
""")

    def test_compound_assignments_return_value(self):
        """Test that compound assignments return the new value."""
        interpreter = DanaInterpreter()
        
        result = interpreter.run("""
x = 10
y = (x += 5)
y
""")
        assert result == 15
        
        # Verify x was also updated
        result = interpreter.run("x", reuse_context=True)
        assert result == 15

    def test_compound_assignments_with_floats(self):
        """Test compound assignments with floating point numbers."""
        interpreter = DanaInterpreter()
        
        result = interpreter.run("""
x = 10.5
x += 2.5
x
""")
        assert result == 13.0
        
        result = interpreter.run("""
y = 7.5
y *= 2
y
""")
        assert result == 15.0


class TestCompoundAssignmentIntegration:
    """Integration tests for compound assignments."""

    def test_compound_assignments_in_loops(self):
        """Test compound assignments inside loops."""
        interpreter = DanaInterpreter()
        
        result = interpreter.run("""
total = 0
for i in [1, 2, 3, 4, 5]:
    total += i
total
""")
        assert result == 15
        
        result = interpreter.run("""
product = 1
for n in [2, 3, 4]:
    product *= n
product
""")
        assert result == 24

    def test_compound_assignments_in_conditionals(self):
        """Test compound assignments in conditional blocks."""
        interpreter = DanaInterpreter()
        
        result = interpreter.run("""
x = 10
if x > 5:
    x += 20
else:
    x -= 5
x
""")
        assert result == 30

    def test_compound_assignments_with_functions(self):
        """Test compound assignments with function calls."""
        interpreter = DanaInterpreter()
        
        result = interpreter.run("""
def double(n):
    return n * 2

x = 5
x += double(3)
x
""")
        assert result == 11

    def test_nested_compound_assignments(self):
        """Test compound assignments with nested data structures."""
        interpreter = DanaInterpreter()
        
        result = interpreter.run("""
data = {"counts": [10, 20, 30]}
data["counts"][1] += 5
data
""")
        assert result == {"counts": [10, 25, 30]}


class TestCompoundAssignmentEdgeCases:
    """Test edge cases for compound assignments."""

    def test_compound_assignment_with_none(self):
        """Test compound assignments with None values."""
        interpreter = DanaInterpreter()
        
        # None should raise an error
        with pytest.raises(SandboxError):
            interpreter.run("""
x = none
x += 5
""")

    def test_compound_assignment_type_coercion(self):
        """Test type coercion in compound assignments."""
        interpreter = DanaInterpreter()
        
        # Int + float should work
        result = interpreter.run("""
x = 10
x += 2.5
x
""")
        assert result == 12.5
        
        # Float / int should work
        result = interpreter.run("""
y = 10.0
y /= 4
y
""")
        assert result == 2.5

    def test_compound_assignment_precedence(self):
        """Test operator precedence with compound assignments."""
        interpreter = DanaInterpreter()
        
        result = interpreter.run("""
x = 10
y = 2
x += y * 3  # Should be x += (y * 3), not (x += y) * 3
x
""")
        assert result == 16


if __name__ == "__main__":
    pytest.main([__file__, "-v"])