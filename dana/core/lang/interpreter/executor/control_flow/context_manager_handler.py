"""
Optimized context manager handling for Dana control flow.

This module provides high-performance context manager processing with
optimizations for with statement execution and variable shadowing detection.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import warnings
from typing import Any

from dana.common.mixins.loggable import Loggable
from dana.core.lang.ast import Identifier, WithStatement
from dana.core.lang.sandbox_context import SandboxContext


class ContextManagerHandler(Loggable):
    """Optimized context manager handler for Dana control flow.

    This handler manages:
    - With statement execution and context manager lifecycle
    - Variable shadowing detection and warnings
    - Context manager argument evaluation
    - Resource cleanup and exception handling

    Performance optimizations:
    - Context manager type caching
    - Variable shadowing pattern recognition
    - Optimized argument evaluation
    - Memory-efficient resource management
    """

    # Configuration constants
    CONTEXT_MANAGER_CACHE_SIZE = 100  # Max cached context manager types
    SHADOWING_PATTERN_CACHE_SIZE = 50  # Max cached shadowing patterns

    def __init__(self, parent_executor=None):
        """Initialize the context manager handler.

        Args:
            parent_executor: Reference to parent executor for statement execution
        """
        super().__init__()
        self.parent_executor = parent_executor
        self._context_manager_cache: dict[type, bool] = {}  # Cache for context manager validation
        self._shadowing_patterns: dict[str, str] = {}  # Cache for shadowing pattern detection
        self._with_statements_executed = 0  # Performance tracking

    def execute_with_stmt(self, node: WithStatement, context: SandboxContext) -> Any:
        """Execute a with statement with optimized context manager handling.

        Args:
            node: The with statement to execute
            context: The execution context

        Returns:
            The result of the last statement executed in the with block
        """
        if self.parent_executor is None:
            raise RuntimeError("Parent executor not available")

        self.debug(f"Starting with statement execution: {node.as_var}")
        self._with_statements_executed += 1

        # Check for variable name shadowing before executing
        self._check_with_variable_shadowing(node, context)

        # Get or create context manager
        context_manager = self._resolve_context_manager(node, context)

        # Validate context manager with caching
        if not self._is_valid_context_manager_cached(context_manager):
            context_manager_desc = node.context_manager if isinstance(node.context_manager, str) else str(node.context_manager)
            raise TypeError(f"Object '{context_manager_desc}' does not return a context manager (missing __enter__ or __exit__ methods)")

        # Execute the with statement using the context manager protocol
        return self._execute_with_protocol(node, context_manager, context)

    def _resolve_context_manager(self, node: WithStatement, context: SandboxContext) -> Any:
        """Resolve the context manager object from the node.

        Args:
            node: The with statement node
            context: The execution context

        Returns:
            The resolved context manager object
        """
        # Check if we have a function call or direct context manager object
        if isinstance(node.context_manager, str):
            # Function call pattern: with mcp(*args, **kwargs) as var:
            return self._create_context_manager_from_function(node, context)
        else:
            # Direct context manager pattern: with mcp_object as var:
            return self._get_context_manager_from_variable(node, context)

    def _create_context_manager_from_function(self, node: WithStatement, context: SandboxContext) -> Any:
        """Create context manager from function call.

        Args:
            node: The with statement node
            context: The execution context

        Returns:
            The context manager created by function call
        """
        if self.parent_executor is None:
            raise RuntimeError("Parent executor not available")

        function_registry = self.parent_executor.function_registry
        if not function_registry:
            raise RuntimeError("No function registry available for with statement")

        context_manager_name = node.context_manager

        # Prepare arguments for the context manager
        args = []
        kwargs = {}

        # Evaluate positional arguments
        for arg in node.args:
            args.append(self.parent_executor.execute(arg, context))

        # Evaluate keyword arguments
        for key, value in node.kwargs.items():
            kwargs[key] = self.parent_executor.execute(value, context)

        kwargs["_name"] = node.as_var

        self.debug(f"Creating context manager from function: {context_manager_name}")
        return function_registry.call(context_manager_name, context, None, *args, **kwargs)

    def _get_context_manager_from_variable(self, node: WithStatement, context: SandboxContext) -> Any:
        """Get context manager from variable reference.

        Args:
            node: The with statement node
            context: The execution context

        Returns:
            The context manager object from variable
        """
        if self.parent_executor is None:
            raise RuntimeError("Parent executor not available")

        # Get the context manager from the context using the full scoped name
        if hasattr(node.context_manager, "name") and isinstance(node.context_manager.name, str):
            # Handle scoped variables (e.g., private:mcp_client)
            if ":" in node.context_manager.name:
                scope, var_name = node.context_manager.name.split(":", 1)
                context_manager = context.get_from_scope(var_name, scope=scope)
            elif "." in node.context_manager.name:
                scope, var_name = node.context_manager.name.split(".", 1)
                context_manager = context.get_from_scope(var_name, scope=scope)
            else:
                context_manager = context.get_from_scope(node.context_manager.name, scope="local")
        else:
            context_manager = self.parent_executor.execute(node.context_manager, context)

        self.debug(f"Retrieved context manager from variable: {type(context_manager).__name__}")
        return context_manager

    def _execute_with_protocol(self, node: WithStatement, context_manager: Any, context: SandboxContext) -> Any:
        """Execute the context manager protocol with proper cleanup.

        Args:
            node: The with statement node
            context_manager: The context manager object
            context: The execution context

        Returns:
            The result of the with block execution
        """
        try:
            # Enter the context
            self.debug("Entering context manager")
            context_value = context_manager.__enter__()

            # Bind the context value to the 'as' variable in the local scope
            # The 'as' variable should always be in the local scope regardless of
            # where the context manager came from
            context.set_in_scope(node.as_var, context_value, scope="local")
            self.debug(f"Bound context value to variable: {node.as_var}")

            # Execute the body
            result = self._execute_statement_list(node.body, context)
            self.debug("With block body executed successfully")

        except Exception as exc:
            # Exit with exception information
            self.debug(f"Exception in with block: {type(exc).__name__}")
            if not context_manager.__exit__(type(exc), exc, exc.__traceback__):
                # If __exit__ returns False (or None), re-raise the exception
                raise
            # If __exit__ returns True, suppress the exception
            result = None

        else:
            # Exit without exception
            # Delete the variable from the local scope
            context.delete_from_scope(node.as_var, scope="local")
            context_manager.__exit__(None, None, None)
            self.debug("Context manager exited successfully")

        return result

    def _is_valid_context_manager_cached(self, obj: Any) -> bool:
        """Check if object is a valid context manager with caching.

        Args:
            obj: The object to check

        Returns:
            True if object has __enter__ and __exit__ methods
        """
        obj_type = type(obj)

        # Check cache first
        if obj_type in self._context_manager_cache:
            return self._context_manager_cache[obj_type]

        # Validate context manager protocol
        result = hasattr(obj, "__enter__") and hasattr(obj, "__exit__")

        # Cache the result with size limit
        if len(self._context_manager_cache) < self.CONTEXT_MANAGER_CACHE_SIZE:
            self._context_manager_cache[obj_type] = result

        return result

    def _check_with_variable_shadowing(self, node: WithStatement, context: SandboxContext) -> None:
        """Check for variable name shadowing in with statements and raise an error if detected.

        Args:
            node: The with statement node
            context: The execution context

        Raises:
            ValueError: If dangerous variable name shadowing is detected
        """
        as_var = node.as_var

        # Check shadowing pattern cache first
        pattern_key = self._get_shadowing_pattern_key(node)
        if pattern_key in self._shadowing_patterns:
            if self._shadowing_patterns[pattern_key] == "dangerous":
                raise ValueError(self._get_dangerous_shadowing_message(as_var))
            elif self._shadowing_patterns[pattern_key] == "warning":
                self._issue_shadowing_warning(as_var)
            return

        # Check if the 'as' variable already exists in the current scope
        if context.has(f"local:{as_var}"):
            # For direct context manager pattern, check if it's the same variable being shadowed
            if not isinstance(node.context_manager, str):
                shadowing_type = self._analyze_variable_shadowing(node, as_var)
                self._shadowing_patterns[pattern_key] = shadowing_type

                if shadowing_type == "dangerous":
                    raise ValueError(self._get_dangerous_shadowing_message(as_var))
                elif shadowing_type == "warning":
                    self._issue_shadowing_warning(as_var)
            else:
                # Function call pattern - issue warning
                self._shadowing_patterns[pattern_key] = "warning"
                self._issue_shadowing_warning(as_var)

    def _get_shadowing_pattern_key(self, node: WithStatement) -> str:
        """Generate a key for shadowing pattern caching.

        Args:
            node: The with statement node

        Returns:
            A key for caching shadowing patterns
        """
        cm_type = "function" if isinstance(node.context_manager, str) else "variable"
        return f"{cm_type}_{node.as_var}"

    def _analyze_variable_shadowing(self, node: WithStatement, as_var: str) -> str:
        """Analyze the type of variable shadowing.

        Args:
            node: The with statement node
            as_var: The as variable name

        Returns:
            "dangerous", "warning", or "safe"
        """
        if isinstance(node.context_manager, Identifier):
            context_manager_var = node.context_manager.name
            # Remove scope prefix to compare just the variable name
            if "." in context_manager_var:
                context_manager_var_name = context_manager_var.split(".")[-1]
            else:
                context_manager_var_name = context_manager_var

            if context_manager_var_name == as_var:
                return "dangerous"

        return "warning"

    def _get_dangerous_shadowing_message(self, as_var: str) -> str:
        """Get the error message for dangerous shadowing.

        Args:
            as_var: The as variable name

        Returns:
            The error message
        """
        return (
            f"Variable name shadowing detected: '{as_var}' is being used as both "
            f"the context manager and the 'as' variable in the with statement. "
            f"This can lead to confusion and loss of access to the original variable. "
            f"Consider using a different name for the 'as' variable, "
            f"such as 'with {as_var} as {as_var}_client:'"
        )

    def _issue_shadowing_warning(self, as_var: str) -> None:
        """Issue a warning for variable shadowing.

        Args:
            as_var: The as variable name
        """
        warnings.warn(
            f"Variable '{as_var}' already exists and will be shadowed by the with statement. "
            f"Consider using a different name for the 'as' variable to avoid confusion.",
            category=UserWarning,
            stacklevel=2,
        )

    def _execute_statement_list(self, statements: list[Any], context: SandboxContext) -> Any:
        """Execute a list of statements with optimization.

        Args:
            statements: The statements to execute
            context: The execution context

        Returns:
            The result of the last statement executed

        Raises:
            ReturnException: If a return statement is encountered
        """
        if self.parent_executor is None:
            raise RuntimeError("Parent executor not available")

        result = None
        for statement in statements:
            try:
                result = self.parent_executor.execute(statement, context)
            except Exception:
                # Let exceptions propagate to context manager protocol
                raise
        return result

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._context_manager_cache.clear()
        self._shadowing_patterns.clear()
        self._with_statements_executed = 0
        self.debug("Context manager handler cache cleared")

    def get_performance_stats(self) -> dict[str, Any]:
        """Get context manager performance statistics."""
        return {
            "with_statements_executed": self._with_statements_executed,
            "context_manager_cache_size": len(self._context_manager_cache),
            "shadowing_patterns_cached": len(self._shadowing_patterns),
            "context_manager_cache_limit": self.CONTEXT_MANAGER_CACHE_SIZE,
            "shadowing_pattern_cache_limit": self.SHADOWING_PATTERN_CACHE_SIZE,
        }
