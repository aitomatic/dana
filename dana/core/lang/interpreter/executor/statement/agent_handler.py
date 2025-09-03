"""
Optimized agent and resource handler for Dana statements.

This module provides high-performance agent, agent pool, use, and resource
statement processing with optimizations for resource management.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any

from dana.common.exceptions import SandboxError
from dana.common.mixins.loggable import Loggable
from dana.core.lang.ast import (
    AgentDefinition,
    BaseAgentSingletonDefinition,
    FunctionDefinition,
    SingletonAgentDefinition,
)
from dana.core.lang.interpreter.functions.dana_function import DanaFunction
from dana.core.lang.sandbox_context import SandboxContext


class AgentHandler(Loggable):
    """Optimized agent and resource handler for Dana statements."""

    # Performance constants
    RESOURCE_TRACE_THRESHOLD = 25  # Number of resource operations before tracing

    def __init__(self, parent_executor: Any = None, function_registry: Any = None):
        """Initialize the agent handler."""
        super().__init__()
        self.parent_executor = parent_executor
        self.function_registry = function_registry
        self._resource_count = 0
        # Track the last agent definition for method association
        self._last_agent_type: Any = None

    # Note: export and struct definition responsibilities moved to dedicated handlers

    def execute_agent_definition(self, node: AgentDefinition, context: SandboxContext) -> None:
        """
        Register an agent blueprint as an AgentType and constructor (instantiable).
        """
        try:
            # Create AgentStructType (blueprint)
            fields = {}
            field_order = []
            field_defaults = {}

            for field in node.fields:
                if field.type_hint is None or not hasattr(field.type_hint, "name"):
                    raise SandboxError(f"Field {field.name} has invalid type hint")
                fields[field.name] = field.type_hint.name
                field_order.append(field.name)
                if field.default_value is not None:
                    # Evaluate default in current context
                    default_value = self.parent_executor.parent.execute(field.default_value, context)
                    field_defaults[field.name] = default_value

            from dana.core.builtin_types.agent_system import AgentType
            from dana.registry import register_agent_type

            agent_type = AgentType(
                name=node.name,
                fields=fields,
                field_order=field_order,
                field_comments={},
                field_defaults=field_defaults or {},
                docstring=getattr(node, "docstring", None),
            )

            register_agent_type(agent_type)
            self.debug(f"Registered agent blueprint type: {agent_type.name}")
            self._last_agent_type = agent_type

            # Register constructor in context to create instances
            def agent_constructor(**kwargs):
                from dana.registry import TYPE_REGISTRY

                return TYPE_REGISTRY.create_instance(agent_type.name, kwargs)

            context.set(f"local:{node.name}", agent_constructor)
            self._trace_resource_operation("agent_blueprint", node.name, len(node.fields), 0)

            # Process agent methods (FunctionDefinition nodes)
            for method_def in node.methods:
                if isinstance(method_def, FunctionDefinition):
                    # Create DanaFunction from FunctionDefinition
                    dana_func = self._create_dana_function_from_definition(method_def, context)

                    # Register the method in unified registry
                    # Agent methods are registered with the agent type name as the receiver type
                    from dana.registry import FUNCTION_REGISTRY

                    FUNCTION_REGISTRY.register_struct_function(agent_type.name, method_def.name.name, dana_func)
                    self.debug(f"Registered agent method {method_def.name.name} for type {agent_type.name}")

        except Exception as e:
            raise SandboxError(f"Failed to register agent blueprint {node.name}: {e}")

        return None

    def _create_dana_function_from_definition(self, func_def: FunctionDefinition, context=None) -> DanaFunction:
        """
        Create a DanaFunction from a FunctionDefinition AST node.

        Args:
            func_def: The FunctionDefinition node
            context: Optional execution context

        Returns:
            DanaFunction object
        """
        # Extract parameter names and defaults
        param_names = []
        param_defaults = {}

        # Handle parameters (including receiver if present)
        all_params = []
        if func_def.receiver:
            all_params.append(func_def.receiver)
        all_params.extend(func_def.parameters)

        for param in all_params:
            if hasattr(param, "name"):
                param_name = param.name
                param_names.append(param_name)

                # Extract default value if present
                if hasattr(param, "default_value") and param.default_value is not None:
                    param_defaults[param_name] = param.default_value

        # Create DanaFunction
        from dana.core.lang.interpreter.functions.dana_function import DanaFunction

        return DanaFunction(
            name=func_def.name.name,
            parameters=param_names,
            defaults=param_defaults,
            body=func_def.body,
            return_type=func_def.return_type,
            decorators=func_def.decorators,
            is_sync=func_def.is_sync,
            location=func_def.location,
        )

    def execute_singleton_agent_definition(self, node: SingletonAgentDefinition, context: SandboxContext) -> None:
        """Create and bind a singleton agent instance from a blueprint with optional overrides."""
        try:
            # Find the blueprint type
            from dana.core.builtin_types.agent_system import AgentInstance, AgentType
            from dana.registry import get_agent_type, register_agent_type

            blueprint_type = get_agent_type(node.blueprint_name)
            if blueprint_type is None:
                raise SandboxError(f"Unknown agent blueprint '{node.blueprint_name}'")

            # Evaluate overrides
            overrides: dict[str, Any] = {}
            for f in node.overrides or []:
                overrides[f.name] = self.parent_executor.parent.execute(f.value, context)

            # Merge with defaults from the type
            merged_defaults: dict[str, Any] = {}
            if getattr(blueprint_type, "field_defaults", None):
                field_defaults = blueprint_type.field_defaults
                if field_defaults:
                    merged_defaults.update(field_defaults)
            merged_defaults.update(overrides)

            # If an alias is provided, create a derived AgentType that inherits blueprint fields/methods
            instance_type = blueprint_type
            if node.alias_name:
                derived = AgentType(
                    name=node.alias_name,
                    fields=dict(getattr(blueprint_type, "fields", {})),
                    field_order=list(getattr(blueprint_type, "field_order", [])),
                    field_defaults=dict(merged_defaults) if merged_defaults else {},
                    field_comments=dict(getattr(blueprint_type, "field_comments", {})),
                )
                # Inherit agent methods and capabilities
                if hasattr(blueprint_type, "_initial_agent_methods"):
                    derived._initial_agent_methods.update(blueprint_type._initial_agent_methods)
                if hasattr(blueprint_type, "reasoning_capabilities") and blueprint_type.reasoning_capabilities:
                    derived.reasoning_capabilities.extend(blueprint_type.reasoning_capabilities)

                register_agent_type(derived)
                instance_type = derived

            # Create the instance
            instance = AgentInstance(instance_type, merged_defaults)

            # Bind the singleton: prefer alias, else bind to blueprint name
            bind_name = node.alias_name or node.blueprint_name
            context.set(f"local:{bind_name}", instance)
            self._trace_resource_operation("agent_singleton", bind_name, 0, len(merged_defaults))

        except Exception as e:
            raise SandboxError(f"Failed to register singleton agent from blueprint {node.blueprint_name}: {e}")

        return None

    def execute_base_agent_singleton_definition(self, node: BaseAgentSingletonDefinition, context: SandboxContext) -> None:
        """Create a base AgentType with default methods and bind an instance to the alias name."""
        try:
            from dana.core.builtin_types.agent_system import AgentInstance, AgentType
            from dana.registry import register_agent_type

            # Create a minimal AgentType with a default 'name' field to satisfy struct requirements
            base_type = AgentType(
                name=node.alias_name,
                fields={"name": "str"},
                field_order=["name"],
                field_defaults={"name": node.alias_name},
                field_comments={},
            )
            register_agent_type(base_type)

            # Create instance with default name
            instance = AgentInstance(base_type, {})

            # Bind to alias
            context.set(f"local:{node.alias_name}", instance)
            self._trace_resource_operation("agent_singleton_base", node.alias_name, 0, 0)

        except Exception as e:
            raise SandboxError(f"Failed to create base agent '{node.alias_name}': {e}")

        return None

    def execute_function_definition(self, node: FunctionDefinition, context: SandboxContext) -> Any:
        """Execute a function definition, potentially associating it with the last agent type.

        Args:
            node: The function definition to execute
            context: The execution context

        Returns:
            The defined function
        """
        # Create the DanaFunction object
        from dana.core.lang.interpreter.functions.dana_function import DanaFunction

        # Extract parameter names and defaults
        param_names = []
        param_defaults = {}
        for param in node.parameters:
            if hasattr(param, "name"):
                param_name = param.name
                param_names.append(param_name)

                # Extract default value if present
                if hasattr(param, "default_value") and param.default_value is not None:
                    # Evaluate the default value expression in the current context
                    try:
                        default_value = self.parent_executor.parent.execute(param.default_value, context)
                        param_defaults[param_name] = default_value
                    except Exception as e:
                        self.debug(f"Failed to evaluate default value for parameter {param_name}: {e}")
                        pass
            else:
                param_names.append(str(param))

        # Extract return type if present
        return_type = None
        if hasattr(node, "return_type") and node.return_type is not None:
            if hasattr(node.return_type, "name"):
                return_type = node.return_type.name
            else:
                return_type = str(node.return_type)

        # Create the base DanaFunction with defaults
        dana_func = DanaFunction(
            body=node.body,
            parameters=param_names,
            context=context,
            return_type=return_type,
            defaults=param_defaults,
            name=node.name.name,
            is_sync=node.is_sync,
        )

        # Check if this function should be associated with an agent type
        # Import here to avoid circular imports
        # from dana.core.builtin_types.agent_system import register_agent_method_from_function_def

        # Try to register as agent method if first parameter is an agent type
        # register_agent_method_from_function_def(node, dana_func)

        # Apply decorators if present
        if node.decorators:
            wrapped_func = self._apply_decorators(dana_func, node.decorators, context)
            # Store the decorated function in context
            context.set(f"local:{node.name.name}", wrapped_func)
            return wrapped_func
        else:
            # No decorators, store the DanaFunction as usual
            context.set(f"local:{node.name.name}", dana_func)
            return dana_func

    def _apply_decorators(self, func, decorators, context):
        """Apply decorators to a function, handling both simple and parameterized decorators."""
        result = func
        # Apply decorators in reverse order (innermost first)
        for decorator in reversed(decorators):
            decorator_func = self._resolve_decorator(decorator, context)

            # Check if decorator has arguments (factory pattern)
            if decorator.args or decorator.kwargs:
                # Evaluate arguments to Python values
                evaluated_args = []
                evaluated_kwargs = {}

                for arg_expr in decorator.args:
                    evaluated_args.append(self.parent_executor.parent.execute(arg_expr, context))

                for key, value_expr in decorator.kwargs.items():
                    evaluated_kwargs[key] = self.parent_executor.parent.execute(value_expr, context)

                # Call the decorator factory with arguments
                actual_decorator = decorator_func(*evaluated_args, **evaluated_kwargs)
                result = actual_decorator(result)
            else:
                # Simple decorator (no arguments)
                result = decorator_func(result)

        return result

    def _resolve_decorator(self, decorator, context):
        """Resolve a decorator to a callable function."""
        # If it's a function call, resolve it
        if hasattr(decorator, "func") and hasattr(decorator, "args"):
            decorator_func = self.parent_executor.parent.execute(decorator.func, context)
            return decorator_func
        else:
            # Simple identifier
            return self.parent_executor.parent.execute(decorator, context)

    def _trace_resource_operation(self, operation_type: str, resource_name: str, arg_count: int, kwarg_count: int) -> None:
        """Trace resource operations for debugging when enabled.

        Args:
            operation_type: The type of resource operation
            resource_name: The name of the resource
            arg_count: Number of positional arguments
            kwarg_count: Number of keyword arguments
        """
        if self._resource_count >= self.RESOURCE_TRACE_THRESHOLD:
            try:
                self.debug(f"Resource #{self._resource_count}: {operation_type} '{resource_name}' (args={arg_count}, kwargs={kwarg_count})")
            except Exception:
                # Don't let tracing errors affect execution
                pass

    def get_stats(self) -> dict[str, Any]:
        """Get resource operation statistics."""
        return {
            "total_resource_operations": self._resource_count,
        }
