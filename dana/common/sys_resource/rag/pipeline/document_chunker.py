"""
Document Chunking Module

This module handles the chunking of documents into smaller, manageable pieces
for better retrieval and processing. It provides configurable chunking strategies
while preserving document metadata and source information.

The DocumentChunker class is responsible for:
- Splitting large documents into smaller chunks
- Preserving metadata and source information across chunks
- Configurable chunk size and overlap parameters
- Maintaining document structure and context
"""

import asyncio
from functools import reduce

from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter

from dana.common.sys_resource.rag.pipeline.base_stage import BaseStage


class DocumentChunker(BaseStage):
    """Handles document chunking strategies only."""

    _NAME = "doc_chunker"
    DEFAULT_CHUNK_SIZE = 512
    DEFAULT_CHUNK_OVERLAP = 128

    def __init__(self, chunk_size: int | None = None, chunk_overlap: int | None = None, use_chunking: bool = True, **kwargs):
        """Initialize DocumentChunker.

        Args:
            chunk_size: Size of each chunk in characters. Defaults to 512.
            chunk_overlap: Overlap between chunks in characters. Defaults to 128.
            use_chunking: Whether to enable chunking. If False, documents are returned as-is.
        """
        super().__init__()
        self.chunk_size = chunk_size if chunk_size is not None else self.DEFAULT_CHUNK_SIZE
        self.chunk_overlap = chunk_overlap if chunk_overlap is not None else self.DEFAULT_CHUNK_OVERLAP
        self.use_chunking = use_chunking

        # Initialize the sentence splitter for chunking
        if self.use_chunking:
            self._splitter = SentenceSplitter(chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)

    async def chunk_documents(self, docs_by_source: dict[str, list[Document]]) -> dict[str, list[Document]]:
        """Split documents into smaller chunks for better retrieval.

        Breaks large documents into overlapping chunks to optimize
        semantic search and context relevance. Preserves metadata
        and source information across chunks.

        Args:
            documents: List of documents to chunk.

        Returns:
            List of document chunks, each with preserved metadata
            and source traceability.
        """
        if not self.use_chunking:
            return docs_by_source

        chunks_by_source = {}

        for source, documents in docs_by_source.items():
            tasks = [self._chunk_single_document(doc) for doc in documents]
            chunks_by_doc = await asyncio.gather(*tasks)
            chunks_by_source[source] = list(reduce(lambda x, y: x + y, chunks_by_doc, []))  # flatten list of lists

        return chunks_by_source

    async def _chunk_single_document(self, doc: Document) -> list[Document]:
        """Split a single document into chunks.

        Args:
            doc: Document to chunk.

        Returns:
            List of document chunks with preserved metadata.
        """
        # Use LlamaIndex's SentenceSplitter for better chunking
        nodes = await self._splitter.aget_nodes_from_documents([doc])

        # Convert nodes back to Documents while preserving metadata
        chunked_docs = []
        for i, node in enumerate(nodes):
            # Create new document with chunk content
            chunk_doc = Document(text=node.text, metadata=doc.metadata.copy() if doc.metadata else {}, id_=f"{doc.doc_id}-{i}-{self.info}")

            # Add chunk-specific metadata
            if chunk_doc.metadata is None:
                chunk_doc.metadata = {}
            chunk_doc.metadata["chunk_index"] = i
            chunk_doc.metadata["total_chunks"] = len(nodes)
            chunk_doc.metadata["original_doc_id"] = doc.doc_id if hasattr(doc, "doc_id") else None
            chunk_doc.metadata.update(self.info)

            chunked_docs.append(chunk_doc)

        return chunked_docs
