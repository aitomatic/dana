"""Capability factory."""

from dana.common.capability.base_capability import BaseCapability
from dana.frameworks.agent.capability.memory_capability import MemoryCapability


class CapabilityFactory:
    """Capability factory."""

    @classmethod
    def create_capability(cls, capability_type: str) -> BaseCapability:
        """Create capability instance."""
        if capability_type == "memory":
            return MemoryCapability()
        raise ValueError(f"Unknown capability: {capability_type}")
