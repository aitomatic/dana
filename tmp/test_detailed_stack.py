#!/usr/bin/env python3

from opendxa.dana.sandbox.interpreter.dana_interpreter import DanaInterpreter
from opendxa.dana.sandbox.parser.dana_parser import DanaParser
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def test_detailed_stack():
    """Test to understand the exact call flow."""

    print("=== DETAILED CALL STACK ANALYSIS ===")
    print()

    # Test case 1: Direct function call
    print("1. DIRECT FUNCTION CALL:")
    dana_code1 = """
def extract_metrics(data):
    total_sales = sum(data["sales"])
    return total_sales

result = extract_metrics({"sales": [100, 200, 300]})
"""

    print("Code:", dana_code1.strip())

    interpreter = DanaInterpreter()
    context = SandboxContext()
    parser = DanaParser()

    try:
        program = parser.parse(dana_code1)
        result = interpreter.execute_program(program, context)
        print(f"Success: {result}")
    except Exception as e:
        print(f"Error: {e}")

    print()

    # Test case 2: Pipeline call
    print("2. PIPELINE CALL:")
    dana_code2 = """
def extract_metrics(data):
    total_sales = sum(data["sales"])
    return total_sales

def format_output(metrics):
    return f"Total sales: {metrics}"

business_intelligence_pipeline = extract_metrics | format_output
test_data = {"sales": [100, 200, 300]}
result = business_intelligence_pipeline(test_data)
"""

    print("Code:", dana_code2.strip())

    interpreter = DanaInterpreter()
    context = SandboxContext()
    parser = DanaParser()

    try:
        program = parser.parse(dana_code2)
        result = interpreter.execute_program(program, context)
        print(f"Success: {result}")
    except Exception as e:
        print(f"Error: {e}")
        print()
        print("ANALYSIS:")
        print("- sum() is called inside extract_metrics()")
        print("- extract_metrics() is called by business_intelligence_pipeline")
        print("- So the error should show: sum() called from extract_metrics")
        print("- But we're seeing: sum() called from business_intelligence_pipeline")
        print("- This suggests the call stack detection is going one level too deep")


if __name__ == "__main__":
    test_detailed_stack()
