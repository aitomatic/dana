"""
Test for the new global registry system.

This test verifies that the new registry system works correctly
before we start integrating it into the Dana system.
"""

import unittest
from dataclasses import dataclass
from typing import Any

from dana.core.lang.interpreter.struct_system import StructInstance, StructType


# Mock classes for testing
@dataclass
class MockAgentType:
    name: str
    fields: dict[str, str]
    field_order: list[str]
    field_defaults: dict[str, Any] = None


@dataclass
class MockResourceType:
    name: str
    fields: dict[str, str]
    field_order: list[str]
    field_defaults: dict[str, Any] = None


@dataclass
class MockStructType:
    name: str
    fields: dict[str, str]
    field_order: list[str]
    field_defaults: dict[str, Any] = None


class TestNewGlobalRegistry(unittest.TestCase):
    """Test the new global registry system."""

    def setUp(self):
        """Set up test fixtures."""
        from dana.registry import clear_all

        clear_all()

    def test_global_registry_singleton(self):
        """Test that GlobalRegistry is a singleton."""
        from dana.registry import GLOBAL_REGISTRY

        registry1 = GLOBAL_REGISTRY
        registry2 = GLOBAL_REGISTRY

        self.assertIs(registry1, registry2)

    def test_type_registration(self):
        """Test type registration and retrieval."""
        from dana.registry import (
            get_agent_type,
            get_resource_type,
            get_struct_type,
            register_agent_type,
            register_resource_type,
            register_struct_type,
        )

        # Create mock types
        agent_type = MockAgentType("TestAgent", {"name": "str"}, ["name"])
        resource_type = MockResourceType("TestResource", {"url": "str"}, ["url"])
        struct_type = MockStructType("TestStruct", {"value": "int"}, ["value"])

        # Register types
        register_agent_type(agent_type)
        register_resource_type(resource_type)
        register_struct_type(struct_type)

        # Retrieve types
        retrieved_agent = get_agent_type("TestAgent")
        retrieved_resource = get_resource_type("TestResource")
        retrieved_struct = get_struct_type("TestStruct")

        # Verify retrieval
        self.assertIs(retrieved_agent, agent_type)
        self.assertIs(retrieved_resource, resource_type)
        self.assertIs(retrieved_struct, struct_type)

    def test_struct_function_registration(self):
        """Test struct function registration and lookup."""
        from dana.registry import has_struct_function, lookup_struct_function, register_struct_function

        # Create mock functions
        def plan_method(agent, task):
            return f"Planning: {task}"

        def solve_method(agent, problem):
            return f"Solving: {problem}"

        # Register struct functions
        register_struct_function("AgentInstance", "plan", plan_method)
        register_struct_function("AgentInstance", "solve", solve_method)

        # Test lookup
        plan_func = lookup_struct_function("AgentInstance", "plan")
        solve_func = lookup_struct_function("AgentInstance", "solve")

        self.assertIs(plan_func, plan_method)
        self.assertIs(solve_func, solve_method)

        # Test existence checks
        self.assertTrue(has_struct_function("AgentInstance", "plan"))
        self.assertTrue(has_struct_function("AgentInstance", "solve"))
        self.assertFalse(has_struct_function("AgentInstance", "nonexistent"))

    def test_instance_tracking(self):
        """Test instance tracking functionality."""
        from dana.registry import GLOBAL_REGISTRY

        registry = GLOBAL_REGISTRY

        # Create proper StructType and StructInstance objects
        agent_struct_type = StructType("TestAgent", {"name": "str"}, ["name"], {"name": "Agent name"})
        resource_struct_type = StructType("TestResource", {"url": "str"}, ["url"], {"url": "Resource URL"})

        agent_instance = StructInstance(agent_struct_type, {"name": "Alice"})
        resource_instance = StructInstance(resource_struct_type, {"url": "https://example.com"})

        # Track instances
        registry.track_agent_instance(agent_instance, "alice_agent")
        registry.track_resource_instance(resource_instance, "main_db")

        # List instances
        agent_instances = registry.list_agent_instances()
        resource_instances = registry.list_resource_instances()

        self.assertEqual(len(agent_instances), 1)
        self.assertEqual(len(resource_instances), 1)
        self.assertIn(agent_instance, agent_instances)
        self.assertIn(resource_instance, resource_instances)

    def test_registry_statistics(self):
        """Test registry statistics."""
        from dana.registry import GLOBAL_REGISTRY, register_agent_type, register_struct_function

        registry = GLOBAL_REGISTRY

        # Add some data
        agent_type = MockAgentType("TestAgent", {"name": "str"}, ["name"])
        register_agent_type(agent_type)

        def test_method(agent):
            return "test"

        register_struct_function("AgentInstance", "test", test_method)

        # Get statistics
        stats = registry.get_statistics()

        self.assertEqual(stats["types"]["agent_types"], 1)
        self.assertEqual(stats["struct_functions"]["total_methods"], 1)
        self.assertEqual(stats["types"]["resource_types"], 0)
        self.assertEqual(stats["types"]["struct_types"], 1)  # Agent types are also registered as struct types

    def test_clear_functionality(self):
        """Test that clear_all() works correctly."""
        from dana.registry import clear_all, get_agent_type, has_struct_function, register_agent_type, register_struct_function

        # Add some data
        agent_type = MockAgentType("TestAgent", {"name": "str"}, ["name"])
        register_agent_type(agent_type)

        def test_method(agent):
            return "test"

        register_struct_function("AgentInstance", "test", test_method)

        # Verify data exists
        self.assertIsNotNone(get_agent_type("TestAgent"))
        self.assertTrue(has_struct_function("AgentInstance", "test"))

        # Clear all
        clear_all()

        # Verify data is gone
        self.assertIsNone(get_agent_type("TestAgent"))
        self.assertFalse(has_struct_function("AgentInstance", "test"))


if __name__ == "__main__":
    unittest.main()
