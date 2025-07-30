"""Recursion Safety and Circular Reference Detection"""

from contextlib import contextmanager
from typing import Any

from dana.common.exceptions import SandboxError
from dana.common.mixins.loggable import Loggable


class RecursionDepthMonitor(Loggable):
    """Monitor and protect against excessive recursion depth."""

    def __init__(self, max_depth: int = 500, warning_threshold: int = 400):
        super().__init__()
        self._current_depth = 0
        self._max_depth = max_depth
        self._warning_threshold = warning_threshold
        self._call_stack: list[str] = []
        self._max_depth_reached = 0

    @contextmanager
    def track_execution(self, node_description: str):
        """Context manager to track execution depth."""
        self._current_depth += 1
        self._call_stack.append(node_description)

        # Update maximum depth reached
        if self._current_depth > self._max_depth_reached:
            self._max_depth_reached = self._current_depth

        try:
            self.check_depth_safety()
            yield
        finally:
            self._current_depth -= 1
            self._call_stack.pop()

    def check_depth_safety(self) -> None:
        """Check if current depth is safe, warn or raise if not."""
        if self._current_depth >= self._max_depth:
            stack_trace = " -> ".join(self._call_stack[-10:])  # Last 10 calls
            raise SandboxError(
                f"Maximum recursion depth ({self._max_depth}) exceeded. "
                f"Current depth: {self._current_depth}. "
                f"Recent call stack: {stack_trace}"
            )

        if self._current_depth >= self._warning_threshold:
            self.warning(f"High recursion depth: {self._current_depth}/{self._max_depth}. Consider optimizing nested expressions.")

    def get_statistics(self) -> dict[str, Any]:
        """Get recursion depth statistics."""
        return {
            "current_depth": self._current_depth,
            "max_depth_reached": self._max_depth_reached,
            "max_depth_limit": self._max_depth,
            "warning_threshold": self._warning_threshold,
            "stack_depth_ratio": self._current_depth / self._max_depth,
            "call_stack_size": len(self._call_stack),
        }

    def reset_statistics(self) -> None:
        """Reset depth tracking statistics."""
        self._max_depth_reached = self._current_depth


class CircularReferenceDetector:
    """Detect circular references in AST traversal."""

    def __init__(self):
        self._visiting: set[int] = set()
        self._visit_path: list[tuple[int, str]] = []

    @contextmanager
    def visit_node(self, node: Any):
        """Track node visitation for cycle detection."""
        node_id = id(node)
        node_desc = f"{type(node).__name__}({node_id})"

        if node_id in self._visiting:
            # Found a cycle - build error message with path
            cycle_start_idx = next(i for i, (path_id, _) in enumerate(self._visit_path) if path_id == node_id)
            cycle_path = " -> ".join(desc for _, desc in self._visit_path[cycle_start_idx:])
            raise SandboxError(f"Circular reference detected in AST traversal. Cycle path: {cycle_path} -> {node_desc}")

        self._visiting.add(node_id)
        self._visit_path.append((node_id, node_desc))

        try:
            yield
        finally:
            self._visiting.remove(node_id)
            self._visit_path.pop()

    def get_current_path(self) -> list[str]:
        """Get current visitation path for debugging."""
        return [desc for _, desc in self._visit_path]

    def clear(self) -> None:
        """Clear all tracking state."""
        self._visiting.clear()
        self._visit_path.clear()
