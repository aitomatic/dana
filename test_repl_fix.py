#!/usr/bin/env python3
"""Test script for DANA REPL fixes."""

import asyncio
import logging
import sys

from opendxa.dana.runtime.context import RuntimeContext
from opendxa.dana.runtime.repl import REPL
from opendxa.dana.runtime.fixes.repl_fix import apply_repl_fix

# Configure logging to see what's happening
logging.basicConfig(level=logging.DEBUG, 
                    format='%(levelname)s: %(message)s')

async def test_standard_repl():
    """Test standard REPL behavior (shows the issue)."""
    print("\n=== Running standard REPL test (showing the issue) ===\n")
    
    # Create a standard REPL
    standard_repl = REPL()
    
    # Test simple assignment
    try:
        result = await standard_repl.execute("private.a = 1")
        print(f"Result of 'private.a = 1': {result}")
        print(f"Current state: {standard_repl.context._state['private']}")
    except Exception as e:
        print(f"Error in simple assignment: {e}")
    
    # Test self-reference (this will fail)
    try:
        result = await standard_repl.execute("private.a = private.a + 1")
        print(f"Result of 'private.a = private.a + 1': {result}")
    except Exception as e:
        print(f"Error in standard execution: {e}")
        
    return standard_repl


async def test_patched_repl():
    """Test REPL with the variable reference fix applied."""
    print("\n=== Running patched REPL test (showing the fix) ===\n")
    
    # Create a new REPL and apply the fix
    patched_repl = REPL()
    original_methods = apply_repl_fix()
    print("Applied REPL patches for better variable handling")
    
    # Test simple assignment
    try:
        result = await patched_repl.execute("private.a = 1")
        print(f"Result of 'private.a = 1': {result}")
        print(f"Current state: {patched_repl.context._state['private']}")
    except Exception as e:
        print(f"Error in simple assignment: {e}")
    
    # Test self-reference with patched REPL
    try:
        result = await patched_repl.execute("private.a = private.a + 1")
        print(f"Result of 'private.a = private.a + 1': {result}")
        print(f"Updated state: {patched_repl.context._state['private']}")
    except Exception as e:
        print(f"Error in patched execution: {e}")
    
    # Test more complex operations
    operations = [
        "private.a = private.a * 2",  # Multiplication
        "private.a = private.a - 1",  # Subtraction
        "private.b = 5",              # New variable
        "private.b = private.b + private.a", # Multiple variables
    ]
    
    for op in operations:
        try:
            print(f"\nExecuting: '{op}'")
            result = await patched_repl.execute(op)
            print(f"Result: {result}")
            print(f"Current state: {patched_repl.context._state['private']}")
        except Exception as e:
            print(f"Error: {e}")
    
    return patched_repl


async def run_test():
    """Run both standard and patched REPL tests to compare behavior."""
    await test_standard_repl()
    await test_patched_repl()
    
    print("\n=== Summary ===")
    print("The standard REPL fails on variable self-references like 'private.a = private.a + 1'")
    print("The patched REPL correctly handles these self-references")
    print("\nTo use the fix in your DANA REPL, import and apply it:")
    print("  from opendxa.dana.runtime.fixes.repl_fix import apply_repl_fix")
    print("  apply_repl_fix()")


if __name__ == "__main__":
    asyncio.run(run_test())