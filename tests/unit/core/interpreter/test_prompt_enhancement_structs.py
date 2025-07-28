"""
Unit tests for Dana struct prompt enhancement functionality.

Tests the POET system's ability to enhance prompts with Dana struct schema information
when reason() is called in a context expecting a struct type.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from unittest.mock import patch

from dana.core.lang.interpreter.context_detection import ContextType, TypeContext
from dana.core.lang.interpreter.prompt_enhancement import PromptEnhancer, enhance_prompt_for_type
from dana.core.lang.interpreter.struct_system import StructType, StructTypeRegistry


class TestDanaStructPromptEnhancement:
    """Test prompt enhancement for Dana struct types."""

    def setup_method(self):
        """Clear struct registry before each test."""
        StructTypeRegistry.clear()
        self.enhancer = PromptEnhancer()

    def test_enhance_for_dana_struct_basic(self):
        """Test basic prompt enhancement for a simple Dana struct."""
        # Register a test struct
        test_struct = StructType(
            name="TestStruct", fields={"name": "str", "value": "int"}, field_order=["name", "value"], field_comments={}
        )
        StructTypeRegistry.register(test_struct)

        # Create type context
        type_context = TypeContext(
            expected_type="TestStruct", context_type=ContextType.ASSIGNMENT, confidence=1.0, source_node=None, metadata={}
        )

        # Test prompt enhancement
        original_prompt = "Create a test struct"
        enhanced_prompt = self.enhancer.enhance_prompt(original_prompt, type_context)

        # Verify enhancement
        assert enhanced_prompt != original_prompt
        assert "TestStruct struct fields:" in enhanced_prompt
        assert "- name: str" in enhanced_prompt
        assert "- value: int" in enhanced_prompt
        assert "JSON Schema:" in enhanced_prompt
        assert "Return format:" in enhanced_prompt
        assert "Return raw JSON only" in enhanced_prompt

    def test_enhance_for_dana_struct_complex(self):
        """Test prompt enhancement for a complex Dana struct with nested types."""
        # Register a complex struct
        complex_struct = StructType(
            name="ComplexStruct",
            fields={"id": "str", "data": "dict", "items": "list", "metadata": "dict"},
            field_order=["id", "data", "items", "metadata"],
            field_comments={},
        )
        StructTypeRegistry.register(complex_struct)

        # Create type context
        type_context = TypeContext(
            expected_type="ComplexStruct", context_type=ContextType.ASSIGNMENT, confidence=1.0, source_node=None, metadata={}
        )

        # Test prompt enhancement
        original_prompt = "Generate complex data structure"
        enhanced_prompt = self.enhancer.enhance_prompt(original_prompt, type_context)

        # Verify enhancement
        assert enhanced_prompt != original_prompt
        assert "ComplexStruct struct fields:" in enhanced_prompt
        assert "- id: str" in enhanced_prompt
        assert "- data: dict" in enhanced_prompt
        assert "- items: list" in enhanced_prompt
        assert "- metadata: dict" in enhanced_prompt
        assert "JSON Schema:" in enhanced_prompt

    def test_enhance_for_unknown_struct(self):
        """Test that unknown struct types don't get enhanced."""
        # Create type context for unknown struct
        type_context = TypeContext(
            expected_type="UnknownStruct", context_type=ContextType.ASSIGNMENT, confidence=1.0, source_node=None, metadata={}
        )

        # Test prompt enhancement
        original_prompt = "Create something"
        enhanced_prompt = self.enhancer.enhance_prompt(original_prompt, type_context)

        # Should return original prompt unchanged
        assert enhanced_prompt == original_prompt

    def test_enhance_for_dana_struct_with_schema_validation(self):
        """Test that the enhanced prompt includes proper JSON schema validation."""
        # Register a struct with specific field types
        validation_struct = StructType(
            name="ValidationStruct",
            fields={"required_field": "str", "optional_field": "int", "nested_field": "dict"},
            field_order=["required_field", "optional_field", "nested_field"],
            field_comments={},
        )
        StructTypeRegistry.register(validation_struct)

        # Create type context
        type_context = TypeContext(
            expected_type="ValidationStruct", context_type=ContextType.ASSIGNMENT, confidence=1.0, source_node=None, metadata={}
        )

        # Test prompt enhancement
        original_prompt = "Create validation data"
        enhanced_prompt = self.enhancer.enhance_prompt(original_prompt, type_context)

        # Verify schema information is included
        assert "JSON Schema:" in enhanced_prompt
        assert "required" in enhanced_prompt
        assert "additionalProperties" in enhanced_prompt
        assert "ValidationStruct" in enhanced_prompt

    def test_enhance_for_dana_struct_field_order_preservation(self):
        """Test that field order is preserved in the enhanced prompt."""
        # Register a struct with specific field order
        ordered_struct = StructType(
            name="OrderedStruct",
            fields={"first": "str", "second": "int", "third": "bool"},
            field_order=["first", "second", "third"],
            field_comments={},
        )
        StructTypeRegistry.register(ordered_struct)

        # Create type context
        type_context = TypeContext(
            expected_type="OrderedStruct", context_type=ContextType.ASSIGNMENT, confidence=1.0, source_node=None, metadata={}
        )

        # Test prompt enhancement
        original_prompt = "Create ordered data"
        enhanced_prompt = self.enhancer.enhance_prompt(original_prompt, type_context)

        # Verify field order is preserved
        first_index = enhanced_prompt.find("- first: str")
        second_index = enhanced_prompt.find("- second: int")
        third_index = enhanced_prompt.find("- third: bool")

        assert first_index < second_index < third_index

    def test_enhance_for_dana_struct_error_handling(self):
        """Test that errors in struct enhancement are handled gracefully."""
        # Mock StructTypeRegistry to raise an exception
        with patch("dana.core.lang.interpreter.struct_system.StructTypeRegistry") as mock_registry:
            mock_registry.exists.return_value = True
            mock_registry.get_schema.side_effect = Exception("Schema error")

            # Create type context
            type_context = TypeContext(
                expected_type="ErrorStruct", context_type=ContextType.ASSIGNMENT, confidence=1.0, source_node=None, metadata={}
            )

            # Test prompt enhancement
            original_prompt = "Create error data"
            enhanced_prompt = self.enhancer.enhance_prompt(original_prompt, type_context)

            # Should return original prompt on error
            assert enhanced_prompt == original_prompt

    def test_enhance_prompt_for_type_convenience_function(self):
        """Test the convenience function enhance_prompt_for_type."""
        # Register a test struct
        test_struct = StructType(name="ConvenienceStruct", fields={"field": "str"}, field_order=["field"], field_comments={})
        StructTypeRegistry.register(test_struct)

        # Create type context
        type_context = TypeContext(
            expected_type="ConvenienceStruct", context_type=ContextType.ASSIGNMENT, confidence=1.0, source_node=None, metadata={}
        )

        # Test convenience function
        original_prompt = "Test convenience function"
        enhanced_prompt = enhance_prompt_for_type(original_prompt, type_context)

        # Verify enhancement
        assert enhanced_prompt != original_prompt
        assert "ConvenienceStruct struct fields:" in enhanced_prompt

    def test_enhance_for_dana_struct_with_different_context_types(self):
        """Test that struct enhancement works with different context types."""
        # Register a test struct
        test_struct = StructType(name="ContextStruct", fields={"data": "str"}, field_order=["data"], field_comments={})
        StructTypeRegistry.register(test_struct)

        # Test with different context types
        context_types = [ContextType.ASSIGNMENT, ContextType.FUNCTION_PARAMETER, ContextType.RETURN_VALUE, ContextType.EXPRESSION]

        for context_type in context_types:
            type_context = TypeContext(
                expected_type="ContextStruct", context_type=context_type, confidence=1.0, source_node=None, metadata={}
            )

            original_prompt = f"Test {context_type.value} context"
            enhanced_prompt = self.enhancer.enhance_prompt(original_prompt, type_context)

            # Should enhance regardless of context type
            assert enhanced_prompt != original_prompt
            assert "ContextStruct struct fields:" in enhanced_prompt

    def test_enhance_for_dana_struct_confidence_levels(self):
        """Test that struct enhancement works with different confidence levels."""
        # Register a test struct
        test_struct = StructType(name="ConfidenceStruct", fields={"value": "int"}, field_order=["value"], field_comments={})
        StructTypeRegistry.register(test_struct)

        # Test with different confidence levels
        confidence_levels = [0.5, 0.8, 1.0]

        for confidence in confidence_levels:
            type_context = TypeContext(
                expected_type="ConfidenceStruct", context_type=ContextType.ASSIGNMENT, confidence=confidence, source_node=None, metadata={}
            )

            original_prompt = f"Test confidence {confidence}"
            enhanced_prompt = self.enhancer.enhance_prompt(original_prompt, type_context)

            # Should enhance regardless of confidence level
            assert enhanced_prompt != original_prompt
            assert "ConfidenceStruct struct fields:" in enhanced_prompt

    def test_enhance_for_dana_struct_metadata_preservation(self):
        """Test that metadata is preserved in the enhanced prompt context."""
        # Register a test struct
        test_struct = StructType(name="MetadataStruct", fields={"info": "str"}, field_order=["info"], field_comments={})
        StructTypeRegistry.register(test_struct)

        # Create type context with metadata
        metadata = {"source": "test", "version": "1.0"}
        type_context = TypeContext(
            expected_type="MetadataStruct", context_type=ContextType.ASSIGNMENT, confidence=1.0, source_node=None, metadata=metadata
        )

        # Test prompt enhancement
        original_prompt = "Test metadata preservation"
        enhanced_prompt = self.enhancer.enhance_prompt(original_prompt, type_context)

        # Should enhance the prompt
        assert enhanced_prompt != original_prompt
        assert "MetadataStruct struct fields:" in enhanced_prompt

        # Metadata should be preserved in the context (not in the prompt itself)
        assert type_context.metadata == metadata


