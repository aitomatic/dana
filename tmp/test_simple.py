from opendxa.dana.sandbox.interpreter.dana_interpreter import DanaInterpreter; interpreter = DanaInterpreter(); code = "def add_ten(x):
    return x + 10

def double(x):
    return x * 2

math_pipeline = add_ten | double
result = math_pipeline(5)
print(str(result))"; result = interpreter.execute(code); print("Success!")
