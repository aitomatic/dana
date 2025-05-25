from opendxa.dana.exec.repl.repl import REPL

repl = REPL()

code = """
def add_ten(x):
    return x + 10

def double(x):
    return x * 2

print("Testing function composition...")
math_pipeline = add_ten | double
result = math_pipeline(5)
print("Result: " + str(result))
"""

try:
    print("=== Testing Unified Function Composition ===")
    result = repl.execute(code)
    print("=== Test completed! ===")
except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()
