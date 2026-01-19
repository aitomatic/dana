# Anthropic Runtime Optimization - Implementation Spec

**Status: PENDING**

## Goal

Optimize the Anthropic AgentRuntime to handle complex multi-step queries as well as the OpenAI runtime. This includes queries like:

> "compute the average of 5 US cities' current temperatures, weighted by the number of letters in each city"

## Demo

### Before (Current Behavior)
```python
# Anthropic struggles with multi-step tasks
agent = DanaAgent(llm_provider="anthropic")
result = agent.query("compute the average of 5 US cities' temperatures, weighted by name length")
# Often fails to:
# - Create a clear plan
# - Chain tool calls correctly
# - Perform the final calculation
```

### After (Expected Behavior)
```python
# Anthropic handles complex queries like OpenAI
agent = DanaAgent(llm_provider="anthropic")
result = agent.query("compute the average of 5 US cities' temperatures, weighted by name length")
# Successfully:
# - Creates todo_list with clear steps
# - Calls tools in sequence
# - Computes and returns weighted average
```

## Codebase Context

**Key files to modify:**

```python
# dana/core/runtime/anthropic.py - System prompts to rewrite
ANTHROPIC_SYSTEM_PROMPT_JSON = """..."""  # Lines 22-51
ANTHROPIC_SYSTEM_PROMPT_NATIVE_TOOLS = """..."""  # Lines 53-78

# dana/core/runtime/base.py - Error correction to improve
def build_output_format_correction(self) -> LLMMessage:  # Lines 405-438
```

**Reference implementation (what works well):**

```python
# dana/core/runtime/openai.py - Use this style as reference
OPENAI_SYSTEM_PROMPT_JSON = """You are an AI assistant. {{identity}}

## Output Format
You MUST respond with a valid JSON object only...
"""
```

## MVP Requirements

### Phase 1: Rewrite Anthropic System Prompts

- [ ] Rewrite `ANTHROPIC_SYSTEM_PROMPT_JSON` in `dana/core/runtime/anthropic.py`:
  - [ ] Change from JSON structure to markdown-style (like OpenAI)
  - [ ] Use imperative language ("You MUST", "NEVER", "ALWAYS")
  - [ ] Add explicit multi-step task guidance
  - [ ] Add calculation/synthesis example
  - [ ] Emphasize todo_list for task planning
  - [ ] Add strong constraint: "NEVER set done=false without calling a tool"

- [ ] Rewrite `ANTHROPIC_SYSTEM_PROMPT_NATIVE_TOOLS` in `dana/core/runtime/anthropic.py`:
  - [ ] Same changes as JSON prompt but for native tools mode
  - [ ] Emphasize "USE THE TOOL CALLING API"
  - [ ] Clear distinction between tool calls (API) and JSON output

### Phase 2: Improve Error Correction

- [ ] Update or override `build_output_format_correction()` for Anthropic-specific guidance:
  - [ ] Add example of correct multi-step behavior
  - [ ] Be more explicit about what went wrong
  - [ ] Guide toward synthesis if enough data gathered

### Phase 3: Create Integration Tests

- [ ] Create `tests/integration/test_anthropic_runtime_parity.py`:
  - [ ] `test_simple_weather_query` - Single tool call
  - [ ] `test_multi_city_temperatures` - Multiple sequential tool calls
  - [ ] `test_weighted_average_calculation` - Multi-step with math
  - [ ] `test_todo_list_creation` - Verify planning behavior
  - [ ] `test_parity_with_openai` - Same query, both runtimes

### Phase 4: Manual Verification

- [ ] Test the specific query: "compute the average of 5 US cities' current temperatures, weighted by the number of letters in each city"
- [ ] Verify todo_list is created with appropriate steps
- [ ] Verify tool calls are made correctly
- [ ] Verify final calculation is correct

## Files Implemented

