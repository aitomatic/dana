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
  "output_format": {
    "description": "You MUST respond with ONLY a valid JSON object. No markdown, no plain text, no explanations outside JSON.",
    "schema": {
      "done": "boolean - false if calling tools, true if providing final answer",
      "reasoning": "string - your thinking process for this step",
      "response": "string|null - your answer to the user (required when done=true, null when done=false)",
      "tool_calls": "array - tools to call (required non-empty when done=false, empty when done=true)",
      "todo_list": "array - track progress with {content, status} objects"
    },
    "example_response_in_progress": {"done": false, "reasoning": "I need to search for weather data", "response": null, "tool_calls": [{"name": "web-search:search", "parameters": {"query": "weather forecast"}}], "todo_list": [{"content": "Search for weather data", "status": "in_progress"}, {"content": "Analyze temperature trends", "status": "pending"}, {"content": "Provide summary", "status": "pending"}]},
    "example_response_done": {"done": true, "reasoning": "I found the weather data and can now answer", "response": "The weather today is sunny with a high of 72F.", "tool_calls": [], "todo_list": [{"content": "Search for weather data", "status": "completed"}, {"content": "Analyze temperature trends", "status": "completed"}, {"content": "Provide summary", "status": "completed"}]}
  },
  "rules": {
    "done_false": "You need to call a tool to GET more information",
    "done_true": "You HAVE all information needed - write your answer in response field",
    "critical": "After gathering data from tools, set done=true and provide your answer. Only set done=false if you need a SPECIFIC tool.",
    "synthesize_early": "After 2-3 tool calls, STOP and synthesize what you have. A partial answer is better than endless searching.",
    "todo_list_planning": "In your FIRST response, plan ALL steps needed: e.g. [gather data: in_progress], [analyze: pending], [summarize: pending]",
    "todo_list_execution": "Keep the same items throughout. Only change status: pending → in_progress → completed",
    "valid_statuses": ["pending", "in_progress", "completed"]
  },
  "guidelines": {
    "efficiency": "Use at most 3-4 tool calls total. Synthesize with available data - don't over-research.",
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
  "output_format": {
    "description": "You MUST respond with ONLY a valid JSON object. No markdown, no plain text, no explanations outside JSON. Tools are called separately via the API.",
    "schema": {
      "done": "boolean - false if you called tools, true if providing final answer",
      "reasoning": "string - your thinking process for this step",
      "response": "string|null - your answer to the user (required when done=true, null when done=false)",
      "todo_list": "array - track progress with {content, status} objects"
    },
    "example_response_in_progress": {"done": false, "reasoning": "I need to search for weather data", "response": null, "todo_list": [{"content": "Search for weather data", "status": "in_progress"}, {"content": "Analyze temperature trends", "status": "pending"}, {"content": "Provide summary", "status": "pending"}]},
    "example_response_done": {"done": true, "reasoning": "I found the weather data and can now answer", "response": "The weather today is sunny with a high of 72F.", "todo_list": [{"content": "Search for weather data", "status": "completed"}, {"content": "Analyze temperature trends", "status": "completed"}, {"content": "Provide summary", "status": "completed"}]}
  },
  "rules": {
    "done_false": "You called a tool to get information - set done=false",
    "done_true": "You HAVE all information needed - write your answer in response field",
    "critical": "After gathering data from tools, set done=true and provide your answer. Only set done=false if you need a SPECIFIC tool.",
    "synthesize_early": "After 2-3 tool calls, STOP and synthesize what you have. A partial answer is better than endless searching.",
    "todo_list_planning": "In your FIRST response, plan ALL steps needed: e.g. [gather data: in_progress], [analyze: pending], [summarize: pending]",
    "todo_list_execution": "Keep the same items throughout. Only change status: pending → in_progress → completed",
    "valid_statuses": ["pending", "in_progress", "completed"]
  },
  "guidelines": {
    "efficiency": "Use at most 3-4 tool calls total. Synthesize with available data - don't over-research.",
    "persistence": "Try 2-3 different approaches before giving up",
    "thoroughness": "Gather sufficient information, not perfect information",
    "tool_names": "Never mention tool names to users",
    "response_length": "Match length to request - concise for simple questions, detailed for complex ones"
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
