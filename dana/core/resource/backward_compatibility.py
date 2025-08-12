"""
Backward Compatibility Bridge for Resource Keyword

This module provides a bridge between the old use() function and the new
resource keyword system to ease migration.
"""

import warnings
from typing import Any

from dana.common.sys_resource.base_sys_resource import BaseSysResource
from dana.core.lang.sandbox_context import SandboxContext

from .context_integration import get_resource_integrator


def create_resource_from_legacy_use(
    context: SandboxContext, function_name: str, *args, _name: str | None = None, **kwargs
) -> BaseSysResource:
    """
    Create a resource using the new resource system based on legacy use() parameters.

    This function bridges the old py_use() interface with the new resource keyword system.
    It creates resources using the new blueprint system while maintaining compatibility
    with existing use() calls.

    Args:
        context: The sandbox context
        function_name: The name of the function to use (e.g., "mcp", "rag")
        *args: Positional arguments for the resource
        _name: Optional name for the resource (auto-generated if not provided)
        **kwargs: Keyword arguments for the resource

    Returns:
        The created resource using the new blueprint system

    Raises:
        NotImplementedError: If the function_name is not supported
    """
    # Issue deprecation warning
    warnings.warn(
        f"use('{function_name}') is deprecated. Please use the new resource keyword syntax: "
        f"resource MyResource({function_name.upper()}Resource): ...",
        DeprecationWarning,
        stacklevel=3,
    )

    # Get the resource integrator
    integrator = get_resource_integrator()

    # Generate name if not provided
    if _name is None:
        from dana.common.utils.misc import Misc

        _name = Misc.generate_base64_uuid(length=6)

    # Map old function names to new resource kinds
    kind_mapping = {
        "mcp": "mcp",
        "rag": "rag",
        "knowledge": "knowledge",
        "human": "human",
        "coding": "coding",
        "financial_tools": "financial_tools",
        "finance_rag": "finance_rag",
    }

    if function_name.lower() not in kind_mapping:
        raise NotImplementedError(f"Function {function_name} not implemented in resource system")

    kind = kind_mapping[function_name.lower()]

    # Convert positional args to keyword args based on resource type
    converted_kwargs = _convert_legacy_args(function_name.lower(), args, kwargs)

    # Create resource using new system
    try:
        resource = integrator.create_resource(kind, _name, context, **converted_kwargs)

        # Apply any legacy-specific post-processing
        _apply_legacy_post_processing(resource, function_name.lower(), converted_kwargs)

        return resource
    except Exception as e:
        # If resource creation fails, fall back to error
        raise NotImplementedError(f"Failed to create resource {function_name}: {e}")


def _convert_legacy_args(function_name: str, args: tuple, kwargs: dict[str, Any]) -> dict[str, Any]:
    """
    Convert legacy positional arguments to keyword arguments for the new resource system.

    Args:
        function_name: The legacy function name
        args: Positional arguments from legacy call
        kwargs: Keyword arguments from legacy call

    Returns:
        Converted keyword arguments for the new resource system
    """
    converted = kwargs.copy()

    if function_name == "mcp":
        # use("mcp", url) -> MCPResource(endpoint=url)
        if args:
            converted["endpoint"] = args[0]
        # Rename url to endpoint for consistency
        if "url" in converted:
            converted["endpoint"] = converted.pop("url")

    elif function_name == "rag":
        # use("rag", documents) -> RAGResource(sources=documents)
        if args:
            converted["sources"] = args[0]
        # Rename documents to sources for consistency
        if "documents" in converted:
            converted["sources"] = converted.pop("documents")

    elif function_name == "knowledge":
        # use("knowledge", sources) -> KnowledgeResource(sources=sources)
        if args:
            converted["sources"] = args[0]

    elif function_name == "human":
        # use("human", interface) -> HumanResource(interface_type=interface)
        if args:
            converted["interface_type"] = args[0]

    elif function_name == "coding":
        # use("coding", languages) -> CodingResource(languages=languages)
        if args:
            converted["languages"] = args[0]

    elif function_name in ["financial_tools", "finance_rag"]:
        # use("financial_tools", formats) -> FinancialResource(supported_formats=formats)
        if args:
            if function_name == "financial_tools":
                converted["supported_formats"] = args[0]
            else:  # finance_rag
                converted["sources"] = args[0]

    return converted


def _apply_legacy_post_processing(resource: BaseSysResource, function_name: str, kwargs: dict[str, Any]):
    """
    Apply any legacy-specific post-processing to maintain compatibility.

    Args:
        resource: The created resource
        function_name: The legacy function name
        kwargs: The converted arguments
    """
    # Apply docstring enrichment for RAG and Knowledge resources
    # This mimics the behavior of the original py_use() function
    if function_name in ["rag", "knowledge"]:
        description = kwargs.get("description", "")
        if hasattr(resource, "sources") and resource.sources:
            filenames = sorted(resource.sources)
            enhanced_description = f"{description}. Data sources: {filenames[:3]}"
            resource.description = enhanced_description

    # Apply any other legacy compatibility adjustments
    # This is where we would add other specific behaviors that the old system had


def get_legacy_use_function():
    """
    Get a use() function that bridges to the new resource system.

    This can be used to replace the old py_use() function in the function registry
    to provide seamless backward compatibility.

    Returns:
        A function that can be called like the old use() function
    """

    def legacy_use_function(context: SandboxContext, function_name: str, *args, _name: str = None, **kwargs):
        """
        Legacy use function that delegates to new resource system.

        Usage:
            use("mcp", url="http://localhost:8880")
            use("rag", ["doc1.pdf", "doc2.txt"], description="My documents")
        """
        return create_resource_from_legacy_use(context, function_name, *args, _name=_name, **kwargs)

    return legacy_use_function
