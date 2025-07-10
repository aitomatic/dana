"""Tests for API server routers."""

from dana.api.server.models import Agent

# Use the global client and db_session fixtures from conftest.py

class TestMainRouter:
    """Test the main router endpoints."""

    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Dana API"

    def test_root_endpoint_with_static_files(self, client):
        response = client.get("/")
        assert response.status_code == 200
        # Should serve index.html from static directory
        assert response.headers["content-type"] == "text/html; charset=utf-8"

class TestAgentRouter:
    """Test the agent router endpoints."""

    def test_list_agents_empty(self, client, db_session):
        response = client.get("/api/agents/")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_list_agents_with_data(self, client, db_session):
        # Create test agents directly in database
        agent1 = Agent(name="Agent 1", description="First agent", config={"model": "gpt-4"})
        agent2 = Agent(name="Agent 2", description="Second agent", config={"model": "claude-3"})
        db_session.add(agent1)
        db_session.add(agent2)
        db_session.commit()
        response = client.get("/api/agents/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Agent 1"
        assert data[1]["name"] == "Agent 2"

    def test_list_agents_with_pagination(self, client, db_session):
        # Create 5 agents
        for i in range(5):
            agent = Agent(name=f"Agent {i}", description=f"Agent {i}", config={"model": f"model-{i}"})
            db_session.add(agent)
        db_session.commit()
        # Test with limit
        response = client.get("/api/agents/?limit=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        # Test with skip
        response = client.get("/api/agents/?skip=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Agent 2"
        assert data[1]["name"] == "Agent 3"

    def test_get_agent_existing(self, client, db_session):
        # Create a test agent
        agent = Agent(name="Test Agent", description="A test agent", config={"model": "gpt-4"})
        db_session.add(agent)
        db_session.commit()
        db_session.refresh(agent)
        response = client.get(f"/api/agents/{agent.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == agent.id
        assert data["name"] == "Test Agent"
        assert data["description"] == "A test agent"
        assert data["config"] == {"model": "gpt-4"}

    def test_get_agent_nonexistent(self, client):
        response = client.get("/api/agents/999")
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Agent not found"

    def test_create_agent_valid(self, client, db_session):
        agent_data = {"name": "New Agent", "description": "A new test agent", "config": {"model": "gpt-4", "temperature": 0.7}}
        response = client.post("/api/agents/", json=agent_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Agent"
        assert data["description"] == "A new test agent"
        assert data["config"] == {"model": "gpt-4", "temperature": 0.7}
        assert "id" in data
        assert isinstance(data["id"], int)

    def test_create_agent_invalid_data(self, client):
        invalid_data = {"name": "Test Agent"}
        response = client.post("/api/agents/", json=invalid_data)
        assert response.status_code == 422  # Validation error

    def test_create_agent_empty_config(self, client, db_session):
        agent_data = {"name": "Empty Config Agent", "description": "Agent with empty config", "config": {}}
        response = client.post("/api/agents/", json=agent_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Empty Config Agent"
        assert data["config"] == {}

    def test_create_agent_complex_config(self, client, db_session):
        complex_config = {
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 1000,
            "nested": {"key": "value", "array": [1, 2, 3], "boolean": True},
        }
        agent_data = {"name": "Complex Config Agent", "description": "Agent with complex config", "config": complex_config}
        response = client.post("/api/agents/", json=agent_data)
        assert response.status_code == 200
        data = response.json()
        assert data["config"] == complex_config
        assert data["config"]["nested"]["array"] == [1, 2, 3]
        assert data["config"]["nested"]["boolean"] is True
