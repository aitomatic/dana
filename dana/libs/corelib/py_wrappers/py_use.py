"""
Use function for Dana standard library.

This module provides the use function for creating and managing resources.
"""

__all__ = ["py_use"]

import asyncio
from collections.abc import Callable
from functools import wraps

from dana.common.resource.base_resource import BaseResource
from dana.common.utils.misc import Misc
from dana.core.lang.sandbox_context import SandboxContext


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


def py_use(context: SandboxContext, function_name: str, *args, _name: str | None = None, **kwargs) -> BaseResource:
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
        from dana.integrations.mcp import MCPResource

        resource = MCPResource(*args, name=_name, **kwargs)
        context.set_resource(_name, resource)
        return resource
    elif function_name.lower() == "rag":
        from dana.common.resource.rag.rag_resource import RAGResource

        resource = RAGResource(*args, name=_name, **kwargs)
        description = kwargs.get("description", None)
        filenames = sorted(resource.filenames)
        doc_string = f"{resource.query.__func__.__doc__ if not description else description}. These are the expertise data sources: {filenames[:3]} known as {_name}"
        resource.query = create_function_with_better_doc_string(resource.query, doc_string)
        context.set_resource(_name, resource)
        return resource
    elif function_name.lower() == "knowledge":
        from dana.common.resource.rag.knowledge_resource import KnowledgeResource

        description = kwargs.get("description", None)
        resource = KnowledgeResource(*args, name=_name, **kwargs)
        doc_string = f"{resource.get_facts.__func__.__doc__}. {'' if not description else description}"
        resource.get_facts = create_function_with_better_doc_string(resource.get_facts, doc_string)
        doc_string = f"{resource.get_plan.__func__.__doc__}. {'' if not description else description}"
        resource.get_plan = create_function_with_better_doc_string(resource.get_plan, doc_string)
        doc_string = f"{resource.get_heuristics.__func__.__doc__}. {'' if not description else description}"
        resource.get_heuristics = create_function_with_better_doc_string(resource.get_heuristics, doc_string)
        context.set_resource(_name, resource)
        return resource
    elif function_name.lower() == "human":
        from dana.common.resource.human_resource import HumanResource

        resource = HumanResource(*args, name=_name, **kwargs)
        context.set_resource(_name, resource)
        return resource
    elif function_name.lower() == "coding":
        from dana.common.resource.coding.coding_resource import CodingResource

        resource = CodingResource(*args, name=_name, **kwargs)
        context.set_resource(_name, resource)
        return resource
    elif function_name.lower() == "finance_coding":
        from dana.common.resource.coding.finance_coding_resource import FinanceCodingResource

        resource = FinanceCodingResource(*args, name=_name, **kwargs)
        context.set_resource(_name, resource)
        return resource
    elif function_name.lower() == "financial_tools":
        from dana.common.resource.financial_resources.financial_stmt_tools import FinancialStatementTools

        resource = FinancialStatementTools(*args, name=_name, **kwargs)
        context.set_resource(_name, resource)
        return resource
    elif function_name.lower() == "finance_rag":
        from dana.common.resource.rag.financial_statement_rag_resource import FinancialStatementRAGResource

        resource = FinancialStatementRAGResource(*args, name=_name, **kwargs)
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
