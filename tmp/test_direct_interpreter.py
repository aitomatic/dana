from opendxa.dana.sandbox.interpreter.dana_interpreter import DanaInterpreter
from opendxa.dana.sandbox.sandbox_context import SandboxContext

interpreter = DanaInterpreter()
context = SandboxContext()

code = """
print("Testing unified pipe")

def add_one(x):
    return x + 1

def double(x):
    return x * 2

print("Testing data pipeline...")
result = 5 | add_one
print("5 | add_one = " + str(result))

print("Testing function composition...")
math_pipeline = add_one | double
print("Created composed function: math_pipeline")

print("Testing composed function call...")
result2 = math_pipeline(5)
print("math_pipeline(5) = " + str(result2))

print("Testing composed function in data pipeline...")
result3 = 7 | math_pipeline
print("7 | math_pipeline = " + str(result3))

print("Done!")
"""

try:
    result = interpreter._eval(code, context)
    print("Execution completed")
except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()
