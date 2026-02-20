"""
Azure Provider Implementation
"""

from openai import AsyncAzureOpenAI
import structlog

from ...config import config_manager
from ..types import LLMMessage, LLMProvider, LLMResponse


logger = structlog.get_logger()


class AzureProvider(LLMProvider):
    """Azure OpenAI provider."""

    @property
    def supports_native_tools(self) -> bool:
        """Azure OpenAI supports native function/tool calling.

        The tool result flow is properly implemented:
        1. tool_call_id is stored when parsing native tool calls
        2. Tool results are sent with role="tool" and matching tool_call_id
        3. Assistant messages with tool_calls are properly formatted
        """
        return True

    @property
    def supports_vision(self) -> bool:
        """Azure OpenAI supports vision but content block format differs from Anthropic.

        Disabled until format-aware injection is implemented.
        Falls back to VisionParser text extraction.
        """
        return False

    def __init__(
        self, api_key: str | None = None, model: str = "gpt-35-turbo", base_url: str | None = None, api_version: str | None = None
    ):
        """
        Initialize Azure OpenAI provider.

        Args:
            api_key: Azure OpenAI API key (defaults to AZURE_OPENAI_API_KEY env var)
            model: Model/deployment name to use
            base_url: Azure OpenAI endpoint URL (e.g., https://your-resource.openai.azure.com)
            api_version: Azure OpenAI API version
        """
        self.model = model
        self.deployment_name = model

        # Get API key from parameter, env var, or config
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = config_manager.get_provider_api_key("azure")

        if not self.api_key:
            config = config_manager.get_provider_config("azure")
            api_key_env = config.get("api_key_env") if config else "AZURE_OPENAI_API_KEY"
            raise ValueError(f"Azure OpenAI API key not found. Set {api_key_env} environment variable.")

        # Get base URL (Azure endpoint) from parameter, env var, or config
        if base_url:
            azure_endpoint = base_url
        else:
            azure_endpoint = config_manager.get_provider_base_url("azure")

        if not azure_endpoint:
            raise ValueError("Azure OpenAI endpoint URL not found. Set AZURE_OPENAI_API_URL environment variable.")

        # Clean up the endpoint URL - remove trailing slashes
        azure_endpoint = azure_endpoint.rstrip("/")

        # Get API version from parameter, env var, or config
        if api_version:
            self.api_version = api_version
        else:
            self.api_version = config_manager.get_provider_api_version("azure") or "2024-02-15-preview"

        # Use the dedicated Azure OpenAI client
        self.client = AsyncAzureOpenAI(
            api_key=self.api_key,
            azure_endpoint=azure_endpoint,
            api_version=self.api_version,
        )

    async def chat(self, messages: list[LLMMessage], tools: list[dict] | None = None, **kwargs) -> LLMResponse:
        """Send messages to Azure OpenAI and get a response.

        Args:
            messages: List of conversation messages
            tools: Optional list of tool schemas for native function calling
            **kwargs: Additional parameters passed to the API
        """
        try:
            # Convert our message format to OpenAI format
            openai_messages = []
            for msg in messages:
                if msg.role == "system":
                    openai_messages.append({"role": "system", "content": msg.content})
                elif msg.role == "user":
                    openai_messages.append({"role": "user", "content": msg.content})
                elif msg.role == "tool":
                    # Tool result message - requires tool_call_id
                    openai_messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": msg.tool_call_id,
                            "content": msg.content,
                        }
                    )
                elif msg.role == "assistant":
                    # Check if this assistant message has native tool_calls
                    if msg.tool_calls:
                        # Format tool_calls for Azure OpenAI API
                        # Support multiple formats:
                        # 1. Runtime format: {"tool_call_id": "...", "function": "name", "arguments": {...}}
                        # 2. NativeToolCall format: {"id": "...", "name": "...", "arguments": {...}}
                        formatted_tool_calls = []
                        for tc in msg.tool_calls:
                            # Get tool call ID (try both key names)
                            tc_id = tc.get("tool_call_id") or tc.get("id", "")
                            # Get function name (try both key names)
                            tc_name = tc.get("function") or tc.get("name", "")
                            formatted_tool_calls.append(
                                {
                                    "id": tc_id,
                                    "type": "function",
                                    "function": {
                                        "name": tc_name,
                                        "arguments": str(tc.get("arguments", {})),
                                    },
                                }
                            )
                        openai_messages.append(
                            {
                                "role": "assistant",
                                "content": msg.content or None,
                                "tool_calls": formatted_tool_calls,
                            }
                        )
                    else:
                        openai_messages.append({"role": "assistant", "content": msg.content})

            # Build request parameters - filter out our custom parameters and None values
            # Note: Some newer Azure OpenAI models reject null values for max_tokens
            filtered_kwargs = {k: v for k, v in kwargs.items() if k not in ["json_mode"] and v is not None}
            request_kwargs = {"model": self.deployment_name, "messages": openai_messages, **filtered_kwargs}

            # Add tools if provided
            if tools:
                request_kwargs["tools"] = tools
                request_kwargs["tool_choice"] = "auto"

            # Enable JSON mode when requested (works with or without tools)
            if kwargs.get("json_mode", False):
                request_kwargs["response_format"] = {"type": "json_object"}

            # Call Azure OpenAI API
            response = await self.client.chat.completions.create(**request_kwargs)

            # Convert response to our format
            choice = response.choices[0]
            message = choice.message

            # Handle both text responses and function calls
            if hasattr(message, "tool_calls") and message.tool_calls:
                # Pass through function calls for base_agent to handle
                content = message.content or ""
                tool_calls = message.tool_calls
            else:
                # Standard text response
                content = message.content or ""
                tool_calls = None

            # Build usage dict
            usage = None
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }

            return LLMResponse(
                content=content,
                model=response.model,
                usage=usage,
                finish_reason=choice.finish_reason,
                tool_calls=tool_calls,
            )

        except Exception as e:
            logger.error("Azure OpenAI API error", error=str(e))
            raise
