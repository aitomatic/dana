"""
Pytest configuration for RAG pipeline tests.

This file contains common fixtures and configuration for testing
the RAG pipeline components.
"""

import shutil
import tempfile
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def temp_test_dir():
    """Create a temporary directory for test files that persists for the session."""
    temp_dir = Path(tempfile.mkdtemp(prefix="rag_pipeline_tests_"))
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_documents():
    """Create sample Document objects for testing."""
    from llama_index.core import Document
    
    return [
        Document(
            text="This is the first test document. It contains some sample content for testing purposes.",
            metadata={"source": "doc1.txt", "author": "test", "type": "sample"}
        ),
        Document(
            text="This is the second test document. It has different content but similar structure to the first one.",
            metadata={"source": "doc2.txt", "author": "test", "type": "sample"}
        ),
        Document(
            text="Short doc.",
            metadata={"source": "doc3.txt", "author": "test", "type": "short"}
        ),
    ]


@pytest.fixture
def long_document():
    """Create a long document that will definitely need chunking."""
    from llama_index.core import Document
    
    long_text = (
        "This is a very long document that is designed to test the chunking functionality. " * 50 +
        "It contains many sentences that repeat the same basic structure. " * 30 +
        "The purpose is to ensure that the document will be split into multiple chunks. " * 40 +
        "Each chunk should preserve the original metadata while adding chunk-specific information. " * 25
    )
    
    return Document(
        text=long_text,
        metadata={
            "source": "long_document.txt", 
            "author": "test_author",
            "type": "long",
            "category": "test"
        }
    )


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires real file I/O)"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically mark integration tests."""
    for item in items:
        # Mark integration tests
        if "integration" in item.nodeid.lower() or "Integration" in item.name:
            item.add_marker(pytest.mark.integration)
        
        # Mark slow tests
        if "slow" in item.nodeid.lower() or "Slow" in item.name:
            item.add_marker(pytest.mark.slow) 