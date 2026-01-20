# Anthropic Runtime Optimization PRD

**Status: DRAFT**

## Goal

Bring the Anthropic AgentRuntime stack to feature parity with the OpenAI stack, ensuring that complex multi-step agentic queries (like "compute the average of 5 US cities' current temperatures, weighted by the number of letters in each city") work equally well on both platforms.

## Problem

The OpenAI AgentRuntime currently handles complex multi-step tasks more reliably than the Anthropic runtime. When testing with queries like:

> "compute the average of 5 US cities' current temperatures, weighted by the number of letters in each city"

OpenAI handles this well while Anthropic struggles with:
1. **Task decomposition** - Breaking the task into clear steps (get cities, get temps, compute weights, calculate average)
2. **Tool chaining** - Sequential tool calls where results inform the next call
3. **Mathematical synthesis** - Combining data from multiple tool results into a final calculation
4. **State tracking** - Maintaining context across multiple tool call rounds

### Root Causes

| Issue | OpenAI Runtime | Anthropic Runtime |
|-------|----------------|-------------------|
| **Prompt Style** | Imperative, action-oriented ("You MUST...", "CALL TOOLS...") | Declarative, descriptive (key-value definitions) |
| **Examples** | Practical, inline markdown examples | Embedded JSON objects (less intuitive) |
| **Tool Emphasis** | Explicit "CALL TOOLS via the function calling API" | Vague "Set when you need to call a tool" |
| **Synthesis Guidance** | Clear rules with urgency | Generic guidelines |
| **Multi-step Planning** | todo_list prominently featured | todo_list mentioned but not emphasized |

## Solution

### 1. Optimize Anthropic System Prompts

Replace the current JSON-structured prompts with more action-oriented, Claude-optimized prompts that:
- Use **imperative language** that Claude responds well to
- Provide **explicit multi-step examples** showing tool chaining
- Include **mathematical/synthesis examples** for complex queries
- Emphasize **todo_list planning** for task decomposition
- Add **strong constraints** on done=false without tool calls

### 2. Enhance Multi-Step Reasoning

Add specific guidance for:
- **Task decomposition**: How to break complex queries into steps
- **Intermediate state**: How to track partial results across tool calls
- **Synthesis patterns**: How to combine results from multiple tools
- **Early termination**: When to stop gathering data and compute the answer

### 3. Improve Tool Calling Clarity

Make Claude understand:
- Native tools are called via the API, not in JSON output
- done=false REQUIRES a tool call to have been made
- Tool results will be provided in the next turn
- Each tool call should have a clear purpose tied to todo_list items

### 4. Add Integration Tests

Create tests that verify both OpenAI and Anthropic handle:
- Simple single-tool queries
- Multi-step queries requiring tool chaining
- Mathematical aggregation queries
- Queries requiring data synthesis from multiple sources

## Design Details

### Current Anthropic Prompt (Problems Highlighted)

```json
{
  "identity": "{{identity}}",
  "output_format": {
    "description": "Respond with ONLY a valid JSON object...",  // ❌ Lacks urgency
    "schema": {
      "done": "boolean - false when calling tools...",  // ❌ Passive language
      ...
    }
  },
  "rules": {
    "done_false": "Set when you need to call a tool...",  // ❌ Vague
    "synthesize": "After 2-3 tool calls, synthesize..."  // ❌ No urgency
  }
}
```

### Proposed Anthropic Prompt (Improvements)

```markdown
You are an AI assistant. {{identity}}

## CRITICAL: Output Format
You MUST respond with ONLY a valid JSON object. No markdown, no explanations.

Schema:
{
  "done": boolean,      // false = you called tools, true = final answer
  "reasoning": string,  // your step-by-step thinking
  "response": string|null,  // required when done=true
  "todo_list": array    // REQUIRED: track your progress
}

## CRITICAL: Tool Calling Rules
- To get information: USE THE TOOL CALLING API to invoke a tool. Then output done=false.
- To give your answer: Output done=true with your complete response.
- NEVER output done=false without having called a tool - this is an error!

## Multi-Step Task Strategy
For complex queries (calculations, aggregations, multi-part questions):

1. PLAN FIRST: Create todo_list with ALL steps before your first tool call
   Example: "average of 5 cities' temperatures weighted by name length"
   - [in_progress] Get 5 US cities
   - [pending] Get temperature for each city
   - [pending] Calculate letter count for each city name
   - [pending] Compute weighted average

2. EXECUTE: Work through todo_list, updating status as you go
3. SYNTHESIZE: After gathering data, compute the final answer
4. RESPOND: Set done=true with your complete calculation shown

## Example: Multi-Step Calculation

User: "What's the average temperature of NYC and LA, weighted by population?"

Step 1 - Plan and get first data:
(Call tool: weather:get_temperature for NYC)
{"done": false, "reasoning": "Planning multi-step task. First getting NYC temp.", "response": null, "todo_list": [{"content": "Get NYC temperature", "status": "in_progress"}, {"content": "Get LA temperature", "status": "pending"}, {"content": "Get city populations", "status": "pending"}, {"content": "Calculate weighted average", "status": "pending"}]}

Step 2 - Continue gathering:
(Call tool: weather:get_temperature for LA)
{"done": false, "reasoning": "Got NYC=45°F. Now getting LA temp.", "response": null, "todo_list": [{"content": "Get NYC temperature", "status": "completed"}, {"content": "Get LA temperature", "status": "in_progress"}, ...]}

Step 3 - Final calculation:
{"done": true, "reasoning": "NYC=45°F (pop 8.3M), LA=72°F (pop 3.9M). Weighted avg = (45×8.3 + 72×3.9)/(8.3+3.9) = 53.6°F", "response": "The population-weighted average temperature is **53.6°F**. NYC (45°F, population 8.3M) and LA (72°F, population 3.9M) were weighted by their populations.", "todo_list": [...all completed...]}

## Rules Summary
1. ALWAYS create a todo_list for any query requiring multiple steps
2. NEVER set done=false without calling a tool
3. After 3-4 tool calls, STOP gathering and SYNTHESIZE your answer
4. Show your work: include calculations in reasoning
5. Be concise but complete in your final response
```

