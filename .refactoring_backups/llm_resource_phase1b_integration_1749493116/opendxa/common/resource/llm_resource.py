"""LLM resource implementation for OpenDXA.

This module provides the LLMResource class, which manages LLM model selection
and interaction. It leverages the ConfigLoader for base configuration and supports
runtime overrides.

Features:
- Centralized configuration via ConfigLoader ('opendxa_config.json').
- Automatic model selection based on preferred models and available API keys.
- Explicit model override via constructor.
- Runtime parameter overrides for LLM calls (temperature, max_tokens, etc.).
- Tool/function calling integration.
- Automatic context window enforcement to prevent token limit errors.
- Enhanced error classification with specialized error types.
- Token estimation and management for reliable LLM communication.
"""

import json
import os
import re
from typing import Any, Callable, Dict, List, Optional, Union, cast

import aisuite as ai
from openai.types.chat import ChatCompletion

from opendxa.common.config.config_loader import ConfigLoader
from opendxa.common.exceptions import (
    ConfigurationError,
    LLMAuthenticationError,
    LLMContextLengthError,
    LLMError,
    LLMProviderError,
    LLMRateLimitError,
)
from opendxa.common.mixins.queryable import QueryStrategy
from opendxa.common.mixins.registerable import Registerable
from opendxa.common.mixins.tool_callable import OpenAIFunctionCall, ToolCallable
from opendxa.common.mixins.tool_formats import ToolFormat
from opendxa.common.resource.base_resource import BaseResource
from opendxa.common.types import BaseRequest, BaseResponse
from opendxa.common.utils.misc import Misc
from opendxa.common.utils.token_management import TokenManagement
from opendxa.common.resource.llm_configuration_manager import LLMConfigurationManager

# To avoid accidentally sending too much data to the LLM,
# we limit the total length of tool-call responses.
MAX_TOOL_CALL_RESPONSE_LENGTH = 10000


