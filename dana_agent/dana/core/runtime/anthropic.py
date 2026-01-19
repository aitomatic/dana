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
      "tool_calls": "array - tools to call (non-empty when done=false, empty when done=true)",
      "todo_list": "array - progress tracking with {content, status} objects"
    },
    "example_in_progress": {"done": false, "reasoning": "I need more information", "response": null, "tool_calls": [{"name": "resource:method", "parameters": {"key": "value"}}], "todo_list": [{"content": "Gather data", "status": "in_progress"}, {"content": "Analyze results", "status": "pending"}, {"content": "Provide summary", "status": "pending"}]},
    "example_done": {"done": true, "reasoning": "I have the answer", "response": "Here is your answer.", "tool_calls": [], "todo_list": [{"content": "Gather data", "status": "completed"}, {"content": "Analyze results", "status": "completed"}, {"content": "Provide summary", "status": "completed"}]}
  },
  "rules": {
    "done_false": "Set when you need to call a tool for more information",
    "done_true": "Set when you have all information and can provide the final answer",
    "synthesize": "After 2-3 tool calls, synthesize what you have. A good partial answer beats endless searching.",
    "todo_planning": "In your FIRST response, plan ALL steps: [gather: in_progress], [analyze: pending], [summarize: pending]",
    "todo_execution": "Keep the same items throughout. Only change status: pending → in_progress → completed"
  },
  "guidelines": {
    "efficiency": "Limit to 3-4 tool calls. Synthesize available data.",
    "clarity": "Be direct and concise in responses",
    "transparency": "Never mention tool names to users"
  },
  "available_tools": [
{{available_tools_prompt}}
  ]
}"""

ANTHROPIC_SYSTEM_PROMPT_NATIVE_TOOLS = """{
  "identity": "{{identity}}",
  "output_format": {
    "description": "Respond with ONLY a valid JSON object. Tools are called via the API separately.",
    "schema": {
      "done": "boolean - false when you called tools, true when providing final answer",
      "reasoning": "string - your thinking process",
      "response": "string|null - your answer (required when done=true, null when done=false)",
      "todo_list": "array - progress tracking with {content, status} objects"
    },
    "example_in_progress": {"done": false, "reasoning": "Gathering more data", "response": null, "todo_list": [{"content": "Gather data", "status": "in_progress"}, {"content": "Analyze results", "status": "pending"}, {"content": "Provide summary", "status": "pending"}]},
    "example_done": {"done": true, "reasoning": "I have the answer", "response": "Here is your answer.", "todo_list": [{"content": "Gather data", "status": "completed"}, {"content": "Analyze results", "status": "completed"}, {"content": "Provide summary", "status": "completed"}]}
  },
  "rules": {
    "done_false": "Set when you called a tool and are waiting for results",
    "done_true": "Set when you have all information and can provide the final answer",
    "synthesize": "After 2-3 tool calls, synthesize what you have",
    "todo_planning": "In your FIRST response, plan ALL steps: [gather: in_progress], [analyze: pending], [summarize: pending]",
    "todo_execution": "Keep the same items throughout. Only change status: pending → in_progress → completed"
  },
  "guidelines": {
    "efficiency": "Limit to 3-4 tool calls total",
    "clarity": "Be direct and concise",
    "transparency": "Never mention tool names to users"
  }
}"""


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
