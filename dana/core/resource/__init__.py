"""
Dana Resource System - Core Implementation

This module provides the core resource classes and types for the Dana language.
Resources are first-class struct types that can only be used within agent contexts.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from .base_resource import BaseResource, ResourceState
from .context_integration import ResourceContextIntegrator, get_resource_integrator

# Core plugins are loaded dynamically, not imported here
# They're available through the ResourceLoader
# Re-export selected core plugin blueprints for convenience
from .plugins import MCPResource
from .resource_handle import ResourceHandle
from .resource_helpers import (
    add_resource_search_path,
    get_resource_stats,
    list_available_resources,
    register_resource,
    register_resource_class,
    reload_resources,
)
from .resource_loader import ResourceLoader, ResourcePlugin
from .resource_registry import ResourceError, ResourceRegistry

try:
    # Import RAGResource from core plugins (moved from stdlib)
    from .plugins.rag_resource import RAGResource  # type: ignore
except Exception:  # pragma: no cover - fallback if core plugins not available
    RAGResource = None  # type: ignore

__all__ = [
    "BaseResource",
    "ResourceState",
    "ResourceHandle",
    "ResourceRegistry",
    "ResourceError",
    "ResourceLoader",
    "ResourcePlugin",
    "ResourceContextIntegrator",
    "get_resource_integrator",
    # Helper functions
    "register_resource",
    "register_resource_class",
    "add_resource_search_path",
    "reload_resources",
    "list_available_resources",
    "get_resource_stats",
    # Commonly used resource blueprints
    "MCPResource",
    "RAGResource",
]
