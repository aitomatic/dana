"""
Unit tests for the unified agent struct system.
Tests AgentStructType, AgentStructInstance, and related functionality.
"""

import unittest

from dana.agent import AgentInstance, AgentType, create_agent_instance
from dana.core.lang.interpreter.struct_system import StructInstance, StructType
from dana.core.lang.sandbox_context import SandboxContext
from dana.registry import TYPE_REGISTRY, get_agent_type, register_agent_type


class TestAgentStructType(unittest.TestCase):
    """Test AgentStructType functionality."""

    def test_agent_type_creation(self):
        """Test creating an AgentType."""
        fields = {"name": "str", "age": "int"}
        field_order = ["name", "age"]
        field_defaults = {"name": "default", "age": 25}

        agent_type = AgentType(
            name="TestAgent",
            fields=fields,
            field_order=field_order,
            field_defaults=field_defaults,
            field_comments={},
            docstring="Test agent type",
        )

        self.assertEqual(agent_type.name, "TestAgent")
        # AgentType automatically adds a 'state' field, so we expect it in addition to the provided fields
        expected_fields = {"state": "str", **fields}
        expected_field_order = ["state"] + field_order
        expected_defaults = {"state": "CREATED", **field_defaults}

        self.assertEqual(agent_type.fields, expected_fields)
        self.assertEqual(agent_type.field_order, expected_field_order)
        self.assertEqual(agent_type.field_defaults, expected_defaults)
        self.assertEqual(agent_type.docstring, "Test agent type")

    def test_agent_type_inheritance(self):
        """Test that AgentType inherits from StructType."""
        agent_type = AgentType(name="TestAgent", fields={"name": "str"}, field_order=["name"], field_comments={})

        self.assertIsInstance(agent_type, StructType)
        self.assertIsInstance(agent_type, AgentType)

    def test_default_agent_methods(self):
        """Test that default agent methods are created."""
        agent_type = AgentType(name="TestAgent", fields={"name": "str"}, field_order=["name"], field_comments={})

        # Check that default agent methods exist
        self.assertIn("plan", agent_type.agent_methods)
        self.assertIn("solve", agent_type.agent_methods)
        self.assertIn("remember", agent_type.agent_methods)
        self.assertIn("recall", agent_type.agent_methods)
        self.assertIn("reason", agent_type.agent_methods)
        self.assertIn("chat", agent_type.agent_methods)

        # Check that methods are callable
        self.assertTrue(callable(agent_type.agent_methods["plan"]))
        self.assertTrue(callable(agent_type.agent_methods["solve"]))
        self.assertTrue(callable(agent_type.agent_methods["remember"]))
        self.assertTrue(callable(agent_type.agent_methods["recall"]))
        self.assertTrue(callable(agent_type.agent_methods["reason"]))
        self.assertTrue(callable(agent_type.agent_methods["chat"]))

    def test_custom_agent_methods(self):
        """Test adding custom agent methods."""

        def custom_plan(agent_instance, sandbox_context, task: str) -> str:
            return f"Custom plan for {task}"

        agent_type = AgentType(
            name="TestAgent", fields={"name": "str"}, field_order=["name"], field_comments={}, agent_methods={"custom_plan": custom_plan}
        )

        self.assertIn("custom_plan", agent_type.agent_methods)
        self.assertEqual(agent_type.agent_methods["custom_plan"], custom_plan)


