"""
Dana Interface System

This module provides interface validation and compliance checking for Dana's
interface system, integrating with the existing function resolution system.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any

from dana.common.mixins.loggable import Loggable
from dana.core.builtin_types.struct_system import InterfaceMethodSpec, InterfaceParameterSpec, InterfaceType
from dana.registry import FUNCTION_REGISTRY


class InterfaceComplianceError(Exception):
    """Exception raised when a type does not satisfy an interface contract."""

    def __init__(
        self,
        type_name: str,
        interface_name: str,
        missing_methods: list[str],
        signature_mismatches: list[tuple[str, str, str]],
        missing_properties: list[str],
    ):
        self.type_name = type_name
        self.interface_name = interface_name
        self.missing_methods = missing_methods
        self.signature_mismatches = signature_mismatches
        self.missing_properties = missing_properties

        # Build detailed error message
        message_parts = [f"{type_name} does not satisfy {interface_name} interface:"]

        if missing_methods:
            message_parts.append(f"  - Missing methods: {', '.join(missing_methods)}")

        if signature_mismatches:
            message_parts.append("  - Signature mismatches:")
            for method_name, expected, found in signature_mismatches:
                message_parts.append(f"    {method_name}: expected {expected}, found {found}")

        if missing_properties:
            message_parts.append(f"  - Missing properties: {', '.join(missing_properties)}")

        super().__init__("\n".join(message_parts))


class InterfaceValidator(Loggable):
    """Validates interface compliance using Dana's function resolution system."""

    def __init__(self):
        """Initialize the interface validator."""
        super().__init__()

    def validate_interface_compliance(self, value: Any, interface_type: InterfaceType) -> bool:
        """Validate that a value satisfies an interface contract.

        Args:
            value: The value to validate
            interface_type: The interface type to validate against

        Returns:
            True if the value satisfies the interface, False otherwise

        Raises:
            InterfaceComplianceError: If validation fails with detailed error information
        """
        self.debug(f"Validating {type(value).__name__} against interface {interface_type.name}")

        # Get the flattened method set (including embedded interfaces)
        flattened_methods = interface_type.flatten_methods()

        missing_methods = []
        signature_mismatches = []
        missing_properties = []

        # Check each required method
        for method_name, method_spec in flattened_methods.items():
            if not self._validate_method(value, method_name, method_spec):
                missing_methods.append(method_name)

        # Check property accessors (getters and setters)
        for method_name, method_spec in flattened_methods.items():
            if method_name.startswith(("get_", "set_")):
                if not self._validate_property_accessor(value, method_name, method_spec):
                    missing_properties.append(method_name)

        # If any validation failed, raise detailed error
        if missing_methods or signature_mismatches or missing_properties:
            raise InterfaceComplianceError(
                type_name=type(value).__name__,
                interface_name=interface_type.name,
                missing_methods=missing_methods,
                signature_mismatches=signature_mismatches,
                missing_properties=missing_properties,
            )

        self.debug(f"✓ {type(value).__name__} satisfies interface {interface_type.name}")
        return True

    def _validate_method(self, value: Any, method_name: str, method_spec: InterfaceMethodSpec) -> bool:
        """Validate that a value has a method with the correct signature.

        Args:
            value: The value to validate
            method_name: The name of the method to check
            method_spec: The method specification from the interface

        Returns:
            True if the method exists with correct signature, False otherwise
        """
        # Look for receiver function using Dana's function resolution system
        receiver_func = FUNCTION_REGISTRY.lookup_struct_function_for_instance(value, method_name)

        if receiver_func is None:
            self.debug(f"Method '{method_name}' not found for {type(value).__name__}")
            return False

        # For now, we'll do basic signature validation
        # In a more complete implementation, we'd parse the function signature
        # and compare parameter types and return types
        self.debug(f"Found method '{method_name}' for {type(value).__name__}")
        return True

    def _validate_property_accessor(self, value: Any, accessor_name: str, method_spec: InterfaceMethodSpec) -> bool:
        """Validate that a value has a property accessor with the correct signature.

        Args:
            value: The value to validate
            accessor_name: The name of the property accessor (get_* or set_*)
            method_spec: The method specification from the interface

        Returns:
            True if the property accessor exists with correct signature, False otherwise
        """
        # Look for receiver function using Dana's function resolution system
        receiver_func = FUNCTION_REGISTRY.lookup_struct_function_for_instance(value, accessor_name)

        if receiver_func is None:
            self.debug(f"Property accessor '{accessor_name}' not found for {type(value).__name__}")
            return False

        # For now, we'll do basic signature validation
        # In a more complete implementation, we'd parse the function signature
        # and compare parameter types and return types
        self.debug(f"Found property accessor '{accessor_name}' for {type(value).__name__}")
        return True

    def validate_interface_type(self, interface_type: InterfaceType) -> bool:
        """Validate that an interface type is well-formed.

        Args:
            interface_type: The interface type to validate

        Returns:
            True if the interface is well-formed, False otherwise
        """
        if not interface_type.name:
            self.error("Interface name cannot be empty")
            return False

        if not interface_type.methods:
            self.error(f"Interface '{interface_type.name}' must have at least one method")
            return False

        # Check for duplicate method names
        method_names = list(interface_type.methods.keys())
        if len(method_names) != len(set(method_names)):
            self.error(f"Interface '{interface_type.name}' has duplicate method names")
            return False

        # Check embedded interfaces exist (if we have access to type registry)
        # This would require passing the type registry to this method

        self.debug(f"✓ Interface '{interface_type.name}' is well-formed")
        return True


def create_interface_type_from_ast(interface_def) -> InterfaceType:
    """Create an InterfaceType from an InterfaceDefinition AST node.

    Args:
        interface_def: The InterfaceDefinition AST node

    Returns:
        InterfaceType with methods and embedded interfaces
    """
    from dana.core.lang.ast import InterfaceDefinition, InterfaceMethod

    if not isinstance(interface_def, InterfaceDefinition):
        raise TypeError(f"Expected InterfaceDefinition, got {type(interface_def)}")

    # Convert InterfaceMethod list to dict
    methods = {}

    for method in interface_def.methods:
        if not isinstance(method, InterfaceMethod):
            raise TypeError(f"Expected InterfaceMethod, got {type(method)}")

        # Convert parameters to InterfaceParameterSpec
        parameters = []
        for param in method.parameters:
            param_spec = InterfaceParameterSpec(
                name=param.name, type_name=param.type_hint.name if param.type_hint else None, has_default=param.default_value is not None
            )
            parameters.append(param_spec)

        # Create method specification
        method_spec = InterfaceMethodSpec(
            name=method.name,
            parameters=parameters,
            return_type=method.return_type.name if method.return_type else None,
            comment=method.comment,
        )

        methods[method.name] = method_spec

    return InterfaceType(
        name=interface_def.name,
        methods=methods,
        embedded_interfaces=interface_def.embedded_interfaces,
        docstring=interface_def.docstring,
    )


def register_interface_from_ast(interface_def) -> InterfaceType:
    """Register an interface type from AST definition.

    Args:
        interface_def: The interface definition AST node

    Returns:
        InterfaceType that was registered
    """
    interface_type = create_interface_type_from_ast(interface_def)
    from dana.registry import TYPE_REGISTRY

    TYPE_REGISTRY.register(interface_type)
    return interface_type
