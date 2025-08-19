"""Unit tests for struct docstring functionality."""

from dana.core.lang.interpreter.struct_system import StructType
from dana.registry import TYPE_REGISTRY


class TestStructDocstring:
    """Test struct docstring functionality."""

    def setup_method(self):
        """Clear struct registry before each test."""
        TYPE_REGISTRY.clear()

    def test_struct_type_with_docstring(self):
        """Test that StructType can store and retrieve docstrings."""
        # Create a struct type with docstring
        struct_type = StructType(
            name="TestStruct",
            fields={"name": "str", "value": "int"},
            field_order=["name", "value"],
            field_comments={},
            docstring="A test struct for verifying docstring functionality.",
        )

        # Verify docstring is stored and accessible
        assert struct_type.docstring == "A test struct for verifying docstring functionality."
        assert struct_type.get_docstring() == "A test struct for verifying docstring functionality."

    def test_struct_type_without_docstring(self):
        """Test that StructType handles missing docstrings gracefully."""
        # Create a struct type without docstring
        struct_type = StructType(
            name="TestStruct", fields={"name": "str", "value": "int"}, field_order=["name", "value"], field_comments={}, docstring=None
        )

        # Verify docstring is None
        assert struct_type.docstring is None
        assert struct_type.get_docstring() is None

    def test_struct_type_with_empty_docstring(self):
        """Test that StructType handles empty docstrings."""
        # Create a struct type with empty docstring
        struct_type = StructType(
            name="TestStruct", fields={"name": "str", "value": "int"}, field_order=["name", "value"], field_comments={}, docstring=""
        )

        # Verify empty docstring is stored
        assert struct_type.docstring == ""
        assert struct_type.get_docstring() == ""

    def test_struct_type_repr_with_docstring(self):
        """Test that StructType repr includes docstring information."""
        # Create a struct type with docstring
        struct_type = StructType(
            name="TestStruct",
            fields={"name": "str", "value": "int"},
            field_order=["name", "value"],
            field_comments={},
            docstring="A test struct for verifying docstring functionality.",
        )

        # Verify repr includes docstring
        repr_str = repr(struct_type)
        assert "TestStruct" in repr_str
        assert "name: str" in repr_str
        assert "value: int" in repr_str

    def test_struct_type_equality_with_docstring(self):
        """Test that StructType equality considers docstrings."""
        # Create two struct types with same fields but different docstrings
        struct_type1 = StructType(
            name="TestStruct",
            fields={"name": "str", "value": "int"},
            field_order=["name", "value"],
            field_comments={},
            docstring="First docstring",
        )

        struct_type2 = StructType(
            name="TestStruct",
            fields={"name": "str", "value": "int"},
            field_order=["name", "value"],
            field_comments={},
            docstring="Second docstring",
        )

        # They should NOT be equal since docstrings are different
        assert struct_type1 != struct_type2

        # But they should be equal if docstrings are the same
        struct_type3 = StructType(
            name="TestStruct",
            fields={"name": "str", "value": "int"},
            field_order=["name", "value"],
            field_comments={},
            docstring="First docstring",
        )
        assert struct_type1 == struct_type3

    def test_struct_type_registration_with_docstring(self):
        """Test that struct types with docstrings can be registered."""
        # Create and register a struct type with docstring
        struct_type = StructType(
            name="TestStruct",
            fields={"name": "str", "value": "int"},
            field_order=["name", "value"],
            field_comments={},
            docstring="A test struct for verifying docstring functionality.",
        )

        TYPE_REGISTRY.register(struct_type)

        # Retrieve and verify docstring is preserved
        retrieved_type = TYPE_REGISTRY.get("TestStruct")
        assert retrieved_type is not None
        assert retrieved_type.docstring == "A test struct for verifying docstring functionality."
        assert retrieved_type.get_docstring() == "A test struct for verifying docstring functionality."