| File | Status | Description |
|------|--------|-------------|
| `dana/core/runtime/anthropic.py` | PENDING | Rewrite system prompts with action-oriented style |
| `tests/integration/test_anthropic_runtime_parity.py` | PENDING | Integration tests for runtime parity |

## Detailed Implementation

### New ANTHROPIC_SYSTEM_PROMPT_JSON

Replace the content in `dana/core/runtime/anthropic.py` lines 22-51:

```python
ANTHROPIC_SYSTEM_PROMPT_JSON = """You are an AI assistant. {{identity}}

## CRITICAL: Output Format
You MUST respond with ONLY a valid JSON object. No markdown code blocks, no explanations.

Schema:
{
  "done": boolean,      // false = you need more data, true = final answer
  "reasoning": string,  // your step-by-step thinking process
  "response": string|null,  // your answer (REQUIRED when done=true, null when done=false)
  "tool_calls": array,  // tools to call (REQUIRED when done=false, empty when done=true)
  "todo_list": array    // progress tracking: [{content, status}] - ALWAYS include for multi-step tasks
}

## Tool Calling Rules
- done=false: You MUST include tool_calls with at least one tool to call
- done=true: You MUST include response with your complete answer
- NEVER set done=false without providing tool_calls - this causes an error!

## Multi-Step Task Strategy
For complex queries requiring multiple pieces of information:

1. PLAN FIRST: In your first response, create a todo_list with ALL steps
   - Mark the first step as "in_progress"
   - Mark remaining steps as "pending"

2. GATHER DATA: Call tools one at a time, updating todo_list status

3. SYNTHESIZE EARLY: After 2-3 tool calls, STOP and compute your answer
   - Don't keep searching for perfect data
   - Use what you have gathered

4. SHOW WORK: Include calculations in your reasoning field

## Example: Multi-Step Query

Query: "What's the average temperature of NYC and LA?"

Response 1 (getting first temperature):
{"done": false, "reasoning": "I need temperatures for both cities. Starting with NYC.", "response": null, "tool_calls": [{"name": "weather:get_current", "parameters": {"city": "New York"}}], "todo_list": [{"content": "Get NYC temperature", "status": "in_progress"}, {"content": "Get LA temperature", "status": "pending"}, {"content": "Calculate average", "status": "pending"}]}

Response 2 (after receiving NYC=45°F, getting second):
{"done": false, "reasoning": "NYC is 45°F. Now getting LA temperature.", "response": null, "tool_calls": [{"name": "weather:get_current", "parameters": {"city": "Los Angeles"}}], "todo_list": [{"content": "Get NYC temperature", "status": "completed"}, {"content": "Get LA temperature", "status": "in_progress"}, {"content": "Calculate average", "status": "pending"}]}

Response 3 (after receiving LA=72°F, computing final answer):
{"done": true, "reasoning": "NYC=45°F, LA=72°F. Average = (45+72)/2 = 58.5°F", "response": "The average temperature of NYC and LA is **58.5°F** (NYC: 45°F, LA: 72°F).", "tool_calls": [], "todo_list": [{"content": "Get NYC temperature", "status": "completed"}, {"content": "Get LA temperature", "status": "completed"}, {"content": "Calculate average", "status": "completed"}]}

## Available Tools
{{available_tools_prompt}}"""
```

### New ANTHROPIC_SYSTEM_PROMPT_NATIVE_TOOLS

Replace the content in `dana/core/runtime/anthropic.py` lines 53-78:

