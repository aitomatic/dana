#!/usr/bin/env python
"""
Diagnostic script to trace differences in executing reason("what is") in
different contexts (REPL vs. Test)
"""

from opendxa.common.resource.llm_resource import LLMResource
from opendxa.dana.repl.repl import REPL
from opendxa.dana.sandbox.context_manager import ContextManager
from opendxa.dana.sandbox.interpreter.executor.expression_evaluator import ExpressionEvaluator
from opendxa.dana.sandbox.interpreter.interpreter import Interpreter
from opendxa.dana.sandbox.parser.dana_parser import DanaParser
from opendxa.dana.sandbox.sandbox_context import SandboxContext

print("\n" + "=" * 50)
print("DIAGNOSTIC EXECUTION PATHS TEST")
print("=" * 50)

# THE IDENTICAL INPUT STRING TO TEST
INPUT_STRING = 'reason("what is")'

# Create resources
context = SandboxContext()
try:
    llm_resource = LLMResource()
    context.set("system.llm_resource", llm_resource)
except Exception as e:
    print(f"Warning: Cannot create LLM resource: {e}")
    print("Continuing without LLM resource")

print("\n" + "-" * 50)
print("TEST 1: Test Environment Execution Path")
print("-" * 50)

# Create interpreter and parser as would be done in tests
interpreter = Interpreter(context)
parser = DanaParser()

print(f"\nParsing in test environment: {INPUT_STRING}")
# This is how tests typically execute code
program = parser.parse(f"result = {INPUT_STRING}", do_type_check=False)
print(f"Program AST: {program}")

# Debug: Print the function call object in the parsed program
for statement in program.statements:
    if hasattr(statement, "value") and hasattr(statement.value, "name"):
        print(f"Function call name: {statement.value.name}")
        print(f"Function args type: {type(statement.value.args)}")
        print(f"Function args: {statement.value.args}")

print("\nExecuting program (test-like execution):")
try:
    result = interpreter.execute_program(program)
    print(f"Execution successful, result type: {type(result)}")
except Exception as e:
    print(f"Error during execution: {e}")

print("\n" + "-" * 50)
print("TEST 2: REPL Environment Execution Path")
print("-" * 50)

# Create a fresh REPL (this is how the REPL would process the input)
repl = REPL(llm_resource=llm_resource)

print(f"\nExecuting in REPL: {INPUT_STRING}")
# This is how the REPL executes code
try:
    # Capture how the REPL parses and processes this
    result = repl.execute(INPUT_STRING)
    print(f"REPL execution successful, result type: {type(result)}")
except Exception as e:
    print(f"Error during REPL execution: {e}")

print("\n" + "-" * 50)
print("TEST 3: Step-by-step REPL parsing")
print("-" * 50)

# Let's manually trace the REPL parsing process
print(f"\nManually tracing REPL parsing of: {INPUT_STRING}")

# Step 1: Parse using REPL's parser
repl_parser = DanaParser()
parse_result = repl_parser.parse(INPUT_STRING, do_type_check=False)
print(f"REPL parser result type: {type(parse_result)}")
print(f"REPL parser result: {parse_result}")

# Step 2: Examine the parsed statements
if hasattr(parse_result, "statements"):
    for i, statement in enumerate(parse_result.statements):
        print(f"\nStatement {i} type: {type(statement)}")
        print(f"Statement {i}: {statement}")

        # If it's a function call, examine in detail
        if hasattr(statement, "name"):
            print(f"Function name: {statement.name}")
            print(f"Function args: {statement.args}")

            # Show how args are processed in the evaluator
            context_manager = ContextManager(context)
            evaluator = ExpressionEvaluator(context_manager)
            evaluator.interpreter = interpreter

            print("\nTracing how evaluator would process this function call:")
            try:
                result = evaluator._evaluate_function_call(statement, None)
                print("Function evaluation successful")
            except Exception as e:
                print(f"Function evaluation error: {e}")

print("\n" + "=" * 50)
print("TESTS COMPLETE")
print("=" * 50)
