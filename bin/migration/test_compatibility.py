#!/usr/bin/env python3
"""Test import compatibility during migration."""

import sys
import importlib
from typing import List, Tuple


# Import mappings to test (old_path, new_path)
IMPORT_MAPPINGS: List[Tuple[str, str]] = [
    # These will be populated as we migrate components
    # Example:
    # ("opendxa.dana.sandbox.parser", "dana.core.lang.parser"),
]


def test_import(module_path: str) -> bool:
    """Test if a module can be imported."""
    try:
        importlib.import_module(module_path)
        return True
    except ImportError:
        return False


def test_dual_imports():
    """Test that both old and new import paths work."""
    print("Testing dual import compatibility...")
    print("=" * 60)
    
    all_passed = True
    
    for old_path, new_path in IMPORT_MAPPINGS:
        # Test new import
        new_works = test_import(new_path)
        old_works = test_import(old_path)
        
        status = "✅" if (new_works and old_works) else "❌"
        all_passed = all_passed and new_works and old_works
        
        print(f"{status} {old_path}")
        print(f"   └─ Old import: {'✓' if old_works else '✗'}")
        print(f"   └─ New import: {'✓' if new_works else '✗'}")
        
        # Test that they reference the same module
        if new_works and old_works:
            old_module = sys.modules.get(old_path)
            new_module = sys.modules.get(new_path)
            if old_module is new_module:
                print(f"   └─ Same module: ✓")
            else:
                print(f"   └─ Same module: ✗ (WARNING: Different modules!)")
                all_passed = False
    
    print("=" * 60)
    
    if not IMPORT_MAPPINGS:
        print("No import mappings configured yet.")
        return True
    
    if all_passed:
        print("✅ All compatibility tests passed!")
    else:
        print("❌ Some compatibility tests failed!")
    
    return all_passed


if __name__ == "__main__":
    # Set up path to include dana directory
    import os
    dana_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    if dana_path not in sys.path:
        sys.path.insert(0, dana_path)
    
    # Test compatibility
    success = test_dual_imports()
    sys.exit(0 if success else 1)