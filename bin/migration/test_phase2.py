#!/usr/bin/env python3
"""Test Phase 2 imports and functionality."""

import os
import sys

# Add dana directory to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

# Set up compatibility layer
from dana.compat import setup_migration_compatibility

setup_migration_compatibility()

# Pre-import new modules to ensure they're available for compatibility


def test_runtime_imports():
    """Test importing runtime components from new dana structure."""
    print("Testing runtime import paths...")
    
    try:
        from dana.core.runtime.modules import loader, registry
        print("✅ dana.core.runtime.modules.registry, loader")
    except ImportError as e:
        print(f"❌ dana.core.runtime.modules: {e}")
        return False
    
    try:
        from dana.core.runtime import registry as rt_registry
        print("✅ dana.core.runtime.registry")
    except ImportError as e:
        print(f"❌ dana.core.runtime.registry: {e}")
        return False
    
    return True


def test_repl_imports():
    """Test importing REPL components from new dana structure."""
    print("\nTesting REPL import paths...")
    
    try:
        from dana.core.repl import dana_main, dana_repl
        print("✅ dana.core.repl.dana_main, dana_repl")
    except ImportError as e:
        print(f"❌ dana.core.repl: {e}")
        return False
    
    try:
        from dana.core.cli.dana import main
        print("✅ dana.core.repl.dana.main")
    except ImportError as e:
        print(f"❌ dana.core.repl.dana.main: {e}")
        return False
    
    return True


def test_core_imports():
    """Test importing from dana.core."""
    print("\nTesting dana.core imports...")
    
    try:
        from dana.core import DanaParser, DanaSandbox, registry
        print("✅ dana.core: DanaParser, DanaSandbox, registry")
    except ImportError as e:
        print(f"❌ dana.core: {e}")
        return False
    
    return True


def test_functionality():
    """Test that module system and REPL functionality works."""
    print("\nTesting functionality...")
    
    try:
        from dana.core import DanaParser, registry
        
        # Basic parser test
        parser = DanaParser()
        ast = parser.parse("x = 5")
        print("✅ Parser works with dana.core imports")
        
        # Basic registry test (if it has callable methods)
        if hasattr(registry, '__name__'):
            print("✅ Registry module accessible")
        
        return True
    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        return False


if __name__ == "__main__":
    print("="*60)
    print("Phase 2 Import Testing - Runtime and Module System")
    print("="*60)
    
    runtime_ok = test_runtime_imports()
    repl_ok = test_repl_imports()
    core_ok = test_core_imports()
    func_ok = test_functionality()
    
    print("\n" + "="*60)
    if runtime_ok and repl_ok and core_ok and func_ok:
        print("✅ All Phase 2 tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)