"""
Unified Function Dispatcher - Central coordination for all function resolution.

This module provides the main dispatcher that replaces the fragmented function
resolution strategies across the Dana interpreter with a single, predictable
resolution order.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any

from dana.common.exceptions import SandboxError
from dana.common.utils.logging import DANA_LOGGER
from dana.core.lang.interpreter.executor.function_name_utils import FunctionNameInfo
from dana.core.lang.interpreter.executor.function_resolver import ResolvedFunction
from dana.core.lang.sandbox_context import SandboxContext

from .base_resolver import FunctionResolverInterface, ResolutionAttempt, ResolutionStatus
from .composed_function_resolver import ComposedFunctionResolver
from .context_function_resolver import ContextFunctionResolver
from .core_function_resolver import CoreFunctionResolver
from .fallback_resolver import FallbackResolver


class UnifiedFunctionDispatcher:
    """
    Central dispatcher for all function resolution in the Dana interpreter.

    This class replaces the fragmented function resolution strategies with a
    single, predictable resolution order:

    1. CoreFunctionResolver (priority 10) - Registry functions
    2. ContextFunctionResolver (priority 20) - User-defined functions
    3. ComposedFunctionResolver (priority 30) - Function composition
    4. FallbackResolver (priority 40) - Error recovery
    """

    def __init__(self, function_registry: Any = None, executor: Any = None):
        """Initialize the unified function dispatcher.

        Args:
            function_registry: The function registry for core functions
            executor: The function executor for result coercion
        """
        self.logger = DANA_LOGGER
        self.function_registry = function_registry
        self.executor = executor

        # Initialize resolvers in priority order
        self.resolvers: list[FunctionResolverInterface] = []
        self._initialize_resolvers()

        # Resolution tracking
        self.resolution_history: list[ResolutionAttempt] = []
        self.stats = {
            "total_resolutions": 0,
            "successful_resolutions": 0,
            "cache_hits": 0,
        }

    def _initialize_resolvers(self) -> None:
        """Initialize all resolvers in priority order."""
        # Create resolvers with their dependencies
        resolvers = [
            CoreFunctionResolver(self.function_registry),
            ContextFunctionResolver(),
            ComposedFunctionResolver(),
            FallbackResolver(),
        ]

        # Sort by priority (lower number = higher priority)
        self.resolvers = sorted(resolvers, key=lambda r: r.get_priority())

        self.logger.debug(f"Initialized {len(self.resolvers)} resolvers: {[r.get_name() for r in self.resolvers]}")

    def resolve_function(self, name_info: FunctionNameInfo, context: SandboxContext) -> ResolvedFunction:
        """Resolve a function using the unified resolution order.

        Args:
            name_info: Parsed function name information
            context: The execution context

        Returns:
            ResolvedFunction with the resolved function and metadata

        Raises:
            SandboxError: If function cannot be resolved by any resolver
        """
        self.stats["total_resolutions"] += 1
        attempts: list[ResolutionAttempt] = []

        self.logger.debug(f"Resolving function: {name_info.original_name}")

        # Try each resolver in priority order
        for resolver in self.resolvers:
            try:
                # Fast check if resolver can handle this function
                if not resolver.can_resolve(name_info, context):
                    attempt = resolver.create_attempt(
                        name_info, ResolutionStatus.NOT_FOUND, error_message="Resolver cannot handle this function type"
                    )
                    attempts.append(attempt)
                    continue

                self.logger.debug(f"Trying resolver: {resolver.get_name()}")

                # Attempt resolution
                result = resolver.resolve(name_info, context)

                if result:
                    # Success!
                    attempt = resolver.create_attempt(name_info, ResolutionStatus.SUCCESS, result=result)
                    attempts.append(attempt)

                    # Store resolution history
                    self.resolution_history.extend(attempts)
                    self.stats["successful_resolutions"] += 1

                    self.logger.debug(f"Function resolved by {resolver.get_name()}: {result}")
                    return result
                else:
                    # Not found by this resolver
                    attempt = resolver.create_attempt(
                        name_info, ResolutionStatus.NOT_FOUND, error_message="Function not found in this resolver"
                    )
                    attempts.append(attempt)

            except Exception as e:
                # Resolver failed with an error
                attempt = resolver.create_attempt(name_info, ResolutionStatus.ERROR, error_message=str(e))
                attempts.append(attempt)
                self.logger.debug(f"Resolver {resolver.get_name()} failed: {e}")
                continue

        # Store failed resolution history
        self.resolution_history.extend(attempts)

        # No resolver could handle the function
        self._raise_function_not_found_error(name_info, attempts)
        # This line will never be reached, but satisfies the type checker
        raise SandboxError("Function resolution failed")

    def execute_function(
        self,
        resolved_func: ResolvedFunction,
        context: SandboxContext,
        evaluated_args: list[Any],
        evaluated_kwargs: dict[str, Any],
        func_name: str,
    ) -> Any:
        """Execute a resolved function with the appropriate execution strategy.

        Args:
            resolved_func: The resolved function
            context: The execution context
            evaluated_args: Evaluated positional arguments
            evaluated_kwargs: Evaluated keyword arguments
            func_name: The function name for error reporting

        Returns:
            The function execution result
        """
        self.logger.debug(f"Executing {resolved_func.func_type.value} function: {func_name}")

        # Import here to avoid circular imports
        from dana.core.lang.interpreter.executor.function_resolver import FunctionType

        if resolved_func.func_type == FunctionType.REGISTRY:
            return self._execute_registry_function(resolved_func, context, evaluated_args, evaluated_kwargs, func_name)
        elif resolved_func.func_type == FunctionType.DANA:
            return self._execute_dana_function(resolved_func, context, evaluated_args, evaluated_kwargs, func_name)
        elif resolved_func.func_type == FunctionType.PYTHON:
            return self._execute_python_function(resolved_func, context, evaluated_args, evaluated_kwargs, func_name)
        elif resolved_func.func_type == FunctionType.CALLABLE:
            return self._execute_callable_function(resolved_func, context, evaluated_args, evaluated_kwargs, func_name)
        else:
            raise SandboxError(f"Unknown function type '{resolved_func.func_type.value}' for function '{func_name}'")

    def _execute_registry_function(
        self,
        resolved_func: ResolvedFunction,
        context: SandboxContext,
        evaluated_args: list[Any],
        evaluated_kwargs: dict[str, Any],
        func_name: str,
    ) -> Any:
        """Execute a registry function."""
        if not self.function_registry:
            raise SandboxError(f"No function registry available to execute function '{func_name}'")

        resolved_name = str(resolved_func.metadata.get("resolved_name") or func_name)

        # Handle context parameter conflict by removing user context from kwargs
        # and merging it into the system context before calling the registry
        user_context = None
        if "context" in evaluated_kwargs:
            user_context = evaluated_kwargs.pop("context")
            if isinstance(user_context, dict):
                # Merge user context into local scope of system context
                for key, value in user_context.items():
                    context.set(f"local:{key}", value)

        # Use None namespace to let the registry search across all namespaces
        raw_result = self.function_registry.call(resolved_name, context, None, *evaluated_args, **evaluated_kwargs)
        return self._assign_and_coerce_result(raw_result, func_name)

    def _execute_dana_function(
        self,
        resolved_func: ResolvedFunction,
        context: SandboxContext,
        evaluated_args: list[Any],
        evaluated_kwargs: dict[str, Any],
        func_name: str,
    ) -> Any:
        """Execute a Dana function with PromiseLimiter integration."""
        from dana.core.lang.interpreter.functions.dana_function import DanaFunction

        # Get PromiseLimiter from context
        promise_limiter = context.promise_limiter

        # For Dana functions, use the function's own context as the base
        # This ensures it has access to module functions and other context
        if isinstance(resolved_func.func, DanaFunction) and resolved_func.func.context is not None:
            # Use the function's context as the base, but merge in the current context
            # This allows the function to access both its module functions and the current context
            execution_context = resolved_func.func.context.create_child_context()
            # Merge the current context's local scope into the execution context
            for key, value in context.get_scope("local").items():
                execution_context.set(f"local:{key}", value)

            # Ensure the interpreter is set in the execution context
            if hasattr(context, "_interpreter") and context._interpreter is not None:
                execution_context._interpreter = context._interpreter
        else:
            # Fallback to current context for non-DanaFunction objects
            execution_context = context

        # Check if this is a sync function (should not be wrapped in Promise)
        is_sync_function = isinstance(resolved_func.func, DanaFunction) and getattr(resolved_func.func, "is_sync", False)

        self.logger.debug(
            f"Function '{func_name}' - is_sync_function: {is_sync_function}, func type: {type(resolved_func.func)}, is_sync: {getattr(resolved_func.func, 'is_sync', 'N/A')}"
        )

        if is_sync_function:
            # Execute sync function synchronously (no Promise wrapping)
            self.logger.debug(f"Executing sync function '{func_name}' synchronously (no Promise wrapping)")
            raw_result = resolved_func.func.execute(execution_context, *evaluated_args, **evaluated_kwargs)
            return self._assign_and_coerce_result(raw_result, func_name)

        # Check if we can create a Promise for this function execution
        can_create = promise_limiter.can_create_promise()
        self.logger.debug(f"Function '{func_name}' - can_create_promise: {can_create}")

        if can_create:
            # Create a computation function that will execute the Dana function
            def dana_function_computation():
                try:
                    return resolved_func.func.execute(execution_context, *evaluated_args, **evaluated_kwargs)
                except Exception as e:
                    self.logger.error(f"Error in Dana function computation: {e}")
                    raise

            # Create EagerPromise for the function execution
            from dana.core.runtime import DanaThreadPool

            executor = DanaThreadPool.get_instance().get_executor()

            promise_result = promise_limiter.create_promise(dana_function_computation, executor=executor, on_delivery=None)

            self.logger.debug(f"Created EagerPromise for Dana function '{func_name}'")
            return self._assign_and_coerce_result(promise_result, func_name)
        else:
            # Fall back to synchronous execution when limits are exceeded
            self.logger.debug(f"PromiseLimiter limits exceeded, executing Dana function '{func_name}' synchronously")
            raw_result = resolved_func.func.execute(execution_context, *evaluated_args, **evaluated_kwargs)
            return self._assign_and_coerce_result(raw_result, func_name)

    def _execute_python_function(
        self,
        resolved_func: ResolvedFunction,
        context: SandboxContext,
        evaluated_args: list[Any],
        evaluated_kwargs: dict[str, Any],
        func_name: str,
    ) -> Any:
        """Execute a Python function."""
        raw_result = resolved_func.func.execute(context, *evaluated_args, **evaluated_kwargs)
        return self._assign_and_coerce_result(raw_result, func_name)

    def _execute_callable_function(
        self,
        resolved_func: ResolvedFunction,
        context: SandboxContext,
        evaluated_args: list[Any],
        evaluated_kwargs: dict[str, Any],
        func_name: str,
    ) -> Any:
        """Execute a regular callable with automatic async detection."""
        import asyncio
        from dana.common.utils.misc import Misc
        
        func = resolved_func.func
        
        # Execute-time async detection and handling
        if asyncio.iscoroutinefunction(func):
            # Function is async - use Misc.safe_asyncio_run
            raw_result = Misc.safe_asyncio_run(func, *evaluated_args, **evaluated_kwargs)
        else:
            # Function is sync - call directly
            raw_result = func(*evaluated_args, **evaluated_kwargs)
            
        return self._assign_and_coerce_result(raw_result, func_name)

    def _assign_and_coerce_result(self, raw_result: Any, func_name: str) -> Any:
        """Assign and coerce function result."""
        # Delegate to the executor if available
        if self.executor and hasattr(self.executor, "_assign_and_coerce_result"):
            return self.executor._assign_and_coerce_result(raw_result, func_name)
        else:
            # Fallback: return the raw result
            return raw_result

    def get_resolution_history(self) -> list[ResolutionAttempt]:
        """Get the history of all resolution attempts.

        Returns:
            List of all resolution attempts
        """
        return self.resolution_history.copy()

    def get_stats(self) -> dict[str, Any]:
        """Get dispatcher statistics.

        Returns:
            Dictionary of statistics
        """
        return self.stats.copy()

    def clear_history(self) -> None:
        """Clear the resolution history (useful for testing)."""
        self.resolution_history.clear()

    def _raise_function_not_found_error(self, name_info: FunctionNameInfo, attempts: list[ResolutionAttempt]) -> None:
        """Raise a comprehensive function not found error.

        Args:
            name_info: Function name information
            attempts: All resolution attempts
        """
        # Create detailed error message with resolution history
        error_lines = [f"Function '{name_info.original_name}' not found."]

        if attempts:
            error_lines.append("Resolution attempts:")
            for attempt in attempts:
                status_str = f"  - {attempt.resolver_name}: {attempt.status.value}"
                if attempt.error_message:
                    status_str += f" ({attempt.error_message})"
                error_lines.append(status_str)

        # TODO: Add suggestions for similar function names
        # TODO: Add list of available functions in relevant namespaces

        error_message = "\n".join(error_lines)
        raise SandboxError(error_message)
