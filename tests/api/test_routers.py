"""Tests for API server routers."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from dana.api.server.server import create_app
from dana.api.server.models import Agent
from dana.api.server.schemas import AgentCreate
from dana.api.server.db import Base, engine, SessionLocal


@pytest.fixture
def client():
    """Create a test client."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def db_session():
    """Create a test database session."""
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


class TestMainRouter:
    """Test the main router endpoints."""

    def test_health_endpoint(self, client):
        """Test the health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Dana API"

    def test_root_endpoint_no_static_files(self, client):
        """Test root endpoint when no static files exist."""
        response = client.get("/")
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert "index.html not found" in data["error"]


class TestAgentRouter:
    """Test the agent router endpoints."""

    def test_list_agents_empty(self, client, db_session):
        """Test listing agents when database is empty."""
        response = client.get("/agents/")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_list_agents_with_data(self, client, db_session):
        """Test listing agents with data."""
        # Create test agents directly in database
        agent1 = Agent(name="Agent 1", description="First agent", config={"model": "gpt-4"})
        agent2 = Agent(name="Agent 2", description="Second agent", config={"model": "claude-3"})

        db_session.add(agent1)
        db_session.add(agent2)
        db_session.commit()

        response = client.get("/agents/")
        assert response.status_code == 200
        data = response.json()

        assert len(data) == 2
        assert data[0]["name"] == "Agent 1"
        assert data[1]["name"] == "Agent 2"

    def test_list_agents_with_pagination(self, client, db_session):
        """Test listing agents with pagination."""
        # Create 5 agents
        for i in range(5):
            agent = Agent(name=f"Agent {i}", description=f"Agent {i}", config={"model": f"model-{i}"})
            db_session.add(agent)
        db_session.commit()

        # Test with limit
        response = client.get("/agents/?limit=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

        # Test with skip
        response = client.get("/agents/?skip=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Agent 2"
        assert data[1]["name"] == "Agent 3"

    def test_get_agent_existing(self, client, db_session):
        """Test getting an existing agent."""
        # Create a test agent
        agent = Agent(name="Test Agent", description="A test agent", config={"model": "gpt-4"})
        db_session.add(agent)
        db_session.commit()
        db_session.refresh(agent)

        response = client.get(f"/agents/{agent.id}")
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == agent.id
        assert data["name"] == "Test Agent"
        assert data["description"] == "A test agent"
        assert data["config"] == {"model": "gpt-4"}

    def test_get_agent_nonexistent(self, client, db_session):
        """Test getting a non-existent agent."""
        response = client.get("/agents/999")
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Agent not found"

    def test_create_agent_valid(self, client, db_session):
        """Test creating an agent with valid data."""
        agent_data = {"name": "New Agent", "description": "A new test agent", "config": {"model": "gpt-4", "temperature": 0.7}}

        response = client.post("/agents/", json=agent_data)
        assert response.status_code == 200
        data = response.json()

        assert data["name"] == "New Agent"
        assert data["description"] == "A new test agent"
        assert data["config"] == {"model": "gpt-4", "temperature": 0.7}
        assert "id" in data
        assert isinstance(data["id"], int)

    def test_create_agent_invalid_data(self, client):
        """Test creating an agent with invalid data."""
        # Missing required fields
        invalid_data = {"name": "Test Agent"}

        response = client.post("/agents/", json=invalid_data)
        assert response.status_code == 422  # Validation error

    def test_create_agent_empty_config(self, client, db_session):
        """Test creating an agent with empty config."""
        agent_data = {"name": "Empty Config Agent", "description": "Agent with empty config", "config": {}}

        response = client.post("/agents/", json=agent_data)
        assert response.status_code == 200
        data = response.json()

        assert data["name"] == "Empty Config Agent"
        assert data["config"] == {}

    def test_create_agent_complex_config(self, client, db_session):
        """Test creating an agent with complex config."""
        complex_config = {
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 1000,
            "nested": {"key": "value", "array": [1, 2, 3], "boolean": True},
        }

        agent_data = {"name": "Complex Config Agent", "description": "Agent with complex config", "config": complex_config}

        response = client.post("/agents/", json=agent_data)
        assert response.status_code == 200
        data = response.json()

        assert data["config"] == complex_config
        assert data["config"]["nested"]["array"] == [1, 2, 3]
        assert data["config"]["nested"]["boolean"] is True
