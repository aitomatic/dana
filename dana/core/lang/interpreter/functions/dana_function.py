"""
Dana function implementation.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any

from dana.common.mixins.loggable import Loggable
from dana.core.lang.interpreter.executor.control_flow.exceptions import ReturnException
from dana.core.lang.interpreter.functions.sandbox_function import SandboxFunction
from dana.core.lang.sandbox_context import SandboxContext


class DanaFunction(SandboxFunction, Loggable):
    """A Dana function that can be called with arguments."""

    def __init__(
        self,
        body: list[Any],
        parameters: list[str],
        context: SandboxContext | None = None,
        return_type: str | None = None,
        defaults: dict[str, Any] | None = None,
        name: str | None = None,
    ):
        """Initialize a Dana function.

        Args:
            body: The function body statements
            parameters: The parameter names
            context: The sandbox context
            return_type: The function's return type annotation
            defaults: Default values for parameters
            name: The function name
        """
        super().__init__(context)
        self.body = body
        self.parameters = parameters
        self.return_type = return_type
        self.defaults = defaults or {}
        self.__name__ = name or "unknown"  # Add __name__ attribute for compatibility
        self.debug(
            f"Created DanaFunction with name={self.__name__}, parameters={parameters}, return_type={return_type}, defaults={self.defaults}"
        )

    @property
    def interpreter(self):
        """Get the interpreter instance."""
        if self._interpreter is None:
            # Try to get from context
            if hasattr(self, 'context') and self.context and hasattr(self.context, '_interpreter'):
                return self.context._interpreter
            raise RuntimeError("Interpreter not set on function")
        return self._interpreter
    
    @interpreter.setter 
    def interpreter(self, value):
        """Set the interpreter instance."""
        self._interpreter = value

    def prepare_context(self, context: SandboxContext | Any, args: list[Any], kwargs: dict[str, Any]) -> SandboxContext:
        """
        Prepare context for a Dana function.

        For Dana functions:
        - Starts with the function's original module context (for access to module variables)
        - Creates a clean local scope for the function
        - Sets up interpreter if needed
        - Applies default values for parameters
        - Maps arguments to the local scope

        Args:
            context: The current execution context or a positional argument
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            Prepared context
        """
        # If context is not a SandboxContext, assume it's a positional argument
        if not isinstance(context, SandboxContext):
            args = [context] + args
            context = self.context.copy() if self.context else SandboxContext()

        # Start with the function's original module context (for access to module's public/private variables)
        if self.context is not None:
            prepared_context = self.context.copy()
            # Copy interpreter from current execution context if the module context doesn't have one
            if not hasattr(prepared_context, "_interpreter") or prepared_context._interpreter is None:
                if hasattr(context, "_interpreter") and context._interpreter is not None:
                    prepared_context._interpreter = context._interpreter
        else:
            # Fallback to current context if no module context available
            prepared_context = context.copy()

        # Store original local scope so we can restore it later
        original_locals = prepared_context.get_scope("local").copy()
        prepared_context._original_locals = original_locals

        # Keep existing variables but prepare to add function parameters
        # Don't clear the local scope - preserve existing variables

        # First, apply default values for all parameters that have them
        for param_name in self.parameters:
            if param_name in self.defaults:
                prepared_context.set(param_name, self.defaults[param_name])

        # Map positional arguments to parameters in the local scope (can override defaults)
        for i, param_name in enumerate(self.parameters):
            if i < len(args):
                prepared_context.set(param_name, args[i])

        # Map keyword arguments to the local scope (can override defaults and positional args)
        for kwarg_name, kwarg_value in kwargs.items():
            if kwarg_name in self.parameters:
                prepared_context.set(kwarg_name, kwarg_value)

        return prepared_context

    def restore_context(self, context: SandboxContext, original_context: SandboxContext) -> None:
        """
        Restore the context after Dana function execution.

        Args:
            context: The current context
            original_context: The original context before execution
        """
        # Restore the original local scope
        if hasattr(context, "_original_locals"):
            context.set_scope("local", context._original_locals)
            delattr(context, "_original_locals")

    def execute(self, context: SandboxContext, *args, **kwargs) -> Any:
        """Execute the function.

        Args:
            context: The execution context
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            The result of executing the function
        """
        # Create new execution context for the function
        func_context = self._create_function_context(context, args, kwargs)
        
        # Push function call onto stack
        location_info = {}
        if hasattr(self.body, 'location') and self.body.location:
            location_info = {
                'file': self.body.location.source,
                'line': self.body.location.line,
                'column': self.body.location.column
            }
        func_context.push_function_call(self.name, location_info)
        
        try:
            # Execute function body
            last_value = None
            for statement in self.body.statements:
                try:
                    result = self.interpreter._executor.execute_statement(statement, func_context)
                    if result is not None:
                        last_value = result
                        func_context.set("system:__last_value", result)
                except ReturnException as e:
                    # Normal return from function
                    return e.value
                except Exception as e:
                    # Enhanced error handling with context
                    error_msg = f"Error executing statement: {e}"
                    if hasattr(statement, 'location') and statement.location:
                        error_msg = f"Error at line {statement.location.line}, column {statement.location.column}: {e}"
                    
                    self.logger.error(error_msg)
                    
                    # Re-raise with function context
                    if self.name:
                        raise SandboxError(f"In function '{self.name}': {error_msg}") from e
                    else:
                        raise
    
            # Return last value if no explicit return
            return last_value
            
        except ReturnException as e:
            # Handle return statement
            return e.value
            
        except Exception as e:
            # Enhanced error handling with full context
            error_msg = str(e)
            if not error_msg.startswith("In function"):
                error_msg = f"Function '{self.name}' execution failed: {error_msg}"
                
            self.logger.error(f"Error executing Dana function: {error_msg}")
            raise SandboxError(error_msg) from e
            
        finally:
            # Always pop the function call from stack
            func_context.pop_function_call()
    
    def _create_function_context(self, parent_context: SandboxContext, args: tuple, kwargs: dict) -> SandboxContext:
        """Create a new context for function execution.
        
        Args:
            parent_context: The parent execution context
            args: Positional arguments
            kwargs: Keyword arguments
            
        Returns:
            New context with function parameters bound
        """
        # Create new context for function execution
        func_context = SandboxContext(parent=parent_context)
        
        # Keep reference to interpreter
        if hasattr(parent_context, '_interpreter'):
            func_context._interpreter = parent_context._interpreter
        
        # Bind parameters to arguments
        param_names = []
        for p in self.parameters:
            if isinstance(p, str):
                param_names.append(p)
            elif hasattr(p, 'name'):
                param_names.append(p.name)
            else:
                param_names.append(str(p))
        
        # Bind positional arguments
        for i, arg in enumerate(args):
            if i < len(param_names):
                func_context.set(f"local:{param_names[i]}", arg)
        
        # Bind keyword arguments
        for name, value in kwargs.items():
            func_context.set(f"local:{name}", value)
        
        # Handle default values for missing parameters
        for i, param in enumerate(self.parameters):
            if isinstance(param, str):
                param_name = param
                param_default = None
            elif hasattr(param, 'name'):
                param_name = param.name
                param_default = getattr(param, 'default', None)
            else:
                param_name = str(param)
                param_default = None
                
            param_key = f"local:{param_name}"
            if not func_context.has(param_key) and param_default is not None:
                # Evaluate default value in parent context
                default_val = parent_context._interpreter._executor.execute(param_default, parent_context)
                func_context.set(param_key, default_val)
        
        return func_context

    def __str__(self) -> str:
        return f"DanaFunction({self.name})"
