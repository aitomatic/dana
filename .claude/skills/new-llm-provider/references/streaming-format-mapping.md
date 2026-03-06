# Streaming Format Mapping

Dana's `LLMStreamChunk` has 3 types that every provider must map to:

```python
@dataclass
class LLMStreamChunk:
    type: str       # "text_delta" | "tool_use" | "thinking"
    content: str    # text content (for text_delta and thinking)
    tool_call: dict | None  # {"id": str, "name": str, "input": dict} (for tool_use)
```

## Provider → LLMStreamChunk Mapping

### OpenAI Chat Completions API (gpt-4o, gpt-4.1, etc.)

| Raw Event | LLMStreamChunk |
|-----------|---------------|
| `chunk.choices[0].delta.content` (not None) | `type="text_delta", content=delta.content` |
| `chunk.choices[0].delta.tool_calls[].function` | Accumulate incrementally by `index` |
| `choice.finish_reason == "tool_calls"` | Flush accumulated → `type="tool_use", tool_call={id, name, input}` |

**Tool calls arrive incrementally** — `id` and `name` come in the first delta, `arguments` stream across multiple deltas as JSON string fragments. Must accumulate by `tool_calls[].index` and flush when `finish_reason == "tool_calls"`.

### OpenAI Responses API (gpt-5+, o3+, o4+)

| Raw Event Type | LLMStreamChunk |
|----------------|---------------|
| `response.output_text.delta` | `type="text_delta", content=event.delta` |
| `response.output_item.done` where `item.type == "function_call"` | `type="tool_use", tool_call={id: item.call_id, name: item.name, input: json.loads(item.arguments)}` |
| `response.reasoning.delta` (if present) | `type="thinking", content=event.delta` |

**Events we DON'T need to handle** (informational only):
- `response.created`, `response.in_progress`, `response.completed` — lifecycle events
- `response.output_item.added` — item announced but not complete yet
- `response.content_part.added`, `response.content_part.done` — part lifecycle
- `response.output_text.done` — final text (already streamed via deltas)
- `response.function_call_arguments.delta` — incremental args (we get complete args at `output_item.done`)
- `response.function_call_arguments.done` — complete args (redundant with `output_item.done`)

**Reasoning quirk**: `gpt-5.2-chat` sends `ResponseReasoningItem` in `output_item.added/done` but does NOT send `response.reasoning.delta`. The reasoning content is opaque (not exposed in the event).

### Anthropic Messages API

| Raw Event | LLMStreamChunk |
|-----------|---------------|
| `event.type == "content_block_delta"` AND `event.delta.type == "text_delta"` | `type="text_delta", content=event.delta.text` |
| `event.type == "content_block_stop"` AND `event.content_block.type == "tool_use"` | `type="tool_use", tool_call={id: block.id, name: block.name, input: block.input}` |

**Tool calls arrive complete** at `content_block_stop` — the SDK assembles the full block. No manual accumulation needed.

**Note**: Uses `client.messages.stream()` context manager, not `client.messages.create(stream=True)`.

### Gemini API

| Raw Event | LLMStreamChunk |
|-----------|---------------|
| `chunk.candidates[0].content.parts[].text` (not None) | `type="text_delta", content=part.text` |
| `chunk.candidates[0].content.parts[].function_call` (not None) | `type="tool_use", tool_call={id: uuid4(), name: fc.name, input: dict(fc.args)}` |

**Gemini quirks**:
- No native `tool_call_id` — must generate UUID
- Tool calls arrive complete per chunk (no incremental assembly)
- Guard against empty candidates/content/parts (all can be None)
- Uses `client.aio.models.generate_content_stream()` (not a streaming context manager)

## Adding a New Provider

When implementing `stream()` for a new provider:

1. **Run the raw diagnostics first** (`test-raw-streaming-diagnostics.py`) to see actual event shapes
2. **Map text deltas** → `LLMStreamChunk(type="text_delta", content=...)`
3. **Map tool calls** → `LLMStreamChunk(type="tool_use", tool_call={"id": ..., "name": ..., "input": ...})`
4. **Map thinking** (if supported) → `LLMStreamChunk(type="thinking", content=...)`
5. **Ignore lifecycle events** (created, completed, etc.) — only yield data-carrying events

### Common Pitfalls
- **Incremental tool calls**: OpenAI Chat Completions sends args as string fragments — must accumulate and `json.loads()` at the end
- **Missing tool_call_id**: Some providers (Gemini) don't provide one — generate a UUID
- **None content guards**: Always check for None before yielding
- **Post-loop flush**: If tool calls weren't flushed on `finish_reason`, flush remaining after the loop ends
- **Input format mismatch (multi-API providers)**: `prepare_messages()` produces Chat Completions format (`tool_calls` field on assistant messages, `role: "tool"` for results). The Responses API rejects this — it expects `{"type": "function_call", ...}` and `{"type": "function_call_output", ...}` as separate input items. Use `_convert_to_responses_input()` to transform. The `id` field must start with `fc_` (not `call_`). Always run Q4 diagnostic to catch this.
