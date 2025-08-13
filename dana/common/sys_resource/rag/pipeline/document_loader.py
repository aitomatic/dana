"""
Document Loading and Preprocessing Module

This module handles the loading and preprocessing of documents from various sources
including local files, directories, and web URLs. It supports multiple document
formats and provides caching capabilities.

The DocumentLoader class is responsible for:
- Loading documents from multiple sources (files, directories, URLs)
- Web content fetching with browser automation
- Document preprocessing and metadata addition
- Caching processed documents for performance
- Source separation and tracking
"""

import asyncio
import os

from llama_index.core import Document

from dana.common.sys_resource.rag.loader.local_loader import LocalLoader
from dana.common.sys_resource.rag.loader.web_loader import WebLoader
from dana.common.sys_resource.rag.pipeline.base_stage import BaseStage


class DocumentLoader(BaseStage):
    """Handles document loading and preprocessing only."""

    _NAME = "doc_loader"
    SUPPORTED_TYPES = [".pdf", ".txt", ".docx", ".md", ".csv", ".json", ".html", ".xml", ".pptx", ".xlsx", ".xls", ".doc"]

    def __init__(self):
        super().__init__()
        self._local_loader = LocalLoader(self.SUPPORTED_TYPES)
        self._web_loader = WebLoader()

    async def load_sources(self, sources: list[str]) -> dict[str, list[Document]]:
        docs_by_source = await self._load_sources(sources)
        return docs_by_source

    async def _load(self, source: str) -> list[Document]:
        if source.startswith("http"):
            return await self._web_loader.load(source)
        else:
            return await self._local_loader.load(source)

    async def _load_sources(self, sources: list[str]) -> dict[str, list[Document]]:
        tasks = [self._load(source) for source in sources]
        results = await asyncio.gather(*tasks)
        return {source: result for source, result in zip(sources, results, strict=False)}

    @staticmethod
    def resolve_single_source(source: str) -> str:
        if source.startswith("http"):
            return source
        else:
            return os.path.abspath(source)
