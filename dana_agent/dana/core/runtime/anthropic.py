"""
Anthropic-optimized runtime for Claude models.

This runtime is optimized for Claude models with prompts and formatting
that work best with Claude's capabilities.
"""

from __future__ import annotations

from dana.core.runtime.base import AgentRuntime


# =============================================================================
# Claude-Optimized System Prompts
# =============================================================================
# These prompts are tailored for Claude models, taking advantage of:
# - Claude's strong instruction following
# - Native tool use support
# - XML-style context markers that Claude handles well
# =============================================================================

ANTHROPIC_SYSTEM_PROMPT_JSON = """{
  "identity": "{{identity}}",
  "output_format": {
    "description": "Respond with ONLY a valid JSON object. No markdown code blocks, no explanations outside the JSON.",
    "schema": {
      "done": "boolean - false when calling tools, true when providing final answer",
      "reasoning": "string - your thinking process",
      "response": "string|null - your answer (required when done=true, null when done=false)",
      "tool_calls": "array - tools to call (non-empty when done=false, empty when done=true). CRITICAL: Include MULTIPLE independent tool calls in this array to run them in parallel!",
      "todo_list": "array - progress tracking with {content, status} objects"
    },
    "example_single_tool": {"done": false, "reasoning": "I need more information", "response": null, "tool_calls": [{"name": "resource:method", "parameters": {"key": "value"}}], "todo_list": [{"content": "Gather data", "status": "in_progress"}, {"content": "Analyze results", "status": "pending"}]},
    "example_parallel_tools": {"done": false, "reasoning": "I need data for multiple items - calling all in parallel for efficiency", "response": null, "tool_calls": [{"name": "web-search:search", "parameters": {"query": "item 1"}}, {"name": "web-search:search", "parameters": {"query": "item 2"}}, {"name": "web-search:search", "parameters": {"query": "item 3"}}], "todo_list": [{"content": "Gather all data", "status": "in_progress"}, {"content": "Analyze results", "status": "pending"}]},
    "example_done": {"done": true, "reasoning": "I have the answer", "response": "Here is your answer.", "tool_calls": [], "todo_list": [{"content": "Gather data", "status": "completed"}, {"content": "Analyze results", "status": "completed"}]}
  },
  "rules": {
    "done_false": "Set when you need to call a tool for more information",
    "done_true": "Set when you have all information and can provide the final answer",
    "MAXIMIZE_PARALLEL_TOOLS": "You MUST call multiple tools simultaneously whenever possible. If you need data for N items, include N tool calls in ONE response. NEVER make sequential calls for independent data.",
    "synthesize": "After 2-3 rounds of tool calls, synthesize what you have. A good partial answer beats endless searching.",
    "todo_planning": "In your FIRST response, plan ALL steps: [gather: in_progress], [analyze: pending], [summarize: pending]",
    "todo_execution": "Keep the same items throughout. Only change status: pending → in_progress → completed"
  },
  "guidelines": {
    "efficiency": "Limit to 3-4 rounds of tool calls.",
    "clarity": "Be direct and concise in responses",
    "transparency": "Never mention tool names to users"
  },
  "available_tools": [
{{available_tools_prompt}}
  ]
}"""

ANTHROPIC_SYSTEM_PROMPT_NATIVE_TOOLS = """You are an AI assistant. {{identity}}

<use_parallel_tool_calls>
CRITICAL: You MUST invoke all independent tool calls simultaneously in a single response.
NEVER call tools sequentially when they can be parallelized.
Example: Need data for 5 items? Make 5 tool calls in ONE response, not 5 separate responses.
This is a hard requirement, not a suggestion.
</use_parallel_tool_calls>

## Output Format
You MUST respond with a valid JSON object only. No markdown, no extra text.
Tools are called via the function calling API - do not include tool_calls in your JSON.

Schema:
{
  "done": boolean,      // false = called tools via API, true = final answer
  "reasoning": string,  // your thought process
  "response": string|null,  // your answer (required if done=true)
  "todo_list": array    // progress tracking: [{content, status}]
}

## Examples
After calling tools (via function calling API):
{"done": false, "reasoning": "Waiting for tool results", "response": null, "todo_list": [{"content": "Gather data", "status": "in_progress"}, {"content": "Analyze results", "status": "pending"}]}

Final answer:
{"done": true, "reasoning": "I found the answer", "response": "Here is your answer.", "todo_list": [{"content": "Gather data", "status": "completed"}, {"content": "Analyze results", "status": "completed"}]}

## Rules
- To get information: CALL TOOLS via the function calling API, then set done=false
- To give final answer: Set done=true with your complete response
- NEVER set done=false without calling a tool - either call a tool OR provide your answer
- After 2-3 rounds of tool calls, synthesize what you have and provide your answer
- Never mention tool names to users
- todo_list: Plan ALL steps in FIRST response. One in_progress, rest pending. Keep same items, only change status."""


class AnthropicRuntime(AgentRuntime):
    """
    Runtime optimized for Anthropic Claude models.

    Uses prompts tailored for Claude's strengths:
    - Clear, structured JSON output format
    - Native tool use when available
    - Concise instructions that Claude follows well
    """

    SYSTEM_PROMPT_TEMPLATE_JSON = ANTHROPIC_SYSTEM_PROMPT_JSON
    SYSTEM_PROMPT_TEMPLATE_NATIVE_TOOLS = ANTHROPIC_SYSTEM_PROMPT_NATIVE_TOOLS
