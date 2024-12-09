"""Tests for the human resource implementation.

This module contains tests for the HumanResource class, which handles
human-in-the-loop interactions within the DXA framework.
"""

from unittest.mock import patch

import pytest

from dxa.core.resource.human_resource import HumanResource, ResourceError

@pytest.fixture
def human_resource():
    """Fixture providing a test human resource instance."""
    return HumanResource(
        name="test_human",
        role="user"
    )

@pytest.mark.asyncio
async def test_human_initialization():
    """Test human resource initialization."""
    human = HumanResource(name="test", role="expert")
    assert human.name == "test"
    assert human.role == "expert"
    assert not human.is_available  # Should be False before initialization
    
    await human.initialize()
    assert human.is_available  # Should be True after initialization
    
    await human.cleanup()
    assert not human.is_available  # Should be False after cleanup

# pylint: disable=redefined-outer-name
@pytest.mark.asyncio
@patch('builtins.input', return_value="test response")
async def test_human_query(mock_input, human_resource):
    """Test human query functionality."""
    await human_resource.initialize()
    response = await human_resource.query({
        "prompt": "Please provide input"
    })
    
    assert response.success is True
    assert response.response == "test response"
    mock_input.assert_called_once()

@pytest.mark.asyncio
@patch('builtins.input', side_effect=EOFError)
async def test_human_query_error(mock_input, human_resource):
    """Test human query error handling."""
    with pytest.raises(ResourceError):
        await human_resource.query({
            "prompt": "Please provide input"
        })
    mock_input.assert_called_once()

@pytest.mark.asyncio
async def test_human_query_no_prompt(human_resource):
    """Test query with no prompt."""
    await human_resource.initialize()
    with patch('builtins.input', return_value="test response") as mock_input:
        response = await human_resource.query({})
        assert response.success is True
        assert response.response == "test response"
        mock_input.assert_called_once()

@pytest.mark.asyncio
async def test_human_query_invalid_request(human_resource):
    """Test query with invalid request format."""
    await human_resource.initialize()
    with pytest.raises(ResourceError):
        await human_resource.query(None)  # None is invalid request format 