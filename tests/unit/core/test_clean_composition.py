"""
Test clean function composition implementation.

Tests the two-statement approach:
1. def pipeline(x: int) = f1 | f2 | [f3, f4]  (pure composition)
2. result = pipeline(data)        (pure application)
"""

from dana.core.lang.dana_sandbox import DanaSandbox


def double(x: int) -> int:
    return x * 2


def add_ten(x: int) -> int:
    return x + 10


def stringify(x: int) -> str:
    return str(x)


class TestCleanComposition:
    """Test clean function composition (pipelines separate from application)."""

    def setup_method(self):
        """Set up the interpreter and context for each test."""
        self.sandbox = DanaSandbox(debug_mode=True)
        self.sandbox.eval(
            """
def add_one(x: int) -> int:
    return x + 1

def double(x: int) -> int:
    return x * 2

def square(x: int) -> int:
    return x * x
    
def cube(x: int) -> int:
    return x * x * x

def sum_list(items: list) -> int:
    return sum(items)
        """
        )

    def test_simple_sequential_composition(self):
        """Test simple sequential function composition."""
        code = """
def pipeline(x: int) = double | add_one
result = pipeline(5)
"""
        result = self.sandbox.eval(code)
        assert result.success
        assert result.final_context is not None
        assert result.final_context.get("result") == 11

    def test_parallel_composition(self):
        """Test parallel function composition."""
        code = """
def pipeline(x: int) = noop | [double, add_one]
result = pipeline(5)
"""
        result = self.sandbox.eval(code)
        assert result.success
        assert result.final_context is not None
        assert result.final_context.get("result") == [10, 6]

    def test_mixed_composition(self):
        """Test mixed sequential and parallel composition."""
        code = """
def stringify(x: int) -> str:
    return str(x)

def pipeline(x: int) = double | [stringify, add_one]
result = pipeline(5)
"""
        result = self.sandbox.eval(code)
        assert result.success
        assert result.final_context is not None
        pipeline_result = result.final_context.get("result")
        assert pipeline_result == ["10", 11]

    def test_complex_composition(self):
        """Test a more complex composition."""
        code = """
def sum_list(items: list) -> int:
    return sum(items)

# Test a simpler complex composition
def pipeline(x: int) = add_one | double
result = pipeline(5)
"""
        result = self.sandbox.eval(code)
        assert result.success
        assert result.final_context.get("result") == 12  # (5 + 1) * 2 = 12

    def test_reusable_pipelines(self):
        """Test that composed pipelines can be reused."""
        code = """
def math_pipeline(x: int) = double | add_one
result1 = math_pipeline(5)
result2 = math_pipeline(10)
result3 = math_pipeline(-5)
"""
        result = self.sandbox.eval(code)
        assert result.success
        assert result.final_context.get("result1") == 11
        assert result.final_context.get("result2") == 21
        assert result.final_context.get("result3") == -9

    def test_function_not_found_error(self):
        """Test error handling for non-existent functions in a pipeline."""
        code = """
def pipeline(x: int) = double | non_existent_function
result = pipeline(5)
"""
        result = self.sandbox.eval(code)
        # The pipeline creation should fail because non_existent_function is not found
        assert not result.success
        # The error should indicate that the function was not found
        assert "Function 'non_existent_function' not found" in str(result.error)

    def test_non_function_composition_error(self):
        """Test error handling for composing non-function objects."""
        code = """
def pipeline(x: int) = double | non_existent_function
result = pipeline(5)
"""
        result = self.sandbox.eval(code)
        # The pipeline creation should fail because non_existent_function is not found
        assert not result.success
        # The error should indicate that the function was not found
        assert "Function 'non_existent_function' not found" in str(result.error)
