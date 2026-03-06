"""
Raw streaming diagnostics — inspect exactly what each provider library sends.

Sends 3 questions through each provider's streaming API and prints every raw
event/chunk with its type, attributes, and data. This helps us understand
the actual chunk shapes so we can handle them correctly in our LLMStreamChunk
mapping code.

Questions:
  1. "Hello" — simple text response
  2. "Think deeply and tell me what is pi as in Life of Pi" — longer/reasoning
  3. "Try calling any tool that I provide to you" — trigger tool_use chunks

Run one provider at a time:
  source /path/to/.env && uv run pytest tests/live/common/llm/providers/test-raw-streaming-diagnostics.py --live -v -s -k azure
  source /path/to/.env && uv run pytest tests/live/common/llm/providers/test-raw-streaming-diagnostics.py --live -v -s -k anthropic
  source /path/to/.env && uv run pytest tests/live/common/llm/providers/test-raw-streaming-diagnostics.py --live -v -s -k openai
  source /path/to/.env && uv run pytest tests/live/common/llm/providers/test-raw-streaming-diagnostics.py --live -v -s -k gemini
"""

import asyncio
from dataclasses import dataclass
import os

from dotenv import load_dotenv
import pytest

from dana.common.llm.types import LLMMessage


load_dotenv()


# ---------------------------------------------------------------------------
# Provider configurations
# ---------------------------------------------------------------------------


@dataclass
class ProviderConfig:
    name: str
    model: str
    env_key: str  # env var that must be set


PROVIDERS = {
    "azure": ProviderConfig("azure", "gpt-5.2-chat", "AZURE_OPENAI_API_KEY"),
    "openai": ProviderConfig("openai", "gpt-5.2", "OPENAI_API_KEY"),
    "anthropic": ProviderConfig("anthropic", "claude-sonnet-4-20250514", "ANTHROPIC_API_KEY"),
    "gemini": ProviderConfig("gemini", "gemini-2.5-flash", "GEMINI_API_KEY"),
}


# ---------------------------------------------------------------------------
# Simple tool definition for tool-calling test
# ---------------------------------------------------------------------------

DUMMY_TOOL = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get the current weather for a given city.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "The city name"},
            },
            "required": ["city"],
        },
    },
}


# ---------------------------------------------------------------------------
# Test questions
# ---------------------------------------------------------------------------

QUESTIONS = [
    {
        "label": "Q1-simple-hello",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello"},
        ],
        "tools": None,
    },
    {
        "label": "Q2-reasoning-life-of-pi",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Think deeply and tell me what is pi as in Life of Pi"},
        ],
        "tools": None,
    },
    {
        "label": "Q3-trigger-tool-call",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant. Use the tools provided when appropriate."},
            {"role": "user", "content": "What's the weather in Tokyo? Use the get_weather tool to find out."},
        ],
        "tools": [DUMMY_TOOL],
    },
]

# Q4 tests multi-turn with tool call history in the input.
# Chat Completions and Responses API use different formats for tool calls,
# so this question is sent separately through our provider layer (not raw SDK)
# to verify the full pipeline handles tool call history correctly.
Q4_MULTI_TURN = {
    "label": "Q4-multi-turn-tool-history",
    "messages": [
        LLMMessage(role="system", content="You are a helpful assistant. Use tools when appropriate."),
        LLMMessage(role="user", content="What's the weather in Tokyo?"),
        LLMMessage(
            role="assistant",
            content="",
            tool_calls=[
                {
                    "tool_call_id": "call_test_001",
                    "function": "get_weather",
                    "arguments": {"city": "Tokyo"},
                }
            ],
        ),
        LLMMessage(role="tool", content="Sunny, 25C", tool_call_id="call_test_001"),
        LLMMessage(role="user", content="Now check Paris too."),
    ],
    "tools": [DUMMY_TOOL],
}


# ---------------------------------------------------------------------------
# Raw streaming helpers — bypass our LLMStreamChunk layer
# ---------------------------------------------------------------------------


