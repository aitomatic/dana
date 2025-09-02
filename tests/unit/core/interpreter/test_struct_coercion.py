"""
Unit tests for Dana struct coercion functionality.

Tests the enhanced coercion system's ability to convert LLM string responses
to custom Dana struct instances. These tests use mocks to avoid LLM dependencies.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import json
import unittest

import pytest

from dana.core.builtins.struct_system import StructInstance, StructType
from dana.core.lang.interpreter.enhanced_coercion import CoercionStrategy, SemanticCoercer
from dana.registry import TYPE_REGISTRY


@pytest.mark.unit
class TestStructCoercion(unittest.TestCase):
    """Test struct coercion functionality with mock responses."""

    def setUp(self):
        """Set up test environment."""
        # Clear struct registry before each test
        TYPE_REGISTRY.clear()
        self.coercer = SemanticCoercer(strategy=CoercionStrategy.ENHANCED)

    def tearDown(self):
        """Clean up after each test."""
        TYPE_REGISTRY.clear()

    def test_coerce_json_string_to_simple_struct(self):
        """Test coercing JSON string to simple struct instance."""
        # Register a test struct
        test_struct = StructType(
            name="TestPerson", fields={"name": "str", "age": "int", "email": "str"}, field_order=["name", "age", "email"], field_comments={}
        )
        TYPE_REGISTRY.register(test_struct)

        # Mock LLM JSON response
        json_response = '{"name": "John Doe", "age": 30, "email": "john@example.com"}'

        # Test coercion
        result = self.coercer.coerce_value(json_response, "TestPerson")

        # Verify result
        self.assertIsInstance(result, StructInstance)
        self.assertEqual(result.struct_type.name, "TestPerson")
        self.assertEqual(result.name, "John Doe")
        self.assertEqual(result.age, 30)
        self.assertEqual(result.email, "john@example.com")

    def test_coerce_task_signature_struct(self):
        """Test coercing to TaskSignature struct (the original bug case)."""
        # Register TaskSignature struct from curate.na
        task_signature = StructType(
            name="TaskSignature",
            fields={
                "entities": "list",
                "knowledge_needs": "list",
                "success_criteria": "list",
                "complexity_level": "str",
                "estimated_minimum_assets": "int",
            },
            field_order=["entities", "knowledge_needs", "success_criteria", "complexity_level", "estimated_minimum_assets"],
            field_comments={},
        )
        TYPE_REGISTRY.register(task_signature)

        # Mock LLM response similar to what reason() would return
        mock_response = json.dumps(
            {
                "entities": ["CNC_Machine", "Vibration_Sensor"],
                "knowledge_needs": ["equipment_specifications", "maintenance_history"],
                "success_criteria": ["reduced_downtime", "predictive_alerts"],
                "complexity_level": "moderate",
                "estimated_minimum_assets": 3,
            }
        )

        # Test coercion
        result = self.coercer.coerce_value(mock_response, "TaskSignature")

        # Verify result - these are the exact operations that were failing
        self.assertIsInstance(result, StructInstance)
        self.assertEqual(result.struct_type.name, "TaskSignature")

        # The bug was task_sig.knowledge_needs failing - this should now work
        self.assertEqual(len(result.knowledge_needs), 2)
        self.assertIn("equipment_specifications", result.knowledge_needs)
        self.assertEqual(result.complexity_level, "moderate")
        self.assertEqual(result.estimated_minimum_assets, 3)

    def test_coerce_dict_to_struct(self):
        """Test coercing dictionary to struct instance."""
        # Register a test struct
        test_struct = StructType(
            name="Address",
            fields={"street": "str", "city": "str", "zipcode": "str"},
            field_order=["street", "city", "zipcode"],
            field_comments={},
        )
        TYPE_REGISTRY.register(test_struct)

        # Mock data (already parsed dict)
        data = {"street": "123 Main St", "city": "San Francisco", "zipcode": "94102"}

        # Test coercion
        result = self.coercer.coerce_value(data, "Address")

        # Verify result
        self.assertIsInstance(result, StructInstance)
        self.assertEqual(result.street, "123 Main St")
        self.assertEqual(result.city, "San Francisco")
        self.assertEqual(result.zipcode, "94102")

    def test_coerce_markdown_json_to_struct(self):
        """Test coercing JSON with markdown code fences to struct."""
        # Register a test struct
        test_struct = StructType(
            name="Product",
            fields={"id": "str", "name": "str", "price": "float", "category": "str"},
            field_order=["id", "name", "price", "category"],
            field_comments={},
        )
        TYPE_REGISTRY.register(test_struct)

        # Mock LLM response with markdown formatting (common LLM behavior)
        markdown_response = """```json
{
    "id": "PROD-001",
    "name": "Gaming Laptop",
    "price": 1299.99,
    "category": "Electronics"
}
```"""

        # Test coercion
        result = self.coercer.coerce_value(markdown_response, "Product")

        # Verify result
        self.assertIsInstance(result, StructInstance)
        self.assertEqual(result.id, "PROD-001")
        self.assertEqual(result.name, "Gaming Laptop")
        self.assertEqual(result.price, 1299.99)
        self.assertEqual(result.category, "Electronics")

    def test_coerce_final_answer_format_to_struct(self):
        """Test coercing response with FINAL_ANSWER format to struct."""
        # Register a test struct
        test_struct = StructType(
            name="Config",
            fields={"timeout": "int", "retries": "int", "debug": "bool"},
            field_order=["timeout", "retries", "debug"],
            field_comments={},
        )
        TYPE_REGISTRY.register(test_struct)

        # Mock LLM response with reasoning and final answer
        response_with_reasoning = """I need to create a configuration with appropriate values.

