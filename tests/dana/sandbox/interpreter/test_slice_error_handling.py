"""
Tests for Phase 2.1: Enhanced Slice Error Handling

Tests comprehensive error handling and validation for slice operations in Dana.
"""

from opendxa.dana.sandbox.dana_sandbox import DanaSandbox


class TestSliceErrorHandling:
    """Test enhanced error handling for slice operations."""

    # Using fresh_sandbox fixture from conftest.py instead of setup_method

    def test_slice_component_type_validation(self, fresh_sandbox):
        """Test that slice components must be integers."""
        # Test non-integer start
        code = """
test_list = [1, 2, 3, 4, 5]
result = test_list["start":2]
"""
        result = fresh_sandbox.eval(code)
        assert not result.success
        assert "Slice start must be integer" in str(result.error)
        assert "got str" in str(result.error)

        # Test non-integer stop
        code = """
test_list = [1, 2, 3, 4, 5]
result = test_list[1:"stop"]
"""
        result = self.sandbox.eval(code)
        assert not result.success
        assert "Slice stop must be integer" in str(result.error)
        assert "got str" in str(result.error)

        # Test non-integer step
        code = """
test_list = [1, 2, 3, 4, 5]
result = test_list[1:4:"step"]
"""
        result = self.sandbox.eval(code)
        assert not result.success
        assert "Slice step must be integer" in str(result.error)
        assert "got str" in str(result.error)

    def test_slice_zero_step_validation(self):
        """Test that step cannot be zero."""
        code = """
test_list = [1, 2, 3, 4, 5]
result = test_list[1:4:0]
"""
        result = self.sandbox.eval(code)
        assert not result.success
        assert "Slice step cannot be zero" in str(result.error)
        assert "positive values" in str(result.error)
        assert "negative values" in str(result.error)

    def test_slice_unsupported_target_validation(self):
        """Test slicing on objects that don't support __getitem__."""
        code = """
test_number = 42
result = test_number[1:3]
"""
        result = self.sandbox.eval(code)
        assert not result.success
        assert "Slice operation not supported on int" in str(result.error)
        assert "lists, tuples, strings, dictionaries" in str(result.error)

    def test_slice_bounds_validation(self):
        """Test bounds validation for slice operations."""
        # Test start index out of bounds
        code = """
test_list = [1, 2, 3]
result = test_list[5:7]
"""
        result = self.sandbox.eval(code)
        assert not result.success
        assert "Slice start index 5 is out of bounds" in str(result.error)
        assert "length 3" in str(result.error)
        assert "Valid range: -3 to 2" in str(result.error)

        # Test stop index out of bounds
        code = """
test_list = [1, 2, 3]
result = test_list[1:10]
"""
        result = self.sandbox.eval(code)
        assert not result.success
        assert "Slice stop index 10 is out of bounds" in str(result.error)
        assert "length 3" in str(result.error)
        assert "Valid range: -3 to 3" in str(result.error)

    def test_reverse_slice_validation(self):
        """Test validation for reverse slicing with negative steps."""
        code = """
test_list = [1, 2, 3, 4, 5]
result = test_list[1:4:-1]
"""
        result = self.sandbox.eval(code)
        assert not result.success
        assert "Invalid reverse slice" in str(result.error)
        assert "when step is negative (-1)" in str(result.error)
        assert "start (1) should be greater than stop (4)" in str(result.error)
        assert "arr[5:2:-1]" in str(result.error)

    def test_enhanced_indexing_errors(self):
        """Test enhanced error messages for regular indexing."""
        # Test out of bounds index
        code = """
test_list = [1, 2, 3]
result = test_list[5]
"""
        result = self.sandbox.eval(code)
        assert not result.success
        assert "Index 5 is out of bounds for list of length 3" in str(result.error)
        assert "Valid indices: 0 to 2" in str(result.error)

        # Test dictionary key not found
        code = """
test_dict = {"a": 1, "b": 2, "c": 3}
result = test_dict["missing_key"]
"""
        result = self.sandbox.eval(code)
        assert not result.success
        assert "Key 'missing_key' not found in dictionary" in str(result.error)
        assert "Available keys include:" in str(result.error)

    def test_slice_component_evaluation_errors(self):
        """Test behavior during slice component evaluation with undefined variables (gracefully handles as None)."""
        code = """
test_list = [1, 2, 3, 4, 5]
undefined_var = undefined_variable
result = test_list[undefined_var:3]
"""
        result = self.sandbox.eval(code)
        # Undefined variables now gracefully resolve to None (becomes 0 in slice context)
        assert result.success
        assert result.final_context is not None
        assert result.final_context.get("local:result") == [1, 2, 3]

    def test_successful_slice_operations(self):
        """Test that valid slice operations still work correctly."""
        # Test basic slice
        code = """
test_list = [1, 2, 3, 4, 5]
result = test_list[1:4]
"""
        result = self.sandbox.eval(code)
        assert result.success
        assert result.final_context is not None
        assert result.final_context.get("local:result") == [2, 3, 4]

        # Test slice with step
        code = """
test_list = [1, 2, 3, 4, 5, 6]
result = test_list[0:6:2]
"""
        result = self.sandbox.eval(code)
        assert result.success
        assert result.final_context is not None
        assert result.final_context.get("local:result") == [1, 3, 5]

        # Test reverse slice (correct syntax)
        code = """
test_list = [1, 2, 3, 4, 5]
result = test_list[4:1:-1]
"""
        result = self.sandbox.eval(code)
        assert result.success
        assert result.final_context is not None
        assert result.final_context.get("local:result") == [5, 4, 3]

        # Test negative indices
        code = """
test_list = [1, 2, 3, 4, 5]
result = test_list[-3:-1]
"""
        result = self.sandbox.eval(code)
        assert result.success
        assert result.final_context is not None
        assert result.final_context.get("local:result") == [3, 4]


