"""
Use function for Dana standard library.

This module provides the use function for creating and managing resources.
"""

__all__ = ["py_use"]

import asyncio
from collections.abc import Callable
from functools import wraps
from typing import Union

from dana.common.sys_resource.base_resource import BaseSysResource
from dana.common.utils.misc import Misc
from dana.core.lang.sandbox_context import SandboxContext
from dana.core.resource.base_resource import BaseResource


def create_function_with_better_doc_string(func: Callable, doc_string: str) -> Callable:
    """Create a function with a better doc string."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        return await func(*args, **kwargs)

    if asyncio.iscoroutinefunction(func):
        async_wrapper.__doc__ = doc_string
        return async_wrapper
    else:
        wrapper.__doc__ = doc_string
        return wrapper


def py_use(context: SandboxContext, function_name: str, *args, _name: str | None = None, **kwargs) -> Union[BaseSysResource, BaseResource]:
    """Use a function to create and manage resources.

    This function is used to create various types of resources like MCP and RAG.

    Args:
        context: The sandbox context
        function_name: The name of the function to use (e.g., "mcp", "rag")
        *args: Positional arguments for the resource
        _name: Optional name for the resource (auto-generated if not provided)
        **kwargs: Keyword arguments for the resource

    Returns:
        The created resource

    Examples:
        use("mcp", "server_url") -> creates an MCP resource
        use("rag", ["doc1.pdf", "doc2.txt"]) -> creates a RAG resource
    """
    if _name is None:
        _name = Misc.generate_base64_uuid(length=6)

    if function_name.lower() == "mcp":
        from dana.core.resource.plugins.mcp_resource import MCPResource

        # MCPResource expects name as first argument, then client args
        if args:
            resource = MCPResource(*args, name=_name, **kwargs)
        else:
            # If no args provided, use a default URL
            resource = MCPResource(name=_name, server_url="http://localhost:3000/sse", **kwargs)
        context.set_resource(_name, resource)
        return resource

    elif function_name.lower() == "rag":
        from dana.core.resource.plugins.rag_resource import RAGResource

        resource = RAGResource(*args, name=_name, **kwargs)
        context.set_resource(_name, resource)
        return resource

    elif function_name.lower() == "knowledge":
        # Use knowledge_base instead of the old knowledge resource
        from dana.core.resource.plugins.knowledge_base_resource import KnowledgeBaseResource

        resource = KnowledgeBaseResource(*args, name=_name, **kwargs)
        context.set_resource(_name, resource)
        return resource

    elif function_name.lower() == "human":
        # HumanResource moved to core resource plugins

        from dana.core.resource.plugins.human_resource import HumanResource

        resource = HumanResource(*args, name=_name, **kwargs)
        context.set_resource(_name, resource)
        return resource

    elif function_name.lower() == "memory":
        from dana.core.resource.plugins.memory_resource import MemoryResource

        resource = MemoryResource(*args, name=_name, **kwargs)
        context.set_resource(_name, resource)
        return resource

    elif function_name.lower() == "knowledge_base":
        from dana.core.resource.plugins.knowledge_base_resource import KnowledgeBaseResource

        resource = KnowledgeBaseResource(*args, name=_name, **kwargs)
        context.set_resource(_name, resource)
        return resource

    elif function_name.lower() == "coding":
        from dana.core.resource.plugins.coding_resource import CodingResource

        resource = CodingResource(*args, name=_name, **kwargs)
        context.set_resource(_name, resource)
        return resource

    elif function_name.lower() == "finance_coding":
        from dana.core.resource.plugins.financial_coding_resource import FinancialCodingResource

        resource = FinancialCodingResource(*args, name=_name, **kwargs)
        resource.initialize()
        context.set_resource(_name, resource)
        return resource

    elif function_name.lower() == "financial_tools":
        from dana.core.resource.plugins.financial_statement_tools_resource import FinancialStatementToolsResource

        resource = FinancialStatementToolsResource(*args, name=_name, **kwargs)
        resource.initialize()
        context.set_resource(_name, resource)
        return resource

    elif function_name.lower() == "finance_rag":
        from dana.core.resource.plugins.financial_statement_rag_resource import FinancialStatementRAGResource

        resource = FinancialStatementRAGResource(*args, name=_name, **kwargs)
        resource.initialize()
        context.set_resource(_name, resource)
        return resource

    elif function_name.lower() == "llm":
        from dana.core.resource.plugins.base_llm_resource import BaseLLMResource

        resource = BaseLLMResource(*args, name=_name, **kwargs)
        context.set_resource(_name, resource)
        return resource

    elif function_name.lower() == "tabular_index":
        from dana.common.resource.tabular_index.tabular_index_resource import TabularIndexResource

        # Extract tabular_index specific parameters from kwargs
        tabular_index_params = kwargs.get("tabular_index_config", {})
        # Create resource with config dict
        resource = TabularIndexResource(
            name=_name,
            **tabular_index_params,
        )
        context.set_resource(_name, resource)
        return resource
    else:
        raise NotImplementedError(f"Function {function_name} not implemented")
