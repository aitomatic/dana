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
    AgentPoolStatement,
    AgentStatement,
    ExportStatement,
    FunctionDefinition,
    StructDefinition,
    UseStatement,
)
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

    def execute_agent_statement(self, node: AgentStatement, context: SandboxContext) -> Any:
        """Execute an agent statement with optimized processing.

        Args:
            node: The agent statement to execute
            context: The execution context

        Returns:
            An A2A agent resource object that can be used to call methods
        """
        self._resource_count += 1

        # Evaluate the arguments efficiently
        if not self.parent_executor or not hasattr(self.parent_executor, "parent"):
            raise SandboxError("Parent executor not properly initialized")

        args = [self.parent_executor.parent.execute(arg, context) for arg in node.args]
        kwargs = {k: self.parent_executor.parent.execute(v, context) for k, v in node.kwargs.items()}

        # Remove any user-provided 'name' parameter - agent names come from variable assignment
        if "name" in kwargs:
            provided_name = kwargs["name"]
            del kwargs["name"]
            self.warning(
                f"Agent name parameter '{provided_name}' will be overridden with variable name. Agent names are automatically derived from variable assignment."
            )

        # Set target name for agent
        target = node.target
        if target is not None:
            target_name = target.name if hasattr(target, "name") else str(target)
            kwargs["_name"] = target_name

        # Trace resource operation
        self._trace_resource_operation("agent", target_name if target else "anonymous", len(args), len(kwargs))

        # Call the agent function through the registry
        if self.function_registry is not None:
            result = self.function_registry.call("agent", context, None, *args, **kwargs)
        else:
            self.warning(f"No function registry available for {self.__class__.__name__}.execute_agent_statement")
            result = None

        return result

    def execute_agent_pool_statement(self, node: AgentPoolStatement, context: SandboxContext) -> Any:
        """Execute an agent pool statement with optimized processing.

        Args:
            node: The agent pool statement to execute
            context: The execution context

        Returns:
            An agent pool resource object that can be used to call methods
        """
        self._resource_count += 1

        # Evaluate the arguments efficiently
        if not self.parent_executor or not hasattr(self.parent_executor, "parent"):
            raise SandboxError("Parent executor not properly initialized")

        args = [self.parent_executor.parent.execute(arg, context) for arg in node.args]
        kwargs = {k: self.parent_executor.parent.execute(v, context) for k, v in node.kwargs.items()}

        # Remove any user-provided 'name' parameter - agent pool names come from variable assignment
        if "name" in kwargs:
            provided_name = kwargs["name"]
            del kwargs["name"]
            self.warning(
                f"Agent pool name parameter '{provided_name}' will be overridden with variable name. Agent pool names are automatically derived from variable assignment."
            )

        # Set target name for agent pool
        target = node.target
        if target is not None:
            target_name = target.name if hasattr(target, "name") else str(target)
            kwargs["_name"] = target_name

        # Trace resource operation
        self._trace_resource_operation("agent_pool", target_name if target else "anonymous", len(args), len(kwargs))

        # Call the agent_pool function through the registry
        if self.function_registry is not None:
            result = self.function_registry.call("agent_pool", context, None, *args, **kwargs)
        else:
            self.warning(f"No function registry available for {self.__class__.__name__}.execute_agent_pool_statement")
            result = None

        return result

    def execute_use_statement(self, node: UseStatement, context: SandboxContext) -> Any:
        """Execute a use statement with optimized processing.

        Args:
            node: The use statement to execute
            context: The execution context

        Returns:
            A resource object that can be used to call methods
        """
        self._resource_count += 1

        # Evaluate the arguments efficiently
        if not self.parent_executor or not hasattr(self.parent_executor, "parent"):
            raise SandboxError("Parent executor not properly initialized")

        args = [self.parent_executor.parent.execute(arg, context) for arg in node.args]
        kwargs = {k: self.parent_executor.parent.execute(v, context) for k, v in node.kwargs.items()}

        # Set target name for resource
        target = node.target
        if target is not None:
            target_name = target.split(".")[-1] if isinstance(target, str) else (target.name if hasattr(target, "name") else str(target))
            kwargs["_name"] = target_name

        # Trace resource operation
        self._trace_resource_operation("use", target_name if target else "anonymous", len(args), len(kwargs))

        # Call the use function through the registry
        if self.function_registry is not None:
            result = self.function_registry.call("use", context, None, *args, **kwargs)
        else:
            self.warning(f"No function registry available for {self.__class__.__name__}.execute_use_statement")
            result = None

        return result

    def execute_export_statement(self, node: ExportStatement, context: SandboxContext) -> None:
        """Execute an export statement with optimized processing.

        Args:
            node: The export statement node
            context: The execution context

        Returns:
            None
        """
        # Get the name to export
        name = node.name

        # Get the value from the local scope (validation step)
        try:
            context.get_from_scope(name, scope="local")
        except Exception:
            # If the value doesn't exist yet, that's okay - it might be defined later
            pass

        # Add to exports efficiently
        if not hasattr(context, "_exports"):
            context._exports = set()
        context._exports.add(name)

        # Trace export operation
        self._trace_resource_operation("export", name, 0, 0)

        # Return None since export statements don't produce a value
        return None

    def execute_struct_definition(self, node: StructDefinition, context: SandboxContext) -> None:
        """Execute a struct definition statement with optimized processing.

        Args:
            node: The struct definition node
            context: The execution context

        Returns:
            None (struct definitions don't produce a value, they register a type)
        """
        # Import here to avoid circular imports
        from dana.core.lang.interpreter.struct_system import create_struct_type_from_ast, StructTypeRegistry

        # Create the struct type and evaluate default values
        try:
            struct_type = create_struct_type_from_ast(node)
            
            # Evaluate default values in the current context
            if struct_type.field_defaults:
                evaluated_defaults = {}
                for field_name, default_expr in struct_type.field_defaults.items():
                    try:
                        # Evaluate the default value expression
                        default_value = self.parent_executor.parent.execute(default_expr, context)
                        evaluated_defaults[field_name] = default_value
                    except Exception as e:
                        raise SandboxError(f"Failed to evaluate default value for field '{field_name}': {e}")
                struct_type.field_defaults = evaluated_defaults
            
            # Register the struct type
            StructTypeRegistry.register(struct_type)
            self.debug(f"Registered struct type: {struct_type.name}")

            # Register struct constructor function in the context
            # This allows `instance = MyStruct(field1=value1, field2=value2)` syntax
            def struct_constructor(**kwargs):
                return StructTypeRegistry.create_instance(struct_type.name, kwargs)

            context.set(f"local:{node.name}", struct_constructor)

            # Trace struct registration
            self._trace_resource_operation("struct", node.name, len(node.fields), 0)

        except Exception as e:
            raise SandboxError(f"Failed to register struct {node.name}: {e}")

        return None

    def execute_agent_definition(self, node: AgentDefinition, context: SandboxContext) -> None:
        """Execute an agent definition statement with optimized processing.

        Args:
            node: The agent definition node
            context: The execution context

        Returns:
            None (agent definitions don't produce a value, they register a type)
        """
        # Import here to avoid circular imports
        from dana.agent.agent_system import AgentTypeRegistry, register_agent_from_ast

        # Create and register the agent type using the new struct-like system
        try:
            agent_type = register_agent_from_ast(node)
            # print(f"[DEBUG] Registered agent type: {agent_type.name}")
            from dana.agent.agent_system import AgentTypeRegistry
            # print(f"[DEBUG] AgentTypeRegistry.list_types(): {AgentTypeRegistry.list_types()}")

            # Store reference to this agent type for method association
            self._last_agent_type = agent_type

            # Register agent constructor function in the context
            # This allows `agent_instance = TestAgent(name="test")` syntax
            def agent_constructor(**kwargs):
                return AgentTypeRegistry.create_instance(agent_type.name, kwargs, context=context)

            context.set(f"local:{node.name}", agent_constructor)

            # Trace agent registration
            self._trace_resource_operation("agent_definition", node.name, len(node.fields), 0)

        except Exception as e:
            raise SandboxError(f"Failed to register agent {node.name}: {e}")

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
            body=node.body, parameters=param_names, context=context, return_type=return_type, defaults=param_defaults, name=node.name.name
        )

        # Check if this function should be associated with an agent type
        # Import here to avoid circular imports
        from dana.agent.agent_system import register_agent_method_from_function_def
        
        # Try to register as agent method if first parameter is an agent type
        register_agent_method_from_function_def(node, dana_func)

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
