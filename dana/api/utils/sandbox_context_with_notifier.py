"""
Dana Sandbox Context with Notifier

This module provides a SandboxContext with notification functionality for variable changes.
Located in the API folder for agent testing purposes.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any, Optional, TYPE_CHECKING, Union
from collections.abc import Callable, Awaitable
import asyncio
from dana.core.lang.sandbox_context import SandboxContext

if TYPE_CHECKING:
    from dana.core.lang.context_manager import ContextManager


class SandboxContextWithNotifier(SandboxContext):
    """
    SandboxContext with notification functionality for variable changes.

    This class extends SandboxContext to notify when variables are changed,
    providing real-time updates to users about what's happening during Dana execution.
    """

    def __init__(
        self,
        parent: Optional["SandboxContext"] = None,
        manager: Optional["ContextManager"] = None,
        notifier: Union[Callable[[str, str, Any, Any], None], Callable[[str, str, Any, Any], Awaitable[None]]] | None = None,
    ):
        """
        Initialize the sandbox context with notifier.

        Args:
            parent: Optional parent context to inherit shared scopes from
            manager: Optional context manager
            notifier: Optional callback function for variable changes.
                     Can be sync or async function.
                     Signature: notifier(scope: str, var_name: str, old_value: Any, new_value: Any)
        """
        super().__init__(parent, manager)
        self._notifier = notifier

    def set_notifier(self, notifier: Union[Callable[[str, str, Any, Any], None], Callable[[str, str, Any, Any], Awaitable[None]]]) -> None:
        """
        Set the notifier callback function.

        Args:
            notifier: Callback function for variable changes (sync or async).
                     Signature: notifier(scope: str, var_name: str, old_value: Any, new_value: Any)
        """
        self._notifier = notifier

    def _notify_change(self, scope: str, var_name: str, old_value: Any, new_value: Any) -> None:
        """
        Notify about a variable change if notifier is set.

        Args:
            scope: The scope where the change occurred
            var_name: The variable name that changed
            old_value: The previous value
            new_value: The new value
        """
        if self._notifier:
            try:
                result = self._notifier(scope, var_name, old_value, new_value)
                # If notifier returns a coroutine, schedule it to run
                if asyncio.iscoroutine(result):
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # If we're in an async context, create a task
                            asyncio.create_task(result)
                        else:
                            # If not in async context, run until complete
                            loop.run_until_complete(result)
                    except RuntimeError:
                        # No event loop running, try to create one
                        try:
                            asyncio.run(result)
                        except Exception as e:
                            print(f"Warning: Async notifier failed: {e}")
            except Exception as e:
                # Don't let notification errors break execution
                print(f"Warning: Notifier failed: {e}")

    def set(self, key: str, value: Any) -> None:
        """
        Sets a value in the context and notifies about the change.

        Args:
            key: The key in format 'scope.variable', 'scope:variable', or just 'variable'
            value: The value to set
        """
        scope, var_name = self._validate_key(key)

        # Get old value for notification
        old_value = self.get(key, None)

        # Call parent implementation to set the value
        super().set(key, value)

        # Notify about the change
        self._notify_change(scope, var_name, old_value, value)

    def set_in_scope(self, var_name: str, value: Any, scope: str = "local") -> None:
        """
        Sets a value in a specific scope and notifies about the change.

        Args:
            var_name: The variable name
            value: The value to set
            scope: The scope to set in (defaults to local)
        """
        # Get old value for notification
        old_value = self.get_from_scope(var_name, scope)

        # Call parent implementation to set the value
        super().set_in_scope(var_name, value, scope)

        # Notify about the change
        self._notify_change(scope, var_name, old_value, value)

    def delete(self, key: str) -> None:
        """
        Delete a key from the context and notify about the change.

        Args:
            key: The key to delete
        """
        scope, var_name = self._validate_key(key)

        # Get old value for notification (before deletion)
        old_value = self.get(key, None)

        # Call parent implementation to delete the value
        super().delete(key)

        # Notify about the deletion
        self._notify_change(scope, var_name, old_value, None)

    def delete_from_scope(self, var_name: str, scope: str = "local") -> None:
        """
        Delete a variable from a specific scope and notify about the change.

        Args:
            var_name: The variable name to delete
            scope: The scope to delete from (defaults to local)
        """
        # Get old value for notification (before deletion)
        old_value = self.get_from_scope(var_name, scope)

        # Call parent implementation to delete the value
        super().delete_from_scope(var_name, scope)

        # Notify about the deletion
        self._notify_change(scope, var_name, old_value, None)

    def clear(self, scope: str | None = None) -> None:
        """
        Clear all variables in a scope or all scopes and notify about changes.

        Args:
            scope: Optional scope to clear (if None, clears all scopes)
        """
        from dana.common.runtime_scopes import RuntimeScopes

        # Get current state before clearing for notifications
        current_state = self.get_state()

        # Call parent implementation to clear
        super().clear(scope)

        # Notify about all cleared variables
        if scope is not None:
            # Clear specific scope
            if scope in current_state:
                for var_name, old_value in current_state[scope].items():
                    self._notify_change(scope, var_name, old_value, None)
        else:
            # Clear all scopes
            for scope_name in RuntimeScopes.ALL:
                if scope_name in current_state:
                    for var_name, old_value in current_state[scope_name].items():
                        self._notify_change(scope_name, var_name, old_value, None)

    def set_state(self, state: dict[str, dict[str, Any]]) -> None:
        """
        Set the state from a dictionary and notify about all changes.

        Args:
            state: The state dictionary to set
        """
        # Get current state before setting for notifications
        old_state = self.get_state()

        # Call parent implementation to set state
        super().set_state(state)

        # Notify about all changes
        from dana.common.runtime_scopes import RuntimeScopes

        all_scopes = set(old_state.keys()) | set(state.keys())

        for scope_name in all_scopes:
            if scope_name not in RuntimeScopes.ALL:
                continue

            old_scope = old_state.get(scope_name, {})
            new_scope = state.get(scope_name, {})

            # Find all variables that changed
            all_vars = set(old_scope.keys()) | set(new_scope.keys())

            for var_name in all_vars:
                old_value = old_scope.get(var_name)
                new_value = new_scope.get(var_name)

                # Only notify if value actually changed
                if old_value != new_value:
                    self._notify_change(scope_name, var_name, old_value, new_value)

    def copy(self) -> "SandboxContextWithNotifier":
        """
        Create a copy of this context with notifier.

        Returns:
            A new SandboxContextWithNotifier with the same state and notifier
        """
        new_context = SandboxContextWithNotifier(parent=self._parent, manager=self._manager, notifier=self._notifier)
        new_context.set_state(self.get_state())
        new_context.set_notifier(self._notifier)

        self._copy_attributes(new_context, skip_state=False, skip_resources=False)

        # Also copy resource and agent registrations (same as parent)
        import copy

        new_context._SandboxContext__resources = copy.copy(self._SandboxContext__resources)
        new_context._SandboxContext__agents = copy.copy(self._SandboxContext__agents)

        # Copy the nested dictionaries for each scope
        for scope in new_context._SandboxContext__resources:
            new_context._SandboxContext__resources[scope] = copy.copy(self._SandboxContext__resources[scope])
        for scope in new_context._SandboxContext__agents:
            new_context._SandboxContext__agents[scope] = copy.copy(self._SandboxContext__agents[scope])

        return new_context

    def merge(self, other: "SandboxContext") -> None:
        """
        Merge another context into this one and notify about changes.

        Args:
            other: The context to merge from
        """
        from dana.common.runtime_scopes import RuntimeScopes

        # Get current state before merging for notifications
        old_state = self.get_state()

        # Call parent implementation to merge
        super().merge(other)

        # Get new state after merging
        new_state = self.get_state()

        # Notify about all changes
        for scope in RuntimeScopes.ALL:
            if scope in old_state or scope in new_state:
                old_scope = old_state.get(scope, {})
                new_scope = new_state.get(scope, {})

                # Find all variables that changed
                all_vars = set(old_scope.keys()) | set(new_scope.keys())

                for var_name in all_vars:
                    old_value = old_scope.get(var_name)
                    new_value = new_scope.get(var_name)

                    # Only notify if value actually changed
                    if old_value != new_value:
                        self._notify_change(scope, var_name, old_value, new_value)

    def set_scope(self, scope: str, context: dict[str, Any] | None = None) -> None:
        """
        Set a value in a specific scope and notify about changes.

        Args:
            scope: The scope to set in
            context: The context to set
        """
        from dana.common.runtime_scopes import RuntimeScopes

        if scope not in RuntimeScopes.ALL:
            # Let parent handle the error
            super().set_scope(scope, context)
            return

        # Get old values for notification
        old_scope = self._state.get(scope, {}).copy()
        new_scope = context or {}

        # Call parent implementation
        super().set_scope(scope, context)

        # Notify about all changes
        all_vars = set(old_scope.keys()) | set(new_scope.keys())

        for var_name in all_vars:
            old_value = old_scope.get(var_name)
            new_value = new_scope.get(var_name)

            # Only notify if value actually changed
            if old_value != new_value:
                self._notify_change(scope, var_name, old_value, new_value)

    def create_child_context(self) -> "SandboxContextWithNotifier":
        """
        Create a child context that inherits from this context with notifier.

        A child context:
        - Has its own fresh local scope
        - Shares global scopes (private, public, system) with the parent
        - Inherits the parent's interpreter and other properties
        - Inherits the notifier from the parent
        - Is useful for function execution where you need isolated local variables
          but want to maintain access to global state

        Returns:
            A new SandboxContextWithNotifier that is a child of this context
        """
        # Create child with this context as parent, and pass the notifier
        child_context = SandboxContextWithNotifier(parent=self, manager=self._manager, notifier=self._notifier)

        # Copy attributes but skip state and resources (inherited via parent chain)
        self._copy_attributes(child_context, skip_state=True, skip_resources=True)

        return child_context

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        base_context: Optional["SandboxContext"] = None,
        notifier: Union[Callable[[str, str, Any, Any], None], Callable[[str, str, Any, Any], Awaitable[None]]] | None = None,
    ) -> "SandboxContextWithNotifier":
        """
        Create a new SandboxContextWithNotifier from a dictionary and base context.

        Args:
            data: Dictionary containing context data
            base_context: Optional existing SandboxContext
            notifier: Optional notifier callback function

        Returns:
            A new SandboxContextWithNotifier instance with the merged data
        """
        # Create new context with notifier
        context = cls(parent=base_context, notifier=notifier)

        # Set values from data (this will trigger notifications)
        from dana.common.runtime_scopes import RuntimeScopes

        for key, value in data.items():
            if ":" in key:
                # Check if it's a scoped variable (scope:variable) - preferred format
                scope, _ = key.split(":", 1)
                if scope in RuntimeScopes.ALL:
                    context.set(key, value)  # This will handle global scope sharing and notify
                else:
                    # If not a valid scope, treat as local variable
                    context.set(key, value)
            elif "." in key:
                # Check if it's a scoped variable (scope.variable) - backward compatibility
                scope, _ = key.split(".", 1)
                if scope in RuntimeScopes.ALL:
                    context.set(key, value)  # This will handle global scope sharing and notify
                else:
                    # If not a valid scope, treat as local variable
                    context.set(key, value)
            else:
                # Unscoped variable goes to local scope
                context.set(key, value)

        return context
