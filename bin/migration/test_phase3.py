#!/usr/bin/env python3
"""Test Phase 3 imports and functionality."""

import os
import sys

# Add dana directory to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

# Set up compatibility layer
from dana.compat import setup_migration_compatibility

setup_migration_compatibility()

# Pre-import new modules to ensure they're available for compatibility

def test_stdlib_imports():
    """Test importing standard library components from new dana structure."""
    print("Testing stdlib import paths...")
    
    try:
        from dana.core.stdlib import DanaFunction, FunctionRegistry
        print("✅ dana.core.stdlib.FunctionRegistry, DanaFunction")
    except ImportError as e:
        print(f"❌ dana.core.stdlib: {e}")
        return False
    
    try:
        from dana.core.stdlib.core import register_core_functions
        print("✅ dana.core.stdlib.core.register_core_functions")
    except ImportError as e:
        print(f"❌ dana.core.stdlib.core: {e}")
        return False
    
    return True


def test_core_functions():
    """Test that core functions can be imported."""
    print("\nTesting core function imports...")
    
    function_modules = [
        'log_function',
        'reason_function', 
        'str_function',
        'print_function',
        'agent_function',
        'poet_function'
    ]
    
    success = True
    for module in function_modules:
        try:
            __import__(f'dana.core.stdlib.core.{module}')
            print(f"✅ dana.core.stdlib.core.{module}")
        except ImportError as e:
            print(f"❌ dana.core.stdlib.core.{module}: {e}")
            success = False
    
    return success


def test_function_registry():
    """Test that function registry works."""
    print("\nTesting function registry...")
    
    try:
        from dana.core.stdlib import FunctionRegistry
        
        # Create a registry instance
        registry = FunctionRegistry()
        print("✅ FunctionRegistry instantiation works")
        
        return True
    except Exception as e:
        print(f"❌ Function registry test failed: {e}")
        return False


def test_core_integration():
    """Test that stdlib integrates with dana.core."""
    print("\nTesting dana.core stdlib integration...")
    
    try:
        from dana.core import FunctionRegistry, register_core_functions
        print("✅ dana.core stdlib components accessible")
        
        return True
    except ImportError as e:
        print(f"❌ dana.core stdlib integration: {e}")
        return False


def test_dana_execution():
    """Test that Dana execution still works with new stdlib structure."""
    print("\nTesting Dana execution with stdlib...")
    
    try:
        # Test that we can still parse and execute Dana code
        from dana.core import DanaParser
        
        parser = DanaParser()
        ast = parser.parse('x = 5\nlog("test")')
        print("✅ Dana parsing works with new stdlib structure")
        
        return True
    except Exception as e:
        print(f"❌ Dana execution test failed: {e}")
        return False


if __name__ == "__main__":
    print("="*60)
    print("Phase 3 Testing - Standard Library Functions")
    print("="*60)
    
    stdlib_ok = test_stdlib_imports()
    core_ok = test_core_functions()
    registry_ok = test_function_registry()
    integration_ok = test_core_integration()
    execution_ok = test_dana_execution()
    
    print("\n" + "="*60)
    if stdlib_ok and core_ok and registry_ok and integration_ok and execution_ok:
        print("✅ All Phase 3 tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)