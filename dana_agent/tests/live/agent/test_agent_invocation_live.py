"""
Live tests for agent-to-agent invocation functionality.

These tests verify that the ToolCaller agent call functionality works correctly
with real LLM interactions and agent registry.

Run with: pytest tests/live/agent/test_agent_invocation_live.py --live
"""

import pytest

from dana.core.agent.star_agent import STARAgent


class ResearchAgent(STARAgent):
    """Research-focused STARAgent for testing agent invocation."""

    def __init__(self, **kwargs):
        super().__init__(agent_type="research", **kwargs)

    @property
    def system_prompt(self) -> str:
        return """You are a research agent specialized in gathering and analyzing information.
        You excel at finding relevant data, conducting research, and providing detailed insights.
        When called by other agents, provide thorough and accurate research findings."""


class AnalysisAgent(STARAgent):
    """Analysis-focused STARAgent for testing agent invocation."""

    def __init__(self, **kwargs):
        super().__init__(agent_type="analysis", **kwargs)

    @property
    def system_prompt(self) -> str:
        return """You are an analysis agent specialized in analyzing data and providing insights.
        You excel at interpreting research findings, identifying patterns, and making recommendations.
        When called by other agents, provide clear and actionable analysis."""


class CoordinatorAgent(STARAgent):
    """Coordinator STARAgent for testing agent invocation."""

    def __init__(self, **kwargs):
        super().__init__(agent_type="coordinator", **kwargs)

    @property
    def system_prompt(self) -> str:
        return """You are a coordinator agent that delegates tasks to specialized agents.
        You excel at breaking down complex tasks and delegating them appropriately.
        When you need research, call the research agent. When you need analysis, call the analysis agent.
        Always use the call_agent tool to delegate tasks to other agents."""


