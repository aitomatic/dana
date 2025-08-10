"""
Base LLM Resource

A bridge to the underlying system LLM resource.
This provides a standard interface while delegating all operations to the actual LLM implementation.
"""

from dataclasses import dataclass, field
from typing import Any

from dana.common.mixins.registerable import Registerable
from dana.common.types import BaseResponse
from dana.common.utils.misc import Misc

from ..base_resource import BaseResource, ResourceState
from ..system_bridge import LLMResourceBridge


@dataclass
class BaseLLMResource(BaseResource, Registerable):
    """
    Bridge to the system LLM resource.

    This is a lightweight wrapper that delegates all operations to the underlying
    system LLM resource without duplicating logic or state.
    """

    kind: str = "llm"
    provider: str = "mock"  # Will be auto-detected
    model: str = "default"  # Will be passed through to system resource
    api_key: str = ""
    endpoint: str = ""
    temperature: float = 0.7
    max_tokens: int = 1000
    timeout: int = 60
    id: str = field(default_factory=lambda: Misc.generate_uuid(8))

    # Bridge to system resource
    _bridge: LLMResourceBridge | None = field(default=None, init=False)

    def initialize(self) -> bool:
        """Initialize the bridge to the system LLM resource."""
        print(f"Initializing LLM bridge '{self.name}' with model '{self.model}'")

        try:
            # Create bridge to system resource
            self._bridge = LLMResourceBridge(
                name=f"{self.name}_bridge", model=self.model, temperature=self.temperature, max_tokens=self.max_tokens
            )

            if self._bridge.initialize():
                # Sync state from bridge
                self.state = self._bridge.state
                self.capabilities = self._bridge.capabilities

                # Get provider info from system resource
                if self._bridge._sys_resource:
                    self.provider = self._get_provider_from_sys_resource()

                return True
            else:
                print("Failed to initialize LLM bridge")
                return False

        except Exception as e:
            print(f"Failed to create LLM bridge: {e}")
            return False

    def _get_provider_from_sys_resource(self) -> str:
        """Get provider info from the system resource."""
        if not self._bridge or not self._bridge._sys_resource:
            return "unknown"

        sys_resource = self._bridge._sys_resource

        # Try to get provider from system resource
        if hasattr(sys_resource, "provider"):
            return sys_resource.provider
        elif hasattr(sys_resource, "model"):
            model = sys_resource.model
            if model and ":" in model:
                return model.split(":")[0]

        return "unknown"

    def cleanup(self) -> bool:
        """Clean up the bridge and system resource."""
        print(f"Cleaning up LLM bridge '{self.name}'")

        if self._bridge:
            self._bridge.cleanup()
            self._bridge = None

        self.state = ResourceState.TERMINATED
        return True

    def query_sync(self, request: Any) -> Any:
        """Synchronous query method for compatibility with reason function."""
        if not self.is_running():
            return BaseResponse(success=False, error=f"LLM bridge {self.name} not running")

        if not self._bridge:
            return BaseResponse(success=False, error=f"LLM bridge {self.name} not initialized")

        return self._bridge.query(request)

    async def query_async(self, request: Any) -> Any:
        """Async query interface for llm function."""
        if not self.is_running():
            return BaseResponse(success=False, error=f"LLM bridge {self.name} not running")

        if not self._bridge:
            return BaseResponse(success=False, error=f"LLM bridge {self.name} not initialized")

        return self._bridge.query(request)

    # For backward compatibility, query defaults to sync
    def query(self, request: Any) -> Any:
        """Synchronous query method (alias for query_sync)."""
        return self.query_sync(request)

    # All operations are delegated to the system resource bridge
    # No duplicate logic or state management here
