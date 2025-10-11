#
# Copyright © 2025 Aitomatic, Inc.
#
# This source code is licensed under the license found in the LICENSE file in the root directory of this source tree
#

"""
Tests for elif chain handling in the Dana parser.
These tests specifically verify the correct nesting of multiple elif statements.
"""

import textwrap

import pytest

from dana.core.lang.ast import BinaryOperator, Conditional
from dana.core.lang.parser.utils.parsing_utils import ParserCache


@pytest.fixture
def parser():
    """Get Dana parser instance."""
    return ParserCache.get_parser("dana")


def get_conditional(program):
    """Extract the first conditional statement from a program."""
    for stmt in program.statements:
        if isinstance(stmt, Conditional):
            return stmt
    raise AssertionError("No Conditional found in program")


def assert_nested_conditional_structure(conditional, expected_conditions):
    """
    Assert that a nested conditional structure matches expected conditions.

    Args:
        conditional: The root Conditional node
        expected_conditions: List of expected condition values (e.g., ['> 0', '< 0', '== 5'])
    """
    current = conditional
    for i, expected_cond in enumerate(expected_conditions):
        assert isinstance(current, Conditional), f"Expected Conditional at level {i}, got {type(current)}"

        # Check the condition (simplified - just check operator for now)
        if ">" in expected_cond:
            assert current.condition.operator == BinaryOperator.GREATER_THAN
        elif "<" in expected_cond:
            assert current.condition.operator == BinaryOperator.LESS_THAN
        elif "==" in expected_cond:
            assert current.condition.operator == BinaryOperator.EQUALS

        # Move to the next level (should be in else_body)
        if i < len(expected_conditions) - 1:
            assert isinstance(current.else_body, list), f"Expected list else_body at level {i}"
            assert len(current.else_body) == 1, f"Expected single item in else_body at level {i}"
            current = current.else_body[0]


def test_three_elif_chain_no_else(parser):
    """Test a chain of 3 elif statements without a final else."""
    code = textwrap.dedent("""
        x = 0
        if x > 10:
            y = "high"
        elif x > 5:
            y = "medium"
        elif x > 0:
            y = "low"
        elif x == 0:
            y = "zero"
    """)

    program = parser.parse(code, do_transform=True)
    conditional = get_conditional(program)

    # Verify the structure: if -> elif -> elif -> elif
    assert_nested_conditional_structure(conditional, ["> 10", "> 5", "> 0", "== 0"])

    # The deepest elif should have an empty else_body
    current = conditional
    while isinstance(current.else_body, list) and current.else_body and isinstance(current.else_body[0], Conditional):
        current = current.else_body[0]
    assert current.else_body == []


def test_three_elif_chain_with_else(parser):
    """Test a chain of 3 elif statements with a final else."""
    code = textwrap.dedent("""
        x = 0
        if x > 10:
            y = "high"
        elif x > 5:
            y = "medium"
        elif x > 0:
            y = "low"
        elif x == 0:
            y = "zero"
        else:
            y = "negative"
    """)

    program = parser.parse(code, do_transform=True)
    conditional = get_conditional(program)

    # Verify the structure: if -> elif -> elif -> elif -> else
    assert_nested_conditional_structure(conditional, ["> 10", "> 5", "> 0", "== 0"])

    # The deepest elif should have a non-empty else_body (the final else block)
    current = conditional
    while isinstance(current.else_body, list) and current.else_body and isinstance(current.else_body[0], Conditional):
        current = current.else_body[0]

    # The final else block should contain statements, not another Conditional
    assert isinstance(current.else_body, list)
    assert len(current.else_body) > 0
    assert not isinstance(current.else_body[0], Conditional)


def test_five_elif_chain_no_else(parser):
    """Test a longer chain of 5 elif statements without a final else."""
    code = textwrap.dedent("""
        score = 85
        if score >= 90:
            grade = "A"
        elif score >= 80:
            grade = "B"
        elif score >= 70:
            grade = "C"
        elif score >= 60:
            grade = "D"
        elif score >= 50:
            grade = "E"
        elif score >= 0:
            grade = "F"
    """)

    program = parser.parse(code, do_transform=True)
    conditional = get_conditional(program)

    # Verify we have the correct nesting depth
    depth = 0
    current = conditional
    while True:
        depth += 1
        if not (isinstance(current.else_body, list) and current.else_body and isinstance(current.else_body[0], Conditional)):
            break
        current = current.else_body[0]

    assert depth == 6, f"Expected depth of 6 (if + 5 elif), got {depth}"

    # The deepest elif should have an empty else_body
    assert current.else_body == []


