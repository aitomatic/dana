"""
Simple tests for Retriever class.
"""

from unittest.mock import Mock

import pytest
from llama_index.core import VectorStoreIndex
from llama_index.core.schema import NodeWithScore

from opendxa.contrib.rag_resource.common.resource.rag.pipeline.retriever import Retriever


class TestRetriever:
    """Simple test cases for Retriever."""

    def test_init(self):
        """Test basic initialization."""
        mock_index = Mock(spec=VectorStoreIndex)
        retriever = Retriever(mock_index)
        assert retriever._index is mock_index

    def test_retrieve_basic(self):
        """Test basic retrieval functionality."""
        # Create mock index and retriever
        mock_index = Mock(spec=VectorStoreIndex)
        mock_index_retriever = Mock()
        mock_index.as_retriever.return_value = mock_index_retriever
        
        # Mock retrieval result
        mock_node = Mock(spec=NodeWithScore)
        mock_index_retriever.retrieve.return_value = [mock_node]
        
        retriever = Retriever(mock_index)
        result = retriever.retrieve("test query", num_results=5)
        
        # Should return the mock result
        assert result == [mock_node]
        mock_index.as_retriever.assert_called_once_with(similarity_top_k=5)
        mock_index_retriever.retrieve.assert_called_once_with("test query")

    @pytest.mark.asyncio
    async def test_aretrieve_basic(self):
        """Test basic async retrieval functionality."""
        # Create mock index and retriever
        mock_index = Mock(spec=VectorStoreIndex)
        mock_index_retriever = Mock()
        mock_index.as_retriever.return_value = mock_index_retriever
        
        # Mock async retrieval result - need AsyncMock for async method
        from unittest.mock import AsyncMock
        mock_node = Mock(spec=NodeWithScore)
        mock_index_retriever.aretrieve = AsyncMock(return_value=[mock_node])
        
        retriever = Retriever(mock_index)
        result = await retriever.aretrieve("test query", num_results=3)
        
        # Should return the mock result
        assert result == [mock_node]
        mock_index.as_retriever.assert_called_once_with(similarity_top_k=3)
        mock_index_retriever.aretrieve.assert_called_once_with("test query") 