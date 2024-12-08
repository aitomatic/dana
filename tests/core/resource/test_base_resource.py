"""Tests for the base resource implementation.

This module contains tests for the BaseResource class, which provides the
foundational interface and functionality for all DXA resources.
"""

from typing import Dict, Any
import pytest
import asyncio
from dxa.core.resource.base_resource import (
    BaseResource,
    ResourceError,
    ResourceUnavailableError,
    ResourceAccessError
)

class MockResource(BaseResource):
    """Mock implementation of BaseResource for testing."""
    
    def __init__(self, name: str, description: str = None, delay: float = 0):
        super().__init__(name=name, description=description)
        self._delay = delay
        self._query_count = 0
    
    async def initialize(self) -> None:
        """Initialize the resource."""
        self._is_available = True

    async def cleanup(self) -> None:
        """Clean up the resource."""
        self._is_available = False

    async def query(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Test query implementation with optional delay."""
        if not self.can_handle(request):
            raise ResourceError("Cannot handle request")
        if self._delay:
            await asyncio.sleep(self._delay)
        self._query_count += 1
        return {"success": True, "query_count": self._query_count}

    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Test can_handle implementation with validation."""
        if not isinstance(request, dict):
            return False
        if not self._is_available:
            return False
        # Complex validation: check for required fields and types
        if "type" in request and not isinstance(request["type"], str):
            return False
        if "data" in request and not isinstance(request["data"], (dict, list)):
            return False
        return True

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

@pytest.mark.asyncio
async def test_concurrent_access():
    """Test concurrent access to resource."""
    resource = MockResource(name="test", delay=0.1)
    await resource.initialize()
    
    async def make_request(request: Dict[str, Any]):
        return await resource.query(request)
    
    # Create multiple concurrent requests
    requests = [{"type": "test", "id": i} for i in range(5)]
    tasks = [make_request(req) for req in requests]
    
    # Execute requests concurrently
    responses = await asyncio.gather(*tasks)
    
    # Verify all requests were processed
    assert len(responses) == 5
    # Verify query count increased sequentially
    query_counts = [resp["query_count"] for resp in responses]
    assert sorted(query_counts) == list(range(1, 6))
    
    await resource.cleanup()

@pytest.mark.asyncio
async def test_state_transitions_during_query():
    """Test resource state transitions during query execution."""
    resource = MockResource(name="test", delay=0.1)
    await resource.initialize()
    
    # Start a long-running query
    query_task = asyncio.create_task(
        resource.query({"type": "long_running"})
    )
    
    # Wait briefly for query to start
    await asyncio.sleep(0.05)
    
    # Verify resource is still available during query
    assert resource.is_available is True
    
    # Try cleanup during active query
    cleanup_task = asyncio.create_task(resource.cleanup())
    
    # Wait for both tasks
    response = await query_task
    await cleanup_task
    
    # Verify query completed successfully before cleanup
    assert response["success"] is True
    assert resource.is_available is False

@pytest.mark.asyncio
async def test_complex_request_validation():
    """Test complex request validation scenarios."""
    resource = MockResource(name="test")
    await resource.initialize()
    
    # Valid requests
    assert resource.can_handle({"type": "test"}) is True
    assert resource.can_handle({"type": "test", "data": {"key": "value"}}) is True
    assert resource.can_handle({"type": "test", "data": [1, 2, 3]}) is True
    
    # Invalid requests
    assert resource.can_handle({"type": 123}) is False  # Wrong type field type
    assert resource.can_handle({"type": "test", "data": "invalid"}) is False  # Wrong data field type
    assert resource.can_handle(None) is False  # Not a dict
    
    # Test with actual queries
    valid_response = await resource.query({"type": "test", "data": {"key": "value"}})
    assert valid_response["success"] is True
    
    with pytest.raises(ResourceError):
        await resource.query({"type": 123})
    
    await resource.cleanup() 