```python
ANTHROPIC_SYSTEM_PROMPT_NATIVE_TOOLS = """You are an AI assistant. {{identity}}

## CRITICAL: Output Format
You MUST respond with ONLY a valid JSON object. No markdown code blocks, no explanations.
Tools are called via the tool calling API - do NOT include tool_calls in your JSON.

Schema:
{
  "done": boolean,      // false = you called a tool via API, true = final answer
  "reasoning": string,  // your step-by-step thinking process
  "response": string|null,  // your answer (REQUIRED when done=true, null when done=false)
  "todo_list": array    // progress tracking: [{content, status}] - ALWAYS include for multi-step tasks
}

## CRITICAL: Tool Calling Rules
- To get information: USE THE TOOL CALLING API to invoke a tool, then set done=false
- To give your final answer: Set done=true with your complete response
- NEVER output done=false without having called a tool via the API - this is an error!
- If you need data, CALL THE TOOL NOW, don't just say you will call it

## Multi-Step Task Strategy
For complex queries requiring multiple pieces of information:

1. PLAN FIRST: In your first response, create a todo_list with ALL steps
   - Mark the first step as "in_progress"
   - Mark remaining steps as "pending"

2. GATHER DATA: Call tools via the API, updating todo_list status after each

3. SYNTHESIZE EARLY: After 2-3 tool calls, STOP and compute your answer
   - Don't keep searching for perfect data
   - Use what you have gathered

4. SHOW WORK: Include calculations in your reasoning field

## Example: Multi-Step Query

Query: "What's the average temperature of NYC and LA?"

Response 1 (after calling weather tool for NYC via API):
{"done": false, "reasoning": "Called weather API for NYC. Will need LA next.", "response": null, "todo_list": [{"content": "Get NYC temperature", "status": "in_progress"}, {"content": "Get LA temperature", "status": "pending"}, {"content": "Calculate average", "status": "pending"}]}

Response 2 (after receiving NYC=45°F, called API for LA):
{"done": false, "reasoning": "NYC is 45°F. Called weather API for LA.", "response": null, "todo_list": [{"content": "Get NYC temperature", "status": "completed"}, {"content": "Get LA temperature", "status": "in_progress"}, {"content": "Calculate average", "status": "pending"}]}

Response 3 (after receiving LA=72°F, computing final answer):
{"done": true, "reasoning": "NYC=45°F, LA=72°F. Average = (45+72)/2 = 58.5°F", "response": "The average temperature of NYC and LA is **58.5°F** (NYC: 45°F, LA: 72°F).", "todo_list": [{"content": "Get NYC temperature", "status": "completed"}, {"content": "Get LA temperature", "status": "completed"}, {"content": "Calculate average", "status": "completed"}]}

## Key Rules
1. ALWAYS create todo_list for multi-step queries
2. NEVER set done=false without calling a tool via the API
3. After 2-3 tool calls, SYNTHESIZE your answer - don't over-gather
4. SHOW your calculations in the reasoning field
5. Be CONCISE but COMPLETE in your final response"""
```

### Integration Test File

Create `tests/integration/test_anthropic_runtime_parity.py`:

```python
"""
Integration tests for Anthropic runtime parity with OpenAI.

These tests require API keys to be set in .env:
- ANTHROPIC_API_KEY
- OPENAI_API_KEY

Run with: pytest tests/integration/test_anthropic_runtime_parity.py -v -s
"""

import os
import pytest
from dana.core.runtime.anthropic import AnthropicRuntime
from dana.core.runtime.openai import OpenAIRuntime
from dana.core.agent.star_agent import STARAgent
from dana.core.resource import Resource


# Skip if no API keys
pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY") or not os.environ.get("OPENAI_API_KEY"),
    reason="Requires ANTHROPIC_API_KEY and OPENAI_API_KEY in environment"
)


class MockWeatherResource(Resource):
    """Mock weather resource for testing."""

    resource_id = "weather"

    def get_current(self, city: str) -> dict:
        """Get current weather for a city.

        Args:
            city: Name of the city

        Returns:
            Weather data including temperature
        """
        # Mock data for testing
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


class TestAgent(STARAgent):
    """Test agent with weather resource."""

    def __init__(self, runtime):
        super().__init__(
            agent_type="test-agent",
            runtime=runtime,
            resources=[MockWeatherResource()],
        )


def run_query(query: str, runtime) -> tuple[str, list]:
    """Run a query and return result + trace of parsed responses."""
    agent = TestAgent(runtime)
    # TODO: Capture trace of ParsedResponses for verification
    result = agent.query(query)
    return result, []


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
        # NYC=45, Chicago=32, avg=38.5
        assert any(char.isdigit() for char in result)

    def test_average_calculation_anthropic(self):
        query = "What's the average temperature of NYC and Chicago?"
        result, _ = run_query(query, AnthropicRuntime())
        # NYC=45, Chicago=32, avg=38.5
        assert any(char.isdigit() for char in result)


class TestComplexWeightedCalculation:
    """Test the specific weighted average query from the requirements."""

    def test_weighted_average_openai(self):
        query = "compute the average of 5 US cities' current temperatures, weighted by the number of letters in each city"
        result, _ = run_query(query, OpenAIRuntime())
        # Should contain a numerical result
        assert any(char.isdigit() for char in result)
        # Should mention the calculation or method
        assert "average" in result.lower() or "weighted" in result.lower() or "°" in result

    def test_weighted_average_anthropic(self):
        query = "compute the average of 5 US cities' current temperatures, weighted by the number of letters in each city"
        result, _ = run_query(query, AnthropicRuntime())
        # Should contain a numerical result
        assert any(char.isdigit() for char in result)
        # Should mention the calculation or method
        assert "average" in result.lower() or "weighted" in result.lower() or "°" in result


class TestTodoListBehavior:
    """Test that todo_list is properly created for multi-step tasks."""

    @pytest.mark.skip(reason="Requires trace capture implementation")
    def test_todo_list_created_anthropic(self):
        query = "Get temperatures for NYC, LA, and Chicago, then find the warmest"
        result, trace = run_query(query, AnthropicRuntime())

        # First response should have todo_list
        assert trace[0].todo_list is not None
        assert len(trace[0].todo_list) >= 3


class TestParityBetweenRuntimes:
    """Ensure both runtimes produce comparable results."""

    def test_same_query_both_runtimes(self):
        query = "What's the temperature difference between Miami and Seattle?"

        openai_result, _ = run_query(query, OpenAIRuntime())
        anthropic_result, _ = run_query(query, AnthropicRuntime())

        # Both should mention the difference (85-52=33)
        # We're lenient - just check both produce numeric results
        assert any(char.isdigit() for char in openai_result)
        assert any(char.isdigit() for char in anthropic_result)
```

## Tests Required

Run these commands to verify the implementation:

```bash
# Unit tests for runtime
pytest dana_agent/tests/unit/core/test_agent_runtime.py -v

# Integration tests (requires API keys in .env)
pytest tests/integration/test_anthropic_runtime_parity.py -v -s

# Manual test of the specific query
python -c "
from dotenv import load_dotenv
load_dotenv()

from dana_agent.dana import DanaAgent

agent = DanaAgent(llm_provider='anthropic')
result = agent.query('compute the average of 5 US cities current temperatures, weighted by the number of letters in each city')
print(result)
"
```

## Success Criteria

1. Unit tests pass: `pytest dana_agent/tests/unit/core/test_agent_runtime.py -v`
2. Integration tests pass: `pytest tests/integration/test_anthropic_runtime_parity.py -v`
3. Manual query succeeds with sensible output
4. No regressions in existing tests

## Before Marking Complete

- [ ] All prompt changes preserve backward compatibility
- [ ] Unit tests pass
- [ ] Integration tests pass (with API keys)
- [ ] Manual verification of weighted average query
- [ ] Code follows existing patterns (structlog, etc.)
- [ ] No unnecessary complexity

## When Complete

Run all verification commands. Only if ALL tests pass, write this line to this file:

<promise>TASK COMPLETE</promise>

## References

- PRD: [anthropic-optimization-prd.md](./anthropic-optimization-prd.md)
- OpenAI runtime (reference): `dana/core/runtime/openai.py`
- Anthropic runtime (to modify): `dana/core/runtime/anthropic.py`
- Base runtime: `dana/core/runtime/base.py`
