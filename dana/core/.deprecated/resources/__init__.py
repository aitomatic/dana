"""
Dana Resource System - Core Implementation

This module provides the core resource classes and types for the Dana language.
Resources are first-class struct types that can only be used within agent contexts.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

# Clean ResourceInstance-based resource system
from dana.common.sys_resource.rag.rag_resource import RAGResource

# Import system resources for compatibility
from dana.integrations.mcp.mcp_resource import MCPResource

# Import compatibility layer
from .compatibility import AgentAccessError, BaseResource, ResourceContextIntegrator, get_resource_integrator
from .resource_handle import ResourceHandle
from .resource_instance import ResourceInstance, ResourceType
from .resource_loader import ResourceLoader, ResourcePlugin
from .resource_registry import ResourceError, ResourceRegistry
from .resource_state import ResourceState

__all__ = [
    "ResourceHandle",
    "ResourceRegistry",
    "ResourceError",
    "ResourceLoader",
    "ResourcePlugin",
    "ResourceInstance",
    "ResourceType",
    "ResourceState",
    "MCPResource",
    "RAGResource",
    "BaseResource",
    "AgentAccessError",
    "ResourceContextIntegrator",
    "get_resource_integrator",
]
