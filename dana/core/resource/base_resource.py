"""
Base Resource

This module defines the foundational BaseResource class that all Dana resources inherit from.
It provides the standard interface and lifecycle management for resources.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from dana.common.types import BaseRequest, BaseResponse


class ResourceState(Enum):
    """Resource lifecycle states."""

    DEFINED = "defined"  # Resource type defined, not instantiated
    CREATED = "created"  # Resource instance created, not initialized
    RUNNING = "running"  # Resource active and available
    SUSPENDED = "suspended"  # Resource temporarily unavailable
    TERMINATED = "terminated"  # Resource permanently shut down


@dataclass
class BaseResource:
    """
    Base resource that all Dana resources inherit from.

    This provides the standard interface and metadata fields required
    for all resources in the Dana ecosystem.
    """

    # Core metadata fields
    kind: str = "base"  # Resource type identifier
    name: str = ""  # Unique name within scope
    version: str = "1.0.0"  # Resource version
    description: str = ""  # Human-readable description
    domain: str = "general"  # Domain classification
    tags: List[str] = field(default_factory=list)  # Discovery/classification tags
    capabilities: List[str] = field(default_factory=list)  # Available capabilities
    permissions: List[str] = field(default_factory=list)  # Required permissions
    config: Dict[str, Any] = field(default_factory=dict)  # Provider-specific config

    # Runtime state
    state: ResourceState = ResourceState.CREATED
    owner_agent: str = ""  # Agent that owns this resource

    def initialize(self) -> bool:
        """Initialize resource - override in concrete implementations."""
        if self.state == ResourceState.CREATED:
            self.state = ResourceState.RUNNING
            return True
        return False

    def cleanup(self) -> bool:
        """Clean up resource - override in concrete implementations."""
        if self.state in [ResourceState.RUNNING, ResourceState.SUSPENDED]:
            self.state = ResourceState.TERMINATED
            return True
        return False

    def can_handle(self, request: BaseRequest) -> bool:
        """Check if resource can handle request - override in implementations."""
        return False

    def query(self, request: BaseRequest) -> BaseResponse:
        """Standard query interface - override in concrete implementations."""
        if self.state != ResourceState.RUNNING:
            return BaseResponse(success=False, error=f"Resource {self.name} not running (state: {self.state})")

        return BaseResponse(success=True, content=request.arguments, error=None)

    def start(self) -> bool:
        """Start the resource if created."""
        if self.state == ResourceState.CREATED:
            return self.initialize()
        return False

    def stop(self) -> bool:
        """Stop the resource if running."""
        if self.state == ResourceState.RUNNING:
            return self.cleanup()
        return False

    def suspend(self) -> bool:
        """Suspend the resource if running."""
        if self.state == ResourceState.RUNNING:
            self.state = ResourceState.SUSPENDED
            return True
        return False

    def resume(self) -> bool:
        """Resume the resource if suspended."""
        if self.state == ResourceState.SUSPENDED:
            self.state = ResourceState.RUNNING
            return True
        return False

    def is_running(self) -> bool:
        """Check if resource is in running state."""
        return self.state == ResourceState.RUNNING

    def get_metadata(self) -> Dict[str, Any]:
        """Get resource metadata for discovery and transfer."""
        return {
            "kind": self.kind,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "domain": self.domain,
            "tags": self.tags,
            "capabilities": self.capabilities,
            "permissions": self.permissions,
            "state": self.state.value,
            "owner_agent": self.owner_agent,
        }
