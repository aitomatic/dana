"""Tests for API server services."""

import pytest

# Skip this entire test file as the service functions it tests don't exist in the refactored API
pytestmark = pytest.mark.skip(reason="Service functions (create_agent, get_agent, get_agents) don't exist in refactored API structure")

from sqlalchemy.orm import Session

from dana.api.core.schemas import AgentCreate


class TestAgentServices:
    """Test the agent service functions."""

    def test_create_agent(self, db_session: Session):
        """Test creating an agent."""
        agent_data = AgentCreate(name="Test Agent", description="A test agent", config={"model": "gpt-4", "temperature": 0.7})

        created_agent = create_agent(db_session, agent_data)

        assert created_agent.id is not None
        assert created_agent.name == "Test Agent"
        assert created_agent.description == "A test agent"
        assert created_agent.config == {"model": "gpt-4", "temperature": 0.7}

        # Verify it was actually saved to the database
        db_session.refresh(created_agent)
        assert created_agent.id is not None

    def test_get_agent_existing(self, db_session: Session):
        """Test getting an existing agent."""
        # Create an agent first
        agent_data = AgentCreate(name="Test Agent", description="A test agent", config={"model": "gpt-4"})
        created_agent = create_agent(db_session, agent_data)

        # Retrieve the agent
        retrieved_agent = get_agent(db_session, created_agent.id)

        assert retrieved_agent is not None
        assert retrieved_agent.id == created_agent.id
        assert retrieved_agent.name == "Test Agent"
        assert retrieved_agent.description == "A test agent"
        assert retrieved_agent.config == {"model": "gpt-4"}

    def test_get_agent_nonexistent(self, db_session: Session):
        """Test getting a non-existent agent."""
        agent = get_agent(db_session, 999)
        assert agent is None

    def test_get_agents_empty(self, db_session: Session):
        """Test getting agents when database is empty."""
        agents = get_agents(db_session)
        assert agents == []

    def test_get_agents_with_data(self, db_session: Session):
        """Test getting agents with data."""
        # Create multiple agents
        agent1_data = AgentCreate(name="Agent 1", description="First agent", config={"model": "gpt-4"})
        agent2_data = AgentCreate(name="Agent 2", description="Second agent", config={"model": "claude-3"})

        create_agent(db_session, agent1_data)
        create_agent(db_session, agent2_data)

        # Get all agents
        agents = get_agents(db_session)

        assert len(agents) == 2
        assert agents[0].name == "Agent 1"
        assert agents[1].name == "Agent 2"

    def test_get_agents_with_pagination(self, db_session: Session):
        """Test getting agents with pagination."""
        # Create 5 agents
        for i in range(5):
            agent_data = AgentCreate(name=f"Agent {i}", description=f"Agent number {i}", config={"model": f"model-{i}"})
            create_agent(db_session, agent_data)

        # Test limit
        agents = get_agents(db_session, limit=3)
        assert len(agents) == 3

        # Test skip
        agents = get_agents(db_session, skip=2, limit=2)
        assert len(agents) == 2
        assert agents[0].name == "Agent 2"
        assert agents[1].name == "Agent 3"

    def test_create_agent_with_empty_config(self, db_session: Session):
        """Test creating an agent with empty config."""
        agent_data = AgentCreate(name="Empty Config Agent", description="Agent with empty config", config={})

        created_agent = create_agent(db_session, agent_data)

        assert created_agent.name == "Empty Config Agent"
        assert created_agent.config == {}

    def test_create_agent_with_complex_config(self, db_session: Session):
        """Test creating an agent with complex nested config."""
        complex_config = {
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 1000,
            "nested": {"key": "value", "array": [1, 2, 3], "boolean": True},
        }

        agent_data = AgentCreate(name="Complex Config Agent", description="Agent with complex config", config=complex_config)

        created_agent = create_agent(db_session, agent_data)

        assert created_agent.config == complex_config
        assert created_agent.config["nested"]["array"] == [1, 2, 3]
        assert created_agent.config["nested"]["boolean"] is True

    def test_create_agent_with_selected_knowledge(self, db_session: Session, tmp_path):
        """Test creating an agent with selected knowledge (documents)."""
        import shutil
        from pathlib import Path

        # Create a test document in the database
        from dana.api.core.models import Document

        # Create test file
        test_file_path = tmp_path / "test_document.txt"
        test_file_path.write_text("This is a test document content")

        # Create document record
        document = Document(
            filename="test_document.txt",
            original_filename="test_document.txt",
            file_path="2025/01/27/test_document.txt",
            file_size=len(test_file_path.read_text()),
            mime_type="text/plain",
        )
        db_session.add(document)
        db_session.commit()

        # Create uploads directory structure
        uploads_dir = Path("./uploads")
        uploads_dir.mkdir(exist_ok=True)
        date_dir = uploads_dir / "2025" / "01" / "27"
        date_dir.mkdir(parents=True, exist_ok=True)

        # Copy test file to uploads directory
        shutil.copy2(test_file_path, date_dir / "test_document.txt")

        # Create agent with selected knowledge
        agent_data = AgentCreate(
            name="Knowledge Agent",
            description="Agent with selected documents",
            config={
                "avatar": "/agent-avatar-1.svg",
                "dana_code": "query = 'Hi'\nresponse = reason(f'Help me: {query}')",
                "selectedKnowledge": {"topics": [], "documents": [document.id]},
            },
        )

        created_agent = create_agent(db_session, agent_data)

        # Verify agent was created
        assert created_agent.name == "Knowledge Agent"
        assert created_agent.config["selectedKnowledge"]["documents"] == [document.id]

        # Verify agent folder was created
        agent_folder = Path(f"./uploads/agents/{created_agent.id}")
        assert agent_folder.exists()

        # Verify file was copied to agent folder
        copied_file = agent_folder / "test_document.txt"
        assert copied_file.exists()
        assert copied_file.read_text() == "This is a test document content"

        # Verify document record was updated
        db_session.refresh(document)
        assert document.agent_id == created_agent.id
        assert document.file_path == f"agents/{created_agent.id}/test_document.txt"

        # Cleanup
        shutil.rmtree(agent_folder, ignore_errors=True)
        shutil.rmtree(uploads_dir, ignore_errors=True)

    def test_agent_generation_endpoint(self, client):
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

    def test_agent_generation_endpoint_mock_mode(self, client, monkeypatch):
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
    def test_agent_generation_with_current_code(self, client, monkeypatch):
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
