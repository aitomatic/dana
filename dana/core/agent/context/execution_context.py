"""
Execution context for runtime state and resource management.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ResourceLimits:
    """Resource limits for execution."""

    max_execution_time: float | None = None  # seconds
    max_memory_mb: float = 1000.0
    max_cpu_percent: float = 90.0
    max_recursion_depth: int = 10


@dataclass
class RuntimeMetrics:
    """Runtime performance metrics."""

    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    execution_time: float = 0.0
    api_calls: int = 0
    token_count: int = 0


@dataclass
class Constraint:
    """Execution constraint."""

    name: str
    type: str  # "resource", "security", "business", etc.
    value: Any
    enforced: bool = True


@dataclass
class ExecutionContext:
    """Runtime execution state and resource management."""

    # Execution identification
    workflow_id: str | None = None
    session_id: str | None = None

    # Execution state
    recursion_depth: int = 0
    is_running: bool = False

    # Resource management
    resource_limits: ResourceLimits = field(default_factory=ResourceLimits)
    current_metrics: RuntimeMetrics = field(default_factory=RuntimeMetrics)

    # Constraints
    constraints: list[Constraint] = field(default_factory=list)

    def can_proceed(self) -> bool:
        """Check if execution can continue based on resources and constraints.

        Returns:
            True if execution can continue, False otherwise
        """
        # Check recursion depth
        if self.recursion_depth >= self.resource_limits.max_recursion_depth:
            return False

        # Check memory usage
        if self.current_metrics.memory_usage_mb > self.resource_limits.max_memory_mb:
            return False

        # Check CPU usage
        if self.current_metrics.cpu_usage_percent > self.resource_limits.max_cpu_percent:
            return False

        # Check execution time
        if (
            self.resource_limits.max_execution_time is not None
            and self.current_metrics.execution_time > self.resource_limits.max_execution_time
        ):
            return False

        # Check enforced constraints
        for constraint in self.constraints:
            if constraint.enforced and constraint.type == "security":
                # Could add specific security checks here
                pass

        return True

    def get_constraints(self) -> dict[str, Any]:
        """Get current execution constraints as a dictionary.

        Returns:
            Dictionary of constraint names to values
        """
        return {constraint.name: constraint.value for constraint in self.constraints if constraint.enforced}

    def add_constraint(self, name: str, value: Any, type: str = "business") -> None:
        """Add a new execution constraint.

        Args:
            name: Constraint name
            value: Constraint value
            type: Constraint type
        """
        self.constraints.append(Constraint(name=name, type=type, value=value))

    def update_metrics(self, **kwargs) -> None:
        """Update runtime metrics.

        Args:
            **kwargs: Metric names and values to update
        """
        for key, value in kwargs.items():
            if hasattr(self.current_metrics, key):
                setattr(self.current_metrics, key, value)

    def enter_recursion(self) -> bool:
        """Enter a new recursion level.

        Returns:
            True if recursion is allowed, False if depth limit reached
        """
        if self.recursion_depth >= self.resource_limits.max_recursion_depth:
            return False
        self.recursion_depth += 1
        return True

    def exit_recursion(self) -> None:
        """Exit current recursion level."""
        if self.recursion_depth > 0:
            self.recursion_depth -= 1

    def get_status(self) -> dict[str, Any]:
        """Get execution status summary.

        Returns:
            Dictionary with execution status information
        """
        return {
            "workflow_id": self.workflow_id,
            "session_id": self.session_id,
            "is_running": self.is_running,
            "recursion_depth": self.recursion_depth,
            "can_proceed": self.can_proceed(),
            "memory_usage_mb": self.current_metrics.memory_usage_mb,
            "cpu_usage_percent": self.current_metrics.cpu_usage_percent,
            "execution_time": self.current_metrics.execution_time,
            "constraints_count": len(self.constraints),
        }
