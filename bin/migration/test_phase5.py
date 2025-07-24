#!/usr/bin/env python3
"""Test Phase 5 imports and functionality."""

import os
import sys

# Add dana directory to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

# Set up compatibility layer
from dana.compat import setup_migration_compatibility

setup_migration_compatibility()

# Pre-import new modules to ensure they're available for compatibility

def test_poet_imports():
    """Test importing POET components from new dana structure."""
    print("Testing POET import paths...")
    
    try:
        from dana.frameworks.poet import POETConfig, POETResult, poet
        print("✅ dana.frameworks.poet: poet, POETConfig, POETResult")
    except ImportError as e:
        print(f"❌ dana.frameworks.poet: {e}")
        return False
    
    try:
        from dana.frameworks.poet import POETEnhancer
        print("✅ dana.frameworks.poet.POETEnhancer")
    except ImportError as e:
        print(f"❌ dana.frameworks.poet.POETEnhancer: {e}")
        return False
    
    return True


def test_poet_domains():
    """Test that POET domains can be imported."""
    print("\nTesting POET domain imports...")
    
    domains = [
        'base',
        'computation',
        'llm_optimization',
        'ml_monitoring',
        'prompt_optimization'
    ]
    
    success = True
    for domain in domains:
        try:
            __import__(f'dana.frameworks.poet.domains.{domain}')
            print(f"✅ dana.frameworks.poet.domains.{domain}")
        except ImportError as e:
            print(f"❌ dana.frameworks.poet.domains.{domain}: {e}")
            success = False
    
    return success


def test_poet_phases():
    """Test that POET phases can be imported."""
    print("\nTesting POET phase imports...")
    
    phases = ['perceive', 'operate', 'enforce']
    
    success = True
    for phase in phases:
        try:
            __import__(f'dana.frameworks.poet.{phase}')
            print(f"✅ dana.frameworks.poet.{phase}")
        except ImportError as e:
            print(f"❌ dana.frameworks.poet.{phase}: {e}")
            success = False
    
    return success


def test_poet_decorator():
    """Test that POET decorator works."""
    print("\nTesting POET decorator...")
    
    try:
        from dana.frameworks.poet import poet
        
        # Try to access the decorator (basic functionality test)
        if callable(poet):
            print("✅ POET decorator is callable")
            return True
        else:
            print("❌ POET decorator is not callable")
            return False
    except Exception as e:
        print(f"❌ POET decorator test failed: {e}")
        return False


def test_framework_integration():
    """Test that POET integrates with dana.frameworks."""
    print("\nTesting framework integration...")
    
    try:
        from dana.frameworks import POETConfig, poet
        print("✅ dana.frameworks POET components accessible")
        
        return True
    except ImportError as e:
        print(f"❌ dana.frameworks integration: {e}")
        return False


def test_top_level_integration():
    """Test that POET integrates with top-level dana."""
    print("\nTesting top-level integration...")
    
    try:
        from dana import POETConfig, poet
        print("✅ Top-level dana POET components accessible")
        
        return True
    except ImportError as e:
        print(f"❌ Top-level dana integration: {e}")
        return False


if __name__ == "__main__":
    print("="*60)
    print("Phase 5 Testing - POET Framework")
    print("="*60)
    
    poet_ok = test_poet_imports()
    domains_ok = test_poet_domains()
    phases_ok = test_poet_phases()
    decorator_ok = test_poet_decorator()
    framework_ok = test_framework_integration()
    toplevel_ok = test_top_level_integration()
    
    print("\n" + "="*60)
    if poet_ok and domains_ok and phases_ok and decorator_ok and framework_ok and toplevel_ok:
        print("✅ All Phase 5 tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)