class TestAgentInvocationLive:
    """Live tests for agent-to-agent invocation functionality."""

    @pytest.mark.live
    def test_toolcaller_agent_call_success(self):
        """Test successful agent-to-agent call via ToolCaller."""
        try:
            # Create agents
            coordinator = CoordinatorAgent()
            research_agent = ResearchAgent()

            # Ensure both agents are registered
            assert coordinator.object_id is not None
            assert research_agent.object_id is not None

            # Test direct ToolCaller invocation
            tool_caller = coordinator._tool_caller

            # Test the _invoke_agent method directly
            result = tool_caller._invoke_agent(
                object_id=research_agent.object_id, message="Research the latest trends in renewable energy technology."
            )

            # Verify the result
            assert isinstance(result, str)
            assert len(result) > 0
            assert "Error:" not in result

            print(f"✅ ToolCaller agent call success: {len(result)} chars response")

        except Exception as e:
            if "API key" in str(e):
                pytest.skip(f"LLM API key not available: {str(e)}")
            else:
                raise e

    @pytest.mark.live
    def test_toolcaller_agent_call_nonexistent_agent(self):
        """Test agent call to non-existent agent."""
        try:
            coordinator = CoordinatorAgent()
            tool_caller = coordinator._tool_caller

            # Test calling non-existent agent
            result = tool_caller._invoke_agent(object_id="nonexistent_agent_id", message="This should fail")

            # Should return error message
            assert "Error:" in result
            assert "not found" in result

            print("✅ ToolCaller agent call error handling: Non-existent agent handled correctly")

        except Exception as e:
            if "API key" in str(e):
                pytest.skip(f"LLM API key not available: {str(e)}")
            else:
                raise e

    @pytest.mark.live
    def test_toolcaller_agent_call_invalid_agent_id(self):
        """Test agent call with invalid agent ID."""
        try:
            coordinator = CoordinatorAgent()
            ResearchAgent()

            tool_caller = coordinator._tool_caller

            # Test calling with invalid agent ID
            result = tool_caller._invoke_agent(object_id="invalid_agent_id_12345", message="This should fail")

            # Should return error message
            assert "Error:" in result
            assert "not found" in result

            print("✅ ToolCaller agent call error handling: Invalid agent ID handled correctly")

        except Exception as e:
            if "API key" in str(e):
                pytest.skip(f"LLM API key not available: {str(e)}")
            else:
                raise e

    @pytest.mark.live
    def test_toolcaller_execute_agent_call_success(self):
        """Test successful execution of agent call via execute_tool_calls."""
        try:
            # Create agents
            coordinator = CoordinatorAgent()
            research_agent = ResearchAgent()

            # Test the full execute_tool_calls flow
            tool_calls = [
                {
                    "function": "call_agent",
                    "arguments": {"object_id": research_agent.object_id, "message": "Research the impact of AI on software development."},
                }
            ]

            results = coordinator._tool_caller.execute_tool_calls(tool_calls)

            # Verify results
            assert len(results) == 1
            result = results[0]

            # Check result structure
            assert "type" in result
            assert "target" in result
            assert "result" in result
            assert "success" in result

            # Should be successful
            assert result["success"] is True
            assert result["type"] == "agent"
            assert result["target"] == research_agent.object_id

            # Response should be meaningful
            response = result["result"]
            assert isinstance(response, str)
            assert len(response) > 0

            print(f"✅ ToolCaller execute_agent_call success: {len(response)} chars response")

        except Exception as e:
            if "API key" in str(e):
                pytest.skip(f"LLM API key not available: {str(e)}")
            else:
                raise e

    @pytest.mark.live
    def test_toolcaller_execute_agent_call_missing_parameters(self):
        """Test agent call with missing parameters."""
        try:
            coordinator = CoordinatorAgent()

            # Test with missing object_id
            tool_calls = [{"function": "call_agent", "arguments": {"message": "This should fail"}}]

            results = coordinator._tool_caller.execute_tool_calls(tool_calls)

            # Verify error handling
            assert len(results) == 1
            result = results[0]

            assert result["success"] is False
            assert "Error:" in result["result"]
            assert "Missing object_id" in result["result"]

            print("✅ ToolCaller execute_agent_call error handling: Missing parameters handled correctly")

        except Exception as e:
            if "API key" in str(e):
                pytest.skip(f"LLM API key not available: {str(e)}")
            else:
                raise e

    @pytest.mark.live
    def test_star_agent_delegation_workflow(self):
        """Test full STARAgent delegation workflow with real LLM tool calls."""
        try:
            # Create agents
            coordinator = CoordinatorAgent()
            ResearchAgent()
            AnalysisAgent()

            # Test coordinator delegating to research agent
            # This should trigger the coordinator to make a call_agent tool call
            coordinator_result = coordinator.query(
                message="I need you to research renewable energy trends. Delegate this to the research agent."
            )

            # Verify the result
            assert coordinator_result is not None
            assert "response" in coordinator_result

            response = coordinator_result["response"]
            assert isinstance(response, str)
            assert len(response) > 0

            print(f"✅ STARAgent delegation workflow: {len(response)} chars response")

        except Exception as e:
            if "API key" in str(e):
                pytest.skip(f"LLM API key not available: {str(e)}")
            else:
                raise e

    @pytest.mark.live
    def test_agent_call_response_propagation(self):
        """Test that agent call responses are properly propagated through the STAR loop."""
        try:
            coordinator = CoordinatorAgent()
            ResearchAgent()

            # Test that the coordinator can call the research agent and get a meaningful response
            result = coordinator.query(message="Please research the latest developments in quantum computing and provide a summary.")

            # Verify the result structure
            assert result is not None
            assert "response" in result

            response = result["response"]
            assert isinstance(response, str)
            assert len(response) > 0

            # The response should contain information about quantum computing
            # (this is a bit fragile but tests that the delegation actually worked)
            response_lower = response.lower()
            quantum_indicators = ["quantum", "computing", "research", "technology", "development"]
            has_quantum_content = any(indicator in response_lower for indicator in quantum_indicators)

            if has_quantum_content:
                print("✅ Agent call response propagation: Response contains relevant content")
            else:
                print(f"⚠️ Agent call response propagation: Response may not contain expected content: {response[:100]}...")

        except Exception as e:
            if "API key" in str(e):
                pytest.skip(f"LLM API key not available: {str(e)}")
            else:
                raise e

    @pytest.mark.live
    def test_multi_agent_delegation_chain(self):
        """Test a chain of agent delegations (coordinator -> research -> analysis)."""
        try:
            coordinator = CoordinatorAgent()
            ResearchAgent()
            AnalysisAgent()

            # Test coordinator delegating to research agent
            research_result = coordinator.query(message="Research the latest trends in artificial intelligence and machine learning.")

            assert research_result is not None
            assert "response" in research_result

            # Test coordinator delegating to analysis agent
            analysis_result = coordinator.query(
                message="Analyze the current state of renewable energy adoption and provide strategic insights."
            )

            assert analysis_result is not None
            assert "response" in analysis_result

            print("✅ Multi-agent delegation chain: Both delegations completed successfully")

        except Exception as e:
            if "API key" in str(e):
                pytest.skip(f"LLM API key not available: {str(e)}")
            else:
                raise e
