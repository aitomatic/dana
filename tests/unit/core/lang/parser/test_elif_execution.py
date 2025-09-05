#
# Copyright © 2025 Aitomatic, Inc.
#
# This source code is licensed under the license found in the LICENSE file in the root directory of this source tree
#

"""
Functional tests for elif chain execution in Dana.
These tests focus on execution behavior and output rather than AST implementation details.
"""

import textwrap

import pytest

from dana.core.lang.dana_sandbox import DanaSandbox


@pytest.fixture
def sandbox():
    """Create a DanaSandbox instance for testing."""
    return DanaSandbox()


def test_basic_elif_execution(sandbox):
    """Test that elif chains execute with correct branching logic."""
    code = textwrap.dedent("""
        def test_elif(x: int) -> str:
            if x > 10:
                return "high"
            elif x > 5:
                return "medium"
            elif x > 0:
                return "low"
            else:
                return "zero or negative"
        
        result1 = test_elif(15)
        result2 = test_elif(8)
        result3 = test_elif(3)
        result4 = test_elif(-1)
    """)

    result = sandbox.execute_string(code)

    # Verify execution was successful
    assert result.success, f"Execution failed: {result.error}"

    # Verify each branch executes correctly
    assert result.final_context.get("result1") == "high"
    assert result.final_context.get("result2") == "medium"
    assert result.final_context.get("result3") == "low"
    assert result.final_context.get("result4") == "zero or negative"


def test_elif_with_complex_conditions(sandbox):
    """Test elif chains with complex boolean conditions."""
    code = textwrap.dedent("""
        def categorize_student(score: int, attendance: int) -> str:
            if score >= 90 and attendance >= 95:
                return "excellent"
            elif score >= 80 and attendance >= 90:
                return "good"
            elif score >= 70 or attendance >= 85:
                return "satisfactory"
            elif score >= 60:
                return "needs improvement"
            else:
                return "failing"
        
        # Test various combinations
        result1 = categorize_student(95, 98)  # excellent
        result2 = categorize_student(85, 92)  # good
        result3 = categorize_student(65, 88)  # satisfactory (attendance >= 85)
        result4 = categorize_student(75, 80)  # satisfactory (score >= 70)
        result5 = categorize_student(65, 80)  # needs improvement
        result6 = categorize_student(50, 70)  # failing
    """)

    result = sandbox.execute_string(code)

    assert result.success, f"Execution failed: {result.error}"
    assert result.final_context.get("result1") == "excellent"
    assert result.final_context.get("result2") == "good"
    assert result.final_context.get("result3") == "satisfactory"
    assert result.final_context.get("result4") == "satisfactory"
    assert result.final_context.get("result5") == "needs improvement"
    assert result.final_context.get("result6") == "failing"


def test_elif_with_side_effects(sandbox):
    """Test that elif chains execute only the correct branch (no side effects from other branches)."""
    code = textwrap.dedent("""
        def test_side_effects(x: int) -> dict:
            executed_branch = ""
            
            if x == 1:
                executed_branch = "first"
            elif x == 2:
                executed_branch = "second"  
            elif x == 3:
                executed_branch = "third"
            else:
                executed_branch = "other"
            
            return {"result": executed_branch, "input": x}
        
        # Test that only the correct branch executes
        result1 = test_side_effects(2)
        result2 = test_side_effects(3)
        result3 = test_side_effects(1)
        result4 = test_side_effects(99)
    """)

    result = sandbox.execute_string(code)

    assert result.success, f"Execution failed: {result.error}"

    # Verify correct results
    result1 = result.final_context.get("result1")
    result2 = result.final_context.get("result2")
    result3 = result.final_context.get("result3")
    result4 = result.final_context.get("result4")

    assert result1["result"] == "second"
    assert result1["input"] == 2
    assert result2["result"] == "third"
    assert result2["input"] == 3
    assert result3["result"] == "first"
    assert result3["input"] == 1
    assert result4["result"] == "other"
    assert result4["input"] == 99


