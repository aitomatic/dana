#!/usr/bin/env python3
"""Test Phase 1 imports and functionality."""

import sys
import os

# Add dana directory to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

# Set up compatibility layer
from dana.compat import setup_migration_compatibility
setup_migration_compatibility()

# Pre-import new modules to ensure they're available for compatibility
import dana.core.lang.parser
import dana.core.lang.interpreter  
import dana.core.lang

def test_new_imports():
    """Test importing from new dana structure."""
    print("Testing new import paths...")
    
    try:
        from dana.core.lang.parser import DanaParser
        print("✅ dana.core.lang.parser.DanaParser")
    except ImportError as e:
        print(f"❌ dana.core.lang.parser.DanaParser: {e}")
        return False
    
    try:
        from dana.core.lang.interpreter import DanaInterpreter
        print("✅ dana.core.lang.interpreter.DanaInterpreter")
    except ImportError as e:
        print(f"❌ dana.core.lang.interpreter.DanaInterpreter: {e}")
        return False
    
    try:
        from dana.core.lang import DanaSandbox
        print("✅ dana.core.lang.DanaSandbox")
    except ImportError as e:
        print(f"❌ dana.core.lang.DanaSandbox: {e}")
        return False
    
    return True


def test_old_imports():
    """Test that old imports still work via compatibility layer."""
    print("\nTesting old import paths (with compatibility)...")
    
    try:
        from opendxa.dana.sandbox.parser import DanaParser
        print("✅ opendxa.dana.sandbox.parser.DanaParser")
    except ImportError as e:
        print(f"❌ opendxa.dana.sandbox.parser.DanaParser: {e}")
        return False
    
    try:
        from opendxa.dana.sandbox.interpreter import DanaInterpreter
        print("✅ opendxa.dana.sandbox.interpreter.DanaInterpreter")
    except ImportError as e:
        print(f"❌ opendxa.dana.sandbox.interpreter.DanaInterpreter: {e}")
        return False
    
    try:
        from opendxa.dana.sandbox import DanaSandbox
        print("✅ opendxa.dana.sandbox.DanaSandbox")
    except ImportError as e:
        print(f"❌ opendxa.dana.sandbox.DanaSandbox: {e}")
        return False
    
    return True


def test_functionality():
    """Test that Dana functionality works with new imports."""
    print("\nTesting Dana functionality...")
    
    try:
        from dana.core.lang import DanaParser, DanaSandbox
        
        # Parse a simple expression
        parser = DanaParser()
        ast = parser.parse("x = 5 + 3")
        print("✅ Parser works with new imports")
        
        # Create sandbox (basic test)
        sandbox = DanaSandbox()
        print("✅ DanaSandbox instantiation works")
        
        return True
    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        return False


if __name__ == "__main__":
    print("="*60)
    print("Phase 1 Import Testing")
    print("="*60)
    
    new_ok = test_new_imports()
    old_ok = test_old_imports()
    func_ok = test_functionality()
    
    print("\n" + "="*60)
    if new_ok and old_ok and func_ok:
        print("✅ All Phase 1 tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)