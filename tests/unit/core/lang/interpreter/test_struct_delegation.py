"""
Test struct delegation functionality.

This test suite verifies that Dana structs support automatic method and field
delegation through underscore-prefixed fields.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from unittest.mock import Mock

import pytest

from dana.core.builtin_types.struct_system import (
    StructInstance,
    StructType,
)
from dana.core.lang.interpreter.struct_functions.lambda_receiver import LambdaMethodDispatcher
from dana.registry import FUNCTION_REGISTRY, TYPE_REGISTRY


class TestStructDelegation:
    """Test struct delegation functionality."""

    def setup_method(self):
        """Reset registries before each test."""
        TYPE_REGISTRY.clear()
        FUNCTION_REGISTRY.clear()

    def teardown_method(self):
        """Reset registries after each test."""
        TYPE_REGISTRY.clear()
        FUNCTION_REGISTRY.clear()

    def test_delegatable_fields_identification(self):
        """Test that underscore-prefixed fields are identified as delegatable."""
        # Create a struct with mixed field types
        struct_type = StructType(
            name="TestStruct",
            fields={"_delegatable": "str", "regular": "str", "_another": "int"},
            field_order=["_delegatable", "regular", "_another"],
            field_comments={},
        )
        TYPE_REGISTRY.register(struct_type)

        instance = StructInstance(struct_type, {"_delegatable": "test", "regular": "normal", "_another": 42})

        delegatable_fields = instance._get_delegatable_fields()
        assert delegatable_fields == ["_delegatable", "_another"]
        assert "regular" not in delegatable_fields

    def test_field_delegation_basic(self):
        """Test basic field delegation from embedded struct."""
        # Create embedded struct type
        embedded_type = StructType(
            name="EmbeddedStruct", fields={"data": "str", "value": "int"}, field_order=["data", "value"], field_comments={}
        )
        TYPE_REGISTRY.register(embedded_type)

        # Create main struct type
        main_type = StructType(
            name="MainStruct",
            fields={"_embedded": "EmbeddedStruct", "regular": "str"},
            field_order=["_embedded", "regular"],
            field_comments={},
        )
        TYPE_REGISTRY.register(main_type)

        # Create instances
        embedded_instance = StructInstance(embedded_type, {"data": "embedded_data", "value": 123})
        main_instance = StructInstance(main_type, {"_embedded": embedded_instance, "regular": "main_data"})

        # Test field delegation
        assert main_instance.data == "embedded_data"
        assert main_instance.value == 123
        assert main_instance.regular == "main_data"

    def test_field_delegation_assignment(self):
        """Test field assignment through delegation."""
        # Create embedded struct type
        embedded_type = StructType(name="EmbeddedStruct", fields={"data": "str"}, field_order=["data"], field_comments={})
        TYPE_REGISTRY.register(embedded_type)

        # Create main struct type
        main_type = StructType(name="MainStruct", fields={"_embedded": "EmbeddedStruct"}, field_order=["_embedded"], field_comments={})
        TYPE_REGISTRY.register(main_type)

        # Create instances
        embedded_instance = StructInstance(embedded_type, {"data": "original"})
        main_instance = StructInstance(main_type, {"_embedded": embedded_instance})

        # Test field assignment through delegation
        main_instance.data = "modified"
        assert main_instance.data == "modified"
        assert embedded_instance.data == "modified"

    def test_multiple_delegation_fields_order(self):
        """Test delegation order with multiple underscore fields."""
        # Create two embedded struct types
        first_type = StructType(
            name="FirstStruct",
            fields={"shared_field": "str", "first_unique": "str"},
            field_order=["shared_field", "first_unique"],
            field_comments={},
        )
        TYPE_REGISTRY.register(first_type)

        second_type = StructType(
            name="SecondStruct",
            fields={"shared_field": "str", "second_unique": "str"},
            field_order=["shared_field", "second_unique"],
            field_comments={},
        )
        TYPE_REGISTRY.register(second_type)

        # Create main struct with delegation fields in specific order
        main_type = StructType(
            name="MainStruct",
            fields={"_first": "FirstStruct", "_second": "SecondStruct"},
            field_order=["_first", "_second"],  # _first comes first
            field_comments={},
        )
        TYPE_REGISTRY.register(main_type)

        # Create instances
        first_instance = StructInstance(first_type, {"shared_field": "from_first", "first_unique": "unique_first"})
        second_instance = StructInstance(second_type, {"shared_field": "from_second", "second_unique": "unique_second"})
        main_instance = StructInstance(main_type, {"_first": first_instance, "_second": second_instance})

        # Test delegation order - first declared field wins
        assert main_instance.shared_field == "from_first"  # _first comes before _second
        assert main_instance.first_unique == "unique_first"
        assert main_instance.second_unique == "unique_second"

    def test_explicit_field_access_still_works(self):
        """Test that explicit field access bypasses delegation."""
        # Create embedded struct type
        embedded_type = StructType(name="EmbeddedStruct", fields={"data": "str"}, field_order=["data"], field_comments={})
        TYPE_REGISTRY.register(embedded_type)

        # Create main struct type
        main_type = StructType(name="MainStruct", fields={"_embedded": "EmbeddedStruct"}, field_order=["_embedded"], field_comments={})
        TYPE_REGISTRY.register(main_type)

        # Create instances
        embedded_instance = StructInstance(embedded_type, {"data": "embedded_data"})
        main_instance = StructInstance(main_type, {"_embedded": embedded_instance})

        # Test explicit access works
        assert main_instance._embedded.data == "embedded_data"
        assert main_instance.data == "embedded_data"  # Through delegation

    def test_method_delegation_identification(self):
        """Test that methods can be found through delegation."""
        # Mock embedded object with a method
        embedded_mock = Mock()
        embedded_mock.test_method = Mock(return_value="delegated_result")

        # Create main struct type
        main_type = StructType(name="MainStruct", fields={"_embedded": "any"}, field_order=["_embedded"], field_comments={})
        TYPE_REGISTRY.register(main_type)

        # Create main instance
        main_instance = StructInstance(main_type, {"_embedded": embedded_mock})

        # Test delegation identification
        delegation_result = main_instance._find_delegated_method_access("test_method")
        assert delegation_result is not None
        delegated_object, method_name = delegation_result
        assert delegated_object is embedded_mock
        assert method_name == "test_method"

    def test_method_delegation_with_lambda_dispatcher(self):
        """Test method delegation through LambdaMethodDispatcher."""
        # Create embedded struct type with registered method
        embedded_type = StructType(name="EmbeddedStruct", fields={"data": "str"}, field_order=["data"], field_comments={})
        TYPE_REGISTRY.register(embedded_type)

        # Register a method for the embedded struct
        def embedded_method(instance, *args, **kwargs):
            return f"method called on {instance.data} with args: {args}"

        FUNCTION_REGISTRY.register_struct_function("EmbeddedStruct", "test_method", embedded_method)

        # Create main struct type
        main_type = StructType(name="MainStruct", fields={"_embedded": "EmbeddedStruct"}, field_order=["_embedded"], field_comments={})
        TYPE_REGISTRY.register(main_type)

        # Create instances
        embedded_instance = StructInstance(embedded_type, {"data": "embedded_data"})
        main_instance = StructInstance(main_type, {"_embedded": embedded_instance})

        # Test that dispatcher can handle delegated method
        assert LambdaMethodDispatcher.can_handle_method_call(main_instance, "test_method")

        # Test method dispatch through delegation
        result = LambdaMethodDispatcher.dispatch_method_call(main_instance, "test_method", "arg1", "arg2")
        assert "method called on embedded_data" in result
        assert "arg1" in result
        assert "arg2" in result

    def test_no_delegation_for_regular_fields(self):
        """Test that fields without underscore prefix don't delegate."""
        # Create embedded struct type
        embedded_type = StructType(name="EmbeddedStruct", fields={"data": "str"}, field_order=["data"], field_comments={})
        TYPE_REGISTRY.register(embedded_type)

        # Create main struct type with regular (non-delegating) field
        main_type = StructType(
            name="MainStruct",
            fields={"embedded": "EmbeddedStruct"},  # No underscore prefix
            field_order=["embedded"],
            field_comments={},
        )
        TYPE_REGISTRY.register(main_type)

        # Create instances
        embedded_instance = StructInstance(embedded_type, {"data": "embedded_data"})
        main_instance = StructInstance(main_type, {"embedded": embedded_instance})

        # Test that delegation doesn't work for regular fields
        with pytest.raises(AttributeError) as exc_info:
            _ = main_instance.data

        assert "has no field or delegated access 'data'" in str(exc_info.value)

    def test_error_messages_with_delegation_info(self):
        """Test that error messages include delegation information."""
        # Create embedded struct type
        embedded_type = StructType(
            name="EmbeddedStruct", fields={"available_field": "str"}, field_order=["available_field"], field_comments={}
        )
        TYPE_REGISTRY.register(embedded_type)

        # Create main struct type
        main_type = StructType(name="MainStruct", fields={"_embedded": "EmbeddedStruct"}, field_order=["_embedded"], field_comments={})
        TYPE_REGISTRY.register(main_type)

        # Create instances
        embedded_instance = StructInstance(embedded_type, {"available_field": "test"})
        main_instance = StructInstance(main_type, {"_embedded": embedded_instance})

        # Test error message includes delegation info
        with pytest.raises(AttributeError) as exc_info:
            _ = main_instance.nonexistent_field

        error_message = str(exc_info.value)
        assert "has no field or delegated access 'nonexistent_field'" in error_message
        assert "Available through delegation" in error_message

    def test_nested_delegation(self):
        """Test deeply nested delegation."""
        # Create deeply nested struct types
        inner_type = StructType(name="InnerStruct", fields={"inner_data": "str"}, field_order=["inner_data"], field_comments={})
        TYPE_REGISTRY.register(inner_type)

        middle_type = StructType(name="MiddleStruct", fields={"_inner": "InnerStruct"}, field_order=["_inner"], field_comments={})
        TYPE_REGISTRY.register(middle_type)

        outer_type = StructType(name="OuterStruct", fields={"_middle": "MiddleStruct"}, field_order=["_middle"], field_comments={})
        TYPE_REGISTRY.register(outer_type)

        # Create instances
        inner_instance = StructInstance(inner_type, {"inner_data": "deep_value"})
        middle_instance = StructInstance(middle_type, {"_inner": inner_instance})
        outer_instance = StructInstance(outer_type, {"_middle": middle_instance})

        # Test that outer can access inner data through middle delegation
        # This requires middle to delegate to inner, then outer to delegate to middle
        assert outer_instance._middle._inner.inner_data == "deep_value"  # Explicit access works
        # Note: Multi-level delegation (outer.inner_data) would require recursive delegation
        # which is not implemented in this basic version

    def test_delegation_with_none_values(self):
        """Test delegation behavior when delegatable fields are None."""
        # Create main struct type
        main_type = StructType(name="MainStruct", fields={"_optional": "any"}, field_order=["_optional"], field_comments={})
        TYPE_REGISTRY.register(main_type)

        # Create instance with None delegatable field
        main_instance = StructInstance(main_type, {"_optional": None})

        # Test that delegation gracefully handles None
        assert main_instance._get_delegatable_fields() == ["_optional"]
        assert main_instance._find_delegated_field_access("any_field") is None
        assert main_instance._find_delegated_method_access("any_method") is None

    def test_backward_compatibility(self):
        """Test that existing struct functionality remains unchanged."""
        # Create a regular struct without delegation
        regular_type = StructType(
            name="RegularStruct", fields={"field1": "str", "field2": "int"}, field_order=["field1", "field2"], field_comments={}
        )
        TYPE_REGISTRY.register(regular_type)

        # Create instance
        instance = StructInstance(regular_type, {"field1": "test", "field2": 42})

        # Test all existing functionality still works
        assert instance.field1 == "test"
        assert instance.field2 == 42
        assert instance.get_field_names() == ["field1", "field2"]
        assert instance.to_dict() == {"field1": "test", "field2": 42}

        # Test field assignment
        instance.field1 = "modified"
        assert instance.field1 == "modified"

        # Test error handling for non-existent fields
        with pytest.raises(AttributeError):
            _ = instance.nonexistent

        with pytest.raises(AttributeError):
            instance.nonexistent = "value"

    def test_performance_delegation_caching(self):
        """Test that delegation lookups don't cause performance issues."""
        # Create embedded struct type
        embedded_type = StructType(name="EmbeddedStruct", fields={"data": "str"}, field_order=["data"], field_comments={})
        TYPE_REGISTRY.register(embedded_type)

        # Create main struct type
        main_type = StructType(name="MainStruct", fields={"_embedded": "EmbeddedStruct"}, field_order=["_embedded"], field_comments={})
        TYPE_REGISTRY.register(main_type)

        # Create instances
        embedded_instance = StructInstance(embedded_type, {"data": "test_data"})
        main_instance = StructInstance(main_type, {"_embedded": embedded_instance})

        # Test repeated access (should be consistent)
        for _ in range(100):
            assert main_instance.data == "test_data"

        # Test that delegation fields list is consistent
        delegatable_fields_1 = main_instance._get_delegatable_fields()
        delegatable_fields_2 = main_instance._get_delegatable_fields()
        assert delegatable_fields_1 == delegatable_fields_2

    def test_mixed_delegation_and_direct_fields(self):
        """Test struct with both delegatable and direct fields."""
        # Create embedded struct type
        embedded_type = StructType(
            name="EmbeddedStruct", fields={"embedded_field": "str"}, field_order=["embedded_field"], field_comments={}
        )
        TYPE_REGISTRY.register(embedded_type)

        # Create main struct type with mixed field types
        main_type = StructType(
            name="MainStruct",
            fields={"direct_field": "str", "_delegatable": "EmbeddedStruct", "another_direct": "int"},
            field_order=["direct_field", "_delegatable", "another_direct"],
            field_comments={},
        )
        TYPE_REGISTRY.register(main_type)

        # Create instances
        embedded_instance = StructInstance(embedded_type, {"embedded_field": "delegated_value"})
        main_instance = StructInstance(main_type, {"direct_field": "direct_value", "_delegatable": embedded_instance, "another_direct": 42})

        # Test all field access types work correctly
        assert main_instance.direct_field == "direct_value"
        assert main_instance.another_direct == 42
        assert main_instance.embedded_field == "delegated_value"  # Through delegation
        assert main_instance._delegatable.embedded_field == "delegated_value"  # Explicit access
