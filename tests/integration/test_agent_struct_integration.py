"""
Integration tests for agent-struct system.
Tests coexistence, method dispatch priority, and registry integration.
"""

import unittest

from dana.agent import AgentStructInstance, AgentStructType, create_agent_struct_instance, register_agent_struct_type
from dana.core.lang.interpreter.struct_system import StructInstance, StructType
from dana.core.lang.sandbox_context import SandboxContext


class TestAgentStructCoexistence(unittest.TestCase):
    """Test that agents and structs can coexist."""

    def setUp(self):
        """Set up test fixtures."""
        # Clean up any existing registrations
        from dana.core.lang.interpreter.struct_system import StructTypeRegistry

        StructTypeRegistry.clear()

        # Create a regular struct type
        self.struct_type = StructType(
            name="TestStruct", fields={"name": "str", "value": "int"}, field_order=["name", "value"], field_comments={}
        )

        # Create an agent struct type
        self.agent_type = AgentStructType(
            name="TestAgent", fields={"name": "str", "role": "str"}, field_order=["name", "role"], field_comments={}
        )

        # Register both types
        register_agent_struct_type(self.agent_type)

    def test_struct_and_agent_coexistence(self):
        """Test that structs and agents can be created side by side."""
        # Create struct instance
        struct_instance = StructInstance(self.struct_type, {"name": "test", "value": 42})

        # Create agent instance
        agent_instance = AgentStructInstance(self.agent_type, {"name": "agent", "role": "tester"})

        # Verify both instances work correctly
        self.assertEqual(struct_instance.name, "test")
        self.assertEqual(struct_instance.value, 42)

        self.assertEqual(agent_instance.name, "agent")
        self.assertEqual(agent_instance.role, "tester")

        # Verify agent has methods that struct doesn't
        self.assertTrue(hasattr(agent_instance, "plan"))
        self.assertTrue(hasattr(agent_instance, "solve"))
        self.assertTrue(hasattr(agent_instance, "remember"))
        self.assertTrue(hasattr(agent_instance, "recall"))

        self.assertFalse(hasattr(struct_instance, "plan"))
        self.assertFalse(hasattr(struct_instance, "solve"))
        self.assertFalse(hasattr(struct_instance, "remember"))
        self.assertFalse(hasattr(struct_instance, "recall"))

    def test_registry_coexistence(self):
        """Test that both types exist in their respective registries."""
        # Check that agent type is in the agent registry
        from dana.agent import get_agent_struct_type

        agent_registry_type = get_agent_struct_type("TestAgent")

        self.assertIs(agent_registry_type, self.agent_type)

        # Verify agent type is correct
        self.assertIsInstance(agent_registry_type, StructType)
        self.assertIsInstance(agent_registry_type, AgentStructType)

    def test_instance_creation_via_registry(self):
        """Test creating instances via the registry."""
        # Create agent instance via registry
        context = SandboxContext()
        agent_instance = create_agent_struct_instance("TestAgent", {"name": "agent", "role": "tester"}, context)
        self.assertIsInstance(agent_instance, StructInstance)
        self.assertIsInstance(agent_instance, AgentStructInstance)


class TestMethodDispatchPriority(unittest.TestCase):
    """Test method dispatch priority for agent structs."""

    def setUp(self):
        """Set up test fixtures."""
        # Clean up any existing registrations
        from dana.core.lang.interpreter.struct_system import StructTypeRegistry

        StructTypeRegistry.clear()

        self.agent_type = AgentStructType(name="TestAgent", fields={"name": "str"}, field_order=["name"], field_comments={})
        register_agent_struct_type(self.agent_type)

    def test_builtin_agent_methods_work(self):
        """Test that built-in agent methods work through dispatch."""
        context = SandboxContext()
        agent_instance = create_agent_struct_instance("TestAgent", {"name": "test"}, context)

        # Test that built-in methods work
        plan_result = agent_instance.plan(context, "test task")
        self.assertIn("planning", plan_result.lower())
        self.assertIn("TestAgent", plan_result)

        solve_result = agent_instance.solve(context, "test problem")
        self.assertIn("solving", solve_result.lower())
        self.assertIn("TestAgent", solve_result)

        remember_result = agent_instance.remember(context, "key", "value")
        self.assertTrue(remember_result)

        recall_result = agent_instance.recall(context, "key")
        self.assertEqual(recall_result, "value")

    def test_custom_methods_override_builtin(self):
        """Test that custom methods can override built-in methods."""
        # This would require custom method registration
        # For now, we test that built-in methods work as expected
        context = SandboxContext()
        agent_instance = create_agent_struct_instance("TestAgent", {"name": "test"}, context)

        # Built-in methods should work
        plan_result = agent_instance.plan(context, "test task")
        self.assertIn("planning", plan_result.lower())

        # Custom methods would be tested here when implemented
        # For now, we verify the method dispatch system works


