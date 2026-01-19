"""
Anthropic Provider Implementation
"""

import json
import anthropic
import structlog

from ...config import config_manager
from ..types import LLMMessage, LLMProvider, LLMResponse


logger = structlog.get_logger()


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider using the official Anthropic library."""

    @property
    def supports_native_tools(self) -> bool:
        """Anthropic supports native tool calling."""
        return True

    def __init__(self, api_key: str | None = None, model: str = "claude-3-sonnet-20240229", base_url: str | None = None):
        """
        Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Model to use
            base_url: Custom base URL (not used with official client)
        """
        self.model = model

        # Get API key from parameter, env var, or config
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = config_manager.get_provider_api_key("anthropic")

        if not self.api_key:
            config = config_manager.get_provider_config("anthropic")
            api_key_env = config.get("api_key_env") if config else "ANTHROPIC_API_KEY"
            raise ValueError(f"Anthropic API key not found. Set {api_key_env} environment variable.")

        # Use official Anthropic client with prompt caching beta header
        self.client = anthropic.AsyncAnthropic(api_key=self.api_key, default_headers={"anthropic-beta": "prompt-caching-2024-07-31"})

    async def chat(self, messages: list[LLMMessage], tools: list[dict] | None = None, **kwargs) -> LLMResponse:
        """Send messages to Anthropic and get a response.

        Args:
            messages: List of conversation messages
            tools: Optional list of tool schemas for native tool calling
            **kwargs: Additional parameters passed to the API
        """
        try:
            # Convert our message format to Anthropic format
            system_message = None
            system_cache_control = None
            anthropic_messages = []
            # Allow json_mode with native tools - we want JSON structured output for reasoning/todo_list
            # even when using native tool calling for tool invocations
            json_mode = kwargs.get("json_mode", False)

            for msg in messages:
                if msg.role == "system":
                    system_message = msg.content
                    system_cache_control = msg.cache_control
                elif msg.role == "user":
                    if msg.cache_control:
                        user_msg = {"role": "user", "content": [{"type": "text", "text": msg.content, "cache_control": msg.cache_control}]}
                    else:
                        user_msg = {"role": "user", "content": msg.content}
                    anthropic_messages.append(user_msg)
                elif msg.role == "tool":
                    # Tool result message - Anthropic uses tool_result content block
                    anthropic_messages.append({
                        "role": "user",
                        "content": [{
                            "type": "tool_result",
                            "tool_use_id": msg.tool_call_id,
                            "content": msg.content,
                        }]
                    })
                elif msg.role == "assistant":
                    # Check if this assistant message has native tool_calls
                    if msg.tool_calls:
                        # Format tool_calls for Anthropic API
                        content_blocks = []
                        if msg.content:
                            content_blocks.append({"type": "text", "text": msg.content})
                        for tc in msg.tool_calls:
                            content_blocks.append({
                                "type": "tool_use",
                                "id": tc.get("tool_call_id", ""),
                                "name": tc.get("function", ""),
                                "input": tc.get("arguments", {}),
                            })
                        anthropic_messages.append({
                            "role": "assistant",
                            "content": content_blocks,
                        })
                    elif msg.cache_control:
                        assistant_msg = {
                            "role": "assistant",
                            "content": [{"type": "text", "text": msg.content, "cache_control": msg.cache_control}],
                        }
                        anthropic_messages.append(assistant_msg)
                    else:
                        anthropic_messages.append({"role": "assistant", "content": msg.content})

            # Add prefill to force JSON output when json_mode is enabled (and not using native tools)
            if json_mode:
                anthropic_messages.append({"role": "assistant", "content": '{"done":'})

            # Prepare request parameters
            request_kwargs = {
                "model": self.model,
                "messages": anthropic_messages,
                "max_tokens": kwargs.get("max_tokens") or 4096,
            }

            # Add temperature if provided
            if "temperature" in kwargs:
                request_kwargs["temperature"] = kwargs["temperature"]

            # Add stop sequences when in json_mode without native tools
            # Skip when using tools as the model outputs JSON + tool_use blocks
            # Note: \n\n is whitespace-only which Anthropic rejects, so we skip it
            if json_mode and not tools:
                request_kwargs["stop_sequences"] = ["\n[", "\nLet me"]

            # Add tools if provided (native tool calling)
            if tools:
                # Convert OpenAI-style tool schemas to Anthropic format
                anthropic_tools = []
                for tool in tools:
                    func = tool.get("function", {})
                    anthropic_tools.append({
                        "name": func.get("name", ""),
                        "description": func.get("description", ""),
                        "input_schema": func.get("parameters", {"type": "object", "properties": {}}),
                    })
                request_kwargs["tools"] = anthropic_tools

            # Add system message if present (with cache_control support)
            if system_message:
                if system_cache_control:
                    request_kwargs["system"] = [{"type": "text", "text": system_message, "cache_control": system_cache_control}]
                else:
                    request_kwargs["system"] = system_message

            # Call Anthropic API
            response = await self.client.messages.create(**request_kwargs)

            # Convert response to our format
            content = ""
            tool_calls = None

            for block in response.content:
                if block.type == "text":
                    content += block.text
                elif block.type == "tool_use":
                    if tool_calls is None:
                        tool_calls = []
                    # Convert to OpenAI-compatible format for our runtime
                    tool_calls.append(type("ToolCall", (), {
                        "id": block.id,
                        "function": type("Function", (), {
                            "name": block.name,
                            "arguments": json.dumps(block.input) if isinstance(block.input, dict) else block.input,
                        })(),
                    })())

            # If we used JSON prefill, prepend the prefill string
            if json_mode:
                content = '{"done":' + content

            # Build usage dict with cache metrics if available
            usage = None
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
                }
                # Anthropic returns cache metrics for prompt caching
                if hasattr(response.usage, "cache_creation_input_tokens"):
                    usage["cache_creation_tokens"] = response.usage.cache_creation_input_tokens
                if hasattr(response.usage, "cache_read_input_tokens"):
                    usage["cached_tokens"] = response.usage.cache_read_input_tokens

            return LLMResponse(
                content=content,
                model=response.model,
                usage=usage,
                finish_reason=response.stop_reason,
                tool_calls=tool_calls,
            )

        except Exception as e:
            logger.error("Anthropic API error", error=str(e))
            raise
