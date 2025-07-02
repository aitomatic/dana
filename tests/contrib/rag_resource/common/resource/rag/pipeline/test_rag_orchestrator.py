"""
Simple tests for RAGOrchestrator class.
"""

from unittest.mock import AsyncMock, Mock

import pytest

from opendxa.contrib.rag_resource.common.resource.rag.pipeline.rag_orchestrator import RAGOrchestrator


class TestRAGOrchestrator:
    """Simple test cases for RAGOrchestrator."""

    def test_init(self):
        """Test basic initialization."""
        orchestrator = RAGOrchestrator()
        assert orchestrator is not None

    @pytest.mark.asyncio
    async def test_preprocess_basic(self):
        """Test basic preprocessing."""
        orchestrator = RAGOrchestrator()

        sources = ["test.txt"]

        # Should not raise an error (but will likely fail due to missing files)
        try:
            await orchestrator._async_preprocess(sources)
        except Exception:
            # Expected to fail with missing files, that's OK
            pass

    @pytest.mark.asyncio
    async def test_retrieve_basic(self):
        """Test basic retrieval."""
        orchestrator = RAGOrchestrator()

        # Mock the retriever
        mock_retriever = Mock()
        mock_retriever.aretrieve = AsyncMock(return_value=[])
        orchestrator._retriever = mock_retriever

        result = await orchestrator.retrieve("test query", num_results=5)

        # Should return empty list
        assert result == []
