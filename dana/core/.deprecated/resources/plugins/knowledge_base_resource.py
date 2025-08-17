"""
Knowledge Base Resource Type Registration

Registers KnowledgeBase as a ResourceType that creates ResourceInstance objects
with KnowledgeBaseResource backend automatically.
"""

from dana.core.lang.interpreter.struct_system import deprecated_StructTypeRegistry
from dana.core.resource.resource_instance import ResourceType

# Define the ResourceType for Knowledge Base
KNOWLEDGE_BASE_RESOURCE_TYPE = ResourceType(
    name="KnowledgeBase",
    fields={"name": "str", "connection_string": "str"},
    field_order=["name", "connection_string"],
    field_defaults={"connection_string": "sqlite:///knowledge.db"},
    field_comments={"name": "Unique name for the knowledge base", "connection_string": "Database connection string"},
    docstring="Knowledge base resource for structured knowledge storage and retrieval",
)

# Register the type so it can be used in Dana
deprecated_StructTypeRegistry.register(KNOWLEDGE_BASE_RESOURCE_TYPE)


def get_knowledge_base_resource_type() -> ResourceType:
    """Get the KnowledgeBase ResourceType for programmatic use."""
    return KNOWLEDGE_BASE_RESOURCE_TYPE


__all__ = ["KNOWLEDGE_BASE_RESOURCE_TYPE", "get_knowledge_base_resource_type"]
