#!/usr/bin/env python3
"""Test Phase 6 imports and functionality."""

import sys
import os

# Add dana directory to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

# Set up compatibility layer
from dana.compat import setup_migration_compatibility
setup_migration_compatibility()

# Pre-import new modules to ensure they're available for compatibility
import dana.frameworks.knows

def test_knows_imports():
    """Test importing KNOWS components from new dana structure."""
    print("Testing KNOWS import paths...")
    
    try:
        from dana.frameworks.knows import DocumentLoader, DocumentParser, KnowledgePoint
        print("✅ dana.frameworks.knows: DocumentLoader, DocumentParser, KnowledgePoint")
    except ImportError as e:
        print(f"❌ dana.frameworks.knows: {e}")
        return False
    
    try:
        from dana.frameworks.knows import MetaKnowledgeExtractor
        print("✅ dana.frameworks.knows.MetaKnowledgeExtractor")
    except ImportError as e:
        print(f"❌ dana.frameworks.knows.MetaKnowledgeExtractor: {e}")
        return False
    
    return True


def test_knows_components():
    """Test that KNOWS components can be imported."""
    print("\nTesting KNOWS component imports...")
    
    components = [
        ('core.base', 'Document'),
        ('core.registry', 'KORegistry'),
        ('document.loader', 'DocumentLoader'),
        ('document.parser', 'DocumentParser'),
        ('document.extractor', 'TextExtractor')
    ]
    
    success = True
    for module_path, component in components:
        try:
            module = __import__(f'dana.frameworks.knows.{module_path}', fromlist=[component])
            getattr(module, component)
            print(f"✅ dana.frameworks.knows.{module_path}.{component}")
        except (ImportError, AttributeError) as e:
            print(f"❌ dana.frameworks.knows.{module_path}.{component}: {e}")
            success = False
    
    return success


def test_extraction_components():
    """Test that extraction components work."""
    print("\nTesting extraction component imports...")
    
    extraction_components = [
        ('extraction.meta.extractor', 'MetaKnowledgeExtractor'),
        ('extraction.meta.categorizer', 'KnowledgeCategorizer'),
        ('extraction.context.expander', 'ContextExpander'),
        ('extraction.context.similarity', 'SimilaritySearcher')
    ]
    
    success = True
    for module_path, component in extraction_components:
        try:
            module = __import__(f'dana.frameworks.knows.{module_path}', fromlist=[component])
            getattr(module, component)
            print(f"✅ dana.frameworks.knows.{module_path}.{component}")
        except (ImportError, AttributeError) as e:
            print(f"❌ dana.frameworks.knows.{module_path}.{component}: {e}")
            success = False
    
    return success


def test_framework_integration():
    """Test that KNOWS integrates with dana.frameworks."""
    print("\nTesting framework integration...")
    
    try:
        from dana.frameworks import DocumentLoader, KnowledgePoint
        print("✅ dana.frameworks KNOWS components accessible")
        
        return True
    except ImportError as e:
        print(f"❌ dana.frameworks integration: {e}")
        return False


def test_top_level_integration():
    """Test that KNOWS integrates with top-level dana."""
    print("\nTesting top-level integration...")
    
    try:
        from dana import DocumentLoader, KnowledgePoint
        print("✅ Top-level dana KNOWS components accessible")
        
        return True
    except ImportError as e:
        print(f"❌ Top-level dana integration: {e}")
        return False


def test_basic_functionality():
    """Test basic KNOWS functionality."""
    print("\nTesting basic KNOWS functionality...")
    
    try:
        from dana.frameworks.knows.core.base import KnowledgePoint
        
        # Test basic KnowledgePoint creation
        kp = KnowledgePoint(
            id="test-1",
            type="fact",
            content="Test knowledge point",
            context={},
            confidence=0.9,
            metadata={}
        )
        
        if hasattr(kp, 'content') and kp.content == "Test knowledge point":
            print("✅ KnowledgePoint creation works")
            return True
        else:
            print("❌ KnowledgePoint creation failed")
            return False
            
    except Exception as e:
        print(f"❌ KNOWS functionality test failed: {e}")
        return False


if __name__ == "__main__":
    print("="*60)
    print("Phase 6 Testing - KNOWS Framework")
    print("="*60)
    
    knows_ok = test_knows_imports()
    components_ok = test_knows_components()
    extraction_ok = test_extraction_components()
    framework_ok = test_framework_integration()
    toplevel_ok = test_top_level_integration()
    functionality_ok = test_basic_functionality()
    
    print("\n" + "="*60)
    if knows_ok and components_ok and extraction_ok and framework_ok and toplevel_ok and functionality_ok:
        print("✅ All Phase 6 tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)