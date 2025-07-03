#!/usr/bin/env python3
"""Test Phase 7 imports and functionality."""

import sys
import os

# Add dana directory to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

# Set up compatibility layer
from dana.compat import setup_migration_compatibility
setup_migration_compatibility()

# Pre-import new modules to ensure they're available for compatibility
import dana.frameworks.agent

def test_agent_imports():
    """Test importing Agent components from new dana structure."""
    print("Testing Agent import paths...")
    
    try:
        from dana.frameworks.agent import Agent, AgentFactory, DomainExpertise
        print("✅ dana.frameworks.agent: Agent, AgentFactory, DomainExpertise")
    except ImportError as e:
        print(f"❌ dana.frameworks.agent: {e}")
        return False
    
    try:
        from dana.frameworks.agent import CapabilityFactory, MemoryCapability
        print("✅ dana.frameworks.agent: CapabilityFactory, MemoryCapability")
    except ImportError as e:
        print(f"❌ dana.frameworks.agent capabilities: {e}")
        return False
    
    return True


def test_agent_components():
    """Test that Agent components can be imported."""
    print("\nTesting Agent component imports...")
    
    components = [
        ('agent', 'Agent'),
        ('agent', 'AgentResponse'),
        ('agent_factory', 'AgentFactory'),
        ('agent_config', 'AgentConfig'),
        ('agent_runtime', 'AgentRuntime')
    ]
    
    success = True
    for module_path, component in components:
        try:
            module = __import__(f'dana.frameworks.agent.{module_path}', fromlist=[component])
            getattr(module, component)
            print(f"✅ dana.frameworks.agent.{module_path}.{component}")
        except (ImportError, AttributeError) as e:
            print(f"❌ dana.frameworks.agent.{module_path}.{component}: {e}")
            success = False
    
    return success


def test_capability_components():
    """Test that capability components work."""
    print("\nTesting capability component imports...")
    
    capability_components = [
        ('capability.domain_expertise', 'DomainExpertise'),
        ('capability.memory_capability', 'MemoryCapability'),
        ('capability.capability_factory', 'CapabilityFactory')
    ]
    
    success = True
    for module_path, component in capability_components:
        try:
            module = __import__(f'dana.frameworks.agent.{module_path}', fromlist=[component])
            getattr(module, component)
            print(f"✅ dana.frameworks.agent.{module_path}.{component}")
        except (ImportError, AttributeError) as e:
            print(f"❌ dana.frameworks.agent.{module_path}.{component}: {e}")
            success = False
    
    return success


def test_resource_components():
    """Test that resource components work."""
    print("\nTesting resource component imports...")
    
    resource_components = [
        ('resource.agent_resource', 'AgentResource'),
        ('resource.expert_resource', 'ExpertResource'),
        ('resource.resource_factory', 'ResourceFactory')
    ]
    
    success = True
    for module_path, component in resource_components:
        try:
            module = __import__(f'dana.frameworks.agent.{module_path}', fromlist=[component])
            getattr(module, component)
            print(f"✅ dana.frameworks.agent.{module_path}.{component}")
        except (ImportError, AttributeError) as e:
            print(f"❌ dana.frameworks.agent.{module_path}.{component}: {e}")
            success = False
    
    return success


def test_framework_integration():
    """Test that Agent integrates with dana.frameworks."""
    print("\nTesting framework integration...")
    
    try:
        from dana.frameworks import Agent, AgentFactory
        print("✅ dana.frameworks Agent components accessible")
        
        return True
    except ImportError as e:
        print(f"❌ dana.frameworks integration: {e}")
        return False


def test_top_level_integration():
    """Test that Agent integrates with top-level dana."""
    print("\nTesting top-level integration...")
    
    try:
        from dana import Agent
        print("✅ Top-level dana Agent accessible")
        
        return True
    except ImportError as e:
        print(f"❌ Top-level dana integration: {e}")
        return False


def test_basic_functionality():
    """Test basic Agent functionality."""
    print("\nTesting basic Agent functionality...")
    
    try:
        from dana.frameworks.agent import Agent
        
        # Test basic Agent creation (without actually running it)
        if callable(Agent):
            print("✅ Agent class is callable")
            return True
        else:
            print("❌ Agent class is not callable")
            return False
            
    except Exception as e:
        print(f"❌ Agent functionality test failed: {e}")
        return False


if __name__ == "__main__":
    print("="*60)
    print("Phase 7 Testing - Agent Framework")
    print("="*60)
    
    agent_ok = test_agent_imports()
    components_ok = test_agent_components()
    capabilities_ok = test_capability_components()
    resources_ok = test_resource_components()
    framework_ok = test_framework_integration()
    toplevel_ok = test_top_level_integration()
    functionality_ok = test_basic_functionality()
    
    print("\n" + "="*60)
    if agent_ok and components_ok and capabilities_ok and resources_ok and framework_ok and toplevel_ok and functionality_ok:
        print("✅ All Phase 7 tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)