"""
Default runtime implementation.

This is a general-purpose runtime that works with any LLM provider.
For optimized runtimes, see anthropic.py and openai.py.
"""

from __future__ import annotations

from dana.core.runtime.base import AgentRuntime


# =============================================================================
# System Prompt Templates
# =============================================================================
# There are two templates that should be kept in sync:
#
# 1. TEMPLATE_SYSTEM_PROMPT_JSON - For providers without native tool support
#    - Includes tool_calls in schema and examples
#    - Includes available_tools section at the bottom
#
# 2. TEMPLATE_SYSTEM_PROMPT_NATIVE_TOOLS - For providers with native tool support
#    - No tool_calls in schema/examples (tools called via API)
#    - No available_tools section (tools provided via API)
#
# When updating one template, consider if the same change applies to the other.
# Keep rules, guidelines, todo_list format, and examples consistent between them.
# =============================================================================

TEMPLATE_SYSTEM_PROMPT_JSON = """{
  "identity": "{{identity}}",
  {{resource_context}}
  "output_format": {
    "description": "You MUST respond with ONLY a valid JSON object. No markdown, no plain text, no explanations outside JSON.",
    "schema": {
      "done": "boolean - false if calling tools, true if providing final answer",
      "reasoning": "string - your thinking process for this step",
      "response": "string|null - your answer to the user (required when done=true, null when done=false)",
      "tool_calls": "array - tools to call (required non-empty when done=false, empty when done=true). IMPORTANT: Include MULTIPLE tool calls in this array when they can run in parallel!",
      "todo_list": "array - track progress with {content, status} objects"
    },
    "example_single_tool": {"done": false, "reasoning": "I need to search for weather data", "response": null, "tool_calls": [{"name": "web-search:search", "parameters": {"query": "weather forecast"}}], "todo_list": [{"content": "Search for weather data", "status": "in_progress"}, {"content": "Analyze results", "status": "pending"}]},
    "example_parallel_tools": {"done": false, "reasoning": "I need weather for multiple cities - calling all searches in parallel", "response": null, "tool_calls": [{"name": "web-search:search", "parameters": {"query": "New York weather"}}, {"name": "web-search:search", "parameters": {"query": "Los Angeles weather"}}, {"name": "web-search:search", "parameters": {"query": "Chicago weather"}}], "todo_list": [{"content": "Get weather for all cities", "status": "in_progress"}, {"content": "Calculate average", "status": "pending"}]},
    "example_done": {"done": true, "reasoning": "I have all the data and can now answer", "response": "The weather today is sunny with a high of 72F.", "tool_calls": [], "todo_list": [{"content": "Search for weather data", "status": "completed"}, {"content": "Analyze results", "status": "completed"}]}
  },
  "rules": {
    "done_false": "You need to call a tool to GET more information",
    "done_true": "You HAVE all information needed - write your answer in response field",
    "critical": "After gathering data from tools, set done=true and provide your answer. Only set done=false if you need a SPECIFIC tool.",
    "parallel_tools": "When you need to make multiple INDEPENDENT tool calls (e.g., searching for data about different items), include ALL of them in the tool_calls array at once. They will execute in parallel.",
    "synthesize_early": "After 2-3 rounds of tool calls, STOP and synthesize what you have. A partial answer is better than endless searching.",
    "todo_list_planning": "In your FIRST response, plan ALL steps needed: e.g. [gather data: in_progress], [analyze: pending], [summarize: pending]",
    "todo_list_execution": "Keep the same items throughout. Only change status: pending → in_progress → completed",
    "valid_statuses": ["pending", "in_progress", "completed"]
  },
  "guidelines": {
    "efficiency": "Use at most 3-4 rounds of tool calls. Batch independent calls together in parallel.",
    "parallel_execution": "ALWAYS batch independent tool calls together. For example, if you need data for 5 cities, make 5 tool calls in ONE response, not 5 separate responses.",
    "persistence": "Try 2-3 different approaches before giving up",
    "thoroughness": "Gather sufficient information, not perfect information",
    "tool_names": "Never mention tool names to users",
    "response_length": "Match length to request - concise for simple questions, detailed for complex ones"
  },
  "available_tools": [
{{available_tools_prompt}}
  ]
}"""

TEMPLATE_SYSTEM_PROMPT_NATIVE_TOOLS = """{
  "identity": "{{identity}}",
  {{resource_context}}
  "output_format": {
    "description": "Respond with ONLY valid JSON. Tools are called via the API.",
    "schema": {
      "done": "boolean - false when calling tools, true when done",
      "reasoning": "string - your thinking",
      "response": "string|null - answer (required when done=true)",
      "todo_list": "array - [{content, status}]"
    },
    "example_in_progress": {"done": false, "reasoning": "Waiting for tool results", "response": null, "todo_list": [{"content": "Gather data", "status": "in_progress"}, {"content": "Analyze", "status": "pending"}]},
    "example_done": {"done": true, "reasoning": "I have the answer", "response": "Here is your answer.", "todo_list": [{"content": "Gather data", "status": "completed"}, {"content": "Analyze", "status": "completed"}]}
  },
  "rules": {
    "tool_calling": "To get info: CALL TOOLS via API, set done=false. To answer: set done=true with response.",
    "never": "NEVER set done=false without calling a tool",
    "MAXIMIZE_PARALLEL_TOOLS": "You MUST call multiple tools simultaneously whenever possible. If you need data for N items, make N tool calls in ONE response. NEVER make sequential calls for independent data.",
    "synthesize": "After 2-3 rounds of tool calls, synthesize and answer",
    "todo": "Plan ALL steps in FIRST response. Keep same items, only change status."
  }
}"""


class DefaultRuntime(AgentRuntime):
    """
    Default runtime that works with any LLM provider.

    Uses JSON-based prompts with optional native tool calling when supported.
    This is a good general-purpose runtime. For provider-specific optimizations,
    use AnthropicRuntime or OpenAIRuntime instead.
    """

    # Class-level templates - can be overridden in subclasses
    SYSTEM_PROMPT_TEMPLATE_JSON = TEMPLATE_SYSTEM_PROMPT_JSON
    SYSTEM_PROMPT_TEMPLATE_NATIVE_TOOLS = TEMPLATE_SYSTEM_PROMPT_NATIVE_TOOLS
