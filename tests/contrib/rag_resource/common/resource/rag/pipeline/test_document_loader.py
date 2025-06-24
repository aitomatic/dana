"""
Unit tests for DocumentLoader class.

Tests document loading, preprocessing, and error handling functionality.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, List

from llama_index.core import Document
from opendxa.contrib.rag_resource.common.resource.rag.pipeline.document_loader import DocumentLoader


class TestDocumentLoader:
    """Test DocumentLoader functionality."""

    def test_init_default_params(self):
        """Test DocumentLoader initialization with default parameters."""
        loader = DocumentLoader()
        
        assert loader._NAME == "doc_loader"
        assert loader._local_loader is not None
        assert loader._web_loader is not None
        assert loader.SUPPORTED_TYPES is not None

    @pytest.mark.asyncio
    async def test_load_sources_local_files(self, sample_documents):
        """Test loading local files only."""
        loader = DocumentLoader()
        
        with patch.object(loader._local_loader, 'load') as mock_local_load, \
             patch.object(loader._web_loader, 'load') as mock_web_load:
            
            # Setup mock to return different documents for different sources
            mock_local_load.side_effect = [
                [sample_documents[0]],  # source1
                [sample_documents[1]]   # source2
            ]
            
            sources = ["file1.txt", "file2.txt"]
            result = await loader.load_sources(sources)
            
            assert len(result) == 2
            assert "file1.txt" in result
            assert "file2.txt" in result
            assert len(result["file1.txt"]) == 1
            assert len(result["file2.txt"]) == 1
            
            # Verify local loader was called, web loader was not
            assert mock_local_load.call_count == 2
            mock_web_load.assert_not_called()

    @pytest.mark.asyncio
    async def test_load_sources_web_urls(self, sample_documents):
        """Test loading web URLs only."""
        loader = DocumentLoader()
        
        with patch.object(loader._local_loader, 'load') as mock_local_load, \
             patch.object(loader._web_loader, 'load') as mock_web_load:
            
            # Setup mock to return different documents for different URLs
            mock_web_load.side_effect = [
                [sample_documents[0]],  # URL1
                [sample_documents[1]]   # URL2
            ]
            
            sources = ["https://example1.com", "https://example2.com"]
            result = await loader.load_sources(sources)
            
            assert len(result) == 2
            assert "https://example1.com" in result
            assert "https://example2.com" in result
            
            # Verify web loader was called, local loader was not
            assert mock_web_load.call_count == 2
            mock_local_load.assert_not_called()

    @pytest.mark.asyncio
    async def test_load_sources_mixed_sources(self, sample_documents):
        """Test loading mixed local and web sources."""
        loader = DocumentLoader()
        
        with patch.object(loader._local_loader, 'load') as mock_local_load, \
             patch.object(loader._web_loader, 'load') as mock_web_load:
            
            mock_local_load.return_value = [sample_documents[0]]
            mock_web_load.return_value = [sample_documents[1]]
            
            sources = ["file.txt", "https://example.com"]
            result = await loader.load_sources(sources)
            
            assert len(result) == 2
            assert "file.txt" in result
            assert "https://example.com" in result
            
            # Verify both loaders were called
            mock_local_load.assert_called_once_with("file.txt")
            mock_web_load.assert_called_once_with("https://example.com")

    @pytest.mark.asyncio
    async def test_load_sources_empty_list(self):
        """Test loading empty source list."""
        loader = DocumentLoader()
        
        result = await loader.load_sources([])
        
        assert result == {}

    @pytest.mark.asyncio
    async def test_load_method_local_source(self, sample_documents):
        """Test _load method with local source."""
        loader = DocumentLoader()
        
        with patch.object(loader._local_loader, 'load', return_value=sample_documents) as mock_local, \
             patch.object(loader._web_loader, 'load') as mock_web:
            
            result = await loader._load("file.txt")
            
            assert result == sample_documents
            mock_local.assert_called_once_with("file.txt")
            mock_web.assert_not_called()

    @pytest.mark.asyncio
    async def test_load_method_web_source(self, sample_documents):
        """Test _load method with web source."""
        loader = DocumentLoader()
        
        with patch.object(loader._local_loader, 'load') as mock_local, \
             patch.object(loader._web_loader, 'load', return_value=sample_documents) as mock_web:
            
            result = await loader._load("https://example.com")
            
            assert result == sample_documents
            mock_web.assert_called_once_with("https://example.com")
            mock_local.assert_not_called()

    @pytest.mark.asyncio
    async def test_load_sources_preserves_structure(self, sample_documents):
        """Test that load_sources preserves the sources-to-documents structure."""
        loader = DocumentLoader()
        
        with patch.object(loader._local_loader, 'load') as mock_local_load:
            
            mock_local_load.side_effect = [
                [sample_documents[0], sample_documents[1]],  # Multiple docs for source1
                [sample_documents[2]]                        # Single doc for source2
            ]
            
            sources = ["source1.txt", "source2.txt"]
            result = await loader.load_sources(sources)
            
            assert len(result) == 2
            assert len(result["source1.txt"]) == 2
            assert len(result["source2.txt"]) == 1
            assert result["source1.txt"] == [sample_documents[0], sample_documents[1]]
            assert result["source2.txt"] == [sample_documents[2]]

    @pytest.mark.asyncio
    async def test_error_handling_in_load(self, sample_documents):
        """Test error handling in load method."""
        loader = DocumentLoader()
        
        with patch.object(loader._local_loader, 'load', side_effect=Exception("Load error")):
            
            with pytest.raises(Exception, match="Load error"):
                await loader._load("error_file.txt")


class TestDocumentLoaderIntegration:
    """Integration tests for DocumentLoader."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_file_loading(self, temp_test_dir):
        """Test actual file loading with real files."""
        # Create test files
        test_file = temp_test_dir / "test.txt"
        test_file.write_text("This is test content for integration testing.")
        
        loader = DocumentLoader()
        sources = [str(test_file)]
        
        result = await loader.load_sources(sources)
        
        assert len(result) == 1
        assert str(test_file) in result
        assert len(result[str(test_file)]) >= 1
        
        # Check that document content was loaded
        docs = result[str(test_file)]
        assert any("test content" in doc.text for doc in docs)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_multiple_sources_integration(self, temp_test_dir):
        """Test loading multiple real sources."""
        # Create test files
        file1 = temp_test_dir / "doc1.txt"
        file1.write_text("Content of document one.")
        
        file2 = temp_test_dir / "doc2.txt"
        file2.write_text("Content of document two.")
        
        loader = DocumentLoader()
        sources = [str(file1), str(file2)]
        
        result = await loader.load_sources(sources)
        
        assert len(result) == 2
        assert str(file1) in result
        assert str(file2) in result
        
        # Verify content was loaded correctly
        docs1 = result[str(file1)]
        docs2 = result[str(file2)]
        
        assert any("document one" in doc.text for doc in docs1)
        assert any("document two" in doc.text for doc in docs2) 