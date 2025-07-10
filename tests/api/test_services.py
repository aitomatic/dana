"""Tests for API server services."""

from sqlalchemy.orm import Session

from dana.api.server.schemas import AgentCreate
from dana.api.server.services import create_agent, get_agent, get_agents


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