def test_five_elif_chain_with_else(parser):
    """Test a longer chain of 5 elif statements with a final else."""
    code = textwrap.dedent("""
        score = 85
        if score >= 90:
            grade = "A"
        elif score >= 80:
            grade = "B"
        elif score >= 70:
            grade = "C"
        elif score >= 60:
            grade = "D"
        elif score >= 50:
            grade = "E"
        elif score >= 0:
            grade = "F"
        else:
            grade = "Invalid"
    """)

    program = parser.parse(code, do_transform=True)
    conditional = get_conditional(program)

    # Verify we have the correct nesting depth
    depth = 0
    current = conditional
    while isinstance(current.else_body, list) and current.else_body and isinstance(current.else_body[0], Conditional):
        depth += 1
        current = current.else_body[0]

    assert depth == 5, f"Expected depth of 5 elif levels, got {depth}"

    # The deepest elif should have a non-empty else_body (the final else block)
    assert isinstance(current.else_body, list)
    assert len(current.else_body) > 0
    assert not isinstance(current.else_body[0], Conditional)


def test_elif_chain_with_complex_conditions(parser):
    """Test elif chain with more complex conditions and bodies."""
    code = textwrap.dedent("""
        x = 5
        y = 10
        if x > 10 and y > 20:
            result = x + y
            log("high values")
        elif x > 5 or y > 15:
            result = x * y
            log("medium values")
        elif x == 5:
            result = x
            log("x is five")
        else:
            result = 0
            log("default case")
    """)

    program = parser.parse(code, do_transform=True)
    conditional = get_conditional(program)

    # Check that each body has multiple statements
    assert len(conditional.body) == 2  # result assignment + log call

    # Navigate to first elif
    first_elif = conditional.else_body[0]
    assert isinstance(first_elif, Conditional)
    assert len(first_elif.body) == 2  # result assignment + log call

    # Navigate to second elif
    second_elif = first_elif.else_body[0]
    assert isinstance(second_elif, Conditional)
    assert len(second_elif.body) == 2  # result assignment + log call

    # Check final else
    final_else = second_elif.else_body
    assert len(final_else) == 2  # result assignment + log call


def test_elif_chain_single_statements(parser):
    """Test elif chain where each block has only a single statement."""
    code = textwrap.dedent("""
        x = 3
        if x == 1:
            pass
        elif x == 2:
            pass
        elif x == 3:
            pass
        elif x == 4:
            pass
    """)

    program = parser.parse(code, do_transform=True)
    conditional = get_conditional(program)

    # Each body should have exactly one statement (pass)
    current = conditional
    count = 0
    while True:
        count += 1
        assert len(current.body) == 1, f"Expected single statement in body at level {count}"

        if not (isinstance(current.else_body, list) and current.else_body and isinstance(current.else_body[0], Conditional)):
            break
        current = current.else_body[0]

    assert count == 4, f"Expected 4 conditions (if + 3 elif), got {count}"


def test_nested_if_within_elif_chain(parser):
    """Test elif chains that contain nested if statements."""
    code = textwrap.dedent("""
        x = 5
        y = 10
        if x > 10:
            result = "x high"
        elif x > 0:
            if y > 5:
                result = "x positive, y high"
            else:
                result = "x positive, y low"
        elif x == 0:
            result = "x zero"
        else:
            result = "x negative"
    """)

    program = parser.parse(code, do_transform=True)
    conditional = get_conditional(program)

    # Navigate to the first elif (which contains a nested if)
    first_elif = conditional.else_body[0]
    assert isinstance(first_elif, Conditional)

    # The body of the first elif should contain a nested conditional
    nested_if = None
    for stmt in first_elif.body:
        if isinstance(stmt, Conditional):
            nested_if = stmt
            break

    assert nested_if is not None, "Expected nested if statement in first elif body"
    assert len(nested_if.body) == 1  # "x positive, y high"
    assert len(nested_if.else_body) == 1  # "x positive, y low"


def test_elif_with_different_data_types(parser):
    """Test elif chains with different data types in conditions and assignments."""
    code = textwrap.dedent("""
        value = "test"
        if isinstance(value, int):
            result = value * 2
        elif isinstance(value, str):
            result = f"{value}_suffix"
        elif isinstance(value, list):
            result = len(value)
        elif value is None:
            result = 0
        else:
            result = "unknown"
    """)

    program = parser.parse(code, do_transform=True)
    conditional = get_conditional(program)

    # Verify we can parse the complex conditions and f-strings
    # Navigate through the elif chain
    current = conditional
    depth = 0
    while isinstance(current.else_body, list) and current.else_body and isinstance(current.else_body[0], Conditional):
        depth += 1
        current = current.else_body[0]

    assert depth == 3, f"Expected 3 elif levels, got {depth}"

    # The final else should contain a string assignment
    final_else = current.else_body
    assert len(final_else) == 1


if __name__ == "__main__":
    pytest.main([__file__])
