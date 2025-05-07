#!/usr/bin/env python
"""
Simple script to run the DANA REPL with minimal configuration.

This script bypasses prompt_toolkit to avoid interactive input issues
in non-terminal environments like CI/CD pipelines or when running through
external tools.

Usage:
    python run_simple_repl.py
"""

import sys
import asyncio
from opendxa.dana.runtime.repl import REPL
from opendxa.dana.runtime.interpreter import LogLevel

async def main():
    # Initialize REPL without LLM resource
    repl = REPL(log_level=LogLevel.INFO)
    
    print("\nDANA REPL (Simple Mode)")
    print("=======================")
    print("Enter DANA code or type 'exit' to quit.")
    print("This is a simplified REPL for testing core functionality.\n")
    
    while True:
        try:
            # Simple input prompt
            sys.stdout.write("dana> ")
            sys.stdout.flush()
            line = sys.stdin.readline().rstrip()
            
            # Check for exit command
            if line.lower() in ["exit", "quit"]:
                print("Exiting REPL.")
                break
                
            # Skip empty lines
            if not line.strip():
                continue
                
            # Execute the line
            await repl.execute(line)
            
        except KeyboardInterrupt:
            print("\nInput cancelled.")
        except Exception as e:
            print(f"Error: {e}")
    
    # Print final context values
    print("\nFinal context values:")
    ctx = repl.get_context()
    try:
        for scope in ["private", "public", "system"]:
            print(f"\n{scope.upper()}:")
            for key, value in ctx._state[scope].items():
                if isinstance(value, dict):
                    print(f"  {key}: <nested object>")
                else:
                    print(f"  {key}: {value}")
    except Exception as e:
        print(f"Error displaying context: {e}")

if __name__ == "__main__":
    asyncio.run(main())