def _dump_obj(obj, depth=0) -> str:
    """Recursively dump an object's attributes for inspection."""
    indent = "  " * depth
    if isinstance(obj, (str, int, float, bool, type(None))):
        return repr(obj)
    if isinstance(obj, dict):
        if not obj:
            return "{}"
        lines = ["{"]
        for k, v in obj.items():
            lines.append(f"{indent}  {k}: {_dump_obj(v, depth + 1)}")
        lines.append(f"{indent}}}")
        return "\n".join(lines)
    if isinstance(obj, (list, tuple)):
        if not obj:
            return "[]"
        lines = ["["]
        for item in obj[:5]:  # cap at 5 items
            lines.append(f"{indent}  {_dump_obj(item, depth + 1)}")
        if len(obj) > 5:
            lines.append(f"{indent}  ... ({len(obj)} total)")
        lines.append(f"{indent}]")
        return "\n".join(lines)
    # Object with attributes
    attrs = {}
    for attr in dir(obj):
        if attr.startswith("_"):
            continue
        try:
            val = getattr(obj, attr)
            if callable(val):
                continue
            attrs[attr] = val
        except Exception:
            pass
    if attrs:
        lines = [f"<{type(obj).__name__}>"]
        for k, v in attrs.items():
            val_str = _dump_obj(v, depth + 1)
            # Truncate long values
            if len(val_str) > 200:
                val_str = val_str[:200] + "..."
            lines.append(f"{indent}  .{k} = {val_str}")
        return "\n".join(lines)
    return repr(obj)


async def _stream_openai_chat_completions(client, model, messages, tools=None):
    """Raw stream via Chat Completions API."""
    kwargs = {"model": model, "messages": messages, "stream": True}
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"

    response = await client.chat.completions.create(**kwargs)
    events = []
    async for chunk in response:
        events.append(chunk)
    return events


async def _stream_openai_responses(client, model, messages, tools=None):
    """Raw stream via Responses API."""
    resp_tools = None
    if tools:
        resp_tools = [
            {
                "type": "function",
                "name": t["function"]["name"],
                "description": t["function"].get("description", ""),
                "parameters": t["function"].get("parameters", {}),
            }
            for t in tools
        ]

    kwargs = {"model": model, "input": messages, "stream": True}
    if resp_tools:
        kwargs["tools"] = resp_tools

    stream = await client.responses.create(**kwargs)
    events = []
    async for event in stream:
        events.append(event)
    return events


async def _stream_anthropic(client, model, messages, tools=None):
    """Raw stream via Anthropic Messages API."""
    system = None
    api_messages = []
    for msg in messages:
        if msg["role"] == "system":
            system = msg["content"]
        else:
            api_messages.append(msg)

    kwargs = {"model": model, "messages": api_messages, "max_tokens": 4096}
    if system:
        kwargs["system"] = system
    if tools:
        kwargs["tools"] = [
            {
                "name": t["function"]["name"],
                "description": t["function"].get("description", ""),
                "input_schema": t["function"].get("parameters", {}),
            }
            for t in tools
        ]

    events = []
    async with client.messages.stream(**kwargs) as stream_resp:
        async for event in stream_resp:
            events.append(event)
    return events


async def _stream_gemini(client, model, messages, tools=None):
    """Raw stream via Gemini API."""
    from google import genai as genai_types

    system_instruction = None
    contents = []
    for msg in messages:
        if msg["role"] == "system":
            system_instruction = msg["content"]
        elif msg["role"] == "user":
            contents.append(genai_types.types.Content(role="user", parts=[genai_types.types.Part(text=msg["content"])]))
        elif msg["role"] == "assistant":
            contents.append(genai_types.types.Content(role="model", parts=[genai_types.types.Part(text=msg["content"])]))

    config = genai_types.types.GenerateContentConfig()
    if system_instruction:
        config.system_instruction = system_instruction
    if tools:
        gemini_tools = []
        for t in tools:
            func = t["function"]
            # Build properties for Gemini schema
            props = {}
            required = func.get("parameters", {}).get("required", [])
            for pname, pdef in func.get("parameters", {}).get("properties", {}).items():
                props[pname] = genai_types.types.Schema(
                    type=genai_types.types.Type.STRING,
                    description=pdef.get("description", ""),
                )
            gemini_tools.append(
                genai_types.types.Tool(
                    function_declarations=[
                        genai_types.types.FunctionDeclaration(
                            name=func["name"],
                            description=func.get("description", ""),
                            parameters=genai_types.types.Schema(
                                type=genai_types.types.Type.OBJECT,
                                properties=props,
                                required=required,
                            ),
                        )
                    ]
                )
            )
        config.tools = gemini_tools

    chunks = []
    stream = await client.aio.models.generate_content_stream(
        model=model,
        contents=contents,
        config=config,
    )
    async for chunk in stream:
        chunks.append(chunk)
    return chunks


