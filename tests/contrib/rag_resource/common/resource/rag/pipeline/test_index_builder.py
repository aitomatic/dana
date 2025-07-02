"""
Unit tests for IndexBuilder class.

Tests individual index creation, error handling, and integration with documents.
"""

import os
from unittest.mock import Mock, patch

import pytest
from llama_index.core import VectorStoreIndex

from opendxa.contrib.rag_resource.common.resource.rag.pipeline.index_builder import IndexBuilder


# Helper function to check if OpenAI API key is available
def has_real_openai_api_key():
    """Check if OpenAI API key is available for integration tests."""
    api_key = os.getenv("OPENAI_API_KEY")
    # Check if we have a real API key, not just the test placeholder
    return bool(api_key) and api_key != "test-key" and not api_key.startswith("test")


def skip_if_no_real_openai_key():
    """Skip test if no real OpenAI API key is available."""
    if not has_real_openai_api_key():
        pytest.skip("Real OpenAI API key required for integration tests (not test-key)")


# Pytest fixture to skip tests requiring OpenAI API key (legacy - kept for compatibility)
openai_required = pytest.mark.skipif(
    not has_real_openai_api_key(), reason="Real OpenAI API key required for integration tests (not test-key)"
)


class TestIndexBuilder:
    """Test IndexBuilder functionality."""

    @pytest.fixture
    def sample_docs_by_source(self, sample_documents):
        """Create sample documents by source structure."""
        return {"source1": sample_documents[:2], "source2": [sample_documents[2]]}

    def test_init_default_params(self):
        """Test IndexBuilder initialization with default parameters."""
        builder = IndexBuilder()

        assert builder.sources_info == []
        assert builder._NAME == "index_builder"

    def test_init_custom_params(self):
        """Test IndexBuilder initialization with custom parameters."""
        sources_info = [("path1", True), ("path2", False)]
        builder = IndexBuilder(sources_info=sources_info)

        assert builder.sources_info == sources_info

    @pytest.mark.asyncio
    async def test_build_indices_success(self, sample_docs_by_source):
        """Test successful index building from documents."""
        builder = IndexBuilder()

        with patch("llama_index.core.VectorStoreIndex.from_documents") as mock_from_docs:
            # Setup mock to return different indices for different sources
            def mock_from_docs_side_effect(docs):
                mock_index = Mock(spec=VectorStoreIndex)
                mock_index.source_key = "mock_index_for_" + str(len(docs))
                return mock_index

            mock_from_docs.side_effect = mock_from_docs_side_effect

            result = await builder.build_indices(sample_docs_by_source)

            assert len(result) == 2
            assert "source1" in result
            assert "source2" in result
            assert all(isinstance(idx, Mock) for idx in result.values())

            # Verify VectorStoreIndex.from_documents was called for each source
            assert mock_from_docs.call_count == 2

    @pytest.mark.asyncio
    async def test_build_indices_empty_input(self):
        """Test build_indices with empty input raises ValueError."""
        builder = IndexBuilder()

        with pytest.raises(ValueError, match="docs_by_source cannot be empty"):
            await builder.build_indices({})

    @pytest.mark.asyncio
    async def test_build_indices_source_with_empty_documents(self, sample_docs_by_source):
        """Test build_indices with source containing empty document list."""
        builder = IndexBuilder()

        # Add source with empty documents
        sample_docs_by_source["empty_source"] = []

        with patch("llama_index.core.VectorStoreIndex.from_documents") as mock_from_docs:
            mock_index = Mock(spec=VectorStoreIndex)
            mock_from_docs.return_value = mock_index

            result = await builder.build_indices(sample_docs_by_source)

            # Should only create indices for non-empty sources
            assert len(result) == 2
            assert "source1" in result
            assert "source2" in result
            assert "empty_source" not in result

            # Verify VectorStoreIndex.from_documents was called only for non-empty sources
            assert mock_from_docs.call_count == 2

    @pytest.mark.asyncio
    async def test_build_indices_all_sources_empty_documents(self):
        """Test build_indices when all sources have empty documents."""
        builder = IndexBuilder()

        docs_by_source = {"empty1": [], "empty2": []}

        with pytest.raises(RuntimeError, match="No indices were successfully created from any source"):
            await builder.build_indices(docs_by_source)

    @pytest.mark.asyncio
    async def test_build_indices_logging(self, sample_docs_by_source):
        """Test that build_indices produces appropriate debug logs."""
        builder = IndexBuilder()

        with patch("llama_index.core.VectorStoreIndex.from_documents") as mock_from_docs, patch.object(builder, "debug") as mock_debug:
            mock_index = Mock(spec=VectorStoreIndex)
            mock_from_docs.return_value = mock_index

            await builder.build_indices(sample_docs_by_source)

            # Check that debug logging was called
            mock_debug.assert_any_call("Building indices for 2 sources")
            mock_debug.assert_any_call("Creating index for source source1 with 2 documents")
            mock_debug.assert_any_call("Creating index for source source2 with 1 documents")
            mock_debug.assert_any_call("Created 2 indices")

    @pytest.mark.asyncio
    async def test_build_indices_with_none_documents(self, sample_documents):
        """Test build_indices gracefully handles None in document lists."""
        builder = IndexBuilder()

        # Create docs_by_source with some None values mixed in
        docs_by_source = {
            "source1": sample_documents[:1] + [None] + sample_documents[1:2],  # Mix None with real docs
            "source2": [sample_documents[2]],
        }

        with patch("llama_index.core.VectorStoreIndex.from_documents") as mock_from_docs:
            mock_index = Mock(spec=VectorStoreIndex)
            mock_from_docs.return_value = mock_index

            result = await builder.build_indices(docs_by_source)

            # Should still create indices (LlamaIndex should handle None filtering)
            assert len(result) == 2
            assert mock_from_docs.call_count == 2

    @pytest.mark.asyncio
    async def test_build_indices_preserves_document_metadata(self, sample_documents):
        """Test that build_indices preserves document metadata."""
        builder = IndexBuilder()

        docs_by_source = {"source1": sample_documents}

        with patch("llama_index.core.VectorStoreIndex.from_documents") as mock_from_docs:
            mock_index = Mock(spec=VectorStoreIndex)
            mock_from_docs.return_value = mock_index

            await builder.build_indices(docs_by_source)

            # Verify that from_documents was called with the original documents
            call_args = mock_from_docs.call_args_list[0]
            passed_documents = call_args[0][0]  # First positional argument

            assert len(passed_documents) == len(sample_documents)
            for i, doc in enumerate(passed_documents):
                assert doc.text == sample_documents[i].text
                assert doc.metadata == sample_documents[i].metadata


