"""
Notifiable protocol for objects that can send notifications.

This module provides the Notifiable protocol and Notifier type for objects
that need to send notifications to external systems or handlers.
"""

from abc import ABC, abstractmethod

import structlog

from .types import DictParams


logger = structlog.get_logger()


class Notifiable(ABC):
    """
    Base class for notifiable objects that can receive notifications.
    """

    @abstractmethod
    def notify(self, notifier: object, message: DictParams) -> None: ...


class Notifier(ABC):
    def __init__(self, **kwargs):
        """
        Initialize the notifier object.

        Args:
            **kwargs: Additional arguments (passed to super for MRO chain)
        """
        # Only pass kwargs if there are other classes in the MRO that can handle them
        try:
            super().__init__(**kwargs)
        except TypeError:
            # If we're at the end of the MRO chain (object.__init__), just call without kwargs
            super().__init__()
        self._notifiables: list[Notifiable] = []
        # Store kwargs for potential future use
        self._kwargs = kwargs

    def with_notifiable(self, *notifiables: Notifiable) -> "Notifier":
        """
        Add notifiables to my list of notifiables.

        Args:
            *notifiables: Variable number of notifiable objects

        Returns:
            Self for method chaining
        """
        self._notifiables.extend(notifiables)
        return self

    def add_notifier(self, notifiable: Notifiable) -> None:
        """
        Add a notification callback.

        Args:
            notifiable: The notifiable object
        """
        if notifiable is not None:
            self._notifiables.append(notifiable)

    def remove_notifiable(self, notifiable: Notifiable) -> bool:
        """
        Remove a specific notification callback.

        Args:
            notifiable: The notifiable object to remove

        Returns:
            True if the notifier was found and removed, False otherwise
        """
        try:
            self._notifiables.remove(notifiable)
            return True
        except ValueError:
            return False

    def broadcast(self, message: DictParams) -> None:
        """
        Send a notification message to all registered notifiers.

        Args:
            message: The notification message to send
        """
        print(f"Broadcasting message to {len(self._notifiables)} notifiables")
        for notifiable in self._notifiables:
            if notifiable is not None:
                try:
                    notifiable.notify(self, message)
                except Exception as e:
                    logger.error(f"Error sending notification to {notifiable}: {e}")
                    # Continue with other notifiers even if one fails
                    pass
