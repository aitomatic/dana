"""
Type handler for Dana statements.

Provides struct and interface definition processing.
"""

from typing import Any

from dana.common.exceptions import SandboxError
from dana.common.mixins.loggable import Loggable
from dana.core.lang.ast import InterfaceDefinition, StructDefinition
from dana.core.lang.sandbox_context import SandboxContext


class TypeHandler(Loggable):
    def __init__(self, parent_executor: Any = None):
        super().__init__()
        self.parent_executor = parent_executor

    def execute_struct_definition(self, node: StructDefinition, context: SandboxContext) -> None:
        """Execute a struct definition statement.

        Registers a struct type and binds a constructor into the local scope.
        """
        # Import here to avoid circular imports
        from dana.core.builtin_types.struct_system import create_struct_type_from_ast
        from dana.registry import TYPE_REGISTRY

        try:
            struct_type = create_struct_type_from_ast(node)

            # Evaluate default values in the current context
            if struct_type.field_defaults:
                evaluated_defaults: dict[str, Any] = {}
                for field_name, default_expr in struct_type.field_defaults.items():
                    try:
                        default_value = self.parent_executor.parent.execute(default_expr, context)
                        evaluated_defaults[field_name] = default_value
                    except Exception as e:
                        raise SandboxError(f"Failed to evaluate default value for field '{field_name}': {e}")
                struct_type.field_defaults = evaluated_defaults

            # Register the struct type
            TYPE_REGISTRY.register(struct_type)
            self.debug(f"Registered struct type: {struct_type.name}")

            # Register struct constructor function in the context
            def struct_constructor(**kwargs):
                return TYPE_REGISTRY.create_instance(struct_type.name, kwargs)

            context.set(f"local:{node.name}", struct_constructor)
            return None

        except Exception as e:
            raise SandboxError(f"Failed to register struct {node.name}: {e}")

    def execute_interface_definition(self, node: InterfaceDefinition, context: SandboxContext) -> None:
        """Execute an interface definition statement.

        Registers an interface type in the type registry.
        """
        # Import here to avoid circular imports
        from dana.core.builtin_types.interface_system import create_interface_type_from_ast
        from dana.registry import TYPE_REGISTRY

        try:
            interface_type = create_interface_type_from_ast(node)

            # Register the interface type
            TYPE_REGISTRY.register(interface_type)
            self.debug(f"Registered interface type: {interface_type.name}")

            # Store the interface type in the context for potential use
            context.set(f"local:{node.name}", interface_type)
            return None

        except Exception as e:
            raise SandboxError(f"Failed to register interface {node.name}: {e}")
