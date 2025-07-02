"""
Tests for slice assignment functionality in Dana language.

This module tests the slice assignment implementation that allows operations like:
- df.iloc[1:3, 0:2] = value (multi-dimensional slice assignment)
- list[2:5] = [values] (single-dimensional slice assignment)
- dict[key] = value (index assignment)
- obj.attr = value (attribute assignment)

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from opendxa.dana.sandbox.dana_sandbox import DanaSandbox


class TestSliceAssignment:
    """Test slice assignment functionality in Dana language."""

    def setup_method(self):
        """Setup test environment before each test."""
        self.sandbox = DanaSandbox()

    def test_single_dimensional_slice_assignment(self):
        """Test single-dimensional slice assignment on lists."""
        code = """
numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
numbers[2:5] = [99, 88, 77]
result = numbers
"""
        result = self.sandbox.eval(code)
        assert result.success
        assert result.final_context is not None
        expected = [1, 2, 99, 88, 77, 6, 7, 8, 9, 10]
        assert result.final_context.get("local:result") == expected

    def test_multi_dimensional_slice_assignment_pandas(self):
        """Test multi-dimensional slice assignment with pandas DataFrames."""
        code = """
import pandas.py as pd
df = pd.DataFrame({"A": [1, 2, 3, 4], "B": [10, 20, 30, 40]})
df.iloc[1:3, 0:2] = 999
result = df.iloc[1, 0]  # Should be 999
"""
        result = self.sandbox.eval(code)
        assert result.success
        assert result.final_context is not None
        assert result.final_context.get("local:result") == 999

    def test_full_column_slice_assignment(self):
        """Test full column slice assignment."""
        code = """
import pandas.py as pd
df = pd.DataFrame({"A": [1, 2, 3], "B": [10, 20, 30], "C": [100, 200, 300]})
df.iloc[:, 1] = 777
result = df.iloc[0, 1]  # Check first row, second column
"""
        result = self.sandbox.eval(code)
        assert result.success
        assert result.final_context is not None
        assert result.final_context.get("local:result") == 777

    def test_full_row_slice_assignment(self):
        """Test full row slice assignment."""
        code = """
import pandas.py as pd
df = pd.DataFrame({"A": [1, 2, 3], "B": [10, 20, 30]})
df.iloc[1, :] = 555
result = df.iloc[1, 0]  # Check second row, first column
"""
        result = self.sandbox.eval(code)
        assert result.success
        assert result.final_context is not None
        assert result.final_context.get("local:result") == 555

    def test_dictionary_index_assignment(self):
        """Test dictionary index assignment."""
        code = """
data = {"x": 1, "y": 2, "z": 3}
data["y"] = 999
result = data["y"]
"""
        result = self.sandbox.eval(code)
        assert result.success
        assert result.final_context is not None
        assert result.final_context.get("local:result") == 999

    def test_string_slice_assignment(self):
        """Test slice assignment on strings (should fail as strings are immutable)."""
        code = """
text = "hello"
text[1:3] = "XX"
"""
        result = self.sandbox.eval(code)
        assert not result.success
        assert "does not support item assignment" in str(result.error)

    def test_slice_assignment_with_step(self):
        """Test slice assignment with step parameter."""
        code = """
numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
numbers[1:8:2] = [99, 88, 77, 66]
result = numbers
"""
        result = self.sandbox.eval(code)
        assert result.success
        assert result.final_context is not None
        expected = [1, 99, 3, 88, 5, 77, 7, 66, 9, 10]
        assert result.final_context.get("local:result") == expected

    def test_nested_slice_assignment(self):
        """Test slice assignment on nested structures."""
        code = """
matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
matrix[1][0:2] = [99, 88]
result = matrix[1]
"""
        result = self.sandbox.eval(code)
        assert result.success
        assert result.final_context is not None
        assert result.final_context.get("local:result") == [99, 88, 6]


class TestSliceAssignmentErrors:
    """Test error handling in slice assignment operations."""

    def setup_method(self):
        """Setup test environment before each test."""
        self.sandbox = DanaSandbox()

    def test_slice_assignment_bounds_error(self):
        """Test slice assignment with out-of-bounds indices (Python allows this)."""
        code = """
numbers = [1, 2, 3]
numbers[5:10] = [99, 88]  # Python allows this, extends the list
result = numbers
"""
        result = self.sandbox.eval(code)
        assert result.success
        assert result.final_context is not None
        # Python extends the list when slice is out of bounds
        assert result.final_context.get("local:result") == [1, 2, 3, 99, 88]

    def test_slice_assignment_type_error(self):
        """Test error handling for invalid assignment target types."""
        code = """
