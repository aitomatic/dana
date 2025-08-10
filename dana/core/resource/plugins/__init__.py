"""
Core Resource Plugins

This directory contains essential Python resource implementations that serve as:
1. Reference implementations for the plugin architecture
2. Fallback options when Dana implementations aren't feasible
3. Core functionality that requires Python libraries

Only the most essential resources should be here. All others should be
implemented as plugins in dana/libs/stdlib/resources/.
"""

from .base_llm_resource import BaseLLMResource
from .coding_resource import CodingResource
from .financial_coding_resource import FinancialCodingResource
from .financial_statement_rag_resource import FinancialStatementRAGResource
from .financial_statement_tools_resource import FinancialStatementToolsResource
from .human_resource import HumanResource
from .knowledge_base_resource import KnowledgeBaseResource
from .knowledge_resource import KnowledgeResource
from .mcp_resource import MCPResource
from .memory_resource import MemoryResource
from .rag_resource import RAGResource
from .sql_resource import SQLResource

__all__ = [
    "MCPResource",
    "BaseLLMResource",
    "RAGResource",
    "KnowledgeResource",
    "HumanResource",
    "MemoryResource",
    "KnowledgeBaseResource",
    "CodingResource",
    "FinancialCodingResource",
    "FinancialStatementRAGResource",
    "FinancialStatementToolsResource",
    "SQLResource",
]