def test_nested_elif_chains(sandbox):
    """Test elif chains nested within other elif chains."""
    code = textwrap.dedent("""
        def process_data(category: str, value: int) -> str:
            if category == "temperature":
                if value > 100:
                    return "too hot"
                elif value > 70:
                    return "hot"
                elif value > 50:
                    return "warm"
                else:
                    return "cold"
            elif category == "speed":
                if value > 80:
                    return "very fast"
                elif value > 60:
                    return "fast"
                elif value > 40:
                    return "moderate"
                else:
                    return "slow"
            else:
                return "unknown category"
        
        temp_result1 = process_data("temperature", 85)
        temp_result2 = process_data("temperature", 45)
        speed_result1 = process_data("speed", 75)
        speed_result2 = process_data("speed", 30)
        unknown_result = process_data("pressure", 50)
    """)

    result = sandbox.execute_string(code)

    assert result.success, f"Execution failed: {result.error}"

    assert result.final_context.get("temp_result1") == "hot"
    assert result.final_context.get("temp_result2") == "cold"
    assert result.final_context.get("speed_result1") == "fast"
    assert result.final_context.get("speed_result2") == "slow"
    assert result.final_context.get("unknown_result") == "unknown category"


def test_elif_with_variable_assignments(sandbox):
    """Test elif chains that modify variables in different branches."""
    code = textwrap.dedent("""
        def calculate_grade(score: int) -> dict:
            grade = ""
            points = 0
            message = ""
            
            if score >= 97:
                grade = "A+"
                points = 4
                message = "Outstanding!"
            elif score >= 93:
                grade = "A"
                points = 4
                message = "Excellent work!"
            elif score >= 90:
                grade = "A-"
                points = 3
                message = "Very good!"
            elif score >= 87:
                grade = "B+"
                points = 3
                message = "Good work!"
            elif score >= 83:
                grade = "B"
                points = 3
                message = "Satisfactory"
            else:
                grade = "C"
                points = 2
                message = "Needs improvement"
            
            return {"grade": grade, "points": points, "message": message}
        
        result_a_plus = calculate_grade(98)
        result_a = calculate_grade(95)
        result_b_plus = calculate_grade(88)
        result_c = calculate_grade(75)
    """)

    result = sandbox.execute_string(code)

    assert result.success, f"Execution failed: {result.error}"

    # Verify A+ grade
    a_plus = result.final_context.get("result_a_plus")
    assert a_plus["grade"] == "A+"
    assert a_plus["points"] == 4
    assert a_plus["message"] == "Outstanding!"

    # Verify A grade
    a_grade = result.final_context.get("result_a")
    assert a_grade["grade"] == "A"
    assert a_grade["points"] == 4
    assert a_grade["message"] == "Excellent work!"

    # Verify B+ grade
    b_plus = result.final_context.get("result_b_plus")
    assert b_plus["grade"] == "B+"
    assert b_plus["points"] == 3
    assert b_plus["message"] == "Good work!"

    # Verify C grade
    c_grade = result.final_context.get("result_c")
    assert c_grade["grade"] == "C"
    assert c_grade["points"] == 2
    assert c_grade["message"] == "Needs improvement"


def test_elif_with_early_return(sandbox):
    """Test that elif chains work correctly with early returns."""
    code = textwrap.dedent("""
        def test_early_return(x: int) -> dict:
            executed_branch = ""
            
            if x == 1:
                executed_branch = "branch1"
                return {"result": "first", "branch": executed_branch}
            elif x == 2:
                executed_branch = "branch2"
                return {"result": "second", "branch": executed_branch}
            elif x == 3:
                executed_branch = "branch3"
                return {"result": "third", "branch": executed_branch}
            
            executed_branch = "default"
            return {"result": "default", "branch": executed_branch}
        
        result1 = test_early_return(2)
        result2 = test_early_return(4)
    """)

    result = sandbox.execute_string(code)

    assert result.success, f"Execution failed: {result.error}"

    # Verify correct returns
    result1 = result.final_context.get("result1")
    result2 = result.final_context.get("result2")

    assert result1["result"] == "second"
    assert result1["branch"] == "branch2"
    assert result2["result"] == "default"
    assert result2["branch"] == "default"