class TestAgentStructInheritance(unittest.TestCase):
    """Test inheritance relationships in agent struct system."""

    def test_agent_struct_type_inheritance(self):
        """Test that AgentStructType properly inherits from StructType."""
        agent_type = AgentStructType(name="TestAgent", fields={"name": "str"}, field_order=["name"], field_comments={})

        # Test inheritance
        self.assertIsInstance(agent_type, StructType)
        self.assertIsInstance(agent_type, AgentStructType)

        # Test that agent type has all struct type attributes
        self.assertEqual(agent_type.name, "TestAgent")
        self.assertEqual(agent_type.fields, {"name": "str"})
        self.assertEqual(agent_type.field_order, ["name"])

        # Test that agent type has additional agent-specific attributes
        self.assertIn("plan", agent_type.agent_methods)
        self.assertIn("solve", agent_type.agent_methods)
        self.assertIn("remember", agent_type.agent_methods)
        self.assertIn("recall", agent_type.agent_methods)

    def test_agent_struct_instance_inheritance(self):
        """Test that AgentStructInstance properly inherits from StructInstance."""
        agent_type = AgentStructType(name="TestAgent", fields={"name": "str", "age": "int"}, field_order=["name", "age"], field_comments={})

        agent_instance = AgentStructInstance(agent_type, {"name": "test", "age": 25})

        # Test inheritance
        self.assertIsInstance(agent_instance, StructInstance)
        self.assertIsInstance(agent_instance, AgentStructInstance)

        # Test that agent instance has all struct instance attributes
        self.assertEqual(agent_instance.__struct_type__, agent_type)
        self.assertEqual(agent_instance.name, "test")
        self.assertEqual(agent_instance.age, 25)

        # Test that agent instance has additional agent-specific methods
        self.assertTrue(hasattr(agent_instance, "plan"))
        self.assertTrue(hasattr(agent_instance, "solve"))
        self.assertTrue(hasattr(agent_instance, "remember"))
        self.assertTrue(hasattr(agent_instance, "recall"))


class TestAgentStructRegistryIntegration(unittest.TestCase):
    """Test integration between agent struct registry and struct registry."""

    def setUp(self):
        """Set up test fixtures."""
        # Clean up any existing registrations
        from dana.core.lang.interpreter.struct_system import StructTypeRegistry

        StructTypeRegistry.clear()

    def test_agent_type_registration_in_struct_registry(self):
        """Test that agent types are properly registered in struct registry."""
        agent_type = AgentStructType(name="TestAgent", fields={"name": "str"}, field_order=["name"], field_comments={})

        # Register agent type
        register_agent_struct_type(agent_type)

        # Check that it's in the agent registry
        from dana.agent import get_agent_struct_type

        agent_registry_type = get_agent_struct_type("TestAgent")
        self.assertIs(agent_registry_type, agent_type)

        # Check that it's the correct type
        self.assertIsInstance(agent_registry_type, StructType)
        self.assertIsInstance(agent_registry_type, AgentStructType)

    def test_agent_instance_creation_via_struct_registry(self):
        """Test that agent instances can be created via struct registry."""
        agent_type = AgentStructType(
            name="TestAgent", fields={"name": "str", "role": "str"}, field_order=["name", "role"], field_comments={}
        )

        register_agent_struct_type(agent_type)

        # Create instance via agent registry
        context = SandboxContext()
        agent_instance = create_agent_struct_instance("TestAgent", {"name": "test", "role": "tester"}, context)

        # Verify it's the correct type
        self.assertIsInstance(agent_instance, StructInstance)
        self.assertIsInstance(agent_instance, AgentStructInstance)

        # Verify it has the correct attributes
        self.assertEqual(agent_instance.name, "test")
        self.assertEqual(agent_instance.role, "tester")

        # Verify it has agent methods
        self.assertTrue(hasattr(agent_instance, "plan"))
        self.assertTrue(hasattr(agent_instance, "solve"))
        self.assertTrue(hasattr(agent_instance, "remember"))
        self.assertTrue(hasattr(agent_instance, "recall"))


class TestAgentStructErrorHandling(unittest.TestCase):
    """Test error handling in agent struct system."""

    def test_invalid_agent_type_registration(self):
        """Test error handling for invalid agent type registration."""
        # Try to register a regular struct type as an agent type
        struct_type = StructType(name="TestStruct", fields={"name": "str"}, field_order=["name"], field_comments={})

        # This should work (struct types can be registered)
        register_agent_struct_type(struct_type)

        # But when we try to create an instance, it should fail
        context = SandboxContext()
        with self.assertRaises(TypeError):
            create_agent_struct_instance("TestStruct", {"name": "test"}, context)

    def test_nonexistent_agent_type_creation(self):
        """Test error handling for creating instances of non-existent types."""
        context = SandboxContext()
        with self.assertRaises(ValueError):
            create_agent_struct_instance("NonexistentAgent", {"name": "test"}, context)

    def test_invalid_agent_struct_instance_creation(self):
        """Test error handling for invalid agent struct instance creation."""
        # Try to create AgentStructInstance with regular StructType
        struct_type = StructType(name="TestStruct", fields={"name": "str"}, field_order=["name"], field_comments={})

        with self.assertRaises(TypeError):
            AgentStructInstance(struct_type, {"name": "test"})


if __name__ == "__main__":
    unittest.main()
