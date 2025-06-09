#!/usr/bin/env python3
"""
Demo script for Step 1: Core Dana-Python Integration

This demonstrates the successful implementation of:
- Dana module import system
- Function wrapping and calling
- Basic argument passing and return values
"""

import os
import sys

# Add the project root to sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def main():
    print("🎯 Dana-Python Integration Step 1 Demo")
    print("=" * 40)
    
    # Install the Dana import system
    print("Installing Dana runtime...")
    import opendxa.dana.runtime  # noqa: F401
    print("✅ Dana runtime installed")
    
    # Check if the import system is actually installed
    from opendxa.dana.runtime.import_system import DanaModuleFinder
    dana_finders = [f for f in sys.meta_path if isinstance(f, DanaModuleFinder)]
    print(f"🔍 Dana module finders in sys.meta_path: {len(dana_finders)}")
    if dana_finders:
        print(f"   Search paths: {dana_finders[0].dana_paths}")
    
    # Import a Dana module
    print("\nImporting Dana module...")
    import dana.simple_module
    print("✅ Dana module imported successfully")
    
    # Show what functions are available
    wrapper = dana.simple_module._dana_wrapper
    functions = wrapper.get_function_names()
    print(f"📋 Available functions: {functions}")
    
    # Demonstrate function calls
    print("\n🧪 Function Call Demonstrations:")
    print("-" * 30)
    
    # Demo 1: Reasoning function
    print("1. Dana reasoning function:")
    result = dana.simple_module.reason_about("quantum computing")
    print("   Input: 'quantum computing'")
    print(f"   Output: {result}")
    
    # Demo 2: Mathematical function
    print("\n2. Dana mathematical function:")
    result = dana.simple_module.add_numbers(15, 27)
    print("   Input: 15, 27")
    print(f"   Output: {result}")
    
    # Demo 3: String formatting
    print("\n3. Dana string formatting:")
    result = dana.simple_module.get_greeting("Python")
    print("   Input: 'Python'")
    print(f"   Output: {result}")
    
    print("\n🎉 Step 1 Demo Complete!")
    print("=" * 40)
    print("✅ Dana modules can be imported like Python modules")
    print("✅ Dana functions can be called from Python")
    print("✅ Arguments and return values work seamlessly")
    print("✅ Ready for Step 2: Advanced Function Wrapping")

if __name__ == "__main__":
    main() 