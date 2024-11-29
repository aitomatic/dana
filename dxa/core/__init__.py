"""Core DXA functionality.

This package provides the fundamental building blocks of the DXA framework:
- Capabilities: Core definitions of agent capabilities
- Resources: Implementation of various agent resources
- Reasoning: Different reasoning patterns for agents

The core package maintains a clean separation between:
- Capability definitions (what agents can do)
- Resource implementations (how agents do it)
- Reasoning patterns (how agents think about it)
"""

from dxa.core.capability.domain_expertise import DomainExpertise
from dxa.core.resource.expert_resource import ExpertResource
from dxa.core.resource.base_resource import BaseResource
from dxa.core.reasoning.base_reasoning import BaseReasoning

__all__ = [
    'DomainExpertise',
    'ExpertResource',
    'BaseResource',
    'BaseReasoning'
]
