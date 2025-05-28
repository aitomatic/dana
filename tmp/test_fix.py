#!/usr/bin/env python3

from opendxa.dana.sandbox.interpreter.dana_interpreter import DanaInterpreter
from opendxa.dana.sandbox.parser.dana_parser import DanaParser
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def test_improved_error_message():
    """Test the improved error message with the original failing case."""

    print("=== Testing Improved Error Message ===")

    # Test the original failing case
    dana_code = """
def extract_metrics(data):
    total_sales = sum(data["sales"])
    return total_sales

def format_output(metrics):
    return f"Total sales: {metrics}"

business_intelligence_pipeline = extract_metrics | format_output
test_data = {"sales": [100, 200, 300]}
result = business_intelligence_pipeline(test_data)
"""

    print("Dana code:")
    print(dana_code)
    print()

    interpreter = DanaInterpreter()
    context = SandboxContext()
    parser = DanaParser()

    try:
        program = parser.parse(dana_code)
        result = interpreter.execute_program(program, context)
        print(f"Success: {result}")
    except Exception as e:
        print("=== IMPROVED ERROR MESSAGE ===")
        print(f"Error: {e}")
        print()

        # Show the error chain
        print("=== ERROR CHAIN ===")
        current = e
        level = 1
        while current:
            print(f"Level {level}: {current}")
            current = current.__cause__
            level += 1
            if level > 5:  # Prevent infinite loops
                break


if __name__ == "__main__":
    test_improved_error_message()
