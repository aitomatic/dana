"""Core capabilities for DXA agents."""

from dana.frameworks.agent.deprecated.capability.capability_factory import CapabilityFactory
from dana.frameworks.agent.deprecated.capability.domain_expertise import DomainExpertise
from dana.frameworks.agent.deprecated.capability.memory_capability import MemoryCapability

__all__ = [
    "CapabilityFactory",
    "DomainExpertise",
    "MemoryCapability",
]
