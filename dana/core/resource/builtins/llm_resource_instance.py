"""
LLM Resource Instance

This module provides LLMResourceInstance, which wraps dana.common.sys_resource.llm.LLMResource
and integrates it with the core resource system by extending ResourceInstance.
"""

from typing import TYPE_CHECKING, Any

from dana.common.types import BaseRequest, BaseResponse
from dana.core.resource.resource_instance import ResourceInstance
from dana.core.resource.resource_type import ResourceType

if TYPE_CHECKING:
    from dana.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource


class LLMResourceInstance(ResourceInstance):
    """
    Resource instance that wraps LLMResource and provides pass-through delegation.

    This class bridges the gap between the core resource system (ResourceInstance)
    and the system resource framework (LLMResource) by wrapping an LLMResource
    and delegating key methods to it.
    """

    def __init__(self, resource_type: "ResourceType", llm_resource: "LegacyLLMResource", values: dict[str, Any] | None = None):
        """
        Initialize LLMResourceInstance with an LLMResource backend.

        Args:
            resource_type: The LLMResourceType that defines this instance
            llm_resource: The LLMResource instance to wrap
            values: Additional field values for the resource instance
        """
        # Initialize with the provided resource type and values
        super().__init__(resource_type, values or {})

        # Store the wrapped LLMResource
        self._llm_resource = llm_resource
        self._backend = llm_resource  # Set backend for compatibility

    @property
    def llm_resource(self) -> "LegacyLLMResource":
        """Get the wrapped LLMResource."""
        return self._llm_resource

    @property
    def name(self) -> str:
        """Get the resource name."""
        return self._llm_resource.name

    @property
    def model(self) -> str | None:
        """Get the current model."""
        return self._llm_resource.model

    @model.setter
    def model(self, value: str) -> None:
        """Set the model."""
        self._llm_resource.model = value
        # Also update the struct field to keep them in sync
        self._values["model"] = value

    def __setattr__(self, name: str, value: Any) -> None:
        """Override setattr to handle model field specially."""
        if name == "model" and hasattr(self, "_llm_resource"):
            # Use our property setter for model
            self._llm_resource.model = value
            self._values["model"] = value
        else:
            # Use parent's setattr for everything else
            super().__setattr__(name, value)

        # Pass-through delegation methods for key LLMResource functionality

    def initialize(self) -> bool:
        """Initialize the LLM resource synchronously."""
        try:
            self.startup()
            self.state = "INITIALIZED"
            return True
        except Exception as e:
            self.state = "ERROR"
            raise e

    async def initialize_async(self) -> bool:
        """Initialize the LLM resource asynchronously."""
        try:
            await self._llm_resource.initialize()
            self.state = "INITIALIZED"
            return True
        except Exception as e:
            self.state = "ERROR"
            raise e

    def cleanup(self) -> bool:
        """Clean up the LLM resource synchronously."""
        try:
            self.shutdown()
            self.state = "TERMINATED"
            return True
        except Exception as e:
            self.state = "ERROR"
            raise e

    async def cleanup_async(self) -> bool:
        """Clean up the LLM resource asynchronously."""
        try:
            await self._llm_resource.cleanup()
            self.state = "TERMINATED"
            return True
        except Exception as e:
            self.state = "ERROR"
            raise e

    def startup(self) -> bool:
        """Start the LLM resource synchronously."""
        try:
            self._llm_resource.startup()
            self.state = "STARTED"
            print(f"CTN >>> LLM resource started: {self._llm_resource}")
            print(f"CTN >>> LLM resource is_available: {self.is_available}")
            return True
        except Exception as e:
            self.state = "ERROR"
            raise e

    def shutdown(self) -> bool:
        """Shut down the LLM resource synchronously."""
        try:
            self._llm_resource.shutdown()
            self.state = "TERMINATED"
            return True
        except Exception as e:
            self.state = "ERROR"
            raise e

    def start(self) -> bool:
        """Start the resource."""
        return self.startup()

    def stop(self) -> bool:
        """Stop the resource."""
        return self.shutdown()

    async def query(self, request: BaseRequest) -> BaseResponse:
        """Query the LLM resource."""
        return await self._llm_resource.query(request)

    def query_sync(self, request: BaseRequest) -> BaseResponse:
        """Query the LLM resource synchronously."""
        return self._llm_resource.query_sync(request)

    def can_handle(self, request: BaseRequest) -> bool:
        """Check if the LLM resource can handle the request."""
        if hasattr(request, "arguments") and isinstance(request.arguments, dict):
            return self._llm_resource.can_handle(request)
        return False

    @property
    def is_available(self) -> bool:
        """Check if the LLM resource is available."""
        return self._llm_resource.is_available

    def get_available_models(self) -> list[str]:
        """Get list of available models."""
        return self._llm_resource.get_available_models()

    def with_mock_llm_call(self, mock_llm_call) -> "LLMResourceInstance":
        """Set mock LLM call and return self for chaining."""
        self._llm_resource.with_mock_llm_call(mock_llm_call)
        return self

    # Delegation for any method not explicitly defined
    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to the wrapped LLMResource."""
        # Don't delegate ResourceInstance-specific attributes that should come from parent
        if name in ["struct_type", "_fields", "_field_order"]:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

        # Delegate to wrapped LLMResource
        return getattr(self._llm_resource, name)

    def __repr__(self) -> str:
        """String representation."""
        return f"LLMResourceInstance(name='{self.name}', model='{self.model}', state='{getattr(self, 'state', 'UNKNOWN')}')"
