# Provider Implementation Patterns

## Pattern 1: OpenAI-Compatible Provider (Most Common)

Most providers (Mistral, Groq, DeepSeek, Together, xAI, etc.) use OpenAI-compatible APIs. Extend `OpenAICompatibleProvider` — only need `__init__`.

```python
"""[ProviderName] Provider Implementation"""

from openai import AsyncOpenAI
import structlog

from ...config import config_manager
from .openai_compatible_base import OpenAICompatibleProvider

logger = structlog.get_logger()


class {Name}Provider(OpenAICompatibleProvider):
    """[ProviderName] API provider."""

    def __init__(self, api_key: str | None = None, model: str = "default-model", base_url: str | None = None):
        self.model = model
        self.api_key = api_key or config_manager.get_provider_api_key("{name}")
        if not self.api_key:
            config = config_manager.get_provider_config("{name}")
            api_key_env = config.get("api_key_env") if config else "{NAME}_API_KEY"
            raise ValueError(f"{Name} API key not found. Set {api_key_env} environment variable.")
        self.base_url = base_url or config_manager.get_provider_base_url("{name}")
        self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
```

`OpenAICompatibleProvider` inherits from `LLMProvider` and provides:
- `chat()` — async chat completion via `self.client.chat.completions.create()`
- `stream()` — auto-selects between Chat Completions and Responses API based on model
- `_stream_chat_completions()` — streaming via `chat.completions.create(stream=True)`
- `_stream_responses()` — streaming via `responses.create(stream=True)` (gpt-5+, o3+, o4+)
- `prepare_messages()` — converts LLMMessage[] to OpenAI wire format
- `prepare_tools()` — converts MethodSignature[] to OpenAI tool schema
- `supports_native_tools = True`

### Model Restrictions

`OpenAICompatibleProvider` auto-filters parameters that certain models don't support. See `MODEL_RESTRICTIONS` dict in `openai_compatible_base.py`. The model family matcher checks prefixes with `-`, `_`, or `.` separators (e.g., `gpt-5.2-chat` matches `gpt-5` family).

## Pattern 2: Custom API Provider

For providers with non-OpenAI APIs (e.g., Anthropic, Gemini), extend `LLMProvider` directly.

```python
"""[ProviderName] Provider Implementation"""

import structlog
from ...config import config_manager
from ..types import LLMProvider, LLMMessage, LLMResponse, LLMStreamChunk

logger = structlog.get_logger()


class {Name}Provider(LLMProvider):
    """[ProviderName] API provider with custom API format."""

    def __init__(self, api_key: str | None = None, model: str = "default-model"):
        self.model = model
        self.api_key = api_key or config_manager.get_provider_api_key("{name}")
        if not self.api_key:
            raise ValueError("{NAME}_API_KEY not found")
        # Initialize provider-specific client here

    @property
    def supports_native_tools(self) -> bool:
        return True  # or False if no tool calling support

    def prepare_messages(self, messages: list[LLMMessage]) -> tuple:
        """Convert LLMMessage[] to provider wire format.
        Returns: (system_param, messages_list)
        """
        # Must handle: system, user, assistant, tool roles
        # Must handle: tool_calls on assistant messages
        # Must handle: tool_call_id on tool messages
        # Must handle: None content (replace with "")
        ...

    async def chat(self, messages: list[LLMMessage], tools=None, **kwargs) -> LLMResponse:
        """Send messages and return LLMResponse."""
        ...

    async def stream(self, messages: list[LLMMessage], tools=None, **kwargs):
        """Yield LLMStreamChunk objects.

        Map provider-specific events to exactly 3 chunk types:
        - LLMStreamChunk(type="text_delta", content="...")
        - LLMStreamChunk(type="tool_use", tool_call={"id": ..., "name": ..., "input": ...})
        - LLMStreamChunk(type="thinking", content="...")

        See references/streaming-format-mapping.md for mapping examples.
        """
        ...
```

### Streaming Implementation Checklist

When implementing `stream()` for a custom provider:

1. **Run diagnostics first**: `test-raw-streaming-diagnostics.py -k {name}` to see raw event shapes
2. **Text deltas**: Map to `LLMStreamChunk(type="text_delta", content=text)`
3. **Tool calls**: Map to `LLMStreamChunk(type="tool_use", tool_call={"id": str, "name": str, "input": dict})`
   - If tool calls arrive incrementally, accumulate and flush when complete
   - If no native `tool_call_id`, generate a UUID
4. **Thinking/reasoning**: Map to `LLMStreamChunk(type="thinking", content=text)` if supported
5. **Ignore lifecycle events**: Don't yield for created/completed/in_progress events
6. **Post-loop flush**: After the stream ends, flush any accumulated tool calls not yet emitted

## Factory Registration

In `dana/common/llm/providers/factory.py`, add:
```python
elif provider_name == "{name}":
    from .{name} import {Name}Provider
    return {Name}Provider(model=model, **kwargs)
```

## Config Registration

In `dana/config.json`, add under `"providers"`:
```json
"{name}": {
    "api_key_env": "{NAME}_API_KEY",
    "default_model": "model-name",
    "base_url": "https://api.provider.com/v1",
    "base_url_env": "{NAME}_BASE_URL",
    "priority": 5
}
```

## Common Pitfalls
- **None content**: APIs reject null content — always default to `""`
- **tool_call_id format**: Must match exactly between assistant tool_calls and tool results
- **Consecutive roles**: Some providers reject consecutive user or assistant messages
- **arguments type**: OpenAI expects `arguments` as JSON string, not dict
- **Streaming tool calls**: OpenAI Chat Completions sends tool call args incrementally — accumulate by index before yielding
- **Model parameter restrictions**: Some models (gpt-5+) reject `temperature=0` — use `_filter_params_for_model()` or add to `MODEL_RESTRICTIONS`
