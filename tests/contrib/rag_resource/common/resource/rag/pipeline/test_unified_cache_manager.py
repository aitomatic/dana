"""
Simple tests for UnifiedCacheManager class.
"""

import os
import tempfile

import pytest
from llama_index.core import Document

from opendxa.contrib.rag_resource.common.resource.rag.pipeline.unified_cache_manager import UnifiedCacheManager


class TestUnifiedCacheManager:
    """Simple test cases for UnifiedCacheManager."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    def test_init(self, temp_cache_dir):
        """Test basic initialization."""
        manager = UnifiedCacheManager(temp_cache_dir)
        assert manager.cache_dir == temp_cache_dir
        assert os.path.exists(temp_cache_dir)

    @pytest.mark.asyncio
    async def test_cache_documents_basic(self, temp_cache_dir):
        """Test basic document caching."""
        manager = UnifiedCacheManager(temp_cache_dir)

        docs_by_source = {"test.txt": [Document(text="Test document")]}

        # Should not raise an error
        await manager.set_docs_by_source(docs_by_source)

    @pytest.mark.asyncio
    async def test_get_documents_empty(self, temp_cache_dir):
        """Test getting documents when cache is empty."""
        manager = UnifiedCacheManager(temp_cache_dir)

        result = await manager.get_docs_by_source(["test.txt"])
        assert result == {"test.txt": None}

    @pytest.mark.asyncio
    async def test_get_indices_empty(self, temp_cache_dir):
        """Test getting indices when cache is empty."""
        manager = UnifiedCacheManager(temp_cache_dir)

        result = await manager.get_indicies_by_source(["test.txt"])
        assert result == {"test.txt": None}

    @pytest.mark.asyncio
    async def test_get_combined_index_empty(self, temp_cache_dir):
        """Test getting combined index when cache is empty."""
        manager = UnifiedCacheManager(temp_cache_dir)

        result = await manager.get_combined_index(["test.txt"])
        assert result is None