number = 42
number[0:2] = [1, 2]
"""
        result = self.sandbox.eval(code)
        assert not result.success
        assert "not support" in str(result.error) or "not subscriptable" in str(result.error)

    def test_multi_dimensional_slice_assignment_error(self):
        """Test multi-dimensional slice assignment with out-of-bounds (pandas handles this)."""
        code = """
import pandas.py as pd
df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
df.iloc[0:2, 0:2] = 999  # Within bounds, should work
result = df.iloc[0, 0]
"""
        result = self.sandbox.eval(code)
        assert result.success
        assert result.final_context is not None
        assert result.final_context.get("local:result") == 999


class TestSliceAssignmentEdgeCases:
    """Test edge cases in slice assignment operations."""

    def setup_method(self):
        """Setup test environment before each test."""
        self.sandbox = DanaSandbox()

    def test_empty_slice_assignment(self):
        """Test assignment to empty slice."""
        code = """
numbers = [1, 2, 3, 4, 5]
numbers[2:2] = []
result = numbers
"""
        result = self.sandbox.eval(code)
        assert result.success
        assert result.final_context is not None
        assert result.final_context.get("local:result") == [1, 2, 3, 4, 5]

    def test_negative_index_slice_assignment(self):
        """Test slice assignment with negative indices."""
        code = """
numbers = [1, 2, 3, 4, 5]
numbers[-3:-1] = [99, 88]
result = numbers
"""
        result = self.sandbox.eval(code)
        assert result.success
        assert result.final_context is not None
        assert result.final_context.get("local:result") == [1, 2, 99, 88, 5]

    def test_slice_assignment_different_lengths(self):
        """Test slice assignment where replacement has different length."""
        code = """
numbers = [1, 2, 3, 4, 5]
numbers[1:3] = [99, 88, 77, 66]  # Replace 2 elements with 4
result = numbers
"""
        result = self.sandbox.eval(code)
        assert result.success
        assert result.final_context is not None
        assert result.final_context.get("local:result") == [1, 99, 88, 77, 66, 4, 5]

    def test_slice_assignment_single_value_to_multiple_positions(self):
        """Test assigning single value to multiple positions via slice."""
        code = """
import pandas.py as pd
df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
df.iloc[0:2, 0] = 999  # Assign single value to multiple positions
result = df.iloc[0, 0]  # Check first position
"""
        result = self.sandbox.eval(code)
        assert result.success
        assert result.final_context is not None
        assert result.final_context.get("local:result") == 999


class TestSliceAssignmentIntegration:
    """Test integration of slice assignment with other Dana features."""

    def setup_method(self):
        """Setup test environment before each test."""
        self.sandbox = DanaSandbox()

    def test_slice_assignment_with_expressions(self):
        """Test slice assignment using expressions for indices and values."""
        code = """
numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
start = 2
end = 5
replacement = [99, 88, 77]
numbers[start:end] = replacement
result = numbers
"""
        result = self.sandbox.eval(code)
        assert result.success
        assert result.final_context is not None
        expected = [1, 2, 99, 88, 77, 6, 7, 8, 9, 10]
        assert result.final_context.get("local:result") == expected

    def test_slice_assignment_in_function(self):
        """Test slice assignment within function definitions."""
        code = """
def modify_list(lst):
    lst[1:3] = [99, 88]
    return lst

numbers = [1, 2, 3, 4, 5]
result = modify_list(numbers)
"""
        result = self.sandbox.eval(code)
        assert result.success
        assert result.final_context is not None
        assert result.final_context.get("local:result") == [1, 99, 88, 4, 5]

    def test_chained_slice_assignments(self):
        """Test multiple slice assignments in sequence."""
        code = """
numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
numbers[0:2] = [99, 88]
numbers[3:5] = [77, 66]
result = numbers
"""
        result = self.sandbox.eval(code)
        assert result.success
        assert result.final_context is not None
        expected = [99, 88, 3, 77, 66, 6, 7, 8, 9, 10]
        assert result.final_context.get("local:result") == expected

    def test_slice_assignment_with_computed_values(self):
        """Test slice assignment with computed replacement values."""
        code = """
numbers = [1, 2, 3, 4, 5]
multiplier = 10
replacement = [2 * multiplier, 3 * multiplier, 4 * multiplier]
numbers[1:4] = replacement
result = numbers
"""
        result = self.sandbox.eval(code)
        assert result.success
        assert result.final_context is not None
        assert result.final_context.get("local:result") == [1, 20, 30, 40, 5]
