"""
Dana Resource System - New Implementation

This module provides the new resource system that uses composition and delegation
and provides a unified type system approach.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from .builtins import LLMResourceInstance, LLMResourceType
from .resource_error import ResourceError
from .resource_instance import ResourceInstance
from .resource_registry import ResourceTypeRegistry
from .resource_state import ResourceState
from .resource_type import ResourceType

__all__ = [
    "ResourceType",
    "ResourceInstance",
    "ResourceTypeRegistry",
    "ResourceState",
    "ResourceError",
    "LLMResourceInstance",
    "LLMResourceType",
]
