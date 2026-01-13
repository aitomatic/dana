"""
Hugging Face Provider Implementation
"""

import ast
import json
import re

from openai import AsyncOpenAI, BadRequestError
import structlog

from ...config import config_manager
from ..types import LLMMessage, LLMProvider, LLMResponse


logger = structlog.get_logger()


def parse_special_format(completion: str) -> dict | None:
    """
    Parse model output that uses special tokens instead of standard XML format.

    Some models trained with custom special tokens may generate output like:
        <|channel|>commentary to=<target> method=<method> <|constrain|>json<|message|>{json_data}
        <|channel|>analysis<|message|>This is reasoning text...

    This parser extracts the intent from such malformed responses to recover from
    API 400 errors caused by these special tokens.

    Args:
        completion: The raw completion string from the model

    Returns:
        Dictionary with parsed components:
            - channel: The channel type (e.g., "analysis", "commentary", "response")
            - target: The target agent/workflow/resource ID (if present)
            - method: The method to call (if present)
            - arguments: JSON string or dict of arguments (if present)
            - message: Extracted message content if present
            - reasoning: Extracted reasoning text (if channel is "analysis")
        Returns None if parsing fails or format is not recognized.

    Examples:
        >>> parse_special_format('<|channel|>commentary to=web-researcher invoke <|message|>{"query":"test"}')
        {'channel': 'commentary', 'target': 'web-researcher', 'method': 'invoke', 'arguments': '{"query":"test"}', 'message': 'test'}

        >>> parse_special_format('<|channel|>analysis<|message|>We need to call the weather API')
        {'channel': 'analysis', 'reasoning': 'We need to call the weather API'}
    """
    if not completion or "<|" not in completion:
        return None

    try:
        result = {}

        # Extract channel type
        channel_match = re.search(r"<\|channel\|>(\w+)", completion)
        if channel_match:
            result["channel"] = channel_match.group(1)

        # If channel is "analysis", extract the message as reasoning text
        if result.get("channel") == "analysis":
            # Extract plain text message (non-JSON) for analysis channel
            message_match = re.search(r"<\|message\|>(.+?)(?:<\||$)", completion, re.DOTALL)
            if message_match:
                reasoning_text = message_match.group(1).strip()
                # If it's not JSON, use it as reasoning
                if not reasoning_text.startswith("{"):
                    result["reasoning"] = reasoning_text
                    return result

        # Extract target from "to=<target>" pattern
        # Matches: to=web-researcher, to=google-lookup, etc.
        target_match = re.search(r"to=([a-zA-Z0-9_-]+)", completion)
        if target_match:
            result["target"] = target_match.group(1)

        # Extract method - try two patterns:
        # 1. Explicit "method=<name>"
        # 2. Implicit method name after target (e.g., "to=google-lookup execute")
        method_match = re.search(r"method=(\w+)", completion)
        if method_match:
            result["method"] = method_match.group(1)
        else:
            # Try to find method name between target and next special token
            implicit_method = re.search(r"to=[a-zA-Z0-9_-]+\s+(\w+)\s*<\|", completion)
            if implicit_method:
                result["method"] = implicit_method.group(1)
            else:
                # Default to 'invoke' if no method found
                result["method"] = "invoke"

        # Extract JSON from <|message|>{...} pattern
        json_match = re.search(r"<\|message\|>(\{.*?\})", completion)
        if json_match:
            json_str = json_match.group(1)
            result["arguments"] = json_str

            # Try to extract a simple message field from the JSON for convenience
            try:
                json_data = json.loads(json_str)
                if isinstance(json_data, dict):
                    # Look for common message field names
                    for key in ["message", "query", "content", "text"]:
                        if key in json_data:
                            result["message"] = json_data[key]
                            break
            except json.JSONDecodeError:
                pass

        # Return if we found reasoning OR a target
        return result if ("reasoning" in result or "target" in result) else None

    except Exception as e:
        logger.warning("Failed to parse special format", error=str(e), completion=completion[:200])
        return None


