"""
Simple tests for RAGResource class.
"""

from unittest.mock import AsyncMock, Mock

import pytest
from llama_index.core.schema import NodeWithScore

from dana.common.resource.rag.rag_resource import RAGResource


class TestRAGResource:
    """Simple test cases for RAGResource."""

    def test_init(self):
        """Test basic initialization."""
        sources = ["test.txt"]
        resource = RAGResource(sources=sources)
        assert resource.sources == sources
        assert resource._is_ready is False

    @pytest.mark.asyncio
    async def test_initialize_basic(self):
        """Test basic initialization."""
        sources = ["test.txt"]
        resource = RAGResource(sources=sources)

        # Mock the orchestrator
        mock_orchestrator = Mock()
        mock_orchestrator._preprocess = Mock()
        resource._orchestrator = mock_orchestrator

        await resource.initialize()

        assert resource._is_ready is True
        mock_orchestrator._preprocess.assert_called_once_with(sources, False)

    @pytest.mark.asyncio
    async def test_retrieve_basic(self):
        """Test basic retrieval."""
        sources = ["test.txt"]
        resource = RAGResource(sources=sources)
        resource._is_ready = True

        # Mock orchestrator response
        mock_node = Mock(spec=NodeWithScore)
        mock_node.node = Mock()
        mock_node.node.get_content.return_value = "Test content"

        mock_orchestrator = Mock()
        mock_orchestrator.retrieve = AsyncMock(return_value=[mock_node])
        resource._orchestrator = mock_orchestrator

        result = await resource.query("test query")

        # RAGResource returns a string, not a list
        assert result == "Test content"
        mock_orchestrator.retrieve.assert_called_once_with("test query", 10)