Let me consider the requirements:
- Timeout should be reasonable for network operations
- Retries should be limited but sufficient
- Debug mode should be enabled for development

FINAL_ANSWER: {"timeout": 30, "retries": 3, "debug": true}"""

        # Test coercion
        result = self.coercer.coerce_value(response_with_reasoning, "Config")

        # Verify result
        self.assertIsInstance(result, StructInstance)
        self.assertEqual(result.timeout, 30)
        self.assertEqual(result.retries, 3)
        self.assertTrue(result.debug)

    def test_coerce_unknown_struct_type_falls_through(self):
        """Test that unknown struct types fall through to original behavior."""
        # Don't register any structs

        json_response = '{"field": "value"}'

        # This should fall through to the "return value as-is" case
        result = self.coercer.coerce_value(json_response, "UnknownStruct")

        # Should return the original string since UnknownStruct is not registered
        self.assertEqual(result, json_response)

    def test_coerce_invalid_json_raises_error(self):
        """Test that invalid JSON for registered struct type raises ValueError."""
        # Register a test struct
        test_struct = StructType(name="TestStruct", fields={"field": "str"}, field_order=["field"], field_comments={})
        TYPE_REGISTRY.register(test_struct)

        # Invalid JSON
        invalid_json = '{"field": "value"'  # Missing closing brace

        # Should raise ValueError
        with self.assertRaises(ValueError) as context:
            self.coercer.coerce_value(invalid_json, "TestStruct")

        self.assertIn("Invalid JSON", str(context.exception))

    def test_coerce_missing_required_fields_raises_error(self):
        """Test that missing required fields raises ValueError."""
        # Register a test struct with multiple required fields
        test_struct = StructType(
            name="RequiredFieldsStruct",
            fields={"name": "str", "age": "int", "email": "str"},
            field_order=["name", "age", "email"],
            field_comments={},
        )
        TYPE_REGISTRY.register(test_struct)

        # JSON missing required fields
        incomplete_json = '{"name": "John"}'  # Missing age and email

        # Should raise ValueError
        with self.assertRaises(ValueError) as context:
            self.coercer.coerce_value(incomplete_json, "RequiredFieldsStruct")

        self.assertIn("Missing required fields", str(context.exception))

    def test_coerce_existing_struct_instance_returns_same(self):
        """Test that existing struct instance of correct type is returned as-is."""
        # Register a test struct
        test_struct = StructType(name="ExistingStruct", fields={"field": "str"}, field_order=["field"], field_comments={})
        TYPE_REGISTRY.register(test_struct)

        # Create an existing struct instance
        existing_instance = TYPE_REGISTRY.create_instance("ExistingStruct", {"field": "value"})

        # Test coercion - should return the same instance
        result = self.coercer.coerce_value(existing_instance, "ExistingStruct")

        # Should be the exact same instance
        self.assertIs(result, existing_instance)

    def test_coerce_list_to_struct_raises_error(self):
        """Test that trying to coerce list to struct raises ValueError."""
        # Register a test struct
        test_struct = StructType(name="ListTestStruct", fields={"field": "str"}, field_order=["field"], field_comments={})
        TYPE_REGISTRY.register(test_struct)

        # Try to coerce a list
        list_value = ["item1", "item2"]

        # Should raise ValueError
        with self.assertRaises(ValueError) as context:
            self.coercer.coerce_value(list_value, "ListTestStruct")

        self.assertIn("Cannot coerce list to struct", str(context.exception))

    def test_coerce_complex_nested_struct(self):
        """Test coercing complex struct with various field types."""
        # Register KnowledgeAsset struct from curate.na
        knowledge_asset = StructType(
            name="KnowledgeAsset",
            fields={
                "id": "str",
                "type": "str",
                "source": "str",
                "content": "str",
                "trust_tier": "str",
                "metadata": "dict",
                "relevance_score": "float",
                "knowledge_category": "str",
            },
            field_order=["id", "type", "source", "content", "trust_tier", "metadata", "relevance_score", "knowledge_category"],
            field_comments={},
        )
        TYPE_REGISTRY.register(knowledge_asset)

        # Mock complex JSON response
        complex_json = json.dumps(
            {
                "id": "asset_001",
                "type": "Manual",
                "source": "Enterprise",
                "content": "Equipment maintenance procedures",
                "trust_tier": "High",
                "metadata": {"schema": "maintenance_v1", "timestamp": "2023-01-01"},
                "relevance_score": 0.9,
                "knowledge_category": "DK",
            }
        )

        # Test coercion
        result = self.coercer.coerce_value(complex_json, "KnowledgeAsset")

        # Verify result
        self.assertIsInstance(result, StructInstance)
        self.assertEqual(result.id, "asset_001")
        self.assertEqual(result.trust_tier, "High")
        self.assertIsInstance(result.metadata, dict)
        self.assertEqual(result.metadata["schema"], "maintenance_v1")
        self.assertEqual(result.relevance_score, 0.9)
        self.assertEqual(result.knowledge_category, "DK")


@pytest.mark.unit
class TestStructCoercionEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions for struct coercion."""

    def setUp(self):
        """Set up test environment."""
        TYPE_REGISTRY.clear()
        self.coercer = SemanticCoercer(strategy=CoercionStrategy.ENHANCED)

    def tearDown(self):
        """Clean up after each test."""
        TYPE_REGISTRY.clear()

    def test_empty_json_object_with_optional_fields(self):
        """Test handling of empty JSON objects."""
        # This test would fail with current implementation since all fields are required
        # but demonstrates the expected behavior for future enhancement
        pass

    def test_extra_fields_in_json_rejected(self):
        """Test that extra fields in JSON are rejected."""
        # Register a test struct
        test_struct = StructType(name="StrictStruct", fields={"name": "str"}, field_order=["name"], field_comments={})
        TYPE_REGISTRY.register(test_struct)

        # JSON with extra fields
        json_with_extra = '{"name": "test", "extra_field": "should_be_rejected"}'

        # Should raise ValueError due to unknown fields
        with self.assertRaises(ValueError) as context:
            self.coercer.coerce_value(json_with_extra, "StrictStruct")

        self.assertIn("Unknown fields", str(context.exception))

    def test_type_validation_in_struct_fields(self):
        """Test that field type validation works correctly."""
        # Register a test struct with specific types
        test_struct = StructType(
            name="TypedStruct",
            fields={"count": "int", "active": "bool", "score": "float"},
            field_order=["count", "active", "score"],
            field_comments={},
        )
        TYPE_REGISTRY.register(test_struct)

        # JSON with correct types
        valid_json = '{"count": 42, "active": true, "score": 95.5}'
        result = self.coercer.coerce_value(valid_json, "TypedStruct")

        self.assertEqual(result.count, 42)
        self.assertTrue(result.active)
        self.assertEqual(result.score, 95.5)


if __name__ == "__main__":
    unittest.main()
