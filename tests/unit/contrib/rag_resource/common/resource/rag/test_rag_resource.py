"""
Simple tests for RAGResource class.
"""

from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest
from llama_index.core.schema import NodeWithScore

from dana.common.exceptions import EmbeddingError
from dana.common.sys_resource.embedding.embedding_utils import has_embedding_api_keys
from dana.common.sys_resource.rag.rag_resource import RAGResource


class TestRAGResource:
    """Simple test cases for RAGResource."""

    def test_init(self):
        """Test basic initialization."""
        if has_embedding_api_keys():
            # If API keys are available, test normal initialization
            sources = ["test.txt"]
            resource = RAGResource(sources=sources)
            # Sources should be resolved to absolute paths
            expected_sources = [str(Path("test.txt").resolve())]
            assert resource.sources == expected_sources
            assert resource._is_ready is False
        else:
            # If no API keys, expect EmbeddingError during initialization
            with pytest.raises(EmbeddingError):
                sources = ["test.txt"]
                RAGResource(sources=sources)

    @pytest.mark.asyncio
    async def test_initialize_basic(self):
        """Test basic initialization."""
        if has_embedding_api_keys():
            # If API keys are available, test normal behavior
            sources = ["test.txt"]
            resource = RAGResource(sources=sources)

            # Mock the orchestrator
            mock_orchestrator = Mock()
            mock_orchestrator._preprocess = Mock()
            resource._orchestrator = mock_orchestrator

            await resource.initialize()

            assert resource._is_ready is True
            # The _preprocess call should use resolved absolute paths
            expected_sources = [str(Path("test.txt").resolve())]
            mock_orchestrator._preprocess.assert_called_once_with(expected_sources, False)
        else:
            # If no API keys, expect EmbeddingError during initialization
            with pytest.raises(EmbeddingError):
                sources = ["test.txt"]
                RAGResource(sources=sources)

    @pytest.mark.asyncio
    async def test_retrieve_basic(self):
        """Test basic retrieval."""
        if has_embedding_api_keys():
            # If API keys are available, test normal behavior
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
        else:
            # If no API keys, expect EmbeddingError during initialization
            with pytest.raises(EmbeddingError):
                sources = ["test.txt"]
                RAGResource(sources=sources)
