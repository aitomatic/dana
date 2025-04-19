"""Capability factory."""


from opendxa.base.capability.base_capability import BaseCapability
from opendxa.agent.capability.memory_capability import MemoryCapability

class CapabilityFactory:
    """Capability factory."""
    @classmethod
    def create_capability(cls, capability_type: str) -> 'BaseCapability':
        """Create capability instance."""
        if capability_type == "memory":
            return MemoryCapability()
        raise ValueError(f"Unknown capability: {capability_type}") 
