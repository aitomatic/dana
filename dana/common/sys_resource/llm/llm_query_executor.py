"""LLM Query Execution Engine for Dana.

This module provides the LLMQueryExecutor class, which handles the core
LLM query execution logic including iterative tool calling and API communication.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import os
from collections.abc import Awaitable, Callable
from typing import Any, cast

import aisuite as ai
from openai import APIStatusError, AuthenticationError, RateLimitError
from openai.types.chat import ChatCompletion

from dana.common.exceptions import (
    LLMAuthenticationError,
    LLMError,
    LLMProviderError,
    LLMRateLimitError,
)
from dana.common.mixins.loggable import Loggable
from dana.common.mixins.queryable import QueryStrategy
from dana.common.mixins.tool_callable import OpenAIFunctionCall
from dana.common.types import BaseResponse
from dana.common.utils.misc import Misc
from dana.common.utils.token_management import TokenManagement
import asyncio


class LLMQueryExecutor(Loggable):
    """Handles LLM query execution and conversation management.

    This class is responsible for:
    - Managing iterative tool calling conversations
    - Making single API calls to LLM providers
    - Handling mock responses for testing
    - Error classification and handling
    - Token management and context window enforcement
    """

    def __init__(
        self,
        client: ai.Client | None = None,
        model: str | None = None,
        query_strategy: QueryStrategy = QueryStrategy.ITERATIVE,
        query_max_iterations: int = 10,
    ):
        """Initialize the query executor.

        Args:
            client: Optional AISuite client instance
            model: Optional model name for queries
            query_strategy: Query strategy (ITERATIVE or ONCE)
            query_max_iterations: Maximum iterations for iterative queries
        """
        super().__init__()
        self._client = client
        self._model = model
        self._query_strategy = query_strategy
        self._query_max_iterations = query_max_iterations
        self._mock_llm_call: bool | Callable[[dict[str, Any]], dict[str, Any]] | None = None

    @property
    def client(self) -> ai.Client | None:
        """Get the AISuite client."""
        return self._client

    @client.setter
    def client(self, value: ai.Client) -> None:
        """Set the AISuite client."""
        self._client = value

    @property
    def model(self) -> str | None:
        """Get the current model."""
        return self._model

    @model.setter
    def model(self, value: str) -> None:
        """Set the current model."""
        self._model = value

    @property
    def query_strategy(self) -> QueryStrategy:
        """Get the query strategy."""
        return self._query_strategy

    @query_strategy.setter
    def query_strategy(self, value: QueryStrategy) -> None:
        """Set the query strategy."""
        self._query_strategy = value

    @property
    def query_max_iterations(self) -> int:
        """Get the maximum query iterations."""
        return self._query_max_iterations

    @query_max_iterations.setter
    def query_max_iterations(self, value: int) -> None:
        """Set the maximum query iterations."""
        self._query_max_iterations = value

    def set_mock_llm_call(self, mock_llm_call: bool | Callable[[dict[str, Any]], dict[str, Any]]) -> None:
        """Set the mock LLM call function for testing.

        Args:
            mock_llm_call: Mock function or boolean flag
        """
        if isinstance(mock_llm_call, Callable) or isinstance(mock_llm_call, bool):
            self._mock_llm_call = mock_llm_call
        else:
            raise LLMError("mock_llm_call must be a Callable or a boolean")

    async def query_iterative(
        self,
        request: dict[str, Any],
        tool_call_handler: Callable[[list[OpenAIFunctionCall]], Awaitable[list[BaseResponse]]] | None = None,
        build_request_params: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Handle a conversation with the LLM that may involve multiple tool calls.

        This method manages the complete conversation flow:
        1. Send initial user request
        2. If LLM requests tools:
           - Store the tool request message
           - Process all requested tool calls
           - Send all tool results back to LLM
           - Continue until LLM provides final response
        3. Return the final response

        Args:
            request: Dictionary containing:
                - user_messages: The user messages
                - system_messages: Optional system messages
                - available_resources: Dictionary of available tools/resources
                - max_iterations: Optional. Maximum number of tool call iterations
                - max_tokens: Optional. Maximum tokens for each response
                - temperature: Optional. Controls response randomness (0.0 to 1.0)
            tool_call_handler: Optional handler for tool calls
            build_request_params: Optional function to build request parameters

        Returns:
            Dict[str, Any]: The final LLM response after all tool calls are complete,
            containing the assistant's message and any tool calls.
        """
        # Initialize variables for the loop
        if self.query_strategy == QueryStrategy.ITERATIVE:
            max_iterations = Misc.get_field(request, "max_iterations", self.query_max_iterations)
        else:
            max_iterations = self.query_max_iterations

        user_messages = Misc.get_field(request, "user_messages", Misc.get_field(request, "messages", ["Hello, how are you?"]))

        # Check if user messages already contain system messages
        has_user_system_messages = any(isinstance(msg, dict) and msg.get("role") == "system" for msg in user_messages)

        # Only add default system prompt if user hasn't provided their own
        if not has_user_system_messages:
            system_messages = Misc.get_field(
                request,
                "system_messages",
                [
                    "You are an assistant. Use tools when necessary to complete tasks. CALLING 1 TOOL AT A TIME."
                    "After receiving tool results, you can request additional tools if needed. DO NOT CALL MULTIPLE TOOLS AT ONCE."
                ],
            )
        else:
            system_messages = Misc.get_field(request, "system_messages", [])

        # Initialize message history with system and user messages
        message_history: list[dict[str, Any]] = []
        if system_messages and not has_user_system_messages:
            # Ensure system messages are strings before joining
            system_content = "\n".join([str(msg) for msg in system_messages])
            message_history.append({"role": "system", "content": system_content})

        if user_messages:
            # Ensure user messages are dicts with 'role' and 'content'
            for msg in user_messages:
                if isinstance(msg, dict) and "role" in msg and "content" in msg:
                    message_history.append(msg)
                elif isinstance(msg, str):
                    # If it's just a string, wrap it in the standard format
                    message_history.append({"role": "user", "content": msg})
                else:
                    # Log a warning for unexpected format
                    self.warning(f"Skipping unexpected user message format: {type(msg)}")

        # Register all resources in the registry
        available_resources = Misc.get_field(request, "available_resources", {})
        for resource in available_resources.values():
            resource.add_to_registry()

        iteration = 0
        response = None

        while iteration < max_iterations:
            self.info(f"Resource calling iteration {iteration}/{max_iterations}")
            iteration += 1

            # Guard rail the total message length before sending
            # message_history = TokenManagement.enforce_context_window(
            #     messages=message_history,
            #     model=self.model,
            #     max_tokens=Misc.get_field(request, "max_tokens"),
            #     preserve_system_messages=True,
            #     preserve_latest_messages=4,
            #     safety_margin=200,
            # )

            # Logging the token count for debugging
            token_count = sum(TokenManagement.estimate_message_tokens(msg) for msg in message_history)
            self.debug(f"Sending messages with estimated token count: {token_count}")

            # Make the LLM query with available resources and message history
            response = await self.query_once(
                {
                    "available_resources": Misc.get_field(request, "available_resources", {}),
                    "max_tokens": Misc.get_field(request, "max_tokens"),
                    "temperature": Misc.get_field(request, "temperature", 0.7),
                    "messages": message_history,  # Pass read-only message history
                },
                build_request_params=build_request_params,
            )

            choices = Misc.get_field(response, "choices", [])
            response_message = Misc.get_field(choices[0], "message") if choices and len(choices) > 0 else None

            if response_message:
                # Only add tool_calls if they exist and are a valid list
                tool_calls: list[OpenAIFunctionCall] = Misc.get_field(response_message, "tool_calls")
                has_tool_calls = tool_calls and isinstance(tool_calls, list)

                if has_tool_calls and tool_call_handler:
                    # Store the tool request message and get responses for all tool calls
                    self.info("LLM is requesting tools, storing tool request message and calling resources")

                    # First add the assistant message with all tool calls
                    message_history.append(
                        {
                            "role": Misc.get_field(response_message, "role"),
                            "content": Misc.get_field(response_message, "content"),
                            "tool_calls": [i.model_dump() if hasattr(i, "model_dump") else i for i in tool_calls],
                        }
                    )

                    # Get responses for all tool calls at once
                    tool_responses = await tool_call_handler(tool_calls)
                    tool_responses_messages = []
                    for response in tool_responses:
                        if isinstance(response, BaseResponse):
                            # NOTE : For BaseResponse, we need to get the content which is a message dict. Do not process otherwise.
                            if Misc.has_field(response, "content"):
                                content = Misc.get_field(response, "content", None)
                                if isinstance(content, dict):
                                    tool_responses_messages.append(content)
                        elif isinstance(response, dict):
                            tool_responses_messages.append(response)
                        else:
                            self.warning(f"Tool response is not a BaseResponse or dict: {type(response)}")
                    message_history.extend(cast(list[dict[str, Any]], tool_responses_messages))
                else:
                    # If LLM is not requesting tools, we're done
                    self.info("LLM is not requesting tools, returning final response")
                    break

        # If we've reached the maximum iterations, return the final response
        if iteration == max_iterations:
            self.info(f"Reached maximum iterations ({max_iterations}), returning final response")

        # Unregister all resources in the registry (to avoid memory leaks)
        for resource in available_resources.values():
            resource.remove_from_registry()

        # Always return dict[str, Any] format
        if isinstance(response, BaseResponse):
            # Convert BaseResponse to dict format for consistency
            return {
                "choices": response.content.get("choices", []) if isinstance(response.content, dict) else [],
                "usage": response.content.get("usage", {}) if isinstance(response.content, dict) else {},
                "model": response.content.get("model", "") if isinstance(response.content, dict) else "",
            }
        else:
            return {
                "choices": (
                    response.get("choices", [])
                    if isinstance(response, dict)
                    else (response.choices if hasattr(response, "choices") else [])
                ),
                "usage": (
                    response.get("usage", {}) if isinstance(response, dict) else (response.usage if hasattr(response, "usage") else {})
                ),
                "model": (
                    response.get("model", "") if isinstance(response, dict) else (response.model if hasattr(response, "model") else "")
                ),
            }

    async def query_once(
        self, request: dict[str, Any], build_request_params: Callable[[dict[str, Any]], dict[str, Any]] | None = None
    ) -> dict[str, Any]:
        """Make a single call to the LLM with the given request.

        This method makes a single API call to the LLM using the provided message history.
        The message history is treated as read-only and should contain the complete
        conversation context including system prompts, user messages, and previous
        tool calls and responses.

        Args:
            request: Dictionary containing:
                - message_history: List of previous messages (read-only)
                - available_resources: Dictionary of available tools/resources
                - max_tokens: Optional. Maximum tokens for the response
                - temperature: Optional. Controls response randomness (0.0 to 1.0)
            build_request_params: Optional function to build request parameters

        Returns:
            Dict[str, Any]: The LLM response object containing:
                - choices[0].message: The assistant's message, which may contain tool_calls
                - usage: Token usage statistics

        Raises:
            LLMContextLengthError: If the messages exceed the context window.
            LLMRateLimitError: If rate limits are exceeded.
            LLMAuthenticationError: If authentication fails.
            LLMProviderError: For other provider-specific errors.
            LLMError: For any other LLM-related errors.
        """
        # Check for mock flag or function
        if callable(self._mock_llm_call):
            return await self._mock_llm_call(request)
        elif self._mock_llm_call:
            return await self.mock_llm_query(request)

        # Also check environment variable for mocking
        if os.environ.get("DANA_MOCK_LLM", "").lower() == "true":
            return await self.mock_llm_query(request)

        if not self._client:
            raise LLMError("LLM client not initialized")

        if not self.model:
            raise LLMError("No LLM model specified. Did you forget to set the API key in .env or your environment?")

        # Get message history (read-only)
        messages = Misc.get_field(request, "messages", [])
        if not messages:
            raise LLMError("messages must be provided and non-empty")

        # Build request parameters
        if build_request_params:
            request_params = build_request_params(request)
        else:
            request_params = self._build_default_request_params(request)

        # Check for local vLLM override for the model parameter
        vllm_override_model = os.getenv("VLLM_API_MODEL_NAME")
        if vllm_override_model and request_params.get("model") == "openai:vllm-local-model":
            self.debug(f"Overriding model with VLLM_API_MODEL_NAME: {vllm_override_model}")
            request_params["model"] = vllm_override_model

        # Log the LLM request at INFO level
        self._log_llm_request(request_params)

        # Make the API call
        try:
            # Make the actual API call (aisuite is synchronous)
            response: ChatCompletion = await asyncio.to_thread(
                self._client.chat.completions.create,
                **request_params,
            )  # Calling to_thread is a workaround to avoid blocking the event loop
            self.info("LLM query successful")
            self._log_llm_response(response)

            # Convert AISuite response to dictionary format
            # AISuite returns ChatCompletionResponse which doesn't have model_dump()
            return self._convert_response_to_dict(response)

        except AuthenticationError as e:
            provider = self.model.split(":", 1)[0] if self.model else "unknown"
            self.error(f"LLM authentication failed for provider '{provider}': {e}")
            raise LLMAuthenticationError(provider, e.status_code, str(e)) from e
        except RateLimitError as e:
            provider = self.model.split(":", 1)[0] if self.model else "unknown"
            self.error(f"LLM rate limit exceeded for provider '{provider}': {e}")
            raise LLMRateLimitError(provider, e.status_code, str(e)) from e
        except APIStatusError as e:
            provider = self.model.split(":", 1)[0] if self.model else "unknown"
            self.error(f"LLM API error for provider '{provider}': {e.message}")
            raise LLMProviderError(provider, e.status_code, str(e.message)) from e
        except Exception as e:
            error_msg = str(e)
            if "connection" in error_msg.lower() or "connect" in error_msg.lower():
                self.debug(f"LLM connection failed: {error_msg}")
                raise LLMError(f"LLM connection failed: {error_msg}. Please check your API key configuration in .env file.") from e
            else:
                self.error(f"An unexpected error occurred during LLM query: {e}")
                raise LLMError(f"An unexpected error occurred: {e}") from e

    async def mock_llm_query(self, request: dict[str, Any]) -> dict[str, Any]:
        """Intelligent mock LLM query that understands POET-enhanced prompts.

        Args:
            request: Dictionary containing the request parameters

        Returns:
            Dict[str, Any]: Mock response with appropriate content based on prompt analysis
        """
        messages = Misc.get_field(request, "messages", [])
        if not messages:
            raise LLMError("messages must be provided and non-empty")

        # Get the last user message
        last_message = next((msg for msg in reversed(messages) if msg["role"] == "user"), None)
        if not last_message:
            raise LLMError("No user message found in message history")

        content = last_message["content"]

        # Intelligent response based on prompt analysis
        mock_content = self._generate_intelligent_mock_response(content)

        # Create a mock response
        return {
            "choices": [{"message": {"role": "assistant", "content": mock_content, "tool_calls": []}}],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "model": "mock-model",
        }

    def _generate_intelligent_mock_response(self, prompt: str) -> str:
        """Generate intelligent mock responses based on prompt analysis.

        Args:
            prompt: The user prompt to analyze

        Returns:
            str: Appropriate mock response
        """
        prompt_lower = prompt.lower()

        # Detect POET-enhanced prompts with format instructions (updated patterns)
        is_boolean_prompt = (
            "respond with clear yes/no" in prompt_lower
            or "respond only with yes or no" in prompt_lower
            or 'return format: "yes" or "no"' in prompt_lower
        )
        is_integer_prompt = "return only the final integer number" in prompt_lower
        is_float_prompt = "return only the final numerical value as a decimal" in prompt_lower
        is_dict_prompt = (
            "return only a valid json object" in prompt_lower
            or "format your response as a json object" in prompt_lower
            or "return a json object" in prompt_lower
        )
        is_list_prompt = (
            "return only a valid json array" in prompt_lower
            or "format your response as a json array" in prompt_lower
            or "return a json array" in prompt_lower
        )

        # Boolean questions with enhanced prompts
        if is_boolean_prompt:
            if any(term in prompt_lower for term in ["invest", "renewable", "proceed", "continue", "approve"]):
                return "yes"
            else:
                return "no"

        # Integer questions with enhanced prompts
        if is_integer_prompt:
            if "planets" in prompt_lower and "solar system" in prompt_lower:
                return "8"
            elif "days" in prompt_lower and "week" in prompt_lower:
                return "7"
            elif "days" in prompt_lower and ("year" in prompt_lower or "10 years" in prompt):
                return "365"
            else:
                return "42"  # Default integer

        # Float questions with enhanced prompts
        if is_float_prompt:
            if "pi" in prompt_lower:
                return "3.14159"
            elif "temperature" in prompt_lower and ("body" in prompt_lower or "human" in prompt_lower):
                return "37.0"
            else:
                return "3.14"  # Default float

        # Dict questions with enhanced prompts
        if is_dict_prompt:
            if "moon" in prompt_lower:
                return '{"diameter_km": "3474.8", "distance_from_earth_km": "384400"}'
            elif "mars" in prompt_lower:
                return '{"diameter_km": "6779", "distance_from_sun_au": "1.52", "orbital_period_days": "687"}'
            else:
                return '{"result": "mock_data", "status": "success"}'

        # List questions with enhanced prompts
        if is_list_prompt:
            if "planets" in prompt_lower and ("first 4" in prompt_lower or "4 planets" in prompt_lower):
                return '["Mercury", "Venus", "Earth", "Mars"]'
            elif "primary colors" in prompt_lower or "3 primary colors" in prompt_lower:
                return '["red", "blue", "yellow"]'
            else:
                return '["item1", "item2", "item3"]'

        # Regular questions without POET enhancement
        if "capital" in prompt_lower and "france" in prompt_lower:
            return "Paris"
        elif "2 + 2" in prompt_lower or "2+2" in prompt_lower:
            return "4"
        elif "5 * 3" in prompt_lower or "5*3" in prompt_lower:
            return "15"
        elif "10 + 20" in prompt_lower or "10+20" in prompt_lower:
            return "30"
        elif "pi" in prompt_lower:
            return "Pi (π) is approximately 3.14159, representing the ratio of a circle's circumference to its diameter."
        elif "sky" in prompt_lower and "blue" in prompt_lower:
            return "The sky appears blue due to Rayleigh scattering of light by molecules in Earth's atmosphere."
        elif "machine learning" in prompt_lower:
            return "Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed."
        elif "weather" in prompt_lower:
            return "I'm a mock assistant and can't access real weather data, but I hope you're having a pleasant day!"
        elif "days" in prompt_lower and "year" in prompt_lower:
            return "There are 365 days in a regular year and 366 days in a leap year."
        elif any(term in prompt_lower for term in ["invest", "renewable", "proceed", "continue"]):
            return "Based on the context, I would recommend proceeding with careful consideration of the relevant factors."
        else:
            return f"This is a mock response. In a real scenario, I would provide a thoughtful answer to: {prompt[:100]}{'...' if len(prompt) > 100 else ''}"

    def _build_default_request_params(self, request: dict[str, Any]) -> dict[str, Any]:
        """Build request parameters for LLM API call.

        Args:
            request: Dictionary containing request parameters

        Returns:
            Dict[str, Any]: Dictionary of request parameters
        """
        logical_model_name = self.model
        final_model_name_for_api = logical_model_name

        # Handle vLLM provider and model name translation
        if logical_model_name and logical_model_name.startswith("vllm:"):
            self.debug(f"Handling vLLM model: {logical_model_name}")
            # Default to using openai provider for aisuite compatibility
            final_model_name_for_api = logical_model_name.replace("vllm:", "openai:", 1)

            # Check if the start script provided a specific physical model name
            physical_model_override = os.getenv("VLLM_API_MODEL_NAME")
            if physical_model_override:
                # The final name for aisuite is "openai:" + the physical name
                final_model_name_for_api = f"openai:{physical_model_override}"
                self.debug(f"Overriding with physical model from VLLM_API_MODEL_NAME: {final_model_name_for_api}")

        # Build basic request parameters
        request_params = {
            "model": final_model_name_for_api,
            "messages": Misc.get_field(request, "messages", [{"role": "user", "content": "Hello"}]),
            "temperature": Misc.get_field(request, "temperature", 0.7),
        }

        # Only include max_tokens if it's actually provided in the request
        if "max_tokens" in request and request["max_tokens"] is not None:
            request_params["max_tokens"] = request["max_tokens"]

        # Include tools if available_resources are provided
        available_resources = Misc.get_field(request, "available_resources", None)
        if available_resources:
            request_params["tools"] = self._get_openai_functions_from_resources(available_resources)

        # Let AISuite handle Anthropic system message transformation automatically
        # Manual transformation causes "multiple values for keyword argument 'system'" error
        # because AISuite also transforms system messages internally

        return request_params

    def _transform_anthropic_system_messages(self, request_params: dict[str, Any]) -> dict[str, Any]:
        """Transform system messages for Anthropic models.

        Anthropic expects system messages as a top-level 'system' parameter,
        not in the messages array.

        Args:
            request_params: Original request parameters

        Returns:
            Dict[str, Any]: Transformed request parameters
        """
        messages = request_params.get("messages", [])
        system_messages = []
        non_system_messages = []

        # Separate system messages from other messages
        for message in messages:
            if message.get("role") == "system":
                content = message.get("content", "")
                system_messages.append(content)  # Include all system messages, even empty ones
            else:
                non_system_messages.append(message)

        # Update request parameters
        result = request_params.copy()
        result["messages"] = non_system_messages

        # Add system parameter if we have system messages
        if system_messages:
            result["system"] = "\n".join(system_messages)

        return result

    def _get_openai_functions_from_resources(self, resources: dict[str, Any]) -> list[dict[str, Any]]:
        """Get OpenAI functions from available resources.

        Args:
            resources: Dictionary of available resources

        Returns:
            List[dict[str, Any]]: List of tool definitions
        """
        functions = []
        for _, resource in resources.items():
            if hasattr(resource, "list_openai_functions"):
                functions.extend(resource.list_openai_functions())
        return functions

    def _log_llm_request(self, request_params: dict[str, Any]) -> None:
        """Log the LLM request details.

        Args:
            request_params: Dictionary containing request parameters
        """
        # Extract messages for cleaner logging
        messages = request_params.get("messages", [])
        model = request_params.get("model", "unknown")
        temperature = request_params.get("temperature", 0.7)
        max_tokens = request_params.get("max_tokens", "unspecified")

        self.info(f"🤖 LLM Request to {model} (temp={temperature}, max_tokens={max_tokens})")

        # Log each message in the conversation
        for i, message in enumerate(messages):
            role = message.get("role", "unknown")
            content = message.get("content", "")

            # Truncate very long content for readability
            if isinstance(content, str) and len(content) > 500:
                content_preview = content[:500] + "... [truncated]"
            else:
                content_preview = content

            self.info(f"  [{i + 1}] {role.upper()}: {content_preview}")

            # Log tool calls if present
            if "tool_calls" in message and message["tool_calls"]:
                self.info(f"    Tool calls: {len(message['tool_calls'])} tools requested")

    def _log_llm_response(self, response: ChatCompletion) -> None:
        """Log LLM response at INFO level.

        Args:
            response: ChatCompletion object containing the response
        """
        # Extract key information from response
        choices = response.choices if hasattr(response, "choices") else []
        usage = response.usage if hasattr(response, "usage") else None
        model = response.model if hasattr(response, "model") else "unknown"

        if choices and len(choices) > 0:
            message = choices[0].message
            role = message.role if hasattr(message, "role") else "assistant"
            content = message.content if hasattr(message, "content") else ""
            tool_calls = message.tool_calls if hasattr(message, "tool_calls") else None

            # Log response summary
            prompt_tokens = usage.prompt_tokens if usage and hasattr(usage, "prompt_tokens") else 0
            completion_tokens = usage.completion_tokens if usage and hasattr(usage, "completion_tokens") else 0

            self.info(f"📝 LLM Response from {model} ({prompt_tokens} + {completion_tokens} tokens)")

            # Log content if present
            if content:
                # Truncate very long content for readability
                if len(content) > 500:
                    content_preview = content[:500] + "... [truncated]"
                else:
                    content_preview = content
                self.info(f"  {role.upper()}: {content_preview}")

            # Log tool calls if present
            if tool_calls:
                self.info(f"  🔧 Tool calls: {len(tool_calls)} tools requested")
                for i, tool_call in enumerate(tool_calls):
                    function_name = (
                        tool_call.function.name if hasattr(tool_call, "function") and hasattr(tool_call.function, "name") else "unknown"
                    )
                    self.info(f"    [{i + 1}] {function_name}")

        # Also keep the debug level logging for full details
        self.debug("LLM response (full): %s", str(response))

    def _convert_response_to_dict(self, response) -> dict[str, Any]:
        """Convert AISuite response object to dictionary format.

        AISuite returns ChatCompletionResponse objects that don't have model_dump().
        This method manually converts them to the expected dictionary format.

        Args:
            response: AISuite ChatCompletionResponse or OpenAI ChatCompletion object

        Returns:
            Dict[str, Any]: Dictionary representation of the response
        """
        # If it's already a dict (from mock), return as-is
        if isinstance(response, dict):
            return response

        # If it has model_dump (OpenAI SDK), use it
        if hasattr(response, "model_dump"):
            return response.model_dump()

        # For AISuite ChatCompletionResponse, manually convert
        result = {}

        # Handle choices
        if hasattr(response, "choices") and response.choices:
            choices = []
            for choice in response.choices:
                choice_dict = {}
                if hasattr(choice, "message"):
                    message_dict = {}
                    if hasattr(choice.message, "role"):
                        message_dict["role"] = choice.message.role
                    if hasattr(choice.message, "content"):
                        message_dict["content"] = choice.message.content
                    if hasattr(choice.message, "tool_calls"):
                        message_dict["tool_calls"] = choice.message.tool_calls
                    choice_dict["message"] = message_dict
                if hasattr(choice, "finish_reason"):
                    choice_dict["finish_reason"] = choice.finish_reason
                choices.append(choice_dict)
            result["choices"] = choices

        # Handle usage
        if hasattr(response, "usage"):
            if isinstance(response.usage, dict):
                result["usage"] = response.usage
            else:
                usage_dict = {}
                if hasattr(response.usage, "prompt_tokens"):
                    usage_dict["prompt_tokens"] = response.usage.prompt_tokens
                if hasattr(response.usage, "completion_tokens"):
                    usage_dict["completion_tokens"] = response.usage.completion_tokens
                if hasattr(response.usage, "total_tokens"):
                    usage_dict["total_tokens"] = response.usage.total_tokens
                result["usage"] = usage_dict

        # Handle model
        if hasattr(response, "model"):
            result["model"] = response.model
        elif self.model:
            # Fallback to current model if response doesn't have it
            result["model"] = self.model

        return result
