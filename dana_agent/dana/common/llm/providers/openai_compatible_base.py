"""OpenAI-compatible provider base class for OpenAI and Azure."""

import json
from typing import Any

import httpx
from openai import APITimeoutError
import structlog

from ..types import LLMMessage, LLMProvider, LLMResponse, LLMStreamChunk, LLMTimeoutError


logger = structlog.get_logger()

# Model families with known parameter restrictions.
# Key is a model prefix matched against the model name.
MODEL_RESTRICTIONS: dict[str, dict] = {
    "gpt-5": {
        "temperature": {"allowed_values": [1], "default": 1},
    },
}

# Model prefixes that default to Responses API
RESPONSES_API_PREFIXES = ("gpt-5", "o3-", "o4-", "o3", "o4")


class OpenAICompatibleProvider(LLMProvider):
    """Base for providers using OpenAI-compatible API (OpenAI, Azure)."""

    client: Any  # AsyncOpenAI or AsyncAzureOpenAI
    model: str
    _use_responses_api: bool | None = None

    @property
    def supports_native_tools(self) -> bool:
        return True

    @staticmethod
    def _get_model_family(model: str) -> str | None:
        """Extract model family from model name for restriction lookup."""
        for family_prefix in MODEL_RESTRICTIONS:
            if model.startswith(family_prefix) and (len(model) == len(family_prefix) or model[len(family_prefix)] in "-_."):
                return family_prefix
        return None

    @staticmethod
    def _filter_params_for_model(model: str, params: dict) -> dict:
        """Filter/adjust parameters based on model-specific restrictions."""
        family = OpenAICompatibleProvider._get_model_family(model)
        if not family:
            return params

        restrictions = MODEL_RESTRICTIONS.get(family, {})
        if not restrictions:
            return params

        filtered = params.copy()
        adjustments_made = []

        for param_name, restriction in restrictions.items():
            if param_name not in filtered:
                continue
            current_value = filtered[param_name]
            allowed_values = restriction.get("allowed_values")
            if allowed_values is not None and current_value not in allowed_values:
                del filtered[param_name]
                adjustments_made.append(f"{param_name}={current_value} removed (model only supports {allowed_values})")

        if adjustments_made:
            logger.debug(
                "Adjusted parameters for model compatibility",
                model=model,
                model_family=family,
                adjustments=adjustments_made,
            )

        return filtered

    def prepare_messages(self, messages: list[LLMMessage]) -> tuple[str | None, list[dict]]:
        """Convert LLMMessage[] to OpenAI API wire format."""
        system = None
        openai_messages = []
        for msg in messages:
            # Guard against None content — Azure/OpenAI APIs reject null content
            safe_content = msg.content if msg.content is not None else ""
            if msg.role == "system":
                system = safe_content
                openai_messages.append({"role": "system", "content": safe_content})
            elif msg.role == "user":
                openai_messages.append({"role": "user", "content": safe_content})
            elif msg.role == "tool":
                openai_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": msg.tool_call_id,
                        "content": safe_content,
                    }
                )
            elif msg.role == "assistant":
                if msg.tool_calls:
                    formatted_tool_calls = []
                    for tc in msg.tool_calls:
                        tc_id = tc.get("tool_call_id") or tc.get("id", "")
                        tc_name = tc.get("function") or tc.get("name", "")
                        formatted_tool_calls.append(
                            {
                                "id": tc_id,
                                "type": "function",
                                "function": {
                                    "name": tc_name,
                                    "arguments": json.dumps(tc.get("arguments", {}))
                                    if isinstance(tc.get("arguments"), dict)
                                    else str(tc.get("arguments", "{}")),
                                },
                            }
                        )
                    openai_messages.append(
                        {
                            "role": "assistant",
                            "content": safe_content,
                            "tool_calls": formatted_tool_calls,
                        }
                    )
                else:
                    openai_messages.append({"role": "assistant", "content": safe_content})
        return system, openai_messages

    def prepare_tools(self, tools) -> list[dict]:
        """Convert tool definitions to OpenAI tool schema format."""
        result = []
        for tool in tools:
            if isinstance(tool, dict):
                result.append(tool)
                continue
            params = {"type": "object", "properties": {}, "required": []}
            for p in tool.parameters:
                prop = {"type": p.type if hasattr(p, "type") else "string"}
                if p.description:
                    prop["description"] = p.description
                params["properties"][p.name] = prop
                if not p.has_default:
                    params["required"].append(p.name)
            result.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": params,
                    },
                }
            )
        return result

    async def chat(self, messages: list[LLMMessage], tools: list[dict] | None = None, **kwargs) -> LLMResponse:
        """Send messages and get a response via Chat Completions API."""
        try:
            _, openai_messages = self.prepare_messages(messages)

            filtered_kwargs = {k: v for k, v in kwargs.items() if k not in ["json_mode"] and v is not None}
            filtered_kwargs = self._filter_params_for_model(self.model, filtered_kwargs)

            request_kwargs = {"model": self.model, "messages": openai_messages, **filtered_kwargs}

            if tools:
                request_kwargs["tools"] = self.prepare_tools(tools)
                request_kwargs["tool_choice"] = "auto"

            if kwargs.get("json_mode", False):
                request_kwargs["response_format"] = {"type": "json_object"}

            response = await self.client.chat.completions.create(
                **request_kwargs,
                timeout=httpx.Timeout(self.DEFAULT_TIMEOUT_SECONDS),
            )

            choice = response.choices[0]
            message = choice.message

            if hasattr(message, "tool_calls") and message.tool_calls:
                content = message.content or ""
                tool_calls = message.tool_calls
            else:
                content = message.content or ""
                tool_calls = None

            usage = None
            reasoning_tokens = None
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
                if hasattr(response.usage, "prompt_tokens_details") and response.usage.prompt_tokens_details:
                    details = response.usage.prompt_tokens_details
                    if hasattr(details, "cached_tokens"):
                        usage["cached_tokens"] = details.cached_tokens
                if hasattr(response.usage, "completion_tokens_details") and response.usage.completion_tokens_details:
                    output_details = response.usage.completion_tokens_details
                    if hasattr(output_details, "reasoning_tokens") and output_details.reasoning_tokens:
                        reasoning_tokens = output_details.reasoning_tokens

            return LLMResponse(
                content=content,
                model=response.model,
                usage=usage,
                finish_reason=choice.finish_reason,
                tool_calls=tool_calls,
                reasoning_tokens=reasoning_tokens,
            )

        except (APITimeoutError, httpx.TimeoutException) as e:
            raise LLMTimeoutError(f"OpenAI-compatible API timeout: {e}") from e
        except Exception as e:
            logger.error("OpenAI-compatible API error", error=str(e))
            raise

    # --- Streaming methods (Phases 2-4) ---

    async def _stream_chat_completions(self, messages: list[LLMMessage], tools: list | None = None, **kwargs):
        """Stream via client.chat.completions.create(stream=True).

        Yields LLMStreamChunk. Accumulates incremental tool call deltas.
        """
        _, openai_messages = self.prepare_messages(messages)

        filtered_kwargs = {k: v for k, v in kwargs.items() if k not in ["json_mode"] and v is not None}
        filtered_kwargs = self._filter_params_for_model(self.model, filtered_kwargs)

        request_kwargs = {"model": self.model, "messages": openai_messages, "stream": True, **filtered_kwargs}

        if tools:
            request_kwargs["tools"] = self.prepare_tools(tools)
            request_kwargs["tool_choice"] = "auto"

        response = await self.client.chat.completions.create(
            **request_kwargs,
            timeout=httpx.Timeout(self.DEFAULT_TIMEOUT_SECONDS),
        )

        tool_calls: dict[int, dict] = {}

        async for chunk in response:
            if not chunk.choices:
                continue

            choice = chunk.choices[0]
            delta = choice.delta

            if delta and delta.content:
                yield LLMStreamChunk(type="text_delta", content=delta.content)

            if delta and delta.tool_calls:
                for tc_delta in delta.tool_calls:
                    idx = tc_delta.index
                    if idx not in tool_calls:
                        tool_calls[idx] = {"id": "", "name": "", "arguments": ""}
                    if tc_delta.id:
                        tool_calls[idx]["id"] = tc_delta.id
                    if tc_delta.function:
                        if tc_delta.function.name:
                            tool_calls[idx]["name"] = tc_delta.function.name
                        if tc_delta.function.arguments:
                            tool_calls[idx]["arguments"] += tc_delta.function.arguments

            if choice.finish_reason == "tool_calls":
                for tc in tool_calls.values():
                    try:
                        parsed_args = json.loads(tc["arguments"]) if tc["arguments"] else {}
                    except json.JSONDecodeError:
                        parsed_args = {}
                    yield LLMStreamChunk(
                        type="tool_use",
                        tool_call={"id": tc["id"], "name": tc["name"], "input": parsed_args},
                    )
                tool_calls.clear()

        # Post-loop flush: yield any remaining tool calls not yet emitted
        if tool_calls:
            for tc in tool_calls.values():
                try:
                    parsed_args = json.loads(tc["arguments"]) if tc["arguments"] else {}
                except json.JSONDecodeError:
                    parsed_args = {}
                yield LLMStreamChunk(
                    type="tool_use",
                    tool_call={"id": tc["id"], "name": tc["name"], "input": parsed_args},
                )

    def _prepare_tools_for_responses(self, tools: list) -> list[dict]:
        """Convert tools to Responses API format (flat, no function wrapper)."""
        chat_tools = self.prepare_tools(tools)
        return [
            {
                "type": "function",
                "name": t["function"]["name"],
                "description": t["function"].get("description", ""),
                "parameters": t["function"].get("parameters", {}),
            }
            for t in chat_tools
        ]

    def _convert_to_responses_input(self, openai_messages: list[dict]) -> list[dict]:
        """Convert Chat Completions wire messages to Responses API input format.

        Chat Completions uses:
          {"role": "assistant", "tool_calls": [...]}
          {"role": "tool", "tool_call_id": "...", "content": "..."}

        Responses API uses:
          {"type": "function_call", "id": "...", "call_id": "...", "name": "...", "arguments": "...", "status": "completed"}
          {"type": "function_call_output", "call_id": "...", "output": "..."}
        """
        result = []
        for msg in openai_messages:
            role = msg.get("role")
            if role == "assistant" and msg.get("tool_calls"):
                # Emit any text content as a regular assistant message
                if msg.get("content"):
                    result.append({"role": "assistant", "content": msg["content"]})
                # Convert each tool call to a function_call item
                for tc in msg["tool_calls"]:
                    call_id = tc.get("id", "")
                    func = tc.get("function", {})
                    # Responses API requires 'id' to start with 'fc_'
                    fc_id = call_id if call_id.startswith("fc_") else f"fc_{call_id}"
                    result.append(
                        {
                            "type": "function_call",
                            "id": fc_id,
                            "call_id": call_id,
                            "name": func.get("name", ""),
                            "arguments": func.get("arguments", "{}"),
                            "status": "completed",
                        }
                    )
            elif role == "tool":
                result.append(
                    {
                        "type": "function_call_output",
                        "call_id": msg.get("tool_call_id", ""),
                        "output": msg.get("content", ""),
                    }
                )
            else:
                result.append(msg)
        return result

    async def _stream_responses(self, messages: list[LLMMessage], tools: list | None = None, **kwargs):
        """Stream via client.responses.create(stream=True).

        For gpt-5+, o3+, o4+ models. Tool calls arrive complete.
        """
        _, openai_messages = self.prepare_messages(messages)
        responses_input = self._convert_to_responses_input(openai_messages)

        filtered_kwargs = {k: v for k, v in kwargs.items() if k not in ["json_mode"] and v is not None}
        filtered_kwargs = self._filter_params_for_model(self.model, filtered_kwargs)

        request_kwargs = {"model": self.model, "input": responses_input, "stream": True, **filtered_kwargs}

        if tools:
            request_kwargs["tools"] = self._prepare_tools_for_responses(tools)

        stream = await self.client.responses.create(
            **request_kwargs,
            timeout=httpx.Timeout(self.DEFAULT_TIMEOUT_SECONDS),
        )

        async for event in stream:
            if event.type == "response.output_text.delta":
                yield LLMStreamChunk(type="text_delta", content=event.delta)

            elif event.type == "response.output_item.done":
                item = event.item
                if getattr(item, "type", None) == "function_call":
                    try:
                        parsed_args = json.loads(item.arguments) if item.arguments else {}
                    except json.JSONDecodeError:
                        parsed_args = {}
                    yield LLMStreamChunk(
                        type="tool_use",
                        tool_call={
                            "id": item.call_id,
                            "name": item.name,
                            "input": parsed_args,
                        },
                    )

            elif event.type == "response.reasoning.delta":
                yield LLMStreamChunk(type="thinking", content=event.delta)

    def _should_use_responses_api(self) -> bool:
        """Determine whether to use Responses API or Chat Completions.

        Priority: config flag > model prefix > default (Chat Completions).
        """
        if self._use_responses_api is not None:
            return self._use_responses_api

        model_lower = self.model.lower()
        for prefix in RESPONSES_API_PREFIXES:
            if model_lower.startswith(prefix):
                return True

        return False

    async def stream(self, messages: list[LLMMessage], tools: list | None = None, **kwargs):
        """Stream LLMStreamChunk, auto-selecting API based on model/config.

        Routes to Responses API for gpt-5+/o3+/o4+ models (or when configured),
        falls back to Chat Completions API otherwise.
        """
        try:
            if self._should_use_responses_api():
                logger.debug("Using Responses API for streaming", model=self.model)
                async for chunk in self._stream_responses(messages, tools=tools, **kwargs):
                    yield chunk
            else:
                logger.debug("Using Chat Completions API for streaming", model=self.model)
                async for chunk in self._stream_chat_completions(messages, tools=tools, **kwargs):
                    yield chunk
        except (APITimeoutError, httpx.TimeoutException) as e:
            raise LLMTimeoutError(f"OpenAI-compatible stream timeout: {e}") from e
        except Exception as e:
            logger.error("Stream error", model=self.model, error=str(e))
            raise