# ---------------------------------------------------------------------------
# Print helpers
# ---------------------------------------------------------------------------


def print_events(events: list, provider: str, label: str):
    """Print raw events with type and key attributes."""
    print(f"\n{'=' * 80}")
    print(f"  {provider.upper()} | {label} | {len(events)} events")
    print(f"{'=' * 80}")

    for i, event in enumerate(events):
        event_type = getattr(event, "type", type(event).__name__)
        print(f"\n  [{i:3d}] type={event_type}")
        print(f"        {_dump_obj(event)}")

        # Safety cap — don't print thousands of identical text deltas
        if i >= 50:
            remaining = len(events) - i - 1
            if remaining > 0:
                # Summarize remaining types
                remaining_types = {}
                for e in events[i + 1 :]:
                    t = getattr(e, "type", type(e).__name__)
                    remaining_types[t] = remaining_types.get(t, 0) + 1
                print(f"\n  ... {remaining} more events: {remaining_types}")
            break


# ---------------------------------------------------------------------------
# Q4 helper — multi-turn with tool history, runs through our provider layer
# ---------------------------------------------------------------------------


async def _stream_q4_via_provider(provider_name: str, model: str):
    """Stream Q4 (multi-turn with tool call history) through our provider.

    This catches format mismatches between Chat Completions and Responses API
    input schemas (e.g., tool_calls field rejected by Responses API).
    """
    from dana.common.llm.llm import LLM

    llm = LLM(provider=provider_name, model=model)
    q = Q4_MULTI_TURN
    chunks = []
    async for chunk in llm.provider.stream(q["messages"], tools=q["tools"]):
        chunks.append(chunk)
    return chunks


# ---------------------------------------------------------------------------
# Test classes — one per provider
# ---------------------------------------------------------------------------


class TestAzureRawStreaming:
    """Diagnose raw Azure OpenAI streaming chunks."""

    @pytest.mark.live
    def test_azure_raw_stream(self):
        from openai import AsyncAzureOpenAI

        cfg = PROVIDERS["azure"]
        api_key = os.environ.get("AZURE_OPENAI_API_KEY")
        endpoint = os.environ.get("AZURE_OPENAI_API_URL")
        api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
        if not api_key or not endpoint:
            pytest.skip("AZURE_OPENAI_API_KEY or AZURE_OPENAI_API_URL not set")

        client = AsyncAzureOpenAI(api_key=api_key, azure_endpoint=endpoint, api_version=api_version)
        is_responses = cfg.model.startswith("gpt-5") or cfg.model.startswith("o3") or cfg.model.startswith("o4")

        for q in QUESTIONS:
            if is_responses:
                events = asyncio.run(_stream_openai_responses(client, cfg.model, q["messages"], q["tools"]))
            else:
                events = asyncio.run(_stream_openai_chat_completions(client, cfg.model, q["messages"], q["tools"]))
            print_events(events, "azure", q["label"])

    @pytest.mark.live
    def test_azure_q4_multi_turn_tool_history(self):
        """Q4: Multi-turn with tool call history — verifies input format conversion."""
        cfg = PROVIDERS["azure"]
        if not os.environ.get("AZURE_OPENAI_API_KEY"):
            pytest.skip("AZURE_OPENAI_API_KEY not set")
        chunks = asyncio.run(_stream_q4_via_provider("azure", cfg.model))
        assert len(chunks) > 0, "Q4 produced no chunks — input format likely rejected"
        types = {c.type for c in chunks}
        print(f"\n  Q4 multi-turn: {len(chunks)} chunks, types={types}")
        # Should produce tool_use (asking for Paris weather) or text_delta
        assert types & {"text_delta", "tool_use"}, f"Unexpected chunk types: {types}"


