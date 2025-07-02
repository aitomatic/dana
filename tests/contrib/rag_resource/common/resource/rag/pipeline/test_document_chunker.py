"""
Simple tests for DocumentChunker class.
"""

import os

import pytest
from llama_index.core import Document

from opendxa.contrib.rag_resource.common.resource.rag.pipeline.document_chunker import DocumentChunker


# Helper function to check if OpenAI API key is available
def has_openai_api_key():
    """Check if OpenAI API key is available for integration tests."""
    return bool(os.getenv("OPENAI_API_KEY"))


# Pytest fixture to skip tests requiring OpenAI API key
openai_required = pytest.mark.skipif(not has_openai_api_key(), reason="OpenAI API key required for integration tests")


class TestDocumentChunker:
    """Simple test cases for DocumentChunker."""

    def test_init_default(self):
        """Test basic initialization."""
        chunker = DocumentChunker()
        assert chunker.chunk_size == DocumentChunker.DEFAULT_CHUNK_SIZE
        assert chunker.chunk_overlap == DocumentChunker.DEFAULT_CHUNK_OVERLAP
        assert chunker.use_chunking is True

    def test_init_custom(self):
        """Test initialization with custom parameters."""
        chunker = DocumentChunker(chunk_size=1024, chunk_overlap=256, use_chunking=False)
        assert chunker.chunk_size == 1024
        assert chunker.chunk_overlap == 256
        assert chunker.use_chunking is False

    @pytest.mark.asyncio
    async def test_chunk_documents_disabled(self):
        """Test that chunking disabled returns original documents."""
        chunker = DocumentChunker(use_chunking=False)

        docs_by_source = {"test.txt": [Document(text="Test document")]}

        result = await chunker.chunk_documents(docs_by_source)
        assert result == docs_by_source

    @pytest.mark.asyncio
    async def test_chunk_documents_empty(self):
        """Test empty input."""
        chunker = DocumentChunker()
        result = await chunker.chunk_documents({})
        assert result == {}

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_chunking(self):
        """Test actual chunking with real SentenceSplitter."""
        chunker = DocumentChunker(chunk_size=50, chunk_overlap=10, use_chunking=True)

        # Long text that will definitely be chunked
        long_text = "This is a sentence. " * 20
        docs_by_source = {"test.txt": [Document(text=long_text, metadata={"source": "test.txt"})]}

        result = await chunker.chunk_documents(docs_by_source)

        # Should have chunks
        chunks = result["test.txt"]
        assert len(chunks) >= 1

        # Each chunk should have metadata
        for chunk in chunks:
            assert "chunk_index" in chunk.metadata
            assert "total_chunks" in chunk.metadata
            assert chunk.metadata["source"] == "test.txt"
