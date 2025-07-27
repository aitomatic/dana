"""Tests for API server services."""

import pytest

# Service functions (create_agent, get_agent, get_agents) don't exist in refactored API structure
# The obsolete TestAgentServices class has been removed


def test_agent_generation_endpoint(client):
    """Test the agent generation endpoint."""
    from dana.api.core.schemas import AgentGenerationRequest, MessageData

    # Test data
    messages = [
        MessageData(role="user", content="I need an agent that can help me with weather information"),
        MessageData(role="assistant", content="I can help you create a weather agent. What specific weather features do you need?"),
        MessageData(role="user", content="I want it to get current weather and provide recommendations based on conditions"),
    ]

    # Create mock agent data for Phase 2 (code_generation requires agent_data)
    agent_data = {
        "id": 1,
        "name": "WeatherAgent",
        "description": "A weather information agent",
        "folder_path": "/tmp/test_agent",
        "generation_metadata": {"conversation_context": []},
    }

    request_data = AgentGenerationRequest(messages=messages, phase="code_generation", agent_data=agent_data)

    # Make request to the endpoint
    response = client.post("/api/agents/generate", json=request_data.model_dump())

    # Check response
    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "success" in data
    assert "dana_code" in data
    assert "phase" in data

    # Check phase-specific behavior
    if data["phase"] == "description":
        # Phase 1: No dana_code, but should have agent info
        assert data["dana_code"] is None
        assert data["agent_name"] is not None
        assert data["agent_description"] is not None
    else:
        # Phase 2: Should have generated code
        if data["success"]:
            assert data["dana_code"] is not None
            assert len(data["dana_code"]) > 0

            # Check if it contains basic Dana structure (new agent syntax)
            dana_code = data["dana_code"]
            assert "agent " in dana_code
            assert "name : str =" in dana_code
            assert "description : str =" in dana_code
            assert "def solve" in dana_code


def test_agent_generation_endpoint_mock_mode(client, monkeypatch):
    """Test the agent generation endpoint with mock mode enabled."""
    from dana.api.core.schemas import AgentGenerationRequest, MessageData

    # Enable mock mode
    monkeypatch.setenv("DANA_MOCK_AGENT_GENERATION", "true")

    # Test data
    messages = [
        MessageData(role="user", content="I need an agent that can help me with weather information"),
        MessageData(role="assistant", content="I can help you create a weather agent. What specific weather features do you need?"),
        MessageData(role="user", content="I want it to get current weather and provide recommendations based on conditions"),
    ]

    # Create mock agent data for Phase 2 (code_generation requires agent_data)
    agent_data = {
        "id": 1,
        "name": "WeatherAgent",
        "description": "A weather information agent",
        "folder_path": "/tmp/test_agent_mock",
        "generation_metadata": {"conversation_context": []},
    }

    request_data = AgentGenerationRequest(messages=messages, phase="code_generation", agent_data=agent_data)

    # Make request to the endpoint
    response = client.post("/api/agents/generate", json=request_data.model_dump())

    # Check response
    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "success" in data
    assert "dana_code" in data
    assert "phase" in data

    # Check phase-specific behavior
    if data["phase"] == "description":
        # Phase 1: No dana_code, but should have agent info
        assert data["dana_code"] is None
        assert data["agent_name"] is not None
        assert data["agent_description"] is not None
    else:
        # Phase 2: Should have generated code
        assert data["success"] is True
        assert data["dana_code"] is not None
        assert len(data["dana_code"]) > 0

        # Check if it contains weather agent structure
        dana_code = data["dana_code"]
        assert "Weather Information Agent" in dana_code
        assert "agent WeatherAgent:" in dana_code
        assert "name : str =" in dana_code
        assert "description : str =" in dana_code
        assert "def solve" in dana_code

        # Verify extracted name and description
        assert data["agent_name"] == "Weather Information Agent"
        assert "weather information" in data["agent_description"].lower()


@pytest.mark.skip(reason="Skipping test_agent_generation_with_current_code")
def test_agent_generation_with_current_code(client, monkeypatch):
    """Test the agent generation endpoint with current code for iterative improvements."""
    from dana.api.core.schemas import AgentGenerationRequest, MessageData

    # Enable mock mode
    monkeypatch.setenv("DANA_MOCK_AGENT_GENERATION", "true")

    # Test data with current code
    messages = [MessageData(role="user", content="Add email functionality to this agent")]

    current_code = '''"""Basic agent."""

# Agent Card declaration
agent BasicAgent:
    name : str = "Basic Agent"
    description : str = "A basic agent"
    resources : list = []

# Agent's problem solver
def solve(basic_agent : BasicAgent, problem : str):
    return reason(f"Help me with: {problem}")'''

    request_data = AgentGenerationRequest(messages=messages, current_code=current_code)

    # Make request to the endpoint
    response = client.post("/api/agents/generate", json=request_data.model_dump())

    # Check response
    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "success" in data
    assert "dana_code" in data
    assert "phase" in data

    # Check phase-specific behavior
    if data["phase"] == "description":
        # Phase 1: No dana_code, but should have agent info
        assert data["dana_code"] is None
        assert data["agent_name"] is not None
        assert data["agent_description"] is not None
    else:
        # Phase 2: Should have generated code
        assert data["success"] is True
        assert data["dana_code"] is not None
        assert len(data["dana_code"]) > 0

        # Check if it contains email agent structure (should improve based on new requirement)
        dana_code = data["dana_code"]
        assert "Email Assistant Agent" in dana_code
        assert "agent EmailAgent:" in dana_code
        assert "email_knowledge" in dana_code
        assert 'use("rag"' in dana_code
