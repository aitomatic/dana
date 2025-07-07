"""
Core executor methods for Dana interpreter.

This module provides core execution methods for specific statement types.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dana.core.lang.ast import ExportStatement


class CoreExecutorMixin:
    """Mixin providing core execution methods."""

    def visit_ExportStatement(self, node: "ExportStatement") -> None:
        """Execute an export statement.

        Args:
            node: Export statement AST node
        """
        # Add name to module's exports
        if not hasattr(self.module, "__exports__"):
            self.module.__exports__ = set()
        self.module.__exports__.add(node.name)
