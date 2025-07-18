"""
Test clean function composition implementation.

Tests the two-statement approach:
1. pipeline = f1 | f2 | [f3, f4]  (pure composition)
2. result = pipeline(data)        (pure application)
"""

from dana.core.lang.dana_sandbox import DanaSandbox


class TestCleanComposition:
    """Test the clean two-statement composition approach."""

    def test_debug_simple_function_call(self):
        """Debug test to understand argument passing."""
        code = """
def double(x):
    return x * 2

# Test direct function call first
result1 = double(5)

# Test function composition
pipeline = double
result2 = pipeline(5)
"""
        with DanaSandbox() as sandbox:
            result = sandbox.eval(code)
            print(f"Debug result: {result}")
            if result.final_context:
                print(f"result1: {result.final_context.get('result1')}")
                print(f"result2: {result.final_context.get('result2')}")
            if not result.success:
                print(f"Error: {result.error}")

    def test_simple_sequential_composition(self):
        """Test basic sequential function composition: f1 | f2."""
        code = """
def double(x):
    return x * 2

def add_ten(x):
    return x + 10

# Define composition
pipeline = double | add_ten

# Apply to data
result = pipeline(5)
"""
        with DanaSandbox() as sandbox:
            result = sandbox.eval(code)
            assert result.success
            assert result.final_context is not None
            # Should be (5 * 2) + 10 = 20
            assert result.final_context.get("result") == 20

    def test_parallel_composition(self):
        """Test parallel function composition: [f1, f2]."""
        code = """
def double(x):
    return x * 2

def triple(x):
    return x * 3

# Define parallel composition
pipeline = [double, triple]

# Apply to data
result = pipeline(5)
"""
        with DanaSandbox() as sandbox:
            result = sandbox.eval(code)
            assert result.success
            assert result.final_context is not None
            # Should be [10, 15]
            result_value = result.final_context.get("result")
            assert isinstance(result_value, list)
            assert len(result_value) == 2
            assert result_value[0] == 10  # 5 * 2
            assert result_value[1] == 15  # 5 * 3

    def test_mixed_composition(self):
        """Test mixed composition: f1 | [f2, f3]."""
        code = """
def add_one(x):
    return x + 1

def double(x):
    return x * 2

def triple(x):
    return x * 3

# Define mixed composition: sequential then parallel
pipeline = add_one | [double, triple]

# Apply to data
result = pipeline(5)
"""
        with DanaSandbox() as sandbox:
            result = sandbox.eval(code)
            assert result.success
            assert result.final_context is not None
            # Should be [(5+1)*2, (5+1)*3] = [12, 18]
            result_value = result.final_context.get("result")
            assert isinstance(result_value, list)
            assert len(result_value) == 2
            assert result_value[0] == 12  # (5+1) * 2
            assert result_value[1] == 18  # (5+1) * 3

    def test_complex_composition(self):
        """Test complex composition: f1 | f2 | [f3, f4] | f5."""
        code = """
def add_one(x):
    return x + 1

def double(x):
    return x * 2

def square(x):
    return x * x

def cube(x):
    return x * x * x

def sum_list(lst):
    total = 0
    for item in lst:
        total = total + item
    return total

# Define complex composition
pipeline = add_one | double | [square, cube] | sum_list

# Apply to data  
result = pipeline(3)
"""
        with DanaSandbox() as sandbox:
            result = sandbox.eval(code)
            assert result.success
            assert result.final_context is not None
            # Should be: 3 -> 4 -> 8 -> [64, 512] -> 576
            assert result.final_context.get("result") == 576

    def test_reusable_pipelines(self):
        """Test that pipelines are reusable with different data."""
        code = """
def double(x):
    return x * 2

def add_ten(x):
    return x + 10

# Define reusable pipeline
pipeline = double | add_ten

# Apply to different data
result1 = pipeline(5)
result2 = pipeline(10)
result3 = pipeline(0)
"""
        with DanaSandbox() as sandbox:
            result = sandbox.eval(code)
            assert result.success
            assert result.final_context is not None

            context = result.final_context
            assert context.get("result1") == 20  # (5 * 2) + 10
            assert context.get("result2") == 30  # (10 * 2) + 10
            assert context.get("result3") == 10  # (0 * 2) + 10

    def test_function_not_found_error(self):
        """Test proper error handling for non-existent functions."""
        code = """
def double(x):
    return x * 2

# Try to compose with non-existent function
pipeline = double | non_existent_function
"""
        with DanaSandbox() as sandbox:
            result = sandbox.eval(code)
            assert not result.success
            assert "not found" in str(result.error).lower()

    def test_non_function_composition_error(self):
        """Test error when trying to compose with non-functions."""
        code = """
def double(x):
    return x * 2

# Try to compose function with data (not allowed)
not_a_function = 42
pipeline = double | not_a_function
"""
        with DanaSandbox() as sandbox:
            result = sandbox.eval(code)
            assert not result.success
            assert "non-function" in str(result.error).lower()
