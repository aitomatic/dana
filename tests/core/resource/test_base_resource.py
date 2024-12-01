"""Tests for the base resource implementation."""

from typing import Dict, Any
import pytest
from dxa.core.resource.base_resource import (
    BaseResource,
    ResourceError,
    ResourceUnavailableError,
    ResourceAccessError
)

class MockResource(BaseResource):
    """Mock implementation of BaseResource for testing."""
    
    async def initialize(self) -> None:
        """Initialize the resource."""
        self._is_available = True

    async def cleanup(self) -> None:
        """Clean up the resource."""
        self._is_available = False

    async def query(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Test query implementation."""
        if not self.can_handle(request):
            raise ResourceError("Cannot handle request")
        return {"success": True}

    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Test can_handle implementation."""
        return self._is_available and isinstance(request, dict)

@pytest.fixture
async def test_base_resource():
    """Fixture providing a test resource instance."""
    resource = MockResource(name="test_resource", description="Test resource")
    yield resource
    await resource.cleanup()

@pytest.mark.asyncio
async def test_resource_initialization():
    """Test basic resource initialization."""
    test_resource = MockResource(name="test", description="Test description")
    assert test_resource.name == "test"
    assert test_resource.description == "Test description"
    assert test_resource.config == {}
    assert test_resource.is_available is True

@pytest.mark.asyncio
async def test_resource_lifecycle():
    """Test resource initialization and cleanup."""
    test_resource = MockResource(name="test", description="Test description")
    assert test_resource.is_available is True
    await test_resource.initialize()
    assert test_resource.is_available is True
    await test_resource.cleanup()
    assert test_resource.is_available is False

@pytest.mark.asyncio
async def test_resource_context_manager():
    """Test resource usage with context manager."""
    async with MockResource(name="test") as test_resource:
        assert test_resource.is_available is True
    assert test_resource.is_available is False

@pytest.mark.asyncio
async def test_resource_error_handling():
    """Test resource error classes."""
    with pytest.raises(ResourceError):
        raise ResourceError("Test error")
    
    with pytest.raises(ResourceUnavailableError):
        raise ResourceUnavailableError("Resource unavailable")
    
    with pytest.raises(ResourceAccessError):
        raise ResourceAccessError("Access denied") 