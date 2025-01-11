"""Tests for FileResource."""

import os
from pathlib import Path

import pytest

from dxa.core.resource import FileResource
from dxa.core.resource.base_resource import ResourceResponse


@pytest.fixture
def docs_path() -> str:
    """Get path to docs/requirements directory."""
    # Start from test file location and navigate to repo root
    current_dir = Path(__file__).parent
    repo_root = current_dir.parent.parent.parent
    return str(repo_root / "docs" / "requirements")


@pytest.mark.asyncio
async def test_file_resource_basic(docs_path: str):
    """Test basic FileResource functionality."""
    # Create resource
    resource = FileResource(path=docs_path)
    
    # Test initial state
    assert not resource.is_available
    assert os.path.basename(docs_path) in resource.name
    assert resource.overview  # Should have some content
    
    # Test initialization
    await resource.initialize()
    assert resource.is_available
    
    # Test querying
    request = {"question": "What are the main requirements?"}
    response = await resource.query(request)
    assert isinstance(response, ResourceResponse)
    assert response.success
    
    # Test can_handle
    assert resource.can_handle({"question": "test"})
    assert not resource.can_handle({"not_a_question": "test"})
    
    # Test cleanup
    await resource.cleanup()
    assert not resource.is_available
