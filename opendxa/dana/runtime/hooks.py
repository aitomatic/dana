"""Extension hooks for the DANA interpreter.

This module provides hooks for extending the DANA interpreter with custom behavior
without modifying the core interpreter code.
"""

from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union

from opendxa.dana.language.ast import Assignment, Conditional, LogStatement, Program


class HookType(Enum):
    """Types of extension hooks that can be registered."""

    # Program-level hooks
    BEFORE_PROGRAM = "before_program"  # Called before executing a program
    AFTER_PROGRAM = "after_program"    # Called after executing a program
    
    # Statement-level hooks
    BEFORE_STATEMENT = "before_statement"  # Called before executing any statement
    AFTER_STATEMENT = "after_statement"    # Called after executing any statement
    
    # Statement-type-specific hooks
    BEFORE_ASSIGNMENT = "before_assignment"  # Called before executing an assignment
    AFTER_ASSIGNMENT = "after_assignment"    # Called after executing an assignment
    BEFORE_CONDITIONAL = "before_conditional"  # Called before executing a conditional
    AFTER_CONDITIONAL = "after_conditional"    # Called after executing a conditional
    BEFORE_LOG = "before_log"  # Called before executing a log statement
    AFTER_LOG = "after_log"    # Called after executing a log statement
    
    # Expression-level hooks
    BEFORE_EXPRESSION = "before_expression"  # Called before evaluating an expression
    AFTER_EXPRESSION = "after_expression"    # Called after evaluating an expression
    
    # Error hooks
    ON_ERROR = "on_error"  # Called when an error occurs


# Type aliases for hook callbacks
HookCallback = Callable[[Dict[str, Any]], None]


class HookRegistry:
    """Registry for interpreter extension hooks.
    
    This class manages hooks that allow extending the interpreter with custom
    behavior at key points in the execution process.
    """
    
    def __init__(self):
        """Initialize an empty hook registry."""
        self._hooks: Dict[HookType, Set[HookCallback]] = {
            hook_type: set() for hook_type in HookType
        }
    
    def register(self, hook_type: HookType, callback: HookCallback) -> None:
        """Register a hook callback for the given hook type.
        
        Args:
            hook_type: The type of hook to register for
            callback: The callback function to call when the hook is triggered
        """
        self._hooks[hook_type].add(callback)
    
    def unregister(self, hook_type: HookType, callback: HookCallback) -> None:
        """Unregister a hook callback for the given hook type.
        
        Args:
            hook_type: The type of hook to unregister from
            callback: The callback function to unregister
            
        Raises:
            KeyError: If the callback is not registered for the hook type
        """
        try:
            self._hooks[hook_type].remove(callback)
        except KeyError:
            raise KeyError(f"Callback {callback} not registered for hook type {hook_type}")
    
    def execute(self, hook_type: HookType, context: Dict[str, Any]) -> None:
        """Execute all callbacks registered for the given hook type.
        
        Args:
            hook_type: The type of hook to execute
            context: Context data to pass to the callbacks
        """
        for callback in self._hooks[hook_type]:
            try:
                callback(context)
            except Exception as e:
                # Log the error but don't let it disrupt execution
                print(f"Error in hook callback: {e}")
    
    def has_hooks(self, hook_type: HookType) -> bool:
        """Check if any hooks are registered for the given hook type.
        
        Args:
            hook_type: The type of hook to check
            
        Returns:
            True if any hooks are registered for the hook type, False otherwise
        """
        return bool(self._hooks[hook_type])
    
    def clear(self) -> None:
        """Clear all registered hooks."""
        for hook_type in self._hooks:
            self._hooks[hook_type].clear()


# Singleton instance for the hook registry
_registry = HookRegistry()


def get_registry() -> HookRegistry:
    """Get the global hook registry instance.
    
    Returns:
        The global HookRegistry instance
    """
    return _registry


# Convenience functions for working with the global registry

def register_hook(hook_type: HookType, callback: HookCallback) -> None:
    """Register a hook callback with the global registry.
    
    Args:
        hook_type: The type of hook to register for
        callback: The callback function to call when the hook is triggered
    """
    _registry.register(hook_type, callback)


def unregister_hook(hook_type: HookType, callback: HookCallback) -> None:
    """Unregister a hook callback from the global registry.
    
    Args:
        hook_type: The type of hook to unregister from
        callback: The callback function to unregister
    """
    _registry.unregister(hook_type, callback)


def execute_hook(hook_type: HookType, context: Dict[str, Any]) -> None:
    """Execute all callbacks registered for the given hook type in the global registry.
    
    Args:
        hook_type: The type of hook to execute
        context: Context data to pass to the callbacks
    """
    _registry.execute(hook_type, context)


def has_hooks(hook_type: HookType) -> bool:
    """Check if any hooks are registered for the given hook type in the global registry.
    
    Args:
        hook_type: The type of hook to check
        
    Returns:
        True if any hooks are registered for the hook type, False otherwise
    """
    return _registry.has_hooks(hook_type)


def clear_hooks() -> None:
    """Clear all registered hooks in the global registry."""
    _registry.clear()