class TestIndexBuilderIntegration:
    """Integration tests for IndexBuilder."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_index_creation(self, sample_documents):
        """Test actual index creation with real LlamaIndex components."""
        skip_if_no_real_openai_key()
        builder = IndexBuilder()

        docs_by_source = {"test_source": sample_documents}

        # This test uses real LlamaIndex - no mocking
        result = await builder.build_indices(docs_by_source)

        assert len(result) == 1
        assert "test_source" in result
        assert isinstance(result["test_source"], VectorStoreIndex)

        # Test that the index can actually be used for retrieval
        index = result["test_source"]
        retriever = index.as_retriever(similarity_top_k=1)
        nodes = retriever.retrieve("test")

        assert len(nodes) >= 0  # Should return some results or empty list

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_multiple_sources_real_indices(self, sample_documents, long_document):
        """Test creating indices for multiple sources with real LlamaIndex."""
        skip_if_no_real_openai_key()
        builder = IndexBuilder()

        docs_by_source = {"short_docs": sample_documents, "long_docs": [long_document]}

        result = await builder.build_indices(docs_by_source)

        assert len(result) == 2
        assert "short_docs" in result
        assert "long_docs" in result

        # Both should be real VectorStoreIndex objects
        for _source_key, index in result.items():
            assert isinstance(index, VectorStoreIndex)

        # Verify indices are independent and functional
        short_retriever = result["short_docs"].as_retriever(similarity_top_k=1)
        long_retriever = result["long_docs"].as_retriever(similarity_top_k=1)

        short_results = short_retriever.retrieve("test")
        long_results = long_retriever.retrieve("document")

        # Should be able to retrieve from both indices
        assert isinstance(short_results, list)
        assert isinstance(long_results, list)
