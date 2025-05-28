from opendxa.dana.exec.repl.repl import REPL

repl = REPL()
code = """
def add_ten(x):
    return x + 10
"""
repl.execute(code)
func = repl.context.get("local.add_ten")
print("Parameters:", func.parameters)
print("Type:", type(func))
