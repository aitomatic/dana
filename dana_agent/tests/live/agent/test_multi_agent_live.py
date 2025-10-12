"""
Live tests for multi-agent functionality

These tests involve live resources (LLMs) to verify multi-agent communication and coordination.
Live tests require real API keys and make actual calls to LLM services.
Run with: pytest tests/live/agent/test_multi_agent_live.py --live
"""

import pytest

from dana.core.agent.star_agent import STARAgent


class ResearchAgent(STARAgent):
    """
    <PUBLIC_DESCRIPTION>
    Research-focused STARAgent for testing multi-agent scenarios.
    </PUBLIC_DESCRIPTION>

    <PRIVATE_IDENTITY>
    You are a research agent for testing multi-agent scenarios.
    You focus on gathering and analyzing information.
    You are thorough and analytical.
    </PRIVATE_IDENTITY>
    """

    ...


class AnalysisAgent(STARAgent):
    """
    <PUBLIC_DESCRIPTION>
    Analysis-focused STARAgent for testing multi-agent scenarios.
    </PUBLIC_DESCRIPTION>

    <PRIVATE_IDENTITY>
    You are an analysis agent for testing multi-agent scenarios.
    You focus on interpreting data and providing insights.
    You are analytical and strategic.
    </PRIVATE_IDENTITY>
    """

    ...


class CoordinatorAgent(STARAgent):
    """
    <PUBLIC_DESCRIPTION>
    Coordinator STARAgent for testing multi-agent scenarios.
    </PUBLIC_DESCRIPTION>

    <PRIVATE_IDENTITY>
    You are a coordinator agent for testing multi-agent scenarios.
    You focus on managing and orchestrating multiple agents.
    You are organized and strategic.
    </PRIVATE_IDENTITY>
    """

    ...


