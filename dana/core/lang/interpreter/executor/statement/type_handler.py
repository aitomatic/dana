"""
Type handler for Dana statements.

Provides struct definition processing.
"""

from typing import Any

from dana.common.exceptions import SandboxError
from dana.common.mixins.loggable import Loggable
from dana.core.lang.ast import StructDefinition
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
        from dana.core.lang.interpreter.struct_system import StructTypeRegistry, create_struct_type_from_ast

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
            StructTypeRegistry.register(struct_type)
            self.debug(f"Registered struct type: {struct_type.name}")

            # Register struct constructor function in the context
            def struct_constructor(**kwargs):
                return StructTypeRegistry.create_instance(struct_type.name, kwargs)

            context.set(f"local:{node.name}", struct_constructor)
            return None

        except Exception as e:
            raise SandboxError(f"Failed to register struct {node.name}: {e}")