def test_elif_chain_with_loops(sandbox):
    """Test elif chains that contain loops and complex logic."""
    code = textwrap.dedent("""
        def process_numbers(numbers: list, operation: str) -> list:
            result = []
            
            if operation == "double":
                for num in numbers:
                    result.append(num * 2)
            elif operation == "square":
                for num in numbers:
                    result.append(num * num)
            elif operation == "filter_even":
                for num in numbers:
                    if num % 2 == 0:
                        result.append(num)
            elif operation == "sum_pairs":
                for i in range(0, len(numbers) - 1, 2):
                    result.append(numbers[i] + numbers[i + 1])
            else:
                result = numbers[:]
            
            return result
        
        input_numbers = [1, 2, 3, 4, 5, 6]
        
        doubled = process_numbers(input_numbers, "double")
        squared = process_numbers(input_numbers, "square")
        evens = process_numbers(input_numbers, "filter_even")
        pairs = process_numbers(input_numbers, "sum_pairs")
        unchanged = process_numbers(input_numbers, "unknown")
    """)

    result = sandbox.execute_string(code)

    assert result.success, f"Execution failed: {result.error}"

    assert result.final_context.get("doubled") == [2, 4, 6, 8, 10, 12]
    assert result.final_context.get("squared") == [1, 4, 9, 16, 25, 36]
    assert result.final_context.get("evens") == [2, 4, 6]
    assert result.final_context.get("pairs") == [3, 7, 11]  # (1+2), (3+4), (5+6)
    assert result.final_context.get("unchanged") == [1, 2, 3, 4, 5, 6]


def test_elif_with_function_calls(sandbox):
    """Test elif chains that call other functions."""
    code = textwrap.dedent("""
        def add_numbers(a: int, b: int) -> int:
            return a + b
        
        def multiply_numbers(a: int, b: int) -> int:
            return a * b
        
        def subtract_numbers(a: int, b: int) -> int:
            return a - b
        
        def calculate(x: int, y: int, operation: str) -> int:
            if operation == "add":
                return add_numbers(x, y)
            elif operation == "multiply":
                return multiply_numbers(x, y)
            elif operation == "subtract":
                return subtract_numbers(x, y)
            elif operation == "power":
                # Using nested elif for power calculation
                if y == 2:
                    return multiply_numbers(x, x)
                elif y == 3:
                    return multiply_numbers(multiply_numbers(x, x), x)
                else:
                    return x
            else:
                return 0
        
        result_add = calculate(5, 3, "add")
        result_multiply = calculate(5, 3, "multiply")
        result_subtract = calculate(5, 3, "subtract")
        result_power2 = calculate(5, 2, "power")
        result_power3 = calculate(5, 3, "power")
        result_unknown = calculate(5, 3, "unknown")
    """)

    result = sandbox.execute_string(code)

    assert result.success, f"Execution failed: {result.error}"

    assert result.final_context.get("result_add") == 8
    assert result.final_context.get("result_multiply") == 15
    assert result.final_context.get("result_subtract") == 2
    assert result.final_context.get("result_power2") == 25
    assert result.final_context.get("result_power3") == 125
    assert result.final_context.get("result_unknown") == 0


def test_elif_execution_order(sandbox):
    """Test that elif conditions are evaluated in the correct order."""
    code = textwrap.dedent("""
        # Test that elif conditions are checked in order and stop at first match
        def test_order(x: int) -> str:
            if x > 5:
                return "greater than 5"
            elif x > 3:  # This should NOT match x=6 because x > 5 already matched
                return "greater than 3"
            elif x > 1:
                return "greater than 1"
            else:
                return "1 or less"
        
        result_6 = test_order(6)   # Should be "greater than 5", not "greater than 3"
        result_4 = test_order(4)   # Should be "greater than 3"
        result_2 = test_order(2)   # Should be "greater than 1"
        result_0 = test_order(0)   # Should be "1 or less"
        
        # Test with overlapping ranges to ensure first match wins
        def test_overlapping(score: int) -> str:
            if score >= 90:
                return "A"
            elif score >= 80:  # This includes 80-89, not 80-100
                return "B"
            elif score >= 70:  # This includes 70-79, not 70-100
                return "C"
            else:
                return "F"
        
        result_95 = test_overlapping(95)  # Should be "A"
        result_85 = test_overlapping(85)  # Should be "B", not "A"
        result_75 = test_overlapping(75)  # Should be "C", not "B"
        result_65 = test_overlapping(65)  # Should be "F"
    """)

    result = sandbox.execute_string(code)

    assert result.success, f"Execution failed: {result.error}"

    # Verify order-dependent evaluation
    assert result.final_context.get("result_6") == "greater than 5"
    assert result.final_context.get("result_4") == "greater than 3"
    assert result.final_context.get("result_2") == "greater than 1"
    assert result.final_context.get("result_0") == "1 or less"

    # Verify overlapping conditions work correctly
    assert result.final_context.get("result_95") == "A"
    assert result.final_context.get("result_85") == "B"
    assert result.final_context.get("result_75") == "C"
    assert result.final_context.get("result_65") == "F"


if __name__ == "__main__":
    pytest.main([__file__])