class LLMResource(BaseResource):
    """LLM resource with flexible model selection and configuration.

    Provides a unified interface for LLM interaction, integrating with the
    centralized ConfigLoader for base settings ('opendxa_config.json') and
    allowing overrides through constructor arguments and request parameters.

    Configuration Hierarchy:
    1. Base configuration loaded by ConfigLoader (using its search order for 'opendxa_config.json').
    2. `preferred_models` list provided to constructor (overrides list from config).
    3. `model` provided to constructor (overrides automatic selection from preferred list or config default).
    4. `kwargs` provided to constructor (overrides default parameters like temperature from config).
    5. Parameters in the `query` request (overrides constructor/config defaults for that specific query).

    Attributes:
        model: The selected LLM model name (can be set explicitly or determined automatically).
        preferred_models: List of preferred models used for automatic selection.
                          Format: `[{"name": "provider:model_name", "required_api_keys": ["ENV_VAR_NAME"]}]`
        config: The final configuration dictionary used for LLM calls, incorporating
                defaults from ConfigLoader and constructor overrides.

    Instantiation Examples:

    1.  **Use Configuration File Defaults (Simplest Case):**
        ```python
        # Instantiating with no arguments uses the name "default_llm".
        # Relies entirely on 'opendxa_config.json' found by ConfigLoader.
        # Requires 'preferred_models' or 'default_model' in the config.
        # Requires relevant API keys (e.g., OPENAI_API_KEY) in environment.
        llm = LLMResource() # Name defaults to "default_llm"

        # You can still provide a custom name:
        # llm = LLMResource(name="my_specific_llm")
        ```

    2.  **Explicitly Specify Model:**
        ```python
        # Overrides automatic selection and 'default_model' from config.
        # Still uses other parameters (e.g., temperature) from config if not overridden.
        # Still requires API keys for the specified model in environment.
        llm = LLMResource(name="gpt4_llm", model="openai:gpt-4")
        ```

    3.  **Override Preferred Models for Selection:**
        ```python
        # Uses a custom list for automatic selection, ignoring the list in the config.
        # Requires API keys for models in *this* list.
        custom_models = [
            {"name": "anthropic:claude-3-opus", "required_api_keys": ["ANTHROPIC_API_KEY"]},
            {"name": "groq:llama3-70b", "required_api_keys": ["GROQ_API_KEY"]}
        ]
        llm = LLMResource(name="custom_selection_llm", preferred_models=custom_models)
        ```

    4.  **Override Specific LLM Parameters:**
        ```python
        # Uses default model selection (from config or overridden preferred_models).
        # Overrides 'temperature' and 'max_tokens' from the config file.
        llm = LLMResource(name="hot_llm", temperature=0.9, max_tokens=4096)
        ```

    5.  **Combine Overrides:**
        ```python
        # Explicit model, overrides preferred list, overrides temperature.
        llm = LLMResource(name="specific_opus",
                          model="anthropic:claude-3-opus",
                          temperature=0.5)
        ```

    **Important:** For automatic model selection (`_find_first_available_model`)
    to work correctly, the environment variables listed in `required_api_keys`
    for the models in the effective `preferred_models` list must be set.
    """

    # Removed hardcoded DEFAULT_PREFERRED_MODELS, loaded from ConfigLoader now

    def __init__(
        self, name: str = "default_llm", model: Optional[str] = None, preferred_models: Optional[List[Dict[str, Any]]] = None, **kwargs
    ):
        """Initializes the LLMResource.

        Loads base configuration using ConfigLoader, applies overrides from
        constructor arguments, and determines the final LLM model to use.

        Args:
            name: The name of the resource instance. Defaults to "default_llm".
            model: Explicitly sets the model to use, overriding automatic selection.
            preferred_models: Overrides the preferred models list from the config file.
                              Used for automatic model selection if `model` is not set.
                              Format: `[{"name": "p:m", "required_api_keys": ["K"]}]`
            **kwargs: Additional configuration parameters (e.g., temperature, max_tokens)
                      that override values from the config file.
        """
        super().__init__(name)

        # Load base configuration from ConfigLoader
        try:
            base_config = ConfigLoader().get_default_config()
            self.log_debug(f"Loaded base config: {list(base_config.keys())}")
        except ConfigurationError as e:
            self.log_warning(f"Could not load default config: {e}. Proceeding with minimal defaults.")
            base_config = {}

        # Determine the preferred models list
        # Priority: constructor arg -> config file -> empty list
        if preferred_models is not None:
            self.preferred_models = preferred_models
            self.log_debug("Using preferred_models from constructor argument.")
        elif "preferred_models" in base_config:
            self.preferred_models = base_config["preferred_models"]
            self.log_debug("Using preferred_models from config file.")
        else:
            self.preferred_models = []
            self.log_warning("No preferred_models list found in config or arguments.")

        # --- Determine the model ---
        # Priority: constructor arg -> find available -> default from config -> None
        if model:
            # Validate the explicitly provided model
            if not self._validate_model(model):
                self.log_warning(f"Explicitly provided model '{model}' seems unavailable (missing API keys?). Continuing anyway.")
            self._model = model  # Use underscore to avoid setter validation initially
            self.log_debug(f"Using explicitly set model: {self._model}")
        else:
            # Automatically find the first available model from the list
            self._model = self._find_first_available_model()
            if not self._model:
                # Fallback to default model from config if auto-selection fails
                config_default_model = base_config.get("default_model")
                if config_default_model:
                    self._model = config_default_model
                    self.log_debug(f"Using default_model from config: {self._model}")
                    if not self._validate_model(self._model):
                        self.log_warning(f"Default model '{self._model}' from config seems unavailable (missing API keys?).")
                else:
                    self.log_error("Could not find an available model and no default_model specified in config.")
                    # self._model remains None, potentially causing issues later

        # --- Build final configuration ---
        # Priority: kwargs -> base_config
        self.config = base_config.copy()  # Start with base config
        self.config.update(kwargs)  # Apply constructor overrides
        # Ensure model is in the final config if determined
        if self._model:
            self.config["model"] = self._model

        self.log_info(f"Initialized LLMResource '{name}' with model '{self.model}'")
        self.log_debug(f"Final LLM config keys: {list(self.config.keys())}")

        # Mocking setup
        self._mock_llm_call: Optional[Union[bool, Callable[[Dict[str, Any]], Dict[str, Any]]]] = None

        # Initialize the LLM client
        self._client = None
        self.provider_configs = {}
        Misc.safe_asyncio_run(self.initialize)

    @property
    def model(self) -> Optional[str]:
        """The currently selected LLM model name."""
        return self._model

    @model.setter
    def model(self, value: str) -> None:
        """Sets the LLM model, validating its availability."""
        if not self._validate_model(value):
            self.log_warning(f"Setting model to '{value}', but it seems unavailable (missing API keys?).")
        self._model = value
        self.config["model"] = value  # Keep config in sync
        self.log_info(f"LLM model set to: {self._model}")

    def query_sync(self, request: BaseRequest) -> BaseResponse:
        """Query the LLM synchronously.

        Args:
            request: The request containing:
                - messages: List of message dictionaries
                - available_resources: List of available resources
                - max_tokens: Optional maximum tokens to generate
                - temperature: Optional temperature for generation

        Returns:
            BaseResponse containing:
                - content: The assistant's message
                - usage: Token usage statistics
        """
        return Misc.safe_asyncio_run(self.query, request)

    async def query(self, request: BaseRequest) -> BaseResponse:
        """Query the LLM.

        Args:
            request: The request containing:
                - messages: List of message dictionaries
                - available_resources: List of available resources
                - max_tokens: Optional maximum tokens to generate
                - temperature: Optional temperature for generation

        Returns:
            BaseResponse containing:
                - content: The assistant's message
                - usage: Token usage statistics
        """
        # Check if we should use mock responses first, even if resource is not available
        should_mock = self._mock_llm_call is not None and (
            self._mock_llm_call is True or callable(self._mock_llm_call) or os.environ.get("OPENDXA_MOCK_LLM", "").lower() == "true"
        )

        if not self._is_available and not should_mock:
            return BaseResponse(
                success=False, content={"error": f"Resource {self.name} not available"}, error=f"Resource {self.name} not available"
            )

        try:
            response = await self._query_iterative(request.arguments)
            return BaseResponse(success=True, content=response)
        except Exception as e:
            return BaseResponse(success=False, content={"error": str(e)}, error=str(e))

    async def initialize(self) -> None:
        """Initialize the AISuite client etc."""
        if not self._client:
            self.debug("Initializing AISuite client...")
            # Handle backward compatibility for top-level api_key
            if "api_key" in self.config and "openai" not in self.provider_configs:
                self.debug("Using top-level api_key for OpenAI provider")
                self.provider_configs["openai"] = {"api_key": self.config["api_key"]}

            self.debug(f"Creating AISuite client with provider configs: {self.provider_configs}")
            self._client = ai.Client(provider_configs=self.provider_configs)

            # Only log if we have a model
            if self.model:
                self.info("LLM client initialized successfully for model: %s", self.model)
                self._is_available = True
            else:
                self.warning("LLM client initialized without a model")
                self._is_available = False

    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self._client:
            self._client = None

    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check if request contains prompt."""
        return "prompt" in request

    def with_mock_llm_call(self, mock_llm_call: Union[bool, Callable[[Dict[str, Any]], Dict[str, Any]]]) -> "LLMResource":
        """Set the mock LLM call function."""
        if isinstance(mock_llm_call, Callable) or isinstance(mock_llm_call, bool):
            self._mock_llm_call = mock_llm_call
        else:
            raise LLMError("mock_llm_call must be a Callable or a boolean")

        return self

    # ===== Core Query Processing Methods =====
    async def _query_iterative(self, request: Dict[str, Any]) -> Dict[str, Any]:
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

        Returns:
            Dict[str, Any]: The final LLM response after all tool calls are complete,
            containing the assistant's message and any tool calls.
        """
        # Initialize variables for the loop
        if self.get_query_strategy() == QueryStrategy.ITERATIVE:
            max_iterations = Misc.get_field(request, "max_iterations", self.get_query_max_iterations())
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
        message_history: List[Dict[str, Any]] = []
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
            response = await self._query_once(
                {
                    "available_resources": Misc.get_field(request, "available_resources", {}),
                    "max_tokens": Misc.get_field(request, "max_tokens"),
                    "temperature": Misc.get_field(request, "temperature", 0.7),
                    "messages": message_history,  # Pass read-only message history
                }
            )

            choices = Misc.get_field(response, "choices", [])
            response_message = Misc.get_field(choices[0], "message") if choices and len(choices) > 0 else None

            if response_message:
                # Only add tool_calls if they exist and are a valid list
                tool_calls: List[OpenAIFunctionCall] = Misc.get_field(response_message, "tool_calls")
                has_tool_calls = tool_calls and isinstance(tool_calls, list)

                if has_tool_calls:
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
                    tool_responses = await self._call_requested_tools(tool_calls)
                    message_history.extend(cast(List[Dict[str, Any]], tool_responses))
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
                "choices": (response.choices if hasattr(response, "choices") else []),
                "usage": (response.usage if hasattr(response, "usage") else {}),
                "model": (response.model if hasattr(response, "model") else ""),
            }
        )

    async def _query_once(self, request: Dict[str, Any]) -> Dict[str, Any]:
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

        Returns:
            Dict[str, Any]: The LLM response object containing:
                - choices[0].message: The assistant's message, which may contain tool_calls
                - usage: Token usage statistics

        Raises:
            LLMContextLengthError: If the messages exceed the context window.
            LLMRateLimitError: If rate limits are exceeded.
            LLMAuthenticationError: If authentication fails.
            LLMProviderError: For other provider-specific errors.
            LLMResponseError: If the response is invalid.
            LLMError: For any other LLM-related errors.
        """
        # Check for mock flag or function
        if callable(self._mock_llm_call):
            return await self._mock_llm_call(request)
        elif self._mock_llm_call:
            return await self._mock_llm_query(request)

        # Also check environment variable for mocking
        if os.environ.get("OPENDXA_MOCK_LLM", "").lower() == "true":
            return await self._mock_llm_query(request)

        if not self._client:
            await self.initialize()
        assert self._client is not None

        if not self.model:
            raise LLMError("No LLM model specified. Did you forget to set the API key in .env or your environment?")

        # Get message history (read-only)
        messages = Misc.get_field(request, "messages", [])
        if not messages:
            raise LLMError("messages must be provided and non-empty")

        # Build request parameters
        request = self._build_request_params(request)

        # Make the API call
        try:
            response = self._client.chat.completions.create(**request)
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

    async def _mock_llm_query(self, request: Dict[str, Any]) -> Dict[str, Any]:
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

    def _build_request_params(self, request: Dict[str, Any], available_resources: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Build request parameters for LLM API call.

        Args:
            request: Dictionary containing request parameters
            available_resources: Optional dictionary of available resources

        Returns:
            Dict[str, Any]: Dictionary of request parameters
        """
        params = {
            "messages": Misc.get_field(request, "messages", []),
            "temperature": Misc.get_field(request, "temperature", 0.7),
            "max_tokens": Misc.get_field(request, "max_tokens"),
        }

        if not available_resources:
            available_resources = Misc.get_field(request, "available_resources", {})

        # Only add model if it's available
        if self.model:
            params["model"] = self.model

        if available_resources:
            params["tools"] = self._get_openai_functions(available_resources)

        return params

    def _get_openai_functions(self, resources: Dict[str, BaseResource]) -> List[OpenAIFunctionCall]:
        """Get OpenAI functions from available resources.

        Args:
            resources: Dictionary of available resources

        Returns:
            List[OpenAIFunctionCall]: List of tool definitions
        """
        functions = []
        for _, resource in resources.items():
            functions.extend(resource.list_openai_functions())
        return functions

    async def _call_requested_tools(
        self, tool_calls: List[OpenAIFunctionCall], max_response_length: Optional[int] = MAX_TOOL_CALL_RESPONSE_LENGTH
    ) -> List[BaseResponse]:
        """Call requested resources and get responses.

        This method handles tool calls from the LLM, executing each requested tool
        and collecting their responses.

        Expected Tool Call Format:
            The format of tool calls is defined by the ToolCallable mixin, which
            converts tool definitions into OpenAI's function calling format.

            Each tool call should be a dictionary with:
            {
                "type": "function",
                "function": {
                    "name": str,  # Format: "{resource_name}__{resource_id}__{tool_name}"
                    "arguments": str  # JSON string of parameter values
                }
            }

            Example:
            {
                "type": "function",
                "function": {
                    "name": "search__123__query",
                    "arguments": '{"query": "find documents", "limit": 5}'
                }
            }

            The method will:
            1. Parse the function name to identify resource and tool
            2. Parse the arguments from JSON string to Python dict
            3. Call the appropriate tool with the arguments
            4. Collect and return all responses

            Each response will be in OpenAI's tool response format:
            {
                "role": "tool",
                "name": str,  # The original function name
                "content": str  # The tool's response or error message
            }

        Args:
            tool_calls: List of tool calls from the LLM
            max_response_length: Optional maximum length for tool responses

        Returns:
            List[BaseResponse]: List of tool responses in OpenAI format
        """
        responses: List[BaseResponse] = []
        for tool_call in tool_calls:
            try:
                # Get the function name and arguments
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)

                # Parse the function name to get the resource name, id, and tool name
                resource_name, resource_id, tool_name = ToolFormat.parse_tool_name(function_name)

                # Get the resource
                resource: Optional[ToolCallable] = cast(Optional[ToolCallable], Registerable.get_from_registry(resource_id))
                if resource is None:
                    self.warning(f"Resource {resource_name} with id {resource_id} not found")
                    continue

                # Call the tool
                response = await resource.call_tool(tool_name, arguments)

                # Convert response to JSON string to ensure JSON-serializability
                if hasattr(response, "to_json") and callable(response.to_json):
                    response = response.to_json()

                # Truncate response if needed
                if max_response_length and isinstance(response, str):
                    response = response[:max_response_length]

            except Exception as e:
                response = f"Tool call failed: {str(e)}"
                self.error(response)

            responses.append(cast(BaseResponse, {"role": "tool", "name": function_name, "content": response, "tool_call_id": tool_call.id}))

        return responses

    def _log_llm_request(self, request: Dict[str, Any]) -> None:
        """Log LLM request.

        Args:
            request: Dictionary containing request parameters
        """
        self.debug("LLM request: %s", json.dumps(request, indent=2))

    def _log_llm_response(self, response: ChatCompletion) -> None:
        """Log LLM response.

        Args:
            response: ChatCompletion object containing the response
        """
        self.debug("LLM response: %s", str(response))

    # TODO: deprecate this
    def _get_default_model(self) -> str:
        """Get default model identifier.

        Returns:
            str: Default model identifier
        """
        return "openai:gpt-4o-mini"

    async def _call_tools(self, tool_calls: List[Dict[str, Any]], available_resources: List[BaseResource]) -> List[BaseResponse]:
        """Call tools based on LLM's tool calls.

        Args:
            tool_calls: List of tool calls from LLM
            available_resources: List of available resources

        Returns:
            List[BaseResponse]: List of tool responses
        """
        responses: List[BaseResponse] = []
        for tool_call in tool_calls:
            # Find matching resource
            resource = next((r for r in available_resources if r.name == tool_call["name"]), None)
            if not resource:
                responses.append(BaseResponse(success=False, error=f"Resource {tool_call['name']} not found"))
                continue

            # Call resource
            try:
                response = await resource.query(BaseRequest(arguments=tool_call["arguments"]))
                responses.append(response)
            except Exception as e:
                responses.append(BaseResponse(success=False, error=str(e)))

        return responses

    def _validate_model(self, model_name: str) -> bool:
        """Checks if the required API keys for a given model are available.

        Args:
            model_name: The name of the model (e.g., "openai:gpt-4").

        Returns:
            True if all required keys are found in environment variables, False otherwise.
        """
        required_keys = []
        for m in self.preferred_models:
            if m.get("name") == model_name:
                required_keys = m.get("required_api_keys", [])
                break

        if not required_keys:
            # If model not in preferred_models list or has no keys listed, assume available
            # Or should we be stricter? For now, allows models not explicitly listed.
            self.log_debug(f"No API keys specified for model '{model_name}'. Assuming available.")
            return True

        missing_keys = [key for key in required_keys if not os.getenv(key)]
        if missing_keys:
            self.log_debug(f"Model '{model_name}' is missing required API keys: {missing_keys}")
            return False

        self.log_debug(f"All required API keys for model '{model_name}' are available.")
        return True

    def _find_first_available_model(self) -> Optional[str]:
        """Finds the first available model from the preferred_models list.

        Iterates through `self.preferred_models` and returns the name of the
        first model for which all `required_api_keys` are set as environment vars.

        Returns:
            The name of the first available model, or None if none are available.
        """
        self.log_debug(f"Searching for available model in preferred list: {self.preferred_models}")
        for model_config in self.preferred_models:
            model_name = model_config.get("name")
            if not model_name:
                self.log_warning("Skipping entry in preferred_models with missing 'name'.")
                continue

            if self._validate_model(model_name):
                self.log_debug(f"Found available model: {model_name}")
                return model_name

        self.log_warning("No available models found in the preferred_models list.")
        return None

    def get_available_models(self) -> List[str]:
        """Gets a list of models from preferred_models that are currently available.

        Checks API key availability for each model in `self.preferred_models`.

        Returns:
            A list of available model names.
        """
        available = []
        for model_config in self.preferred_models:
            model_name = model_config.get("name")
            if model_name and self._validate_model(model_name):
                available.append(model_name)
        self.log_debug(f"Available models based on API keys: {available}")
        return available
