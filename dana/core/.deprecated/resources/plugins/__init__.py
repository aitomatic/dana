"""
Core Resource Plugins

This directory contains essential Python resource implementations that serve as:
1. Reference implementations for the plugin architecture
2. Fallback options when Dana implementations aren't feasible
3. Core functionality that requires Python libraries

Only the most essential resources should be here. All others should be
implemented as plugins in dana/libs/stdlib/resources/.
"""

from .knowledge_base_resource import get_knowledge_base_resource_type

__all__ = [
    "get_knowledge_base_resource_type",
]
