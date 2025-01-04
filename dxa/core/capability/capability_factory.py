"""Capability factory."""


from .base_capability import BaseCapability
from .memory_capability import MemoryCapability
class CapabilityFactory:
    """Capability factory."""
    @classmethod
    def create_capability(cls, capability_type: str) -> 'BaseCapability':
        """Create capability instance."""
        if capability_type == "memory":
            return MemoryCapability()
        raise ValueError(f"Unknown capability: {capability_type}") 
