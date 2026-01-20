"""
Integration tests for Anthropic runtime parity with OpenAI.

These tests require API keys to be set in .env:
- ANTHROPIC_API_KEY
- OPENAI_API_KEY

Run with: pytest tests/integration/test_anthropic_runtime_parity.py --live -v -s
"""

import os

import pytest

from dana.core.agent.star_agent import STARAgent
from dana.core.resource import BaseResource
from dana.core.runtime.anthropic import AnthropicRuntime
from dana.core.runtime.openai import OpenAIRuntime


pytestmark = [
    pytest.mark.live,
    pytest.mark.requires_api_keys,
    pytest.mark.skipif(
        not os.environ.get("ANTHROPIC_API_KEY") or not os.environ.get("OPENAI_API_KEY"),
        reason="Requires ANTHROPIC_API_KEY and OPENAI_API_KEY in environment",
    ),
]


class MockWeatherResource(BaseResource):
    """Mock weather resource for testing."""

    def __init__(self) -> None:
        super().__init__(resource_type="weather", resource_id="weather", auto_register=False)

    def get_current(self, city: str) -> dict:
        """Get current weather for a city."""
        temps = {
            "new york": 45,
            "nyc": 45,
            "los angeles": 72,
            "la": 72,
            "chicago": 32,
            "miami": 85,
            "seattle": 52,
            "denver": 40,
            "boston": 38,
            "phoenix": 95,
            "dallas": 78,
            "atlanta": 65,
        }
        city_lower = city.lower()
        for key, temp in temps.items():
            if key in city_lower or city_lower in key:
                return {"city": city, "temperature_f": temp, "conditions": "clear"}
        return {"city": city, "temperature_f": 60, "conditions": "unknown"}


class WeatherAgent(STARAgent):
    """Agent with weather resource for integration tests."""

    def __init__(self, runtime) -> None:
        super().__init__(
            agent_type="test-agent",
            runtime=runtime,
            auto_register=False,
            enable_web_search=False,
            enable_skills=False,
            enable_code_execution=False,
        )
        self.with_resources(MockWeatherResource())


def run_query(query: str, runtime) -> tuple[str, list]:
    """Run a query and return result + trace of parsed responses."""
    agent = WeatherAgent(runtime)
    result = agent.query(message=query)
    if isinstance(result, dict):
        result = result.get("response", str(result))
    return str(result), []


class TestSimpleQueries:
    """Test simple single-tool queries work on both runtimes."""

    def test_simple_weather_openai(self):
        result, _ = run_query("What's the temperature in NYC?", OpenAIRuntime())
        assert "45" in result or "temperature" in result.lower()

    def test_simple_weather_anthropic(self):
        result, _ = run_query("What's the temperature in NYC?", AnthropicRuntime())
        assert "45" in result or "temperature" in result.lower()


class TestMultiStepQueries:
    """Test multi-step queries requiring tool chaining."""

    def test_two_city_comparison_openai(self):
        query = "Compare the temperatures in NYC and LA. Which is warmer?"
        result, _ = run_query(query, OpenAIRuntime())
        assert "la" in result.lower() or "los angeles" in result.lower()
        assert "warmer" in result.lower() or "72" in result

    def test_two_city_comparison_anthropic(self):
        query = "Compare the temperatures in NYC and LA. Which is warmer?"
        result, _ = run_query(query, AnthropicRuntime())
        assert "la" in result.lower() or "los angeles" in result.lower()
        assert "warmer" in result.lower() or "72" in result

    def test_average_calculation_openai(self):
        query = "What's the average temperature of NYC and Chicago?"
        result, _ = run_query(query, OpenAIRuntime())
        assert any(char.isdigit() for char in result)

    def test_average_calculation_anthropic(self):
        query = "What's the average temperature of NYC and Chicago?"
        result, _ = run_query(query, AnthropicRuntime())
        assert any(char.isdigit() for char in result)


class TestComplexWeightedCalculation:
    """Test the specific weighted average query from the requirements."""

    def test_weighted_average_openai(self):
        query = (
            "compute the average of 5 US cities' current temperatures, "
            "weighted by the number of letters in each city"
        )
        result, _ = run_query(query, OpenAIRuntime())
        assert any(char.isdigit() for char in result)
        assert "average" in result.lower() or "weighted" in result.lower() or "f" in result.lower()

    def test_weighted_average_anthropic(self):
        query = (
            "compute the average of 5 US cities' current temperatures, "
            "weighted by the number of letters in each city"
        )
        result, _ = run_query(query, AnthropicRuntime())
        assert any(char.isdigit() for char in result)
        assert "average" in result.lower() or "weighted" in result.lower() or "f" in result.lower()


class TestTodoListBehavior:
    """Test that todo_list is properly created for multi-step tasks."""

    @pytest.mark.skip(reason="Requires trace capture implementation")
    def test_todo_list_created_anthropic(self):
        query = "Get temperatures for NYC, LA, and Chicago, then find the warmest"
        result, trace = run_query(query, AnthropicRuntime())

        assert trace[0].todo_list is not None
        assert len(trace[0].todo_list) >= 3


class TestParityBetweenRuntimes:
    """Ensure both runtimes produce comparable results."""

    def test_same_query_both_runtimes(self):
        query = "What's the temperature difference between Miami and Seattle?"

        openai_result, _ = run_query(query, OpenAIRuntime())
        anthropic_result, _ = run_query(query, AnthropicRuntime())

        assert any(char.isdigit() for char in openai_result)
        assert any(char.isdigit() for char in anthropic_result)
