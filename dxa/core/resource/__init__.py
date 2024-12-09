"""Resource management for DXA.

This module provides the core resource classes and configurations used in the DXA system.
"""

from .base_resource import BaseResource, ResourceConfig, ResourceResponse  # Importing base resource classes
from .human_resource import HumanResource  # Importing HumanResource
from .expert_resource import ExpertResource  # Assuming ExpertResource exists
from .agent_resource import AgentResource  # Assuming AgentResource exists
from .llm_resource import LLMResource  # Assuming LLMResource exists

__all__ = [
    'BaseResource',
    'ResourceConfig',
    'ResourceResponse',
    'HumanResource',
    'ExpertResource',  # Added ExpertResource
    'AgentResource',  # Added AgentResource
    'LLMResource'  # Added LLMResource
]
