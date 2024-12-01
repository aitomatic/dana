import pytest
from unittest.mock import patch
from dxa.core.resource.human_resource import HumanResource, ResourceError

@pytest.fixture
async def human_resource():
    """Fixture providing a test human resource instance."""
    resource = HumanResource(name="test_human", role="user")
    await resource.initialize()
    yield resource
    await resource.cleanup()

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

@pytest.mark.asyncio
async def test_can_handle():
    """Test request handling capability check."""
    human = HumanResource(name="test", role="user")
    await human.initialize()
    
    assert human.can_handle({}) is True  # Empty dict is valid
    assert human.can_handle({"prompt": "test"}) is True
    assert human.can_handle(None) is False  # None is invalid
    assert human.can_handle("invalid") is False  # String is invalid
    
    await human.cleanup()
    assert human.can_handle({}) is False  # Resource unavailable after cleanup

@pytest.mark.asyncio
@patch('builtins.input', return_value="test response")
async def test_human_query(mock_input, human_resource):
    """Test human query functionality."""
    response = await human_resource.query({
        "prompt": "Please provide input"
    })
    
    assert response["success"] is True
    assert response["response"] == "test response"
    mock_input.assert_called_once()

@pytest.mark.asyncio
@patch('builtins.input', side_effect=EOFError)
async def test_human_query_error(mock_input, human_resource):
    """Test human query error handling."""
    with pytest.raises(ResourceError):
        await human_resource.query({
            "prompt": "Please provide input"
        })

@pytest.mark.asyncio
async def test_human_query_no_prompt(human_resource):
    """Test query with no prompt."""
    with patch('builtins.input', return_value="test response") as mock_input:
        response = await human_resource.query({})
        assert response["success"] is True
        assert response["response"] == "test response"
        mock_input.assert_called_once()

@pytest.mark.asyncio
async def test_human_query_invalid_request(human_resource):
    """Test query with invalid request format."""
    with pytest.raises(ResourceError):
        await human_resource.query(None)  # None is invalid request format 