class TestAgentInstance(unittest.TestCase):
    """Test AgentInstance functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.agent_type = AgentType(name="TestAgent", fields={"name": "str", "age": "int"}, field_order=["name", "age"], field_comments={})
        self.sandbox_context = SandboxContext()

    def test_agent_instance_creation(self):
        """Test creating an AgentInstance."""
        values = {"name": "Alice", "age": 30}
        agent_instance = AgentInstance(self.agent_type, values)

        self.assertEqual(agent_instance.__struct_type__, self.agent_type)
        self.assertEqual(agent_instance.name, "Alice")
        self.assertEqual(agent_instance.age, 30)

    def test_agent_instance_inheritance(self):
        """Test that AgentInstance inherits from StructInstance."""
        values = {"name": "Alice", "age": 30}
        agent_instance = AgentInstance(self.agent_type, values)

        self.assertIsInstance(agent_instance, StructInstance)
        self.assertIsInstance(agent_instance, AgentInstance)

    def test_agent_method_binding(self):
        """Test that agent methods are bound to instances."""
        values = {"name": "Alice", "age": 30}
        agent_instance = AgentInstance(self.agent_type, values)

        # Check that methods are bound to the instance
        self.assertTrue(hasattr(agent_instance, "plan"))
        self.assertTrue(hasattr(agent_instance, "solve"))
        self.assertTrue(hasattr(agent_instance, "remember"))
        self.assertTrue(hasattr(agent_instance, "recall"))
        self.assertTrue(hasattr(agent_instance, "chat"))

        # Check that methods are callable
        self.assertTrue(callable(agent_instance.plan))
        self.assertTrue(callable(agent_instance.solve))
        self.assertTrue(callable(agent_instance.remember))
        self.assertTrue(callable(agent_instance.recall))
        self.assertTrue(callable(agent_instance.chat))

    def test_agent_method_execution(self):
        """Test that agent methods execute correctly."""
        values = {"name": "Alice", "age": 30}
        agent_instance = AgentInstance(self.agent_type, values)

        # Set up LLM resource in context for agent methods
        from dana.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource
        from dana.core.resource.builtins.llm_resource_instance import LLMResourceInstance
        from dana.core.resource.builtins.llm_resource_type import LLMResourceType

        llm_resource = LLMResourceInstance(LLMResourceType(), LegacyLLMResource(name="test_llm", model="openai:gpt-4o-mini"))
        llm_resource.initialize()
        llm_resource.with_mock_llm_call(True)  # Enable mock mode
        self.sandbox_context.set_system_llm_resource(llm_resource)

        # Test plan method
        plan_result = agent_instance.plan(self.sandbox_context, "test task")
        # Since DANA_MOCK_LLM is true, we should get a mock response
        self.assertIn("mock", plan_result.lower())
        self.assertIn("TestAgent", plan_result)

        # Test solve method
        solve_result = agent_instance.solve(self.sandbox_context, "test problem")
        # Since DANA_MOCK_LLM is true, we should get a mock response
        self.assertIn("mock", solve_result.lower())
        self.assertIn("TestAgent", solve_result)

        # Test memory methods
        remember_result = agent_instance.remember(self.sandbox_context, "test_key", "test_value")
        self.assertTrue(remember_result)

        recall_result = agent_instance.recall(self.sandbox_context, "test_key")
        self.assertEqual(recall_result, "test_value")

    def test_agent_memory_isolation(self):
        """Test that agent memory is isolated between instances."""
        values1 = {"name": "Alice", "age": 30}
        values2 = {"name": "Bob", "age": 25}

        agent1 = AgentInstance(self.agent_type, values1)
        agent2 = AgentInstance(self.agent_type, values2)

        # Store different values in each agent's memory
        agent1.remember(self.sandbox_context, "key", "value1")
        agent2.remember(self.sandbox_context, "key", "value2")

        # Check that memories are isolated
        self.assertEqual(agent1.recall(self.sandbox_context, "key"), "value1")
        self.assertEqual(agent2.recall(self.sandbox_context, "key"), "value2")

    def test_invalid_struct_type(self):
        """Test that AgentInstance rejects non-AgentStructType."""
        regular_struct_type = StructType(name="RegularStruct", fields={"name": "str"}, field_order=["name"], field_comments={})

        with self.assertRaises(TypeError):
            AgentInstance(regular_struct_type, {"name": "test"})


class TestAgentTypeRegistry(unittest.TestCase):
    """Test AgentTypeRegistry functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.registry = TYPE_REGISTRY
        # Clear registry to ensure clean state for each test
        self.registry.clear()

    def test_singleton_pattern(self):
        """Test that global_agent_type_registry follows singleton pattern."""
        # The global registry should be a singleton
        registry1 = TYPE_REGISTRY
        registry2 = TYPE_REGISTRY

        # They should be the same instance with singleton pattern
        self.assertIs(registry1, registry2)

    def test_register_and_get_agent_type(self):
        """Test registering and retrieving agent types."""
        agent_type = AgentType(name="TestAgent", fields={"name": "str"}, field_order=["name"], field_comments={})

        # Register the agent type
        self.registry.register_agent_type(agent_type)

        # Retrieve the agent type
        retrieved_type = self.registry.get_agent_type("TestAgent")
        # Check that we get the same agent type back (object identity should be preserved)
        self.assertIs(retrieved_type, agent_type)

    def test_get_nonexistent_agent_type(self):
        """Test getting a non-existent agent type."""
        retrieved_type = self.registry.get_agent_type("NonexistentAgent")
        self.assertIsNone(retrieved_type)

    def test_agent_type_exists(self):
        """Test checking if an agent type exists."""
        agent_type = AgentType(name="TestAgent", fields={"name": "str"}, field_order=["name"], field_comments={})

        self.registry.register_agent_type(agent_type)

        # Check if it exists by trying to get it
        retrieved_type = self.registry.get_agent_type("TestAgent")
        self.assertIsNotNone(retrieved_type)

        # Check non-existent type
        missing_type = self.registry.get_agent_type("NonexistentAgent")
        self.assertIsNone(missing_type)


