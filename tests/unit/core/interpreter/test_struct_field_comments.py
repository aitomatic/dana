"""
Unit tests for Dana struct field comments functionality.

Tests the ability to capture and use field comments from struct definitions
for enhanced LLM prompts.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from dana.core.builtin_types.struct_system import StructType, create_struct_type_from_ast
from dana.core.lang.ast import StructDefinition, StructField, TypeHint
from dana.core.lang.interpreter.context_detection import ContextType, TypeContext
from dana.core.lang.interpreter.prompt_enhancement import PromptEnhancer
from dana.registry import TYPE_REGISTRY


class TestStructFieldComments:
    """Test struct field comment functionality."""

    def setup_method(self):
        """Clear struct registry before each test."""
        TYPE_REGISTRY.clear()

    def test_struct_field_with_comment(self):
        """Test that struct fields with comments are properly captured."""
        # Create a struct field with comment
        field = StructField(name="name", type_hint=TypeHint(name="str"), comment="the name of the person")

        assert field.name == "name"
        assert field.type_hint.name == "str"
        assert field.comment == "the name of the person"

    def test_struct_field_without_comment(self):
        """Test that struct fields without comments work correctly."""
        # Create a struct field without comment
        field = StructField(name="age", type_hint=TypeHint(name="int"))

        assert field.name == "age"
        assert field.type_hint.name == "int"
        assert field.comment is None

    def test_struct_type_with_field_comments(self):
        """Test that StructType properly stores and provides field comments."""
        # Create struct type with field comments
        struct_type = StructType(
            name="TestPerson",
            fields={"name": "str", "age": "int", "email": "str"},
            field_order=["name", "age", "email"],
            field_comments={"name": "the name of the person", "age": "the age in years", "email": "the email address"},
        )

        # Test field comment retrieval
        assert struct_type.get_field_comment("name") == "the name of the person"
        assert struct_type.get_field_comment("age") == "the age in years"
        assert struct_type.get_field_comment("email") == "the email address"
        assert struct_type.get_field_comment("nonexistent") is None

    def test_field_description_with_comment(self):
        """Test that field descriptions include comments when available."""
        struct_type = StructType(
            name="TestPerson",
            fields={"name": "str", "age": "int"},
            field_order=["name", "age"],
            field_comments={"name": "the name of the person", "age": "the age in years"},
        )

        # Test field descriptions
        assert struct_type.get_field_description("name") == "name: str  # the name of the person"
        assert struct_type.get_field_description("age") == "age: int  # the age in years"

    def test_field_description_without_comment(self):
        """Test that field descriptions work without comments."""
        struct_type = StructType(name="TestPerson", fields={"name": "str", "age": "int"}, field_order=["name", "age"], field_comments={})

        # Test field descriptions without comments
        assert struct_type.get_field_description("name") == "name: str"
        assert struct_type.get_field_description("age") == "age: int"

    def test_create_struct_type_from_ast_with_comments(self):
        """Test that create_struct_type_from_ast captures field comments."""
        # Create struct definition with field comments
        fields = [
            StructField(name="name", type_hint=TypeHint(name="str"), comment="the name of the person"),
            StructField(name="age", type_hint=TypeHint(name="int"), comment="the age in years"),
            StructField(name="email", type_hint=TypeHint(name="str")),  # No comment
        ]

        struct_def = StructDefinition(name="TestPerson", fields=fields)

        # Create struct type from AST
        struct_type = create_struct_type_from_ast(struct_def)

        # Verify field comments are captured
        assert struct_type.name == "TestPerson"
        assert struct_type.get_field_comment("name") == "the name of the person"
        assert struct_type.get_field_comment("age") == "the age in years"
        assert struct_type.get_field_comment("email") is None

    def test_prompt_enhancement_with_field_comments(self):
        """Test that prompt enhancement includes field comments."""
        # Register a struct type with field comments
        struct_type = StructType(
            name="TestPerson",
            fields={"name": "str", "age": "int"},
            field_order=["name", "age"],
            field_comments={"name": "the name of the person", "age": "the age in years"},
        )
        TYPE_REGISTRY.register(struct_type)

        # Create type context
        type_context = TypeContext(
            expected_type="TestPerson", context_type=ContextType.ASSIGNMENT, confidence=1.0, source_node=None, metadata={}
        )

        # Test prompt enhancement
        enhancer = PromptEnhancer()
        original_prompt = "Create a person"
        enhanced_prompt = enhancer.enhance_prompt(original_prompt, type_context)

        # Verify field descriptions include comments
        assert "name: str  # the name of the person" in enhanced_prompt
        assert "age: int  # the age in years" in enhanced_prompt
        assert enhanced_prompt != original_prompt

    def test_prompt_enhancement_without_field_comments(self):
        """Test that prompt enhancement works without field comments."""
        # Register a struct type without field comments
        struct_type = StructType(name="TestPerson", fields={"name": "str", "age": "int"}, field_order=["name", "age"], field_comments={})
        TYPE_REGISTRY.register(struct_type)

        # Create type context
        type_context = TypeContext(
            expected_type="TestPerson", context_type=ContextType.ASSIGNMENT, confidence=1.0, source_node=None, metadata={}
        )

        # Test prompt enhancement
        enhancer = PromptEnhancer()
        original_prompt = "Create a person"
        enhanced_prompt = enhancer.enhance_prompt(original_prompt, type_context)

        # Verify field descriptions work without comments
        assert "name: str" in enhanced_prompt
        assert "age: int" in enhanced_prompt
        assert enhanced_prompt != original_prompt


class TestStructFieldCommentsIntegration:
    """Integration tests for struct field comments."""

    def setup_method(self):
        """Clear struct registry before each test."""
        TYPE_REGISTRY.clear()

    def test_mixed_comments_and_no_comments(self):
        """Test struct with some fields having comments and others not."""
        # Create struct definition with mixed comments
        fields = [
            StructField(name="id", type_hint=TypeHint(name="str"), comment="unique identifier"),
            StructField(name="name", type_hint=TypeHint(name="str")),  # No comment
            StructField(name="active", type_hint=TypeHint(name="bool"), comment="whether the item is active"),
        ]

        struct_def = StructDefinition(name="TestItem", fields=fields)
        struct_type = create_struct_type_from_ast(struct_def)

        # Verify mixed comments are handled correctly
        assert struct_type.get_field_description("id") == "id: str  # unique identifier"
        assert struct_type.get_field_description("name") == "name: str"
        assert struct_type.get_field_description("active") == "active: bool  # whether the item is active"

    def test_complex_field_types_with_comments(self):
        """Test complex field types with comments."""
        # Create struct definition with complex types and comments
        fields = [
            StructField(name="metadata", type_hint=TypeHint(name="dict"), comment="additional metadata dictionary"),
            StructField(name="tags", type_hint=TypeHint(name="list"), comment="list of tags"),
            StructField(name="config", type_hint=TypeHint(name="dict"), comment="configuration settings"),
        ]

        struct_def = StructDefinition(name="ComplexStruct", fields=fields)
        struct_type = create_struct_type_from_ast(struct_def)

        # Verify complex types with comments
        assert struct_type.get_field_description("metadata") == "metadata: dict  # additional metadata dictionary"
        assert struct_type.get_field_description("tags") == "tags: list  # list of tags"
        assert struct_type.get_field_description("config") == "config: dict  # configuration settings"
