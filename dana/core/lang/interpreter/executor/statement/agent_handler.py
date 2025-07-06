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
from dana.core.lang.parser.ast import AgentPoolStatement, AgentStatement, ExportStatement, StructDefinition, UseStatement
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
        from dana.core.lang.interpreter.struct_system import register_struct_from_ast

        # Register the struct type in the global registry
        try:
            struct_type = register_struct_from_ast(node)
            self.debug(f"Registered struct type: {struct_type.name}")

            # Trace struct registration
            self._trace_resource_operation("struct", node.name, len(node.fields), 0)

        except Exception as e:
            raise SandboxError(f"Failed to register struct {node.name}: {e}")

        return None

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
