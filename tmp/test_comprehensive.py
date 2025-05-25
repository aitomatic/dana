from opendxa.dana.exec.repl.repl import REPL


def test_comprehensive_composition():
    """Test comprehensive function composition scenarios."""

    repl = REPL()

    print("=== Comprehensive Function Composition Test ===")

    # Test 1: Basic function composition
    print("\n1. Basic Function Composition:")
    code1 = """
def add_ten(x):
    return x + 10

def double(x):
    return x * 2

math_pipeline = add_ten | double
result1 = math_pipeline(5)
print("math_pipeline(5) = " + str(result1))
"""
    repl.execute(code1)

    # Test 2: Data pipeline with composed function
    print("\n2. Data Pipeline with Composed Function:")
    code2 = """
result2 = 7 | math_pipeline
print("7 | math_pipeline = " + str(result2))
"""
    repl.execute(code2)

    # Test 3: Triple composition
    print("\n3. Triple Function Composition:")
    code3 = """
def stringify(x):
    return "Result: " + str(x)

full_pipeline = add_ten | double | stringify
result3 = full_pipeline(3)
print("full_pipeline(3) = " + str(result3))
"""
    repl.execute(code3)

    # Test 4: Data pipeline with triple composition
    print("\n4. Data Pipeline with Triple Composition:")
    code4 = """
result4 = 2 | full_pipeline
print("2 | full_pipeline = " + str(result4))
"""
    repl.execute(code4)

    print("\n=== All tests completed successfully! ===")


if __name__ == "__main__":
    test_comprehensive_composition()
