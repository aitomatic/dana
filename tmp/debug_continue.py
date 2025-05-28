#!/usr/bin/env python3

from opendxa.dana.sandbox.interpreter.dana_interpreter import DanaInterpreter
from opendxa.dana.sandbox.parser.dana_parser import DanaParser
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def test_continue_debug():
    """Debug continue statement behavior."""
    
    print("=== DEBUGGING CONTINUE STATEMENTS ===")
    
    # Test 1: Simple while loop with continue
    print("\n1. WHILE LOOP TEST:")
    while_code = """
x = 0
sum = 0
while x < 5:
    x = x + 1
    if x % 2 == 0:  # Skip even numbers
        continue
    sum = sum + x
"""
    
    print("Code:", while_code.strip())
    
    interpreter = DanaInterpreter()
    context = SandboxContext()
    parser = DanaParser()
    
    try:
        program = parser.parse(while_code)
        result = interpreter.execute_program(program, context)
        print(f"Final x: {context.get('local.x')}")
        print(f"Final sum: {context.get('local.sum')}")
        print(f"Expected sum: 9 (1 + 3 + 5)")
        
        # Manual calculation:
        # x=1: 1%2=1 (odd), sum = 0 + 1 = 1
        # x=2: 2%2=0 (even), continue (skip sum)
        # x=3: 3%2=1 (odd), sum = 1 + 3 = 4  
        # x=4: 4%2=0 (even), continue (skip sum)
        # x=5: 5%2=1 (odd), sum = 4 + 5 = 9
        
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Simple for loop with continue
    print("\n2. FOR LOOP TEST:")
    for_code = """
sum = 0
for i in [1, 2, 3, 4, 5]:
    if i % 2 == 0:  # Skip even numbers
        continue
    sum = sum + i
"""
    
    print("Code:", for_code.strip())
    
    interpreter = DanaInterpreter()
    context = SandboxContext()
    parser = DanaParser()
    
    try:
        program = parser.parse(for_code)
        result = interpreter.execute_program(program, context)
        print(f"Final i: {context.get('local.i')}")
        print(f"Final sum: {context.get('local.sum')}")
        print(f"Expected sum: 9 (1 + 3 + 5)")
        
        # Manual calculation:
        # i=1: 1%2=1 (odd), sum = 0 + 1 = 1
        # i=2: 2%2=0 (even), continue (skip sum)
        # i=3: 3%2=1 (odd), sum = 1 + 3 = 4
        # i=4: 4%2=0 (even), continue (skip sum)  
        # i=5: 5%2=1 (odd), sum = 4 + 5 = 9
        
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Simple loop without continue (control)
    print("\n3. CONTROL TEST (no continue):")
    control_code = """
sum = 0
for i in [1, 3, 5]:
    sum = sum + i
"""
    
    print("Code:", control_code.strip())
    
    interpreter = DanaInterpreter()
    context = SandboxContext()
    parser = DanaParser()
    
    try:
        program = parser.parse(control_code)
        result = interpreter.execute_program(program, context)
        print(f"Final i: {context.get('local.i')}")
        print(f"Final sum: {context.get('local.sum')}")
        print(f"Expected sum: 9 (1 + 3 + 5)")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_continue_debug() 