class TestOpenAIRawStreaming:
    """Diagnose raw OpenAI streaming chunks."""

    @pytest.mark.live
    def test_openai_raw_stream(self):
        from openai import AsyncOpenAI

        cfg = PROVIDERS["openai"]
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set")

        client = AsyncOpenAI(api_key=api_key)
        is_responses = cfg.model.startswith("gpt-5") or cfg.model.startswith("o3") or cfg.model.startswith("o4")

        for q in QUESTIONS:
            if is_responses:
                events = asyncio.run(_stream_openai_responses(client, cfg.model, q["messages"], q["tools"]))
            else:
                events = asyncio.run(_stream_openai_chat_completions(client, cfg.model, q["messages"], q["tools"]))
            print_events(events, "openai", q["label"])

    @pytest.mark.live
    def test_openai_q4_multi_turn_tool_history(self):
        """Q4: Multi-turn with tool call history — verifies input format conversion."""
        cfg = PROVIDERS["openai"]
        if not os.environ.get("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not set")
        chunks = asyncio.run(_stream_q4_via_provider("openai", cfg.model))
        assert len(chunks) > 0, "Q4 produced no chunks — input format likely rejected"
        types = {c.type for c in chunks}
        print(f"\n  Q4 multi-turn: {len(chunks)} chunks, types={types}")
        assert types & {"text_delta", "tool_use"}, f"Unexpected chunk types: {types}"


class TestAnthropicRawStreaming:
    """Diagnose raw Anthropic streaming events."""

    @pytest.mark.live
    def test_anthropic_raw_stream(self):
        import anthropic

        cfg = PROVIDERS["anthropic"]
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set")

        client = anthropic.AsyncAnthropic(api_key=api_key)

        for q in QUESTIONS:
            events = asyncio.run(_stream_anthropic(client, cfg.model, q["messages"], q["tools"]))
            print_events(events, "anthropic", q["label"])

    @pytest.mark.live
    def test_anthropic_q4_multi_turn_tool_history(self):
        """Q4: Multi-turn with tool call history — verifies input format conversion."""
        cfg = PROVIDERS["anthropic"]
        if not os.environ.get("ANTHROPIC_API_KEY"):
            pytest.skip("ANTHROPIC_API_KEY not set")
        chunks = asyncio.run(_stream_q4_via_provider("anthropic", cfg.model))
        assert len(chunks) > 0, "Q4 produced no chunks — input format likely rejected"
        types = {c.type for c in chunks}
        print(f"\n  Q4 multi-turn: {len(chunks)} chunks, types={types}")
        assert types & {"text_delta", "tool_use"}, f"Unexpected chunk types: {types}"


class TestGeminiRawStreaming:
    """Diagnose raw Gemini streaming chunks."""

    @pytest.mark.live
    def test_gemini_raw_stream(self):
        cfg = PROVIDERS["gemini"]
        if not os.environ.get(cfg.env_key):
            pytest.skip(f"{cfg.env_key} not set")

        from google import genai

        client = genai.Client(api_key=os.environ[cfg.env_key])

        for q in QUESTIONS:
            chunks = asyncio.run(_stream_gemini(client, cfg.model, q["messages"], q["tools"]))
            print_events(chunks, "gemini", q["label"])

    @pytest.mark.live
    def test_gemini_q4_multi_turn_tool_history(self):
        """Q4: Multi-turn with tool call history — verifies input format conversion."""
        cfg = PROVIDERS["gemini"]
        if not os.environ.get(cfg.env_key):
            pytest.skip(f"{cfg.env_key} not set")
        chunks = asyncio.run(_stream_q4_via_provider("gemini", cfg.model))
        assert len(chunks) > 0, "Q4 produced no chunks — input format likely rejected"
        types = {c.type for c in chunks}
        print(f"\n  Q4 multi-turn: {len(chunks)} chunks, types={types}")
        assert types & {"text_delta", "tool_use"}, f"Unexpected chunk types: {types}"