### Implementation Approach

The key insight is that Claude models respond better to:
1. **Markdown-style prompts** (like OpenAI) rather than JSON-structured prompts
2. **Imperative instructions** ("You MUST", "NEVER", "ALWAYS")
3. **Concrete examples** showing the exact flow
4. **Visual emphasis** (## headers, bold, numbered lists)

## MVP Requirements

### Phase 1: Prompt Optimization

- [ ] Rewrite `ANTHROPIC_SYSTEM_PROMPT_JSON` with action-oriented style
- [ ] Rewrite `ANTHROPIC_SYSTEM_PROMPT_NATIVE_TOOLS` with action-oriented style
- [ ] Add multi-step calculation examples to prompts
- [ ] Add explicit todo_list planning guidance
- [ ] Add stronger constraints on done=false + no tool calls

### Phase 2: Error Handling Improvements

- [ ] Update `build_output_format_correction()` in base runtime for better Anthropic guidance
- [ ] Add retry logic specific to common Anthropic failure modes
- [ ] Improve JSON extraction for Claude's output patterns

### Phase 3: Integration Tests

- [ ] Create test cases for multi-step queries
- [ ] Test weighted average calculation scenario
- [ ] Test multi-city temperature aggregation
- [ ] Test data synthesis from multiple tool results
- [ ] Ensure parity between OpenAI and Anthropic on all test cases

### Phase 4: Documentation & Examples

- [ ] Update dana-agent docs with Anthropic best practices
- [ ] Add example queries that demonstrate multi-step reasoning
- [ ] Document differences between runtime behaviors

## File Changes

| File | Change |
|------|--------|
| `dana/core/runtime/anthropic.py` | UPDATE: Rewrite system prompts |
| `dana/core/runtime/base.py` | UPDATE: Improve error correction messages |
| `tests/integration/test_runtime_parity.py` | NEW: Multi-step query tests |
| `examples/multi_step_queries.py` | NEW: Example complex queries |

## Success Criteria

1. **Parity Test**: The query "compute the average of 5 US cities' current temperatures, weighted by the number of letters in each city" succeeds on both OpenAI and Anthropic runtimes
2. **Task Decomposition**: Anthropic creates appropriate todo_list for multi-step tasks
3. **Tool Chaining**: Anthropic correctly chains multiple tool calls
4. **Synthesis**: Anthropic correctly computes mathematical aggregations
5. **No Regressions**: All existing tests continue to pass

## Testing Strategy

### Unit Tests
- Prompt rendering produces expected output
- JSON extraction handles Claude response patterns
- Error correction messages are appropriate

### Integration Tests (requires API keys in .env)
```python
@pytest.mark.integration
def test_weighted_temperature_average():
    """Test multi-step calculation works on both runtimes."""
    query = "compute the average of 5 US cities' current temperatures, weighted by the number of letters in each city"

    # Test with OpenAI
    openai_result = run_query_with_runtime(query, OpenAIRuntime())
    assert "average" in openai_result.lower()
    assert any(char.isdigit() for char in openai_result)  # Has a number

    # Test with Anthropic
    anthropic_result = run_query_with_runtime(query, AnthropicRuntime())
    assert "average" in anthropic_result.lower()
    assert any(char.isdigit() for char in anthropic_result)

@pytest.mark.integration
def test_todo_list_creation():
    """Test that todo_list is created for multi-step tasks."""
    query = "Get temperatures for NYC, LA, and Chicago, then tell me which is warmest"

    result, trace = run_query_with_trace(query, AnthropicRuntime())

    # Verify todo_list was created in first response
    first_response = trace[0]
    assert first_response.todo_list is not None
    assert len(first_response.todo_list) >= 3  # At least one item per city + comparison
```

## Non-Goals

- Changing the base AgentRuntime API
- Modifying OpenAI runtime (it's working well)
- Adding new tool types or capabilities
- Changing how native tools are registered

## References

- OpenAI runtime: `dana/core/runtime/openai.py` (reference for prompt style)
- Anthropic runtime: `dana/core/runtime/anthropic.py` (file to modify)
- Base runtime: `dana/core/runtime/base.py` (shared logic)
- Agent runtime PRD: `dana/specs/agent-runtime-prd.md`
