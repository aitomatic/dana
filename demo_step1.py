#!/usr/bin/env python3
"""
Demo script for Dana Module System

This demonstrates the Dana module system functionality:
- Module importing
- Function calling
- Type safety
- Error handling
"""

import os
import sys

# Add the project root to sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def main():
    print("🎯 Dana Module System Demo")
    print("=" * 40)

    # Initialize the Dana module system
    print("Initializing Dana module system...")
    from opendxa.dana.module.core import initialize_module_system

    initialize_module_system()
    print("✅ Dana module system initialized")

    # Import a Dana module
    print("\nImporting Dana module...")
    try:
        import dana.simple_module

        print("✅ Dana module imported successfully")

        # Show module information
        print("\n📋 Module Information:")
        print(f"   Name: {dana.simple_module.__name__}")
        print(f"   File: {dana.simple_module.__file__}")
        print(f"   Exports: {dana.simple_module.__exports__}")

        # Demonstrate function calls
        print("\n🧪 Function Call Demonstrations:")
        print("-" * 30)

        # Demo 1: Basic function call
        print("1. Basic function call:")
        result = dana.simple_module.add_numbers(15, 27)
        print("   Input: 15, 27")
        print(f"   Output: {result}")

        # Demo 2: Type-safe function
        print("\n2. Type-safe function:")
        try:
            result = dana.simple_module.add_numbers("15", 27)
            print("   ❌ Should have raised TypeError")
        except TypeError as e:
            print(f"   ✅ Correctly raised TypeError: {e}")

        # Demo 3: Module-level constant
        print("\n3. Module constant:")
        print(f"   DEFAULT_GREETING = {dana.simple_module.DEFAULT_GREETING}")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

    print("\n🎉 Module System Demo Complete!")
    print("=" * 40)
    print("✅ Modules can be imported")
    print("✅ Functions can be called")
    print("✅ Type safety is enforced")
    print("✅ Error handling works")


if __name__ == "__main__":
    main()
