from .document_loader import DocumentLoader
from dana.common.sys_resource.rag.loader.json_knowledge_loader import JsonKnowledgeLoader
from llama_index.core import Document
import asyncio


class KnowledgeLoader(DocumentLoader):
    """Handles document loading and preprocessing only."""

    _NAME = "knowledge_loader"
    SUPPORTED_TYPES = [".pdf", ".txt", ".docx", ".md", ".csv", ".json", ".html", ".xml", ".pptx", ".xlsx", ".xls", ".doc"]

    def __init__(self):
        super().__init__()
        self._json_loader = JsonKnowledgeLoader(self.SUPPORTED_TYPES)

    async def load_sources(self, sources: list[str]) -> dict[str, list[Document]]:
        docs_by_source = await self._load_sources(sources)
        return docs_by_source

    async def _load(self, source: str) -> list[Document]:
        if source.startswith("http"):
            return await self._web_loader.load(source)
        else:
            return await self._json_loader.load(source)

    async def _load_sources(self, sources: list[str]) -> dict[str, list[Document]]:
        tasks = [self._load(source) for source in sources]
        results = await asyncio.gather(*tasks)
        return {source: result for source, result in zip(sources, results, strict=False)}
