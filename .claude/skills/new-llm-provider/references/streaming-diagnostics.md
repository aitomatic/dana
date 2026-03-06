# Streaming Diagnostics

## Purpose

The diagnostic test at `tests/live/common/llm/providers/test-raw-streaming-diagnostics.py` bypasses Dana's `LLMStreamChunk` layer and prints raw events/chunks from each provider's SDK. Run this BEFORE implementing a new provider to understand the exact event shapes.

## How to Run

```bash
cd dana_agent
uv run pytest tests/live/common/llm/providers/test-raw-streaming-diagnostics.py --live -v -s -k {provider}
```

Supported providers: `azure`, `openai`, `anthropic`, `gemini`.

## Adding a New Provider

Add a test class to `test-raw-streaming-diagnostics.py`:

```python
class TestNewProviderRawStreaming:
    """Diagnose raw {Name} streaming chunks."""

    @pytest.mark.live
    def test_{name}_raw_stream(self):
        # Option A: OpenAI-compatible (use AsyncOpenAI)
        from openai import AsyncOpenAI
        api_key = os.environ.get("{NAME}_API_KEY")
        if not api_key:
            pytest.skip("{NAME}_API_KEY not set")
        client = AsyncOpenAI(api_key=api_key, base_url="https://api.provider.com/v1")

        cfg = PROVIDERS["{name}"]
        for q in QUESTIONS:
            events = asyncio.run(
                _stream_openai_chat_completions(client, cfg.model, q["messages"], q["tools"])
            )
            print_events(events, "{name}", q["label"])

        # Option B: Custom SDK — write a dedicated _stream_{name}() helper
```

Also add the provider config to `PROVIDERS` dict:
```python
PROVIDERS = {
    ...
    "{name}": ProviderConfig("{name}", "model-name", "{NAME}_API_KEY"),
}
```

## What the Output Tells You

### Text Streaming
Look for events with text content. Note the event type and which attribute holds the text:
- OpenAI Chat: `chunk.choices[0].delta.content`
- OpenAI Responses: `event.delta` (on `response.output_text.delta`)
- Anthropic: `event.delta.text` (on `content_block_delta`)
- Gemini: `chunk.candidates[0].content.parts[0].text`

### Tool Calling
Look for how tool calls arrive:
- **Incremental** (OpenAI Chat): `delta.tool_calls[].function.arguments` fragments → must accumulate
- **Complete at end** (OpenAI Responses): `output_item.done` with full `ResponseFunctionToolCall`
- **Complete at block stop** (Anthropic): `content_block_stop` with assembled `tool_use` block
- **Complete per chunk** (Gemini): `part.function_call` with full args

### Reasoning/Thinking
Look for thinking-related events:
- OpenAI Responses: `response.reasoning.delta` or `ResponseReasoningItem` in `output_item`
- Anthropic: `thinking` content blocks (when extended thinking enabled)
- Others: typically not supported

## 4 Test Questions

| # | Label | Purpose | Layer |
|---|-------|---------|-------|
| 1 | `Q1-simple-hello` | Basic text streaming — verify `text_delta` mapping | Raw SDK |
| 2 | `Q2-reasoning-life-of-pi` | Longer response — reveals reasoning/thinking chunks | Raw SDK |
| 3 | `Q3-trigger-tool-call` | Tool calling — reveals `tool_use` chunk format | Raw SDK |
| 4 | `Q4-multi-turn-tool-history` | Multi-turn with tool call history in input | Provider layer |

Q3 uses a `get_weather` dummy tool that asks about Tokyo weather, forcing the model to emit a tool call.

Q4 is different from Q1-Q3: it runs through our `provider.stream()` method (not raw SDK) with a conversation that includes a prior assistant tool call and tool result. This catches **input format mismatches** — e.g., Chat Completions `tool_calls` field being rejected by the Responses API, which expects `function_call` / `function_call_output` items instead.
