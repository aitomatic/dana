"""DXA resource module."""

from .base_resource import BaseResource
from .llm_resource import LLMResource
from .expert_resource import ExpertResource
from .resource_factory import ResourceFactory
from .human_resource import HumanResource

__all__ = ['BaseResource', 'LLMResource', 'ExpertResource', 'ResourceFactory', 'HumanResource']
