#!/usr/bin/env python
"""
Diagnostic script to identify which parameter difference causes the divergent behavior
between test and REPL environments.
"""

from opendxa.common.resource.llm_resource import LLMResource
from opendxa.dana.sandbox.interpreter.executor.expression_evaluator import ExpressionEvaluator
from opendxa.dana.sandbox.interpreter.interpreter import Interpreter
from opendxa.dana.sandbox.parser.dana_parser import DanaParser
from opendxa.dana.sandbox.sandbox_context import SandboxContext

# Create base resources
context = SandboxContext()
try:
    llm_resource = LLMResource()
    context.set("system.llm_resource", llm_resource)
except Exception as e:
    print(f"Warning: Cannot create LLM resource: {e}")


def print_separator(title):
    print("\n" + "=" * 70)
    print(f"{title}")
    print("=" * 70)


def trace_expression_type(expression):
    """Helper to print the type of expression being evaluated"""
    print(f"EXPRESSION TYPE: {type(expression)}")
    if isinstance(expression, list) and len(expression) > 0:
        print(f"LIST ITEM TYPE: {type(expression[0])}")
        if hasattr(expression[0], "value"):
            print(f"LIST ITEM VALUE: {expression[0].value}")
    elif hasattr(expression, "name"):
        print(f"FUNCTION NAME: {expression.name}")
        print(f"ARGS: {expression.args}")


# ===== TEST 1: Varying do_type_check parameter =====
print_separator("TEST 1: Varying do_type_check parameter")

# Test 1A: With do_type_check=False (like tests)
print("\nTest 1A: do_type_check=False (test-like)")
interpreter = Interpreter(context)
parser = DanaParser()
program = parser.parse('reason("what is")', do_type_check=False)
print(f"Program AST: {program}")
print(f"Statement type: {type(program.statements[0])}")

# Monkey patch ExpressionEvaluator.evaluate to trace types
original_evaluate = ExpressionEvaluator.evaluate


def trace_evaluate(self, expression, local_context=None):
    print("\nTRACING EVALUATE CALL:")
    trace_expression_type(expression)
    return original_evaluate(self, expression, local_context)


ExpressionEvaluator.evaluate = trace_evaluate

try:
    result = interpreter.execute_program(program)
    print("Execution successful")
except Exception as e:
    print(f"Execution error: {e}")

# Test 1B: With do_type_check=True (like REPL)
print("\nTest 1B: do_type_check=True (REPL-like)")
interpreter = Interpreter(context)
parser = DanaParser()
program = parser.parse('reason("what is")', do_type_check=True)
print(f"Program AST: {program}")
print(f"Statement type: {type(program.statements[0])}")
try:
    result = interpreter.execute_program(program)
    print("Execution successful")
except Exception as e:
    print(f"Execution error: {e}")

# ===== TEST 2: Varying input structure =====
print_separator("TEST 2: Varying input structure")

# Test 2A: With assignment (like tests)
print("\nTest 2A: Assignment statement (test-like)")
interpreter = Interpreter(context)
parser = DanaParser()
program = parser.parse('result = reason("what is")', do_type_check=False)
print(f"Program AST: {program}")
print(f"Statement type: {type(program.statements[0])}")
try:
    result = interpreter.execute_program(program)
    print("Execution successful")
except Exception as e:
    print(f"Execution error: {e}")

# Test 2B: With bare function call (like REPL)
print("\nTest 2B: Bare function call (REPL-like)")
interpreter = Interpreter(context)
parser = DanaParser()
program = parser.parse('reason("what is")', do_type_check=False)
print(f"Program AST: {program}")
print(f"Statement type: {type(program.statements[0])}")
try:
    result = interpreter.execute_program(program)
    print("Execution successful")
except Exception as e:
    print(f"Execution error: {e}")

# ===== TEST 3: Varying do_transform parameter =====
print_separator("TEST 3: Varying do_transform parameter")

# Test 3A: With do_transform=True (default)
print("\nTest 3A: do_transform=True (default)")
interpreter = Interpreter(context)
parser = DanaParser()
program = parser.parse('reason("what is")', do_type_check=False, do_transform=True)
print(f"Program AST: {program}")
print(f"Statement type: {type(program.statements[0])}")
try:
    result = interpreter.execute_program(program)
    print("Execution successful")
except Exception as e:
    print(f"Execution error: {e}")

# Test 3B: With do_transform=False
print("\nTest 3B: do_transform=False")
interpreter = Interpreter(context)
parser = DanaParser()
program = parser.parse('reason("what is")', do_type_check=False, do_transform=False)
print(f"Program AST: {program}")
print(f"Statement type: {type(program.statements[0])}")
try:
    result = interpreter.execute_program(program)
    print("Execution successful")
except Exception as e:
    print(f"Execution error: {e}")

# Restore original evaluate method
ExpressionEvaluator.evaluate = original_evaluate

print("\nAll tests completed")
