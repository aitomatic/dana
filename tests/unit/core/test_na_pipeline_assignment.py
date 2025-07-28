"""
Test runner for pipeline assignment functionality.

Tests the pattern: pipeline = f1 | f2 | f3 and then result = pipeline(x)
"""

from dana.core.lang.dana_sandbox import DanaSandbox


def test_pipeline_assignment_basic():
    """Test basic pipeline assignment and application."""
    sandbox = DanaSandbox(debug_mode=True)

    test_code = """
def double(x: int) -> int:
    return x * 2

def add_ten(x: int) -> int:
    return x + 10

# Test basic pipeline assignment
pipeline = double | add_ten
result = pipeline(5)
"""

    result = sandbox.eval(test_code)
    assert result.success, f"Pipeline assignment test failed: {result.error}"


def test_pipeline_assignment_reusable():
    """Test reusable pipeline assignment."""
    sandbox = DanaSandbox(debug_mode=True)

    test_code = """
def double(x: int) -> int:
    return x * 2

def add_ten(x: int) -> int:
    return x + 10

def square(x: int) -> int:
    return x * x

# Test reusable pipeline
math_pipeline = double | add_ten
result1 = math_pipeline(3)
result2 = math_pipeline(7)
result3 = math_pipeline(-5)
"""

    result = sandbox.eval(test_code)
    assert result.success, f"Pipeline assignment test failed: {result.error}"


def test_pipeline_assignment_complex():
    """Test complex pipeline assignment."""
    sandbox = DanaSandbox(debug_mode=True)

    test_code = """
def double(x: int) -> int:
    return x * 2

def square(x: int) -> int:
    return x * x

def add_ten(x: int) -> int:
    return x + 10

# Test complex pipeline
complex_pipeline = double | square | add_ten
final_result = complex_pipeline(3)
"""

    result = sandbox.eval(test_code)
    assert result.success, f"Complex pipeline test failed: {result.error}"
