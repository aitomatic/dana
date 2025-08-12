"""
Resource Handle for Transfer

This module defines the ResourceHandle struct used for transferring resources
between agents in a portable, serializable format.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ResourceHandle:
    """
    Portable handle for resource transfer between agents.

    Contains the essential metadata needed to reconstruct or reference
    a resource in a different agent context.
    """

    kind: str  # Resource type identifier
    name: str  # Resource name
    version: str  # Resource version
    description: str  # Description
    domain: str  # Domain classification
    tags: List[str] = field(default_factory=list)  # Classification tags
    capabilities: List[str] = field(default_factory=list)  # Available capabilities
    permissions: List[str] = field(default_factory=list)  # Required permissions
    config: Dict[str, Any] = field(default_factory=dict)  # Portable config subset

    # Transfer metadata
    source_agent: str = ""  # Agent that created this handle
    transfer_timestamp: str = ""  # When handle was created

    def to_dict(self) -> Dict[str, Any]:
        """Convert handle to dictionary for serialization."""
        return {
            "kind": self.kind,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "domain": self.domain,
            "tags": self.tags,
            "capabilities": self.capabilities,
            "permissions": self.permissions,
            "config": self.config,
            "source_agent": self.source_agent,
            "transfer_timestamp": self.transfer_timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResourceHandle":
        """Create handle from dictionary."""
        return cls(
            kind=data.get("kind", ""),
            name=data.get("name", ""),
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            domain=data.get("domain", "general"),
            tags=data.get("tags", []),
            capabilities=data.get("capabilities", []),
            permissions=data.get("permissions", []),
            config=data.get("config", {}),
            source_agent=data.get("source_agent", ""),
            transfer_timestamp=data.get("transfer_timestamp", ""),
        )

    def is_compatible_with(self, target_kind: str) -> bool:
        """Check if this handle is compatible with target resource type."""
        return self.kind == target_kind

    def validate(self) -> bool:
        """Validate that handle has required fields."""
        return bool(self.kind and self.name and self.version)
