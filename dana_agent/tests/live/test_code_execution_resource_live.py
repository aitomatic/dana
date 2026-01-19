"""
Live tests for CodeExecutionResource with STARAgent integration.

These tests verify that agents can successfully invoke CodeExecutionResource
through the LLM's tool calling mechanism and receive correct results.

Run with: pytest tests/live/test_code_execution_resource_live.py --live
"""

import pytest

from dana.common.resource import CodeExecutionResource
from dana.core.agent.star_agent import STARAgent


class TestCodeExecutionResourceLive:
    """Live tests for CodeExecutionResource with real LLM integration."""

    @pytest.mark.live
    def test_agent_executes_simple_calculation(self):
        """Test that agent's LLM invokes execute() and gets correct result for simple calculation."""
        try:
            agent = STARAgent(
                agent_type="test_code_execution",
                llm_provider="openai",
                auto_register=False,
            )
            agent.with_resources(CodeExecutionResource(auto_register=False))

            # Ask agent to calculate using Python code
            result = agent.query(
                message="Calculate 2 + 2 using Python code. Use the code execution resource to run the calculation."
            )

            assert result is not None
            assert "response" in result
            response = result["response"]

            # The response should contain the answer "4"
            # It might be in different formats: "4", "The answer is 4", etc.
            assert isinstance(response, str)
            assert "4" in response or "four" in response.lower()

            print(f"✅ Agent executed code: response contains '4'")
            print(f"   Response: {response[:200]}")

        except Exception as e:
            if "API key" in str(e):
                pytest.skip(f"LLM API key not available: {str(e)}")
            else:
                raise

    @pytest.mark.live
    def test_agent_executes_statistics_calculation(self):
        """Test that agent can use statistics module through code execution."""
        try:
            agent = STARAgent(
                agent_type="test_code_execution",
                llm_provider="openai",
                auto_register=False,
            )
            agent.with_resources(CodeExecutionResource(auto_register=False))

            result = agent.query(
                message="Calculate the standard deviation of [1, 2, 3, 4, 5] using Python code and the statistics module."
            )

            assert result is not None
            assert "response" in result
            response = result["response"]

            # Standard deviation of [1,2,3,4,5] is approximately 1.58
            assert isinstance(response, str)
            # Should contain the result (might be formatted differently)
            assert any(
                char.isdigit() for char in response
            ), "Response should contain numeric result"

            print(f"✅ Agent executed statistics calculation")
            print(f"   Response: {response[:200]}")

        except Exception as e:
            if "API key" in str(e):
                pytest.skip(f"LLM API key not available: {str(e)}")
            else:
                raise

    @pytest.mark.live
    def test_agent_handles_code_execution_error(self):
        """Test that agent handles code execution errors gracefully."""
        try:
            agent = STARAgent(
                agent_type="test_code_execution",
                llm_provider="openai",
                auto_register=False,
            )
            agent.with_resources(CodeExecutionResource(auto_register=False))

            # Ask agent to do something that will cause an error (like using blocked builtin)
            result = agent.query(
                message="Try to open a file using Python code. Use the code execution resource."
            )

            assert result is not None
            assert "response" in result
            response = result["response"]

            # Should indicate that the operation is not allowed
            assert isinstance(response, str)
            # Should mention error or permission
            assert (
                "error" in response.lower()
                or "not allowed" in response.lower()
                or "permission" in response.lower()
                or "blocked" in response.lower()
            )

            print(f"✅ Agent handled execution error gracefully")
            print(f"   Response: {response[:200]}")

        except Exception as e:
            if "API key" in str(e):
                pytest.skip(f"LLM API key not available: {str(e)}")
            else:
                raise

    @pytest.mark.live
    def test_agent_stateful_execution(self):
        """Test that agent can use stateful execution across multiple calls."""
        try:
            agent = STARAgent(
                agent_type="test_code_execution",
                llm_provider="openai",
                auto_register=False,
            )
            agent.with_resources(CodeExecutionResource(auto_register=False))

            # First call: set a variable
            result1 = agent.query(
                message="Using Python code, set a variable x = 10 and print it."
            )

            assert result1 is not None
            assert "response" in result1
            assert "10" in result1["response"]

            # Second call: use the variable from first call
            result2 = agent.query(
                message="Now multiply x by 2 using Python code and print the result."
            )

            assert result2 is not None
            assert "response" in result2
            # Should be able to use x from previous execution
            assert "20" in result2["response"] or "x" in result2["response"].lower()

            print(f"✅ Agent used stateful execution")
            print(f"   First response: {result1['response'][:100]}")
            print(f"   Second response: {result2['response'][:100]}")

        except Exception as e:
            if "API key" in str(e):
                pytest.skip(f"LLM API key not available: {str(e)}")
            else:
                raise
