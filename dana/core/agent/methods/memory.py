from typing import Any

from dana.core.lang.sandbox_context import SandboxContext


class MemoryMixin:
    def remember_sync(self, key: str, value: Any, sandbox_context: SandboxContext | None = None) -> str:
        """Synchronous agent memory storage method."""
        self.debug(f"REMEMBER: Storing key '{key}' with value: {value}")

        # Store in centralized working memory
        try:
            self.state.mind.memory.working.store(key, value)
            return f"Stored '{key}' in working memory"
        except Exception as e:
            self.debug(f"Failed to store in centralized memory: {e}")
            # Fallback to direct working memory access
            try:
                self._memory.store(key, value)
                return f"Stored '{key}' in working memory (fallback mode)"
            except Exception as e2:
                self.debug(f"Fallback memory storage also failed: {e2}")
                return f"Failed to store '{key}' in memory"

    def recall_sync(self, key: str, sandbox_context: SandboxContext | None = None) -> Any:
        """Synchronous agent memory retrieval method."""
        self.debug(f"RECALL: Retrieving key '{key}'")

        # Try centralized working memory first
        try:
            value = self.state.mind.memory.working.recall(key)
            if value is not None:
                self.debug(f"Found in centralized working memory: {value}")
                return value
        except Exception as e:
            self.debug(f"Failed to access centralized memory: {e}")

        # Fallback to direct working memory access
        try:
            value = self._memory.recall(key)
            if value is not None:
                self.debug(f"Found in working memory (fallback): {value}")
                return value
        except Exception as e:
            self.debug(f"Fallback memory access also failed: {e}")

        self.debug(f"Key '{key}' not found in memory")
        return None
