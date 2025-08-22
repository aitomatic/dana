"""
Test runner for declarative function pipeline functionality.

Tests the pattern: def pipeline(x) = f1 | f2 | f3 and then result = pipeline(x)
"""

from dana.core.lang.dana_sandbox import DanaSandbox


def test_pipeline_assignment_basic():
    """Test basic declarative function pipeline and application."""
    sandbox = DanaSandbox(debug_mode=True)

    test_code = """
def double(x: int) -> int:
    return x * 2

def add_ten(x: int) -> int:
    return x + 10

# Test basic declarative function pipeline
def pipeline(x: int) -> int = double | add_ten
result = pipeline(5)
"""

    result = sandbox.execute_string(test_code)
    assert result.success, f"Declarative function pipeline test failed: {result.error}"


def test_pipeline_assignment_reusable():
    """Test reusable declarative function pipeline."""
    sandbox = DanaSandbox(debug_mode=True)

    test_code = """
def double(x: int) -> int:
    return x * 2

def add_ten(x: int) -> int:
    return x + 10

def square(x: int) -> int:
    return x * x

# Test reusable declarative function pipeline
def math_pipeline(x: int) -> int = double | add_ten
result1 = math_pipeline(3)
result2 = math_pipeline(7)
result3 = math_pipeline(-5)
"""

    result = sandbox.execute_string(test_code)
    assert result.success, f"Declarative function pipeline test failed: {result.error}"


def test_pipeline_assignment_complex():
    """Test complex declarative function pipeline."""
    sandbox = DanaSandbox(debug_mode=True)

    test_code = """
def double(x: int) -> int:
    return x * 2

def square(x: int) -> int:
    return x * x

def add_ten(x: int) -> int:
    return x + 10

# Test complex declarative function pipeline
def complex_pipeline(x: int) -> int = double | square | add_ten
final_result = complex_pipeline(3)
"""

    result = sandbox.execute_string(test_code)
    assert result.success, f"Complex declarative function pipeline test failed: {result.error}"


def test_pipeline_assignment_rejected():
    """Test that old pipeline assignment syntax is properly rejected."""
    sandbox = DanaSandbox(debug_mode=True)

    test_code = """
def double(x: int) -> int:
    return x * 2

def add_ten(x: int) -> int:
    return x + 10

# This should be rejected - old assignment syntax
pipeline = double | add_ten
"""

    result = sandbox.execute_string(test_code)
    assert not result.success, "Old pipeline assignment syntax should be rejected"
    assert "Pipe expressions (|) are only allowed in declarative function definitions" in str(
        result.error
    ), f"Expected pipe restriction error, got: {result.error}"


def test_pipe_expression_in_invalid_context():
    """Test that pipe expressions in invalid contexts are rejected."""
    sandbox = DanaSandbox(debug_mode=True)

    test_code = """
def double(x: int) -> int:
    return x * 2

# This should be rejected - pipe expression in invalid context
result = 5 | double
"""

    result = sandbox.execute_string(test_code)
    assert not result.success, "Pipe expression in invalid context should be rejected"
    assert "Pipe expressions (|) are only allowed in declarative function definitions" in str(
        result.error
    ), f"Expected pipe restriction error, got: {result.error}"
