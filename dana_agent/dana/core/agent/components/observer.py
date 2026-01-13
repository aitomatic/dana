"""
Observer Protocol for observing environment data.

This module provides the ObserverProtocol interface that allows extensible
connections to sensors and environment monitoring systems. Events in the
EventLog come ONLY from Observer.observe().
"""

from abc import ABC, abstractmethod
from typing import Any


class ObserverProtocol(ABC):
    """
    Protocol for observing environment data.

    Events in the EventLog come ONLY from Observer.observe().
    This is the extension point for domain-specific sensors (HVAC, IoT, etc.).
    """

    @abstractmethod
    def observe(self) -> dict[str, Any]:
        """
        Observe the environment and return data.

        Returns:
            Dictionary with observed data (e.g., {"temp": 72.5, "zone": "floor_2"})
            Returns empty dict {} if no data available.
        """
        pass

    @abstractmethod
    def start(self) -> None:
        """Start observing (if needed for continuous monitoring)."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop observing."""
        pass


class NullObserver(ObserverProtocol):
    """
    Default observer that does nothing.

    Used when no observer is provided - returns empty observations.
    """

    def observe(self) -> dict[str, Any]:
        """Return empty dict - no observations."""
        return {}

    def start(self) -> None:
        """No-op."""
        pass

    def stop(self) -> None:
        """No-op."""
        pass