class TestSliceContextualErrors:
    """Test contextual error information in slice operations."""

    def setup_method(self):
        """Setup test environment before each test."""
        self.sandbox = DanaSandbox()

    def test_error_context_includes_target_info(self):
        """Test that errors include helpful target information."""
        code = """
test_list = [1, 2, 3]
result = test_list[10:20]
"""
        result = self.sandbox.eval(code)
        assert not result.success
        # Should include target type and length in error context
        error_str = str(result.error)
        assert "Target type: list" in error_str
        assert "Target length: 3" in error_str

    def test_slice_repr_in_error_messages(self):
        """Test that slice representation is included in error messages."""
        # Test a slice that triggers bounds validation
        code = """
test_string = "hello"
result = test_string[1:10:2]  # Stop index out of bounds, should show slice repr in error
"""
        result = self.sandbox.eval(code)
        # This should fail due to improved bounds validation
        assert not result.success
        assert "10 is out of bounds" in str(result.error)
        assert "Target type: str" in str(result.error)

    def test_empty_result_validation(self):
        """Test validation of edge cases in reverse slicing."""
        # Test case where reverse slice has start == stop (invalid)
        code = """
test_list = [1, 2, 3, 4, 5]
result = test_list[2:2:-1]  # Invalid: start equals stop with negative step
"""
        result = self.sandbox.eval(code)
        # This should fail due to improved reverse slice validation
        assert not result.success
        assert "Invalid reverse slice" in str(result.error)
        assert "start (2) should be greater than stop (2)" in str(result.error)


class TestSliceValidationEdgeCases:
    """Test edge cases in slice validation."""

    def setup_method(self):
        """Setup test environment before each test."""
        self.sandbox = DanaSandbox()

    def test_none_components_validation(self):
        """Test that None slice components are handled correctly."""
        # Test slice with all None components
        code = """
test_list = [1, 2, 3, 4, 5]
result = test_list[:]
"""
        result = self.sandbox.eval(code)
        assert result.success
        assert result.final_context is not None
        assert result.final_context.get("local:result") == [1, 2, 3, 4, 5]

        # Test slice with some None components
        code = """
test_list = [1, 2, 3, 4, 5]
result = test_list[2:]
"""
        result = self.sandbox.eval(code)
        assert result.success
        assert result.final_context is not None
        assert result.final_context.get("local:result") == [3, 4, 5]

    def test_slice_on_strings(self):
        """Test slice operations on strings."""
        code = """
test_string = "hello world"
result = test_string[0:5]
"""
        result = self.sandbox.eval(code)
        assert result.success
        assert result.final_context is not None
        assert result.final_context.get("local:result") == "hello"

        # Test string slice bounds validation
        code = """
test_string = "hi"
result = test_string[10:15]
"""
        result = self.sandbox.eval(code)
        assert not result.success
        assert "Slice start index 10 is out of bounds" in str(result.error)
        assert "length 2" in str(result.error)

    def test_slice_on_tuples(self):
        """Test slice operations on tuples."""
        code = """
test_tuple = (1, 2, 3, 4, 5)
result = test_tuple[1:4]
"""
        result = self.sandbox.eval(code)
        assert result.success
        assert result.final_context is not None
        assert result.final_context.get("local:result") == (2, 3, 4)