def convert_special_format_to_xml(parsed: dict) -> str:
    """
    Convert parsed special format to standard XML response format.

    Converts the parsed model output into the XML format expected by the system:
        <response>
            <type>in_progress</type>
            <content>...</content>
            <tool_calls>...</tool_calls>
        </response>

    Or for reasoning-only (analysis channel):
        <response>
            <type>in_progress</type>
            <reasoning>...</reasoning>
            <content>Analyzing the request...</content>
        </response>

    Args:
        parsed: Dictionary from parse_special_format with target, method, arguments, or reasoning

    Returns:
        XML-formatted string in the system's expected format
    """
    # Check if this is a reasoning-only response (analysis channel)
    if "reasoning" in parsed and "target" not in parsed:
        reasoning = parsed["reasoning"]
        xml = f"""<response>
<type>in_progress</type>
<reasoning>{reasoning}</reasoning>
<content>Processing your request...</content>
</response>"""
        return xml

    # Otherwise, it's a tool call response
    target = parsed.get("target", "unknown")
    method = parsed.get("method", "invoke")
    arguments = parsed.get("arguments", "{}")
    message = parsed.get("message", "")
    reasoning = parsed.get("reasoning", "Recovered from special token format and converting to standard tool call.")

    """ do not specify target type
    # Determine target type based on common patterns
    # This is a heuristic - adjust based on your system's naming conventions
    if "workflow" in target.lower() or target in ["google-lookup"]:
        target_type = "workflow"
    elif "resource" in target.lower():
        target_type = "resource"
    else:
        target_type = "agent"
    <target type="{target_type}" id="{target}"/>
    """

    # Create explanation based on what we're doing
    explanation = f"Calling {target}" + (f" - {message}" if message else "")

    # Build XML response
    xml = f"""<response>
<type>in_progress</type>
<reasoning>{reasoning}</reasoning>
<content>{explanation}</content>
<tool_calls>
<tool_call>
<target type="unknown" id="{target}"/>
<method>{method}</method>
<arguments>{arguments}</arguments>
</tool_call>
</tool_calls>
</response>"""

    return xml


