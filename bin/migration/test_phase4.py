#!/usr/bin/env python3
"""Test Phase 4 imports and functionality."""

import os
import sys

# Add dana directory to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

# Set up compatibility layer
from dana.compat import setup_migration_compatibility

setup_migration_compatibility()

# Pre-import new modules to ensure they're available for compatibility

def test_common_imports():
    """Test importing common utilities from new dana structure."""
    print("Testing common utility import paths...")
    
    try:
        from dana.common import DANA_LOGGER, DXA_LOGGER, DXALogger
        print("✅ dana.common loggers: DXA_LOGGER, DANA_LOGGER, DXALogger")
    except ImportError as e:
        print(f"❌ dana.common loggers: {e}")
        return False
    
    try:
        from dana.common.utils.logging import DANA_LOGGER as dana_log
        print("✅ dana.common.utils.logging.DANA_LOGGER")
    except ImportError as e:
        print(f"❌ dana.common.utils.logging.DANA_LOGGER: {e}")
        return False
    
    return True


def test_mixins():
    """Test that mixins can be imported."""
    print("\nTesting mixin imports...")
    
    mixin_modules = [
        'loggable',
        'configurable', 
        'identifiable',
        'queryable',
        'registerable'
    ]
    
    success = True
    for module in mixin_modules:
        try:
            __import__(f'dana.common.mixins.{module}')
            print(f"✅ dana.common.mixins.{module}")
        except ImportError as e:
            print(f"❌ dana.common.mixins.{module}: {e}")
            success = False
    
    return success


def test_resources():
    """Test that resources can be imported."""
    print("\nTesting resource imports...")
    
    try:
        from dana.common.resource import LLMResource, MemoryResource
        print("✅ dana.common.resource: LLMResource, MemoryResource")
    except ImportError as e:
        print(f"❌ dana.common.resource: {e}")
        return False
    
    try:
        from dana.common.resource.llm_resource import LLMResource as LLM
        print("✅ dana.common.resource.llm_resource.LLMResource")
    except ImportError as e:
        print(f"❌ dana.common.resource.llm_resource: {e}")
        return False
    
    return True


def test_graph_and_io():
    """Test graph and IO utilities."""
    print("\nTesting graph and IO imports...")
    
    try:
        from dana.common.graph import DirectedGraph
        print("✅ dana.common.graph.DirectedGraph")
    except ImportError as e:
        print(f"❌ dana.common.graph: {e}")
        return False
    
    try:
        from dana.common.io import ConsoleIO
        print("✅ dana.common.io.ConsoleIO")
    except ImportError as e:
        print(f"❌ dana.common.io: {e}")
        return False
    
    return True


def test_logger_functionality():
    """Test that both loggers work."""
    print("\nTesting logger functionality...")
    
    try:
        from dana.common import DANA_LOGGER, DXA_LOGGER
        
        # Test that loggers can be used
        DXA_LOGGER.info("Testing DXA_LOGGER compatibility")
        DANA_LOGGER.info("Testing new DANA_LOGGER")
        
        print("✅ Both loggers functional")
        return True
    except Exception as e:
        print(f"❌ Logger functionality test failed: {e}")
        return False


def test_integration():
    """Test that common utilities integrate properly."""
    print("\nTesting integration...")
    
    try:
        # Test accessing through dana.common
        from dana.common import DXALogger, Loggable
        
        print("✅ Integration with dana.common works")
        return True
    except ImportError as e:
        print(f"❌ Integration test failed: {e}")
        return False


if __name__ == "__main__":
    print("="*60)
    print("Phase 4 Testing - Common Utilities")
    print("="*60)
    
    common_ok = test_common_imports()
    mixins_ok = test_mixins()
    resources_ok = test_resources()
    graph_io_ok = test_graph_and_io()
    logger_ok = test_logger_functionality()
    integration_ok = test_integration()
    
    print("\n" + "="*60)
    if common_ok and mixins_ok and resources_ok and graph_io_ok and logger_ok and integration_ok:
        print("✅ All Phase 4 tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)