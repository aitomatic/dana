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
from collections.abc import Callable
from typing import Any, cast

import aisuite as ai
from openai.types.chat import ChatCompletion

from opendxa.common.config import ConfigLoader
from opendxa.common.exceptions import (
    ConfigurationError,
    LLMError,
    ResourceError,
)
from opendxa.common.mixins.tool_callable import OpenAIFunctionCall
from opendxa.common.resource.base_resource import BaseResource
from opendxa.common.resource.llm_configuration_manager import LLMConfigurationManager
from opendxa.common.resource.llm_query_executor import LLMQueryExecutor
from opendxa.common.resource.llm_tool_call_manager import LLMToolCallManager
from opendxa.common.types import BaseRequest, BaseResponse
from opendxa.common.utils.misc import Misc

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

    def __init__(self, name: str = "default_llm", model: str | None = None, preferred_models: list[dict[str, Any]] | None = None, **kwargs):
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

        # Initialize configuration manager (Phase 1B integration)
        self._config_manager = LLMConfigurationManager(explicit_model=model, config=kwargs)

        # Initialize tool call manager (Phase 4A integration)
        self._tool_call_manager = LLMToolCallManager()
        # Load base configuration from ConfigLoader
        try:
            base_config = ConfigLoader().get_default_config()
            self.debug(f"Loaded base config: {list(base_config.keys())}")
        except ConfigurationError as e:
            self.warning(f"Could not load default config: {e}. Proceeding with minimal defaults.")
            base_config = {}

        # Determine the preferred models list
        # Priority: constructor arg -> config file -> empty list
        if preferred_models is not None:
            self.preferred_models = preferred_models
            self.debug("Using preferred_models from constructor argument.")
        elif "llm" in base_config and "preferred_models" in base_config["llm"]:
            self.preferred_models = base_config["llm"]["preferred_models"]
            self.debug("Using preferred_models from config file (llm section).")
        else:
            self.preferred_models = []
            self.warning("No preferred_models list found in config or arguments.")

        # --- Determine the model ---
        # Priority: constructor arg -> find available -> default from config -> None
        if model:
            # Validate the explicitly provided model
            if not self._validate_model(model):
                self.warning(f"Explicitly provided model '{model}' seems unavailable (missing API keys?). Continuing anyway.")
            self._model = model  # Use underscore to avoid setter validation initially
            self.debug(f"Using explicitly set model: {self._model}")
        else:
            # Automatically find the first available model from the list
            self._model = self._find_first_available_model()
            if not self._model:
                # If auto-selection fails, log an error (unless in mock mode).
                # We no longer fall back to `default_model`.
                is_mock_mode = os.environ.get("OPENDXA_MOCK_LLM", "").lower() == "true"
                if not is_mock_mode:
                    self.error(
                        "Could not find an available model from the preferred_models list. "
                        "No explicit model was provided, and the fallback to 'default_model' is no longer used."
                    )
                else:
                    self.debug("No available model found, but mock mode is enabled. This is expected in test environments.")
                # self._model remains None.

        # Initialize query executor (Phase 5A integration)
        self._query_executor = LLMQueryExecutor(
            client=None,  # Will be set in initialize()
            model=self._model,
            query_strategy=self.get_query_strategy(),
            query_max_iterations=self.get_query_max_iterations(),
        )
        # --- Build final configuration ---
        # Priority: kwargs -> base_config
        self.config = base_config.copy()  # Start with base config
        self.config.update(kwargs)  # Apply constructor overrides
        # Ensure model is in the final config if determined
        if self._model:
            self.config["model"] = self._model

        self.info(f"Initialized LLMResource '{name}' with model '{self.model}'")
        self.debug(f"Final LLM config keys: {list(self.config.keys())}")

        # Mocking setup
        self._mock_llm_call: bool | Callable[[dict[str, Any]], dict[str, Any]] | None = None

        # Initialize the LLM client
        self._client = None
        self.provider_configs = {}
        self._started = False
        # Don't auto-initialize - use lazy initialization

    @property
    def model(self) -> str | None:
        """The currently selected LLM model name."""
        return self._model

    @model.setter
    def model(self, value: str) -> None:
        """Sets the LLM model, validating its availability."""
        try:
            self._config_manager.selected_model = value
            self._model = value  # Keep backward compatibility
            self.config["model"] = value  # Keep config in sync
            self.info(f"LLM model set to: {self._model}")
        except Exception as e:
            self.warning(f"Setting model to '{value}', but validation failed: {e}")
            # Still set it for backward compatibility
            self._model = value
            self.config["model"] = value

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
        # Lazy initialization - ensure LLM is started before use
        if not self._started:
            await self.initialize()
            self._started = True

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

            # Prepare provider configs for aisuite
            final_provider_configs = self.provider_configs.copy()

            # If 'local' model is configured, check for environment variables.
            # If they exist, point the 'openai' provider to the local server.
            # Otherwise, log a warning and continue, allowing fallback to other models.
            preferred_model_names = [p.get("name") for p in self.config.get("preferred_models", [])]
            if "local" in preferred_model_names:
                self.debug("Local LLM detected in preferences, checking environment variables...")
                local_url = os.getenv("LOCAL_LLM_URL")
                local_name = os.getenv("LOCAL_LLM_NAME")

                if local_url and local_name:
                    # If env vars are set, re-route the openai provider to the local URL.
                    self.debug(f"Local LLM environment variables found. Re-routing 'openai' provider to {local_url}")
                    if "openai" not in final_provider_configs:
                        final_provider_configs["openai"] = {}
                    final_provider_configs["openai"]["base_url"] = local_url
                    # Explicitly set api_key to empty to prevent sending AUTH headers to local server
                    final_provider_configs["openai"]["api_key"] = ""
                else:
                    # If env vars are not set, just log a warning. The 'local' model
                    # will be skipped later in the availability check.
                    self.warning(
                        "Local LLM is configured, but 'LOCAL_LLM_URL' or 'LOCAL_LLM_NAME' is missing. "
                        "The 'local' model will be unavailable."
                    )

            try:
                self._client = ai.Client(provider_configs=final_provider_configs)
                self.debug("AISuite client initialized successfully.")

                # Set client on query executor
                self._query_executor.client = self._client
                self._query_executor.model = self.model

                # Only log if we have a model
                if self.model:
                    self.info("LLM client initialized successfully for model: %s", self.model)
                    self._is_available = True
                else:
                    self.warning("LLM client initialized without a model")
                    self._is_available = False
            except Exception as e:
                self.error(f"Failed to initialize AISuite client: {e}")
                self._is_available = False

    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self._client:
            self._client = None

    def startup(self) -> None:
        """Synchronous startup - initialize LLM client"""
        if self._started:
            return

        Misc.safe_asyncio_run(self.initialize)
        self._started = True
        self.info(f"LLMResource '{self.name}' started synchronously")

    def shutdown(self) -> None:
        """Synchronous shutdown - cleanup LLM client"""
        if not self._started:
            return

        Misc.safe_asyncio_run(self.cleanup)
        self._started = False
        self.info(f"LLMResource '{self.name}' shut down")

    def _ensure_started(self) -> None:
        """Ensure LLM resource is started before use"""
        if not self._started:
            self.startup()

    def can_handle(self, request: dict[str, Any]) -> bool:
        """Check if request contains prompt."""
        return "prompt" in request

    def with_mock_llm_call(self, mock_llm_call: bool | Callable[[dict[str, Any]], dict[str, Any]]) -> "LLMResource":
        """Set the mock LLM call function."""
        if isinstance(mock_llm_call, Callable) or isinstance(mock_llm_call, bool):
            self._mock_llm_call = mock_llm_call
        else:
            raise LLMError("mock_llm_call must be a Callable or a boolean")

        return self

    # ===== Core Query Processing Methods =====
    async def _query_iterative(self, request: dict[str, Any]) -> dict[str, Any]:
        """Handle a conversation with the LLM that may involve multiple tool calls.

        This method delegates to the query executor for actual execution.

        Args:
            request: Dictionary containing query parameters

        Returns:
            Dict[str, Any]: The final LLM response after all tool calls are complete
        """
        # Update query executor with current settings
        self._query_executor.model = self.model
        self._query_executor.query_strategy = self.get_query_strategy()
        self._query_executor.query_max_iterations = self.get_query_max_iterations()

        # Set mock if configured
        if self._mock_llm_call is not None:
            self._query_executor.set_mock_llm_call(self._mock_llm_call)

        # Delegate to query executor
        return await self._query_executor.query_iterative(
            request, tool_call_handler=self._call_requested_tools, build_request_params=self._build_request_params
        )

    async def _query_once(self, request: dict[str, Any]) -> dict[str, Any]:
        """Make a single call to the LLM with the given request.

        This method delegates to the query executor for actual execution.

        Args:
            request: Dictionary containing query parameters

        Returns:
            Dict[str, Any]: The LLM response object
        """
        # Update query executor with current settings
        self._query_executor.model = self.model
        self._query_executor.client = self._client

        # Set mock if configured
        if self._mock_llm_call is not None:
            self._query_executor.set_mock_llm_call(self._mock_llm_call)

        # Delegate to query executor
        return await self._query_executor.query_once(request, build_request_params=self._build_request_params)

    async def _mock_llm_query(self, request: dict[str, Any]) -> dict[str, Any]:
        """Mock LLM query for testing purposes.

        This method delegates to the query executor for mock execution.

        Args:
            request: Dictionary containing the request parameters

        Returns:
            Dict[str, Any]: Mock response
        """
        return await self._query_executor.mock_llm_query(request)

    def _build_request_params(self, request: dict[str, Any], available_resources: dict[str, Any] | None = None) -> dict[str, Any]:
        """Build request parameters for LLM API call.

        Args:
            request: Dictionary containing request parameters
            available_resources: Optional dictionary of available resources

        Returns:
            Dict[str, Any]: Dictionary of request parameters
        """
        return self._tool_call_manager.build_request_params(request, self.model, available_resources)

    def _get_openai_functions(self, resources: dict[str, BaseResource]) -> list[OpenAIFunctionCall]:
        """Get OpenAI functions from available resources.

        Args:
            resources: Dictionary of available resources

        Returns:
            List[OpenAIFunctionCall]: List of tool definitions
        """
        return self._tool_call_manager.get_openai_functions(resources)

    async def _call_requested_tools(
        self, tool_calls: list[OpenAIFunctionCall], max_response_length: int | None = MAX_TOOL_CALL_RESPONSE_LENGTH
    ) -> list[BaseResponse]:
        """Call requested resources and get responses.

        This method handles tool calls from the LLM, executing each requested tool
        and collecting their responses.

        Args:
            tool_calls: List of tool calls from the LLM
            max_response_length: Optional maximum length for tool responses

        Returns:
            List[BaseResponse]: List of tool responses in OpenAI format
        """
        # Set the max response length on the manager if provided
        if max_response_length is not None:
            old_max_length = self._tool_call_manager.max_response_length
            self._tool_call_manager.max_response_length = max_response_length

        try:
            dict_responses = await self._tool_call_manager.call_requested_tools(tool_calls)
            # Convert dict responses to BaseResponse objects
            responses: list[BaseResponse] = []
            for response_dict in dict_responses:
                content = response_dict.get("content", "")
                success = not content.startswith("Tool call failed:")
                error = None if success else content
                # NOTE : response_dict include `tool_call_id` and need to be kept untouched
                responses.append(BaseResponse(success=success, content=response_dict, error=error))
            return responses
        finally:
            # Restore original max length if we changed it
            if max_response_length is not None:
                self._tool_call_manager.max_response_length = old_max_length

    def _log_llm_request(self, request: dict[str, Any]) -> None:
        """Log LLM request at INFO level.

        Args:
            request: Dictionary containing request parameters
        """
        # Extract key information for cleaner logging
        messages = request.get("messages", [])
        model = request.get("model", self.model or "unknown")
        temperature = request.get("temperature", 0.7)
        max_tokens = request.get("max_tokens", "unspecified")
        
        self.info(f"🤖 LLM Request to {model} (temp={temperature}, max_tokens={max_tokens})")
        
        # Log each message in the conversation
        for i, message in enumerate(messages):
            role = message.get("role", "unknown")
            content = message.get("content", "")
            
            # Truncate very long content for readability
            if isinstance(content, str) and len(content) > 300:
                content_preview = content[:300] + "... [truncated]"
            else:
                content_preview = content
                
            self.info(f"  [{i+1}] {role.upper()}: {content_preview}")
            
            # Log tool calls if present
            if "tool_calls" in message and message["tool_calls"]:
                self.info(f"    Tool calls: {len(message['tool_calls'])} tools requested")
        
        # Keep debug level for full request details
        self.debug("LLM request (full): %s", json.dumps(request, indent=2))

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
                if len(content) > 300:
                    content_preview = content[:300] + "... [truncated]"
                else:
                    content_preview = content
                self.info(f"  {role.upper()}: {content_preview}")
            
            # Log tool calls if present
            if tool_calls:
                self.info(f"  🔧 Tool calls: {len(tool_calls)} tools requested")
                for i, tool_call in enumerate(tool_calls):
                    function_name = tool_call.function.name if hasattr(tool_call, "function") and hasattr(tool_call.function, "name") else "unknown"
                    self.info(f"    [{i+1}] {function_name}")
        
        # Keep debug level for full response details
        self.debug("LLM response (full): %s", str(response))

    async def _call_tools(self, tool_calls: list[dict[str, Any]], available_resources: list[BaseResource]) -> list[BaseResponse]:
        """Call tools based on LLM's tool calls.

        Args:
            tool_calls: List of tool calls from LLM
            available_resources: List of available resources

        Returns:
            List[BaseResponse]: List of tool responses
        """
        responses: list[BaseResponse] = []
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
        """Checks if the necessary API keys for a given model are available.

        This method delegates to the LLMConfigurationManager, which now uses
        ValidationUtilities.validate_model_availability() for centralized,
        consistent validation logic across the OpenDXA framework.

        Args:
            model_name: Name of the model to validate

        Returns:
            True if the model is available and properly configured, False otherwise
        """
        return self._config_manager._validate_model(model_name)

    def _find_first_available_model(self) -> str | None:
        """Finds the first available model from the preferred_models list.

        Iterates through `self.preferred_models` and returns the name of the
        first model for which all `required_api_keys` are set as environment vars.

        Returns:
            The name of the first available model, or None if none are available.
        """
        return self._config_manager._find_first_available_model()

    def get_available_models(self) -> list[str]:
        """Gets a list of models from preferred_models that are currently available.

        Checks API key availability for each model in `self.preferred_models`.

        Returns:
            A list of available model names.
        """
        available = self._config_manager.get_available_models()
        self.debug(f"Available models based on API keys: {available}")
        return available

    def _is_model_available(self, model_info: dict[str, Any]) -> bool:
        """Check if a given model is available based on required API keys."""
        model_name = model_info.get("name")
        if not model_name:
            return False

        # Special handling for the 'local' model
        if model_name == "local":
            local_url = os.getenv("LOCAL_LLM_URL")
            local_name = os.getenv("LOCAL_LLM_NAME")
            if local_url and local_name:
                self.debug("Found 'local' model with required environment variables.")
                return True
            self.debug("Skipping 'local' model as environment variables are not set.")
            return False

        # Standard handling for other models
        try:
            provider, _ = model_name.split(":", 1)
        except ValueError:
            self.warning(f"Invalid model format: {model_name}")
            return False

        # Check if the provider is available
        if provider not in self.provider_configs:
            self.warning(f"Provider {provider} not found in provider_configs")
            return False

        # Check if the model is available
        if model_name not in self.provider_configs[provider]:
            self.warning(f"Model {model_name} not found in provider_configs")
            return False

        return True
