"""Capability factory."""

from dana.common.deprecated.capability.base_capability import BaseCapability
from dana.frameworks.agent.deprecated.capability.memory_capability import MemoryCapability


class CapabilityFactory:
    """Capability factory."""

    @classmethod
    def create_capability(cls, capability_type: str) -> BaseCapability:
        """Create capability instance."""
        if capability_type == "memory":
            return MemoryCapability()
        raise ValueError(f"Unknown capability: {capability_type}")
