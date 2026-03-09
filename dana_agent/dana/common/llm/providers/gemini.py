"""
Gemini Provider Implementation

Uses the google-genai SDK async client for Google Gemini models.
"""

import json
import uuid

from google import genai
from google.genai import types as genai_types
import httpx
import structlog

from ...config import config_manager
from ..types import LLMMessage, LLMProvider, LLMResponse, LLMStreamChunk, LLMTimeoutError


logger = structlog.get_logger()


class GeminiProvider(LLMProvider):
    """Google Gemini provider using the google-genai SDK."""

    @property
    def supports_native_tools(self) -> bool:
        return True

    def __init__(self, api_key: str | None = None, model: str = "gemini-2.5-flash"):
        self.model = model

        if api_key:
            self.api_key = api_key
        else:
            self.api_key = config_manager.get_provider_api_key("gemini")

        if not self.api_key:
            raise ValueError("Gemini API key not found. Set GEMINI_API_KEY environment variable.")

        self.client = genai.Client(api_key=self.api_key)

    def prepare_messages(self, messages: list[LLMMessage]) -> tuple[str | None, list[genai_types.Content]]:
        """Convert LLMMessage[] to Gemini API format.

        Returns: (system_instruction, contents)
        """
        system_parts: list[str] = []
        contents: list[genai_types.Content] = []

        for msg in messages:
            safe_content = msg.content if msg.content is not None else ""

            if msg.role == "system":
                system_parts.append(safe_content if isinstance(safe_content, str) else json.dumps(safe_content))

            elif msg.role == "user":
                text = safe_content if isinstance(safe_content, str) else json.dumps(safe_content)
                contents.append(genai_types.Content(role="user", parts=[genai_types.Part(text=text)]))

            elif msg.role == "assistant":
                parts: list[genai_types.Part] = []
                if safe_content:
                    text = safe_content if isinstance(safe_content, str) else json.dumps(safe_content)
                    parts.append(genai_types.Part(text=text))
                if msg.tool_calls:
                    for tc in msg.tool_calls:
                        tc_name = tc.get("function") or tc.get("name", "")
                        tc_args = tc.get("arguments", {})
                        if isinstance(tc_args, str):
                            try:
                                tc_args = json.loads(tc_args)
                            except json.JSONDecodeError:
                                tc_args = {}
                        parts.append(
                            genai_types.Part(
                                function_call=genai_types.FunctionCall(
                                    name=tc_name,
                                    args=tc_args,
                                )
                            )
                        )
                if parts:
                    contents.append(genai_types.Content(role="model", parts=parts))

            elif msg.role == "tool":
                tc_name = self._find_tool_call_name(messages, msg.tool_call_id)
                try:
                    result_data = json.loads(safe_content) if isinstance(safe_content, str) else safe_content
                except (json.JSONDecodeError, TypeError):
                    result_data = {"result": safe_content}
                if not isinstance(result_data, dict):
                    result_data = {"result": result_data}

                contents.append(
                    genai_types.Content(
                        role="user",
                        parts=[
                            genai_types.Part(
                                function_response=genai_types.FunctionResponse(
                                    name=tc_name or "unknown_tool",
                                    response=result_data,
                                )
                            )
                        ],
                    )
                )

        system_instruction = "\n\n".join(system_parts) if system_parts else None
        return system_instruction, contents

    def prepare_tools(self, tools: list) -> list[genai_types.Tool]:
        """Convert OpenAI-style tool defs or MethodSignature to Gemini function_declarations."""
        declarations = []
        for tool in tools:
            if isinstance(tool, dict):
                func = tool.get("function", tool)
                declarations.append(
                    genai_types.FunctionDeclaration(
                        name=func.get("name", ""),
                        description=func.get("description", ""),
                        parameters=func.get("parameters"),
                    )
                )
            else:
                params = {"type": "object", "properties": {}, "required": []}
                for p in tool.parameters:
                    prop = {"type": p.type if hasattr(p, "type") else "string"}
                    if p.description:
                        prop["description"] = p.description
                    params["properties"][p.name] = prop
                    if not p.has_default:
                        params["required"].append(p.name)
                declarations.append(
                    genai_types.FunctionDeclaration(
                        name=tool.name,
                        description=tool.description,
                        parameters=params,
                    )
                )
        return [genai_types.Tool(function_declarations=declarations)]

    async def chat(self, messages: list[LLMMessage], tools: list | None = None, **kwargs) -> LLMResponse:
        """Send messages to Gemini and get a response."""
        try:
            system_instruction, contents = self.prepare_messages(messages)

            config = genai_types.GenerateContentConfig(
                http_options=genai_types.HttpOptions(timeout=self.DEFAULT_TIMEOUT_SECONDS),
            )
            if system_instruction:
                config.system_instruction = system_instruction
            if "temperature" in kwargs:
                config.temperature = kwargs["temperature"]
            if "max_tokens" in kwargs:
                config.max_output_tokens = kwargs["max_tokens"]
            if tools:
                config.tools = self.prepare_tools(tools)

            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=contents,
                config=config,
            )

            content = ""
            tool_calls = None

            if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.text:
                        content += part.text
                    elif part.function_call:
                        if tool_calls is None:
                            tool_calls = []
                        tool_calls.append(self._part_to_tool_call(part.function_call))

            usage = None
            if response.usage_metadata:
                usage = {
                    "prompt_tokens": response.usage_metadata.prompt_token_count or 0,
                    "completion_tokens": response.usage_metadata.candidates_token_count or 0,
                    "total_tokens": response.usage_metadata.total_token_count or 0,
                }

            finish_reason = None
            if response.candidates:
                fr = response.candidates[0].finish_reason
                if fr:
                    finish_reason = str(fr)

            return LLMResponse(
                content=content,
                model=self.model,
                usage=usage,
                finish_reason=finish_reason,
                tool_calls=tool_calls,
            )

        except httpx.TimeoutException as e:
            raise LLMTimeoutError(f"Gemini API timeout: {e}") from e
        except Exception as e:
            logger.error("Gemini API error", error=str(e))
            raise

    async def stream(self, messages: list[LLMMessage], tools: list | None = None, **kwargs):
        """Stream LLMStreamChunk from Gemini."""
        try:
            system_instruction, contents = self.prepare_messages(messages)

            config = genai_types.GenerateContentConfig(
                http_options=genai_types.HttpOptions(timeout=self.DEFAULT_TIMEOUT_SECONDS),
            )
            if system_instruction:
                config.system_instruction = system_instruction
            if "temperature" in kwargs:
                config.temperature = kwargs["temperature"]
            if "max_tokens" in kwargs:
                config.max_output_tokens = kwargs["max_tokens"]
            if tools:
                config.tools = self.prepare_tools(tools)

            stream = await self.client.aio.models.generate_content_stream(
                model=self.model,
                contents=contents,
                config=config,
            )
            async for chunk in stream:
                if not chunk.candidates or not chunk.candidates[0].content or not chunk.candidates[0].content.parts:
                    continue

                for part in chunk.candidates[0].content.parts:
                    if part.text:
                        yield LLMStreamChunk(type="text_delta", content=part.text)
                    elif part.function_call:
                        yield LLMStreamChunk(
                            type="tool_use",
                            tool_call={
                                "id": str(uuid.uuid4()),
                                "name": part.function_call.name,
                                "input": dict(part.function_call.args) if part.function_call.args else {},
                            },
                        )

        except httpx.TimeoutException as e:
            raise LLMTimeoutError(f"Gemini stream timeout: {e}") from e
        except Exception as e:
            logger.error("Gemini stream error", error=str(e))
            raise

    @staticmethod
    def _find_tool_call_name(messages: list[LLMMessage], tool_call_id: str | None) -> str:
        """Look back through messages to find the tool name for a given tool_call_id."""
        if not tool_call_id:
            return ""
        for prev in messages:
            if prev.role == "assistant" and prev.tool_calls:
                for tc in prev.tool_calls:
                    tc_id = tc.get("tool_call_id") or tc.get("id", "")
                    if tc_id == tool_call_id:
                        return tc.get("function") or tc.get("name", "")
        return ""

    @staticmethod
    def _part_to_tool_call(function_call):
        """Convert a Gemini FunctionCall part to an object compatible with LLMResponse.

        Returns an object with .id and .function.name/.function.arguments attributes,
        matching the OpenAI SDK ToolCall shape that consumers expect.
        """
        return type(
            "ToolCall",
            (),
            {
                "id": str(uuid.uuid4()),
                "function": type(
                    "Function",
                    (),
                    {
                        "name": function_call.name,
                        "arguments": json.dumps(function_call.args) if function_call.args else "{}",
                    },
                )(),
            },
        )()