class HuggingFaceProvider(LLMProvider):
    """Hugging Face Inference API provider."""

    def __init__(self, api_key: str | None = None, model: str = "microsoft/DialoGPT-medium", base_url: str | None = None):
        """
        Initialize Hugging Face provider.

        Args:
            api_key: Hugging Face API key (defaults to HF_TOKEN env var)
            model: Model to use
            base_url: Custom base URL
        """
        self.model = model

        # Get API key from parameter, env var, or config
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = config_manager.get_provider_api_key("huggingface")

        if not self.api_key:
            config = config_manager.get_provider_config("huggingface")
            api_key_env = config.get("api_key_env") if config else "HF_TOKEN"
            raise ValueError(f"Hugging Face API key not found. Set {api_key_env} environment variable.")

        # Get base URL from parameter, env var, or config
        if base_url:
            self.base_url = base_url
        else:
            self.base_url = config_manager.get_provider_base_url("huggingface")

        # Use OpenAI client with Hugging Face endpoint
        # Configure retry behavior: 2 retries max (default is 2, but making it explicit)
        # The OpenAI client will retry on 429 (rate limit) and 5xx (server errors)
        client_kwargs = {
            "api_key": self.api_key,
            "base_url": self.base_url,
            "max_retries": 2,  # Retry up to 2 times on transient errors
            "timeout": 60.0,  # 60 second timeout per request
        }

        self.client = AsyncOpenAI(**client_kwargs)

    async def chat(self, messages: list[LLMMessage], **kwargs) -> LLMResponse:
        """Send messages to Hugging Face and get a response."""
        try:
            # Convert our message format to OpenAI format
            openai_messages = []
            for msg in messages:
                if msg.role == "system":
                    openai_messages.append({"role": "system", "content": msg.content})
                elif msg.role == "user":
                    openai_messages.append({"role": "user", "content": msg.content})
                elif msg.role == "assistant":
                    openai_messages.append({"role": "assistant", "content": msg.content})

            # Call Hugging Face API (OpenAI-compatible)
            response = await self.client.chat.completions.create(model=self.model, messages=openai_messages, **kwargs)

            # Handle different response formats
            if hasattr(response, "choices") and response.choices:
                choice = response.choices[0]
                message = choice.message

                # Check if this is a function calling response
                if hasattr(message, "tool_calls") and message.tool_calls and choice.finish_reason == "tool_calls":
                    # Pass through function calls for base_agent to handle
                    content = ""  # Empty content when using function calls
                    tool_calls = message.tool_calls
                else:
                    # Standard text response
                    content = message.content or ""
                    tool_calls = None

                model = response.model
                usage = (
                    {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens,
                    }
                    if response.usage
                    else None
                )
                finish_reason = choice.finish_reason
            else:
                # Handle string response or other formats
                content = str(response) if response else ""
                model = self.model
                usage = None
                finish_reason = None
                tool_calls = None

            return LLMResponse(
                content=content,
                model=model,
                usage=usage,
                finish_reason=finish_reason,
                tool_calls=tool_calls,
            )

        except BadRequestError as e:
            # Try to recover from 400 errors caused by special token format
            if e.status_code == 400:
                try:
                    # Parse the error body - it's embedded in the exception's string representation
                    error_str = str(e)
                    # Extract the dict portion between 'Error code: 400 - ' and the end
                    if "Error code: 400 - " in error_str:
                        dict_str = error_str.split("Error code: 400 - ", 1)[1]
                        # Use ast.literal_eval to safely parse the dict string
                        error_body = ast.literal_eval(dict_str)

                        raw_output = error_body.get("raw_output", {})
                        completion = raw_output.get("completion", "")

                        # Check if error mentions special tokens
                        error_message = error_body.get("error", {}).get("message", "")
                        if completion and ("unexpected tokens" in error_message or "<|" in completion):
                            logger.warning(
                                "Detected special token format in model output, attempting to parse",
                                completion_preview=completion[:200],
                                error_message=error_message,
                            )

                            # Try to parse the special format
                            parsed = parse_special_format(completion)
                            if parsed:
                                # Convert to standard XML format
                                xml_content = convert_special_format_to_xml(parsed)

                                logger.info(
                                    "Successfully recovered from special token format",
                                    target=parsed.get("target"),
                                    method=parsed.get("method"),
                                )

                                # Return as a valid response with the converted XML
                                return LLMResponse(
                                    content=xml_content,
                                    model=self.model,
                                    usage=None,  # Usage info not available in error
                                    finish_reason="recovered_from_special_format",
                                    tool_calls=None,
                                )
                            else:
                                logger.warning("Failed to parse special token format, falling through to error")
                except Exception as parse_error:
                    logger.warning(
                        "Error while trying to parse special format", error=str(parse_error), error_type=type(parse_error).__name__
                    )

            # If we couldn't recover, log and raise the original error
            logger.error("Hugging Face HTTP error", status_code=e.status_code, error=str(e))
            raise

        except Exception as e:
            logger.error("Hugging Face API error", error=str(e), error_type=type(e).__name__)
            raise

    async def chat_tgi(self, messages: list[LLMMessage], **kwargs) -> LLMResponse:
        """Send messages to Hugging Face using TGI native endpoint with cache_prompt support.

        Note: Only works with self-hosted TGI or dedicated HF Inference Endpoints.
        Most providers (including Fireworks) only expose OpenAI-compatible API.
        """
        import httpx

        try:
            # Convert messages to a single prompt string (TGI native format)
            prompt_parts = []
            for msg in messages:
                if msg.role == "system":
                    prompt_parts.append(f"System: {msg.content}")
                elif msg.role == "user":
                    prompt_parts.append(f"User: {msg.content}")
                elif msg.role == "assistant":
                    prompt_parts.append(f"Assistant: {msg.content}")

            prompt = "\n\n".join(prompt_parts)
            if not prompt.endswith("Assistant:"):
                prompt += "\n\nAssistant:"

            # Build TGI native request
            # Base URL should be without /v1 suffix for native endpoint
            base_url = self.base_url.rstrip("/v1") if self.base_url else ""
            endpoint = f"{base_url}/generate"

            request_data = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": kwargs.get("max_tokens", 1000),
                    "temperature": kwargs.get("temperature", 0.7),
                    "top_p": kwargs.get("top_p", 0.9),
                    "do_sample": kwargs.get("temperature", 0.7) > 0,
                },
            }

            # Add cache_prompt if specified
            if kwargs.get("cache_prompt", False):
                request_data["parameters"]["cache_prompt"] = True

            # Make direct HTTP request to TGI native endpoint
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    endpoint,
                    json=request_data,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                )
                response.raise_for_status()
                result = response.json()

            # Parse TGI response
            # TGI returns: {"generated_text": "...", "details": {...}}
            if isinstance(result, dict):
                content = result.get("generated_text", "")
                details = result.get("details", {})

                # Extract usage if available
                usage = None
                if details:
                    usage = {
                        "prompt_tokens": details.get("prefill", [{}])[0].get("length", 0) if details.get("prefill") else 0,
                        "completion_tokens": details.get("generated_tokens", 0),
                        "total_tokens": (
                            details.get("prefill", [{}])[0].get("length", 0) + details.get("generated_tokens", 0)
                            if details.get("prefill")
                            else details.get("generated_tokens", 0)
                        ),
                    }

                return LLMResponse(
                    content=content,
                    model=self.model,
                    usage=usage,
                    finish_reason=details.get("finish_reason"),
                    tool_calls=None,
                )
            else:
                # Fallback for unexpected response format
                return LLMResponse(
                    content=str(result),
                    model=self.model,
                    usage=None,
                    finish_reason=None,
                    tool_calls=None,
                )

        except httpx.HTTPStatusError as e:
            logger.error("TGI native API HTTP error", status_code=e.response.status_code, error=str(e))
            raise
        except Exception as e:
            logger.error("TGI native API error", error=str(e), error_type=type(e).__name__)
            raise
