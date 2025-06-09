"""LLM Query Execution Engine for OpenDXA.

This module provides the LLMQueryExecutor class, which handles the core
LLM query execution logic including iterative tool calling and API communication.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import os
import re
from collections.abc import Awaitable, Callable
from typing import Any, cast

import aisuite as ai
from openai.types.chat import ChatCompletion

from opendxa.common.exceptions import (
    LLMAuthenticationError,
    LLMContextLengthError,
    LLMError,
    LLMProviderError,
    LLMRateLimitError,
)
from opendxa.common.mixins.loggable import Loggable
from opendxa.common.mixins.queryable import QueryStrategy
from opendxa.common.mixins.tool_callable import OpenAIFunctionCall
from opendxa.common.types import BaseResponse
from opendxa.common.utils.misc import Misc
from opendxa.common.utils.token_management import TokenManagement


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
            max_iterations = 1

        # Add a system prompt that encourages resource use if not provided
        system_messages = Misc.get_field(
            request,
            "system_messages",
            [
                "You are an assistant. Use tools when necessary to complete tasks. "
                "After receiving tool results, you can request additional tools if needed."
            ],
        )

        user_messages = Misc.get_field(request, "user_messages", Misc.get_field(request, "messages", ["Hello, how are you?"]))

        # Initialize message history with system and user messages
        message_history: list[dict[str, Any]] = []
        if system_messages:
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
            message_history = TokenManagement.enforce_context_window(
                messages=message_history,
                model=self.model,
                max_tokens=Misc.get_field(request, "max_tokens"),
                preserve_system_messages=True,
                preserve_latest_messages=4,
                safety_margin=200,
            )

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
                    message_history.extend(cast(list[dict[str, Any]], tool_responses))
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

        return (
            response
            if isinstance(response, BaseResponse)
            else {
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
        )

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
        if os.environ.get("OPENDXA_MOCK_LLM", "").lower() == "true":
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

        # Make the API call
        try:
            response = self._client.chat.completions.create(**request_params)
            self._log_llm_response(response)
            return response
        except Exception as e:
            error_message = str(e)
            self.error("LLM query failed: %s", error_message)

            # Determine the provider from the model
            provider = "unknown"
            if self.model and ":" in self.model:
                provider = self.model.split(":", 1)[0]

            # Extract HTTP status code if available
            status_code = None
            status_match = re.search(r"status[\s_]*code[:\s]+(\d+)", error_message, re.IGNORECASE)
            if status_match:
                status_code = int(status_match.group(1))

            # Classify the error based on message patterns and status codes
            if any(term in error_message.lower() for term in ["context length", "token limit", "too many tokens", "maximum context"]):
                raise LLMContextLengthError(provider, status_code, error_message) from e
            elif any(term in error_message.lower() for term in ["rate limit", "ratelimit", "too many requests", "429"]):
                raise LLMRateLimitError(provider, status_code, error_message) from e
            elif any(
                term in error_message.lower() for term in ["authenticate", "authentication", "unauthorized", "auth", "api key", "401"]
            ):
                raise LLMAuthenticationError(provider, status_code, error_message) from e
            elif "invalid_request_error" in error_message.lower() or "bad request" in error_message.lower():
                raise LLMProviderError(provider, status_code, error_message) from e
            else:
                # Default case - generic LLM error
                raise LLMError(f"LLM query failed: {error_message}") from e

    async def mock_llm_query(self, request: dict[str, Any]) -> dict[str, Any]:
        """Mock LLM query for testing purposes.

        Args:
            request: Dictionary containing the request parameters

        Returns:
            Dict[str, Any]: Mock response
        """
        messages = Misc.get_field(request, "messages", [])
        if not messages:
            raise LLMError("messages must be provided and non-empty")

        # Get the last user message
        last_message = next((msg for msg in reversed(messages) if msg["role"] == "user"), None)
        if not last_message:
            raise LLMError("No user message found in message history")

        # Create a mock response
        return {
            "choices": [{"message": {"role": "assistant", "content": f"Mock response to: {last_message['content']}", "tool_calls": []}}],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "model": "mock-model",
        }

    def _build_default_request_params(self, request: dict[str, Any]) -> dict[str, Any]:
        """Build default request parameters for LLM API call.

        Args:
            request: Dictionary containing request parameters

        Returns:
            Dict[str, Any]: Dictionary of request parameters
        """
        params = {
            "messages": Misc.get_field(request, "messages", []),
            "temperature": Misc.get_field(request, "temperature", 0.7),
            "max_tokens": Misc.get_field(request, "max_tokens"),
        }

        # Only add model if it's available
        if self.model:
            params["model"] = self.model

        return params

    def _log_llm_response(self, response: ChatCompletion) -> None:
        """Log LLM response.

        Args:
            response: ChatCompletion object containing the response
        """
        self.debug("LLM response: %s", str(response))
