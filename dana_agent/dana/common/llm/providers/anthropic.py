"""
Anthropic Provider Implementation
"""

import json

import anthropic
import structlog

from ...config import config_manager
from ..types import LLMMessage, LLMProvider, LLMResponse


logger = structlog.get_logger()


def _ensure_content_blocks(content) -> list[dict]:
    """Convert any content value to a list of Anthropic content blocks."""
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    elif isinstance(content, list):
        return list(content)
    return [{"type": "text", "text": str(content)}]


def _merge_consecutive_same_role(messages: list[dict]) -> list[dict]:
    """Merge consecutive messages with the same role into one message."""
    if not messages:
        return messages
    merged = [messages[0]]
    for msg in messages[1:]:
        if msg["role"] == merged[-1]["role"]:
            prev_blocks = _ensure_content_blocks(merged[-1]["content"])
            new_blocks = _ensure_content_blocks(msg["content"])
            merged[-1]["content"] = prev_blocks + new_blocks
        else:
            merged.append(msg)
    return merged


def prepare_anthropic_messages(
    messages: list[LLMMessage],
) -> tuple[str | list[dict] | None, list[dict]]:
    """Convert LLMMessage objects to Anthropic API format.

    Returns:
        (system, messages) where system is None, a plain string, or a list
        of content blocks; and messages is the list of user/assistant dicts.
    """
    system_blocks: list[dict] = []
    anthropic_messages: list[dict] = []

    for msg in messages:
        if msg.role == "system":
            block = {"type": "text", "text": msg.content}
            if msg.cache_control:
                block["cache_control"] = msg.cache_control
            system_blocks.append(block)

        elif msg.role == "user":
            if msg.cache_control:
                user_msg = {"role": "user", "content": [{"type": "text", "text": msg.content, "cache_control": msg.cache_control}]}
            else:
                user_msg = {"role": "user", "content": msg.content}
            anthropic_messages.append(user_msg)

        elif msg.role == "tool":
            tool_result_block = {
                "type": "tool_result",
                "tool_use_id": msg.tool_call_id,
                "content": msg.content,
            }
            # Group parallel tool results into one user message
            if (
                anthropic_messages
                and anthropic_messages[-1].get("role") == "user"
                and isinstance(anthropic_messages[-1].get("content"), list)
                and anthropic_messages[-1]["content"]
                and anthropic_messages[-1]["content"][0].get("type") == "tool_result"
            ):
                anthropic_messages[-1]["content"].append(tool_result_block)
            else:
                anthropic_messages.append({"role": "user", "content": [tool_result_block]})

        elif msg.role == "assistant":
            if msg.tool_calls:
                content_blocks = []
                if msg.content:
                    content_blocks.append({"type": "text", "text": msg.content})
                for tc in msg.tool_calls:
                    tc_id = tc.get("tool_call_id") or tc.get("id", "")
                    tc_name = tc.get("function") or tc.get("name", "")
                    content_blocks.append(
                        {
                            "type": "tool_use",
                            "id": tc_id,
                            "name": tc_name,
                            "input": tc.get("arguments", {}),
                        }
                    )
                anthropic_messages.append(
                    {
                        "role": "assistant",
                        "content": content_blocks,
                    }
                )
            elif msg.cache_control:
                anthropic_messages.append(
                    {
                        "role": "assistant",
                        "content": [{"type": "text", "text": msg.content, "cache_control": msg.cache_control}],
                    }
                )
            else:
                anthropic_messages.append({"role": "assistant", "content": msg.content})

    # Merge consecutive same-role messages
    anthropic_messages = _merge_consecutive_same_role(anthropic_messages)

    # Compute system return value
    if not system_blocks:
        system = None
    elif len(system_blocks) == 1 and "cache_control" not in system_blocks[0]:
        system = system_blocks[0]["text"]
    else:
        system = system_blocks

    return system, anthropic_messages


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider using the official Anthropic library."""

    @property
    def supports_native_tools(self) -> bool:
        """Anthropic supports native tool calling."""
        return True

    @property
    def supports_vision(self) -> bool:
        """Claude models support vision/image input."""
        return True

    def __init__(self, api_key: str | None = None, model: str = "claude-3-sonnet-20240229", base_url: str | None = None):
        """
        Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Model to use
            base_url: Custom base URL (defaults to ANTHROPIC_BASE_URL env var or config)
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

        # Get base URL from parameter or config (which checks ANTHROPIC_BASE_URL env var)
        if base_url:
            self.base_url = base_url
        else:
            self.base_url = config_manager.get_provider_base_url("anthropic")

        # Use official Anthropic client with prompt caching beta header
        client_kwargs = {
            "api_key": self.api_key,
            "default_headers": {"anthropic-beta": "prompt-caching-2024-07-31"},
        }
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
        self.client = anthropic.AsyncAnthropic(**client_kwargs)

    async def chat(self, messages: list[LLMMessage], tools: list[dict] | None = None, **kwargs) -> LLMResponse:
        """Send messages to Anthropic and get a response.

        Args:
            messages: List of conversation messages
            tools: Optional list of tool schemas for native tool calling
            **kwargs: Additional parameters passed to the API
        """
        try:
            system, anthropic_messages = prepare_anthropic_messages(messages)
            json_mode = kwargs.get("json_mode", False)

            # Add prefill to force JSON output when json_mode is enabled
            # Note: With native tools, Claude outputs text content (JSON) + tool_use blocks
            # The prefill helps ensure the text content is valid JSON
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
                    anthropic_tools.append(
                        {
                            "name": func.get("name", ""),
                            "description": func.get("description", ""),
                            "input_schema": func.get("parameters", {"type": "object", "properties": {}}),
                        }
                    )
                request_kwargs["tools"] = anthropic_tools
                # Enable parallel tool use (similar to OpenAI's tool_choice="auto")
                # This explicitly allows Claude to call multiple tools in a single response
                request_kwargs["tool_choice"] = {"type": "auto", "disable_parallel_tool_use": False}

            # Add system message if present
            if system is not None:
                request_kwargs["system"] = system

            # Call Anthropic API
            try:
                response = await self.client.messages.create(**request_kwargs)
            except Exception as e:
                logger.error("Anthropic API error", error=str(e))
                raise

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
                    tool_calls.append(
                        type(
                            "ToolCall",
                            (),
                            {
                                "id": block.id,
                                "function": type(
                                    "Function",
                                    (),
                                    {
                                        "name": block.name,
                                        "arguments": json.dumps(block.input) if isinstance(block.input, dict) else block.input,
                                    },
                                )(),
                            },
                        )()
                    )

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