class TestHelperFunctions(unittest.TestCase):
    """Test helper functions for agent system."""

    def setUp(self):
        """Set up test fixtures."""
        # Clean up any existing registrations

        TYPE_REGISTRY.clear()

    def tearDown(self):
        """Clean up after tests."""

        TYPE_REGISTRY.clear()

    def test_register_agent_type(self):
        """Test register_agent_type helper function."""
        agent_type = AgentType(name="TestAgent", fields={"name": "str"}, field_order=["name"], field_comments={})

        # Register using helper function
        register_agent_type(agent_type)

        # Verify registration
        retrieved_type = get_agent_type("TestAgent")
        self.assertIs(retrieved_type, agent_type)

    def test_get_agent_type(self):
        """Test get_agent_type helper function."""
        agent_type = AgentType(name="TestAgent", fields={"name": "str"}, field_order=["name"], field_comments={})

        register_agent_type(agent_type)

        # Get using helper function
        retrieved_type = get_agent_type("TestAgent")
        self.assertIs(retrieved_type, agent_type)

    def test_create_agent_instance(self):
        """Test create_agent_instance helper function."""
        agent_type = AgentType(name="TestAgent", fields={"name": "str", "age": "int"}, field_order=["name", "age"], field_comments={})

        register_agent_type(agent_type)

        # Create instance using helper function
        values = {"name": "Alice", "age": 30}
        context = SandboxContext()
        agent_instance = create_agent_instance("TestAgent", values, context)

        self.assertIsInstance(agent_instance, AgentInstance)
        self.assertEqual(agent_instance.name, "Alice")
        self.assertEqual(agent_instance.age, 30)

    def test_create_agent_instance_nonexistent(self):
        """Test create_agent_instance with non-existent type."""
        context = SandboxContext()
        with self.assertRaises(ValueError):
            create_agent_instance("NonexistentAgent", {}, context)


class TestAgentStructIntegration(unittest.TestCase):
    """Test integration between agent system and struct system."""

    def setUp(self):
        """Set up test fixtures."""
        # Clean up any existing registrations

        TYPE_REGISTRY.clear()

    def tearDown(self):
        """Clean up after tests."""

        TYPE_REGISTRY.clear()

    def test_agent_type_in_struct_registry(self):
        """Test that agent types are registered in struct registry."""
        agent_type = AgentType(name="TestAgent", fields={"name": "str"}, field_order=["name"], field_comments={})

        register_agent_type(agent_type)

        # Check that it's in the agent registry
        retrieved_type = get_agent_type("TestAgent")
        self.assertIs(retrieved_type, agent_type)

    def test_agent_instance_creation_via_struct_registry(self):
        """Test creating agent instances via agent registry."""
        agent_type = AgentType(name="TestAgent", fields={"name": "str", "age": "int"}, field_order=["name", "age"], field_comments={})

        register_agent_type(agent_type)

        # Create instance via agent registry
        values = {"name": "Alice", "age": 30}
        context = SandboxContext()
        agent_instance = create_agent_instance("TestAgent", values, context)

        self.assertIsInstance(agent_instance, AgentInstance)
        self.assertEqual(agent_instance.name, "Alice")
        self.assertEqual(agent_instance.age, 30)


if __name__ == "__main__":
    unittest.main()