class TestDanaStructPromptEnhancementIntegration:
    """Integration tests for Dana struct prompt enhancement."""

    def setup_method(self):
        """Clear struct registry before each test."""
        StructTypeRegistry.clear()

    def test_curate_na_struct_types(self):
        """Test prompt enhancement for the actual struct types used in curate.na."""
        # Register the struct types from curate.na
        struct_definitions = {
            "TaskSignature": {
                "fields": {"entities": "list", "knowledge_needs": "list", "success_criteria": "list"},
                "order": ["entities", "knowledge_needs", "success_criteria"],
            },
            "KnowledgeAsset": {
                "fields": {"id": "str", "type": "str", "source": "str", "content": "str", "trust_tier": "str", "metadata": "dict"},
                "order": ["id", "type", "source", "content", "trust_tier", "metadata"],
            },
            "KnowledgeRecipe": {
                "fields": {
                    "transformation_steps": "list",
                    "data_structures": "list",
                    "storage_formats": "list",
                    "query_patterns": "list",
                    "performance_notes": "str",
                    "runtime_queries": "list",
                },
                "order": [
                    "transformation_steps",
                    "data_structures",
                    "storage_formats",
                    "query_patterns",
                    "performance_notes",
                    "runtime_queries",
                ],
            },
        }

        # Register all struct types
        for name, definition in struct_definitions.items():
            struct_type = StructType(name=name, fields=definition["fields"], field_order=definition["order"], field_comments={})
            StructTypeRegistry.register(struct_type)

        enhancer = PromptEnhancer()

        # Test each struct type
        for struct_name in struct_definitions.keys():
            type_context = TypeContext(
                expected_type=struct_name, context_type=ContextType.ASSIGNMENT, confidence=1.0, source_node=None, metadata={}
            )

            original_prompt = f"Create {struct_name} data"
            enhanced_prompt = enhancer.enhance_prompt(original_prompt, type_context)

            # Verify enhancement
            assert enhanced_prompt != original_prompt
            assert f"{struct_name} struct fields:" in enhanced_prompt
            assert "JSON Schema:" in enhanced_prompt
            assert "Return format:" in enhanced_prompt

    def test_multiple_struct_types_same_session(self):
        """Test that multiple struct types can be enhanced in the same session."""
        # Register multiple struct types
        structs = [
            ("SimpleStruct", {"name": "str"}, ["name"]),
            ("ComplexStruct", {"data": "dict", "items": "list"}, ["data", "items"]),
            ("NestedStruct", {"parent": "str", "children": "list"}, ["parent", "children"]),
        ]

        for name, fields, order in structs:
            struct_type = StructType(name=name, fields=fields, field_order=order, field_comments={})
            StructTypeRegistry.register(struct_type)

        enhancer = PromptEnhancer()

        # Test each struct type
        for name, fields, _ in structs:
            type_context = TypeContext(
                expected_type=name, context_type=ContextType.ASSIGNMENT, confidence=1.0, source_node=None, metadata={}
            )

            original_prompt = f"Create {name}"
            enhanced_prompt = enhancer.enhance_prompt(original_prompt, type_context)

            # Verify enhancement
            assert enhanced_prompt != original_prompt
            assert f"{name} struct fields:" in enhanced_prompt

            # Verify all fields are included
            for field_name in fields.keys():
                assert f"- {field_name}:" in enhanced_prompt
