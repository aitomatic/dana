"""DXA resource module."""

from .base_resource import BaseResource
from .llm_resource import LLMResource
from .resource_factory import ResourceFactory

__all__ = ['BaseResource', 'LLMResource', 'ResourceFactory']
