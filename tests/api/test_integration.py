"""Integration tests for the API server."""


# Use the global client fixture from conftest.py


class TestAgentAPIIntegration:
    """Integration tests for the Agent API."""

    def test_full_agent_lifecycle(self, client, db_session):
        """Test the complete lifecycle of an agent: create, read, list."""
        # 1. Create an agent
        create_data = {
            "name": "Integration Test Agent",
            "description": "Agent for integration testing",
            "config": {"model": "gpt-4", "temperature": 0.7, "max_tokens": 1000},
        }

        create_response = client.post("/api/agents/", json=create_data)
        assert create_response.status_code == 200
        created_agent = create_response.json()

        agent_id = created_agent["id"]
        assert agent_id is not None
        assert created_agent["name"] == "Integration Test Agent"
        assert created_agent["description"] == "Agent for integration testing"
        assert created_agent["config"]["model"] == "gpt-4"

        # 2. Read the created agent
        read_response = client.get(f"/api/agents/{agent_id}")
        assert read_response.status_code == 200
        read_agent = read_response.json()

        assert read_agent["id"] == agent_id
        assert read_agent["name"] == "Integration Test Agent"
        assert read_agent["description"] == "Agent for integration testing"
        assert read_agent["config"]["temperature"] == 0.7

        # 3. List all agents (should include our created agent)
        list_response = client.get("/api/agents/")
        assert list_response.status_code == 200
        agents = list_response.json()

        assert len(agents) >= 1
        # Find our agent in the list
        found_agent = next((a for a in agents if a["id"] == agent_id), None)
        assert found_agent is not None
        assert found_agent["name"] == "Integration Test Agent"

    def test_multiple_agents_management(self, client, db_session):
        """Test managing multiple agents."""
        # Create multiple agents
        agents_data = [
            {"name": "Agent Alpha", "description": "First test agent", "config": {"model": "gpt-4", "temperature": 0.5}},
            {"name": "Agent Beta", "description": "Second test agent", "config": {"model": "claude-3", "temperature": 0.8}},
            {"name": "Agent Gamma", "description": "Third test agent", "config": {"model": "gpt-3.5", "temperature": 0.3}},
        ]

        created_agents = []
        for agent_data in agents_data:
            response = client.post("/api/agents/", json=agent_data)
            assert response.status_code == 200
            created_agents.append(response.json())

        # Verify all agents were created with unique IDs
        agent_ids = [agent["id"] for agent in created_agents]
        assert len(set(agent_ids)) == 3  # All IDs should be unique

        # List all agents
        list_response = client.get("/api/agents/")
        assert list_response.status_code == 200
        all_agents = list_response.json()

        assert len(all_agents) >= 3

        # Verify we can read each agent individually
        for created_agent in created_agents:
            read_response = client.get(f"/api/agents/{created_agent['id']}")
            assert read_response.status_code == 200
            read_agent = read_response.json()
            assert read_agent["id"] == created_agent["id"]
            assert read_agent["name"] == created_agent["name"]

    def test_pagination_integration(self, client, db_session):
        """Test pagination with real data."""
        # Create 10 agents
        for i in range(10):
            agent_data = {
                "name": f"Pagination Agent {i}",
                "description": f"Agent for pagination test {i}",
                "config": {"model": f"model-{i}", "index": i},
            }
            response = client.post("/api/agents/", json=agent_data)
            assert response.status_code == 200

        # Test first page (limit 3)
        response = client.get("/api/agents/?limit=3")
        assert response.status_code == 200
        first_page = response.json()
        assert len(first_page) == 3
        assert first_page[0]["name"] == "Pagination Agent 0"
        assert first_page[1]["name"] == "Pagination Agent 1"
        assert first_page[2]["name"] == "Pagination Agent 2"

        # Test second page (skip 3, limit 3)
        response = client.get("/api/agents/?skip=3&limit=3")
        assert response.status_code == 200
        second_page = response.json()
        assert len(second_page) == 3
        assert second_page[0]["name"] == "Pagination Agent 3"
        assert second_page[1]["name"] == "Pagination Agent 4"
        assert second_page[2]["name"] == "Pagination Agent 5"

    def test_error_handling_integration(self, client, db_session):
        """Test error handling in the API."""
        # Test getting non-existent agent
        response = client.get("/api/agents/99999")
        assert response.status_code == 404
        error_data = response.json()
        assert error_data["detail"] == "Agent not found"

        # Test creating agent with invalid data
        invalid_data = {
            "name": "Test Agent",
            # Missing description and config
        }
        response = client.post("/api/agents/", json=invalid_data)
        assert response.status_code == 422  # Validation error

        # Test creating agent with invalid config type
        invalid_config_data = {
            "name": "Test Agent",
            "description": "Test description",
            "config": "not a dict",  # Should be dict
        }
        response = client.post("/api/agents/", json=invalid_config_data)
        assert response.status_code == 422  # Validation error

    def test_complex_config_integration(self, client, db_session):
        """Test handling of complex nested configurations."""
        complex_config = {
            "model": "gpt-4",
            "parameters": {"temperature": 0.7, "max_tokens": 1000, "top_p": 0.9},
            "tools": [{"type": "function", "function": {"name": "get_weather"}}, {"type": "function", "function": {"name": "get_time"}}],
            "metadata": {
                "version": "1.0",
                "tags": ["test", "integration"],
                "nested": {"deep": {"level": 3, "array": [1, 2, 3, 4, 5], "boolean": True, "null_value": None}},
            },
        }

        agent_data = {"name": "Complex Config Agent", "description": "Agent with complex nested configuration", "config": complex_config}

        # Create agent
        create_response = client.post("/api/agents/", json=agent_data)
        assert create_response.status_code == 200
        created_agent = create_response.json()

        # Read agent back
        read_response = client.get(f"/api/agents/{created_agent['id']}")
        assert read_response.status_code == 200
        read_agent = read_response.json()

        # Verify complex config is preserved exactly
        assert read_agent["config"] == complex_config
        assert read_agent["config"]["parameters"]["temperature"] == 0.7
        assert read_agent["config"]["tools"][0]["function"]["name"] == "get_weather"
        assert read_agent["config"]["metadata"]["nested"]["deep"]["array"] == [1, 2, 3, 4, 5]
        assert read_agent["config"]["metadata"]["nested"]["deep"]["boolean"] is True
        assert read_agent["config"]["metadata"]["nested"]["deep"]["null_value"] is None
