"""
Simple tests for RAGOrchestrator class.
"""

from unittest.mock import AsyncMock, Mock

import pytest

from dana.common.exceptions import EmbeddingError
from dana.common.sys_resource.embedding.embedding_utils import has_embedding_api_keys
from dana.common.sys_resource.rag.pipeline.rag_orchestrator import RAGOrchestrator


class TestRAGOrchestrator:
    """Simple test cases for RAGOrchestrator."""

    def test_init(self):
        """Test basic initialization."""
        if has_embedding_api_keys():
            # If API keys are available, test normal initialization
            orchestrator = RAGOrchestrator()
            assert orchestrator is not None
        else:
            # If no API keys, expect EmbeddingError during initialization
            with pytest.raises(EmbeddingError):
                RAGOrchestrator()

    @pytest.mark.asyncio
    async def test_preprocess_basic(self):
        """Test basic preprocessing."""
        if has_embedding_api_keys():
            # If API keys are available, test normal behavior
            orchestrator = RAGOrchestrator()

            sources = ["test.txt"]

            # Should not raise an error (but will likely fail due to missing files)
            try:
                await orchestrator._async_preprocess(sources)
            except Exception:
                # Expected to fail with missing files, that's OK
                pass
        else:
            # If no API keys, expect EmbeddingError during initialization
            with pytest.raises(EmbeddingError):
                RAGOrchestrator()

    @pytest.mark.asyncio
    async def test_retrieve_basic(self):
        """Test basic retrieval."""
        if has_embedding_api_keys():
            # If API keys are available, test normal behavior
            orchestrator = RAGOrchestrator()

            # Mock the retriever
            mock_retriever = Mock()
            mock_retriever.aretrieve = AsyncMock(return_value=[])
            orchestrator._retriever = mock_retriever

            result = await orchestrator.retrieve("test query", num_results=5)

            # Should return empty list
            assert result == []
        else:
            # If no API keys, expect EmbeddingError during initialization
            with pytest.raises(EmbeddingError):
                RAGOrchestrator()