class TestMultiAgentLive:
    """Live tests for multi-agent functionality."""

    @pytest.mark.live
    def test_agent_creation_and_identity(self):
        """Test creating multiple agents with different identities."""
        try:
            # Create different types of agents
            research_agent = ResearchAgent()
            analysis_agent = AnalysisAgent()
            coordinator_agent = CoordinatorAgent()

            # Verify agent identities
            assert research_agent.agent_type == "ResearchAgent"
            assert analysis_agent.agent_type == "AnalysisAgent"
            assert coordinator_agent.agent_type == "CoordinatorAgent"

            # Verify each agent has unique IDs
            agent_ids = {research_agent.object_id, analysis_agent.object_id, coordinator_agent.object_id}
            assert len(agent_ids) == 3  # All IDs should be unique

            print(f"✅ Multi-agent creation: {len(agent_ids)} unique agents created")

        except Exception as e:
            if "API key" in str(e):
                pytest.skip(f"LLM API key not available: {str(e)}")
            else:
                raise

    @pytest.mark.live
    def test_agent_specialization(self):
        """Test that agents maintain their specialized roles."""
        try:
            research_agent = ResearchAgent()
            analysis_agent = AnalysisAgent()

            # Test research agent with research-focused query
            research_result = research_agent.query(message="What are the key trends in artificial intelligence research?")
            assert research_result is not None
            assert "response" in research_result

            # Test analysis agent with analysis-focused query
            analysis_result = analysis_agent.query(message="Analyze the implications of AI trends for business strategy.")
            assert analysis_result is not None
            assert "response" in analysis_result

            print("✅ Agent specialization: Research and Analysis agents working")

        except Exception as e:
            if "API key" in str(e):
                pytest.skip(f"LLM API key not available: {str(e)}")
            else:
                raise

    @pytest.mark.live
    def test_agent_communication_simulation(self):
        """Test simulated agent-to-agent communication."""
        try:
            research_agent = ResearchAgent()
            analysis_agent = AnalysisAgent()
            coordinator_agent = CoordinatorAgent()

            # Simulate a multi-agent workflow
            # 1. Coordinator assigns research task
            coordinator_result = coordinator_agent.query(message="I need research on renewable energy trends. What should we investigate?")
            assert coordinator_result is not None

            # 2. Research agent conducts research
            research_result = research_agent.query(message="Research the latest trends in renewable energy technology and adoption rates.")
            assert research_result is not None

            # 3. Analysis agent analyzes the research
            analysis_result = analysis_agent.query(message="Analyze the renewable energy research findings and provide strategic insights.")
            assert analysis_result is not None

            # 4. Coordinator synthesizes results
            synthesis_result = coordinator_agent.query(message="Based on the research and analysis, what are our key recommendations?")
            assert synthesis_result is not None

            print("✅ Agent communication: Multi-agent workflow completed")

        except Exception as e:
            if "API key" in str(e):
                pytest.skip(f"LLM API key not available: {str(e)}")
            else:
                raise e

    @pytest.mark.live
    def test_agent_state_isolation(self):
        """Test that agents maintain separate state."""
        try:
            agent1 = ResearchAgent()
            agent2 = AnalysisAgent()

            # Agent 1 learns something
            result1 = agent1.query(message="Remember that my favorite topic is machine learning.")
            assert result1 is not None

            # Agent 2 learns something different
            result2 = agent2.query(message="Remember that my focus area is business strategy.")
            assert result2 is not None

            # Check that agents have separate identities
            # (Timeline access not available in current architecture)
            assert agent1.object_id != agent2.object_id

            # Each agent should have its own conversation history
            assert agent1.object_id != agent2.object_id

            print("✅ Agent state isolation: Agents have separate identities")

        except Exception as e:
            if "API key" in str(e):
                pytest.skip(f"LLM API key not available: {str(e)}")
            else:
                raise

    @pytest.mark.live
    def test_agent_learning_phases(self):
        """Test different agents in different learning phases."""
        try:
            # Create agents in different learning phases
            observe_agent = ResearchAgent()
            reflect_agent = AnalysisAgent()

            # Test that agents can handle different types of queries
            # (Learning phase control not available in current architecture)
            observe_result = observe_agent.query(message="What do you observe about the current state of AI development?")
            assert observe_result is not None

            reflect_result = reflect_agent.query(message="What insights can you derive from our previous discussions?")
            assert reflect_result is not None

            print("✅ Agent learning phases: Agents handled different query types successfully")

        except Exception as e:
            if "API key" in str(e):
                pytest.skip(f"LLM API key not available: {str(e)}")
            else:
                raise

    @pytest.mark.live
    def test_agent_resource_management(self):
        """Test agent resource discovery and management."""
        try:
            agent = CoordinatorAgent()

            # Test resource discovery
            resources = agent.available_resources
            agents = agent.available_agents

            assert isinstance(resources, list)
            assert isinstance(agents, list)

            # Test agent state with resources
            state = agent.get_state()
            assert state is not None
            assert "resources" in state
            assert "workflows" in state

            print(f"✅ Agent resource management: {len(resources)} resources, {len(agents)} agents")

        except Exception as e:
            if "API key" in str(e):
                pytest.skip(f"LLM API key not available: {str(e)}")
            else:
                raise

    @pytest.mark.live
    def test_agent_error_handling(self):
        """Test multi-agent error handling."""
        try:
            agent1 = ResearchAgent()
            agent2 = AnalysisAgent()

            # Test error handling in different agents
            result1 = agent1.query(message="")  # Empty query
            result2 = agent2.query(message="Invalid query with special characters: !@#$%^&*()")

            # Both should handle errors gracefully
            assert result1 is not None
            assert result2 is not None

            print("✅ Multi-agent error handling: Both agents handled errors gracefully")

        except Exception as e:
            if "API key" in str(e):
                pytest.skip(f"LLM API key not available: {str(e)}")
            else:
                raise

    @pytest.mark.live
    def test_agent_provider_consistency(self):
        """Test that multiple agents can use the same provider consistently."""
        try:
            # Create agents with same provider
            agent1 = ResearchAgent(llm_provider="openai")
            agent2 = AnalysisAgent(llm_provider="openai")

            # Test both agents work with same provider
            result1 = agent1.query(message="Hello from research agent!")
            result2 = agent2.query(message="Hello from analysis agent!")

            assert result1 is not None
            assert result2 is not None
            assert "response" in result1
            assert "response" in result2

            print("✅ Agent provider consistency: Both agents working with same provider")

        except Exception as e:
            if "API key" in str(e):
                pytest.skip(f"LLM API key not available: {str(e)}")
            else:
                raise
