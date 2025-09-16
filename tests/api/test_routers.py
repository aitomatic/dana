"""Tests for API server routers."""

import os
from unittest.mock import patch

from dana.api.core.models import Agent

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
        # Test the root endpoint - it should either serve index.html or return 404 if not found
        response = client.get("/")

        # The endpoint should either return 200 (if index.html exists) or 404 (if it doesn't)
        # In test environment, static files typically don't exist, so 404 is expected
        if response.status_code == 200:
            # If static files exist, should serve HTML
            assert response.headers["content-type"] == "text/html; charset=utf-8"
        elif response.status_code == 404:
            # If static files don't exist, should return JSON error
            data = response.json()
            assert "error" in data
        else:
            # Unexpected status code
            raise AssertionError(f"Unexpected status code: {response.status_code}")

    def test_root_endpoint_with_mocked_static_files(self, client):
        """Test root endpoint when static files exist (using a real temp file)"""
        import tempfile

        # Create a real temporary index.html file
        with tempfile.TemporaryDirectory() as tmpdir:
            index_path = os.path.join(tmpdir, "index.html")
            with open(index_path, "w") as f:
                f.write("<html><body>Test</body></html>")
            # Patch os.path.exists and os.path.abspath to point to our temp file
            with patch("os.path.exists", side_effect=lambda p: p == index_path), patch("os.path.abspath", return_value=index_path):
                response = client.get("/")
                assert response.status_code == 200
                assert b"Test" in response.content


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

    def test_create_agent_invalid_data(self, client):
        invalid_data = {"name": "Test Agent"}
        response = client.post("/api/agents/", json=invalid_data)
        assert response.status_code == 422  # Validation error
