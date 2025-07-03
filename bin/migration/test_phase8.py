#!/usr/bin/env python3
"""Test Phase 8 imports and functionality."""

import sys
import os

# Add dana directory to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

# Set up compatibility layer
from dana.compat import setup_migration_compatibility
setup_migration_compatibility()

# Pre-import new modules to ensure they're available for compatibility
import dana.integrations

def test_integration_imports():
    """Test importing Integration components from new dana structure."""
    print("Testing Integration import paths...")
    
    try:
        from dana.integrations import DanaModule, RAGResource, McpResource
        print("✅ dana.integrations: DanaModule, RAGResource, MCPResource")
    except ImportError as e:
        print(f"❌ dana.integrations: {e}")
        return False
    
    return True


def test_python_integration():
    """Test Python-Dana integration."""
    print("\nTesting Python integration...")
    
    try:
        from dana.integrations.python import Dana, DanaModule, enable_dana_imports
        print("✅ dana.integrations.python: Dana, DanaModule, enable_dana_imports")
    except ImportError as e:
        print(f"❌ dana.integrations.python: {e}")
        return False
    
    try:
        # Test basic functionality
        dana_instance = Dana()
        if hasattr(dana_instance, 'reason'):
            print("✅ Dana instance has reason method")
        else:
            print("❌ Dana instance missing reason method")
            return False
    except Exception as e:
        print(f"❌ Python integration test failed: {e}")
        return False
    
    return True


def test_rag_integration():
    """Test RAG integration."""
    print("\nTesting RAG integration...")
    
    try:
        from dana.integrations.rag import RAGResource
        print("✅ dana.integrations.rag.RAGResource")
    except ImportError as e:
        print(f"❌ dana.integrations.rag: {e}")
        return False
    
    try:
        # Test basic functionality
        if callable(RAGResource):
            print("✅ RAGResource is callable")
        else:
            print("❌ RAGResource is not callable")
            return False
    except Exception as e:
        print(f"❌ RAG integration test failed: {e}")
        return False
    
    return True


def test_mcp_integration():
    """Test MCP integration."""
    print("\nTesting MCP integration...")
    
    try:
        from dana.integrations.mcp import McpResource, A2AAgent
        print("✅ dana.integrations.mcp: MCPResource, A2AAgent")
    except ImportError as e:
        print(f"❌ dana.integrations.mcp: {e}")
        return False
    
    try:
        # Test basic functionality
        if callable(McpResource) and callable(A2AAgent):
            print("✅ MCP components are callable")
        else:
            print("❌ MCP components not callable")
            return False
    except Exception as e:
        print(f"❌ MCP integration test failed: {e}")
        return False
    
    return True


def test_llm_integration():
    """Test LLM integration."""
    print("\nTesting LLM integration...")
    
    try:
        from dana.integrations.llm import LLMResource, LLMConfigurationManager
        print("✅ dana.integrations.llm: LLMResource, LLMConfigurationManager")
    except ImportError as e:
        print(f"❌ dana.integrations.llm: {e}")
        return False
    
    try:
        # Test basic functionality
        if callable(LLMResource) and callable(LLMConfigurationManager):
            print("✅ LLM components are callable")
        else:
            print("❌ LLM components not callable")
            return False
    except Exception as e:
        print(f"❌ LLM integration test failed: {e}")
        return False
    
    return True


def test_integration_structure():
    """Test integration directory structure."""
    print("\nTesting integration structure...")
    
    integrations = [
        'dana.integrations.python.core',
        'dana.integrations.rag.common',
        'dana.integrations.mcp.a2a',
        'dana.integrations.mcp.core'
    ]
    
    success = True
    for integration in integrations:
        try:
            __import__(integration)
            print(f"✅ {integration}")
        except ImportError as e:
            print(f"❌ {integration}: {e}")
            success = False
    
    return success


def test_basic_functionality():
    """Test basic integration functionality."""
    print("\nTesting basic integration functionality...")
    
    try:
        # Test that we can create instances
        from dana.integrations.python import Dana
        from dana.integrations.rag import RAGResource
        
        dana_instance = Dana()
        print("✅ Dana instance creation works")
        
        return True
            
    except Exception as e:
        print(f"❌ Integration functionality test failed: {e}")
        return False


if __name__ == "__main__":
    print("="*60)
    print("Phase 8 Testing - External Integrations")
    print("="*60)
    
    imports_ok = test_integration_imports()
    python_ok = test_python_integration()
    rag_ok = test_rag_integration()
    mcp_ok = test_mcp_integration()
    llm_ok = test_llm_integration()
    structure_ok = test_integration_structure()
    functionality_ok = test_basic_functionality()
    
    print("\n" + "="*60)
    if imports_ok and python_ok and rag_ok and mcp_ok and llm_ok and structure_ok and functionality_ok:
        print("✅ All Phase 8 tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)