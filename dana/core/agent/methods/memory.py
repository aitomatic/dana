from typing import Any

from dana.core.lang.sandbox_context import SandboxContext


class MemoryMixin:
    def remember_sync(self, key: str, value: Any, sandbox_context: SandboxContext | None = None) -> Any:
        """Synchronous agent memory storage method."""
        return self._remember_impl(sandbox_context or SandboxContext(), key, value)

    def recall_sync(self, key: str, sandbox_context: SandboxContext | None = None) -> Any:
        """Synchronous agent memory retrieval method."""
        return self._recall_impl(sandbox_context or SandboxContext(), key)

    def _remember_impl(self, sandbox_context: SandboxContext, key: str, value: Any) -> str:
        """Implementation of memory storage functionality."""
        self.debug(f"REMEMBER: Storing key '{key}' with value: {value}")

        # Store in agent's memory
        self._memory[key] = value

        # Note: ConversationMemory doesn't have add_memory method
        # Memory is stored in agent's internal _memory dict
        # Conversation memory is used for conversation turns, not key-value storage

        return f"Stored '{key}' in memory"

    def _recall_impl(self, sandbox_context: SandboxContext, key: str) -> Any:
        """Implementation of memory retrieval functionality."""
        self.debug(f"RECALL: Retrieving key '{key}'")

        # Try agent's memory first
        if key in self._memory:
            self.debug(f"Found in agent memory: {self._memory[key]}")
            return self._memory[key]

        # Note: ConversationMemory doesn't have get_memory method
        # Memory is stored in agent's internal _memory dict
        # Conversation memory is used for conversation turns, not key-value storage

        self.debug(f"Key '{key}' not found in memory")
        return None
