"""Mixin for registry observability."""

from abc import ABC
from collections.abc import Callable
from typing import Generic, TypeVar

ItemT = TypeVar("ItemT")


class RegistryObservable(Generic[ItemT], ABC):
    """Mixin for objects that can be observed for registry events.

    This mixin provides observability capabilities for registries,
    allowing them to emit registration and unregistration events.
    """

    def __init__(self):
        """Initialize the registry observable."""
        self._event_handlers: dict[str, list[Callable]] = {}
        self._registration_handlers: list[Callable] = []
        self._unregistration_handlers: list[Callable] = []

    def on_event(self, event_type: str, handler: Callable[[str, ItemT], None]) -> None:
        """Register a handler for a specific event type.

        Args:
            event_type: The type of event to handle (e.g., "registered", "unregistered", "updated")
            handler: Callback function with signature (item_id: str, item: ItemT) -> None
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)

    def on_registered(self, handler: Callable[[str, ItemT], None]) -> None:
        """Register a handler for registration events.

        Args:
            handler: Callback function with signature (item_id: str, item: ItemT) -> None
        """
        self._registration_handlers.append(handler)

    def on_unregistered(self, handler: Callable[[str, ItemT], None]) -> None:
        """Register a handler for unregistration events.

        Args:
            handler: Callback function with signature (item_id: str, item: ItemT) -> None
        """
        self._unregistration_handlers.append(handler)

    def _trigger_event(self, event_type: str, item_id: str, item: ItemT) -> None:
        """Trigger an event and call all registered handlers.

        Args:
            event_type: The type of event being triggered
            item_id: The ID of the item involved in the event
            item: The item involved in the event
        """
        # Call general event handlers
        if event_type in self._event_handlers:
            for handler in self._event_handlers[event_type]:
                try:
                    handler(item_id, item)
                except Exception as e:
                    # Log error but don't fail the event
                    self._log_event_error(event_type, handler, e)

        # Call specific event handlers
        if event_type == "registered" and self._registration_handlers:
            for handler in self._registration_handlers:
                try:
                    handler(item_id, item)
                except Exception as e:
                    self._log_event_error("registered", handler, e)
        elif event_type == "unregistered" and self._unregistration_handlers:
            for handler in self._unregistration_handlers:
                try:
                    handler(item_id, item)
                except Exception as e:
                    self._log_event_error("unregistered", handler, e)

    def _log_event_error(self, event_type: str, handler: Callable, error: Exception) -> None:
        """Log an error that occurred during event handling.

        Args:
            event_type: The type of event that failed
            handler: The handler that failed
            error: The exception that occurred
        """
        # Default implementation - can be overridden by subclasses
        print(f"Error in {event_type} event handler {handler}: {error}")

    def clear_event_handlers(self, event_type: str | None = None) -> None:
        """Clear event handlers.

        Args:
            event_type: If specified, clear only handlers for this event type.
                       If None, clear all event handlers.
        """
        if event_type is None:
            self._event_handlers.clear()
            self._registration_handlers.clear()
            self._unregistration_handlers.clear()
        elif event_type == "registered":
            # Clear both specific registration handlers and general event handlers for "registered"
            self._registration_handlers.clear()
            if "registered" in self._event_handlers:
                self._event_handlers["registered"].clear()
        elif event_type == "unregistered":
            # Clear both specific unregistration handlers and general event handlers for "unregistered"
            self._unregistration_handlers.clear()
            if "unregistered" in self._event_handlers:
                self._event_handlers["unregistered"].clear()
        elif event_type in self._event_handlers:
            self._event_handlers[event_type].clear()

    def get_event_handler_count(self, event_type: str | None = None) -> int:
        """Get the number of registered event handlers.

        Args:
            event_type: If specified, count only handlers for this event type.
                       If None, count all event handlers.

        Returns:
            Number of registered handlers
        """
        if event_type is None:
            total = len(self._registration_handlers) + len(self._unregistration_handlers)
            for handlers in self._event_handlers.values():
                total += len(handlers)
            return total
        elif event_type == "registered":
            # Count both specific registration handlers and general event handlers for "registered"
            count = len(self._registration_handlers)
            if "registered" in self._event_handlers:
                count += len(self._event_handlers["registered"])
            return count
        elif event_type == "unregistered":
            # Count both specific unregistration handlers and general event handlers for "unregistered"
            count = len(self._unregistration_handlers)
            if "unregistered" in self._event_handlers:
                count += len(self._event_handlers["unregistered"])
            return count
        elif event_type in self._event_handlers:
            return len(self._event_handlers[event_type])
        return 0
