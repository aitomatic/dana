"""
Built-in Resource Types and Instances

This module provides built-in resource types and instances that wrap common system resources
and integrate them with the core resource system.
"""

from .llm_resource_instance import LLMResourceInstance
from .llm_resource_type import LLMResourceType

__all__ = [
    "LLMResourceInstance",
    "LLMResourceType",
]
