"""LLM resource implementation for Dana.

This module provides the LLMResource class, which manages LLM model selection
and interaction. It leverages the ConfigLoader for base configuration and supports
runtime overrides.

Features:
- Centralized configuration via ConfigLoader ('dana_config.json').
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
from typing import Any

# Apply AISuite/Anthropic compatibility patch
from dana.common.utils.aisuite_patch import apply_aisuite_patch, is_patch_applied

# Ensure patch is applied
if not is_patch_applied():
    apply_aisuite_patch()

import aisuite as ai
from openai.types.chat import ChatCompletion

from dana.common.config import ConfigLoader
from dana.common.exceptions import (
    ConfigurationError,
    LLMError,
)
from dana.common.mixins.tool_callable import OpenAIFunctionCall
from dana.common.sys_resource.base_sys_resource import BaseSysResource
from dana.common.sys_resource.llm.llm_configuration_manager import LLMConfigurationManager
from dana.common.sys_resource.llm.llm_query_executor import LLMQueryExecutor
from dana.common.sys_resource.llm.llm_tool_call_manager import LLMToolCallManager
from dana.common.types import BaseRequest, BaseResponse
from dana.common.utils.misc import Misc

# To avoid accidentally sending too much data to the LLM,
# we limit the total length of tool-call responses.
MAX_TOOL_CALL_RESPONSE_LENGTH = 10000

# Removed parameter filtering - config file controls what gets sent to AISuite


class LegacyLLMResource(BaseSysResource):
    """LLM resource with flexible model selection and configuration.

    Provides a unified interface for LLM interaction, integrating with the
    centralized ConfigLoader for base settings ('dana_config.json') and
    allowing overrides through constructor arguments and request parameters.

    Configuration Hierarchy:
    1. Base configuration loaded by ConfigLoader (using its search order for 'dana_config.json').
    2. `preferred_models` list provided to constructor (overrides list from config).
    3. `model` provided to constructor (overrides automatic selection from preferred list or config default).
    4. `kwargs` provided to constructor (overrides default parameters like temperature from config).
    5. Parameters in the `query` request (overrides constructor/config defaults for that specific query).

    Attributes:
        model: The selected LLM model name (can be set explicitly or determined automatically).
        preferred_models: List of preferred models used for automatic selection.
                          Format: `[{"name": "provider:model_name", "required_env_vars": ["ENV_VAR_NAME"]}]`
        config: The final configuration dictionary used for LLM calls, incorporating
                defaults from ConfigLoader and constructor overrides.

    Instantiation Examples:

    1.  **Use Configuration File Defaults (Simplest Case):**
        ```python
        # Instantiating with no arguments uses the name "system_llm".
        # Relies entirely on 'dana_config.json' found by ConfigLoader.
        # Requires 'preferred_models' or 'default_model' in the config.
        # Requires relevant API keys (e.g., OPENAI_API_KEY) in environment.
        llm = LLMResource() # Name defaults to "system_llm"

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
            {"name": "anthropic:claude-3-opus", "required_env_vars": ["ANTHROPIC_API_KEY"]},
            {"name": "groq:llama3-70b", "required_env_vars": ["GROQ_API_KEY"]}
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
    to work correctly, the environment variables listed in `required_env_vars`
    for the models in the effective `preferred_models` list must be set.
    """

    # Removed hardcoded DEFAULT_PREFERRED_MODELS, loaded from ConfigLoader now

    def __init__(self, name: str = "system_llm", model: str | None = None, preferred_models: list[dict[str, Any]] | None = None, **kwargs):
        """Initializes the LLMResource.

        Loads base configuration using ConfigLoader, applies overrides from
        constructor arguments, and determines the final LLM model to use.

        Args:
            name: The name of the resource instance. Defaults to "system_llm".
            model: Explicitly sets the model to use, overriding automatic selection.
            preferred_models: Overrides the preferred models list from the config file.
                              Used for automatic model selection if `model` is not set.
                              Format: `[{"name": "p:m", "required_env_vars": ["K"]}]`
            **kwargs: Additional configuration parameters (e.g., temperature, max_tokens)
                      that override values from the config file.
        """
        super().__init__(name)

        # Initialize configuration manager (Phase 1B integration)
        self._config_manager = LLMConfigurationManager(explicit_model=model)

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
        # Priority: constructor arg -> find available -> None (let user figure it out)
        if model and model != "auto":
            # Accept any explicitly provided model without validation
            self._model = model
            self.debug(f"Using explicitly set model: {self._model}")
        else:
            # Try to find an available model, but don't fail if none found
            self._model = self._find_first_available_model()
            if self._model:
                self.debug(f"Auto-selected model: {self._model}")
            else:
                self.debug("No model auto-selected - will be determined at usage time")

        # Initialize query executor (Phase 5A integration)
        self._query_executor = LLMQueryExecutor(
            client=None,  # Will be set in initialize()
            model=self._model,
            query_strategy=self.get_query_strategy(),
            query_max_iterations=self.get_query_max_iterations(),
        )
        # Initialize the LLM client
        self._client = None

        # Load provider configs from base_config
        if "llm" in base_config and "provider_configs" in base_config["llm"]:
            raw_provider_configs = base_config["llm"]["provider_configs"]
            self.debug(f"Raw provider_configs from config: {raw_provider_configs}")
            self.provider_configs = self._resolve_env_vars_in_provider_configs(raw_provider_configs)
            self.debug(f"Resolved provider_configs: {self.provider_configs}")
        else:
            self.provider_configs = {}
            self.debug("No provider_configs found in config file, using empty dict.")

        # Merge provider_configs from kwargs (allows overriding config file settings)
        if "provider_configs" in kwargs:
            self.debug("Merging provider_configs from constructor arguments.")
            for provider, config in kwargs["provider_configs"].items():
                if provider in self.provider_configs:
                    # Update existing provider config with new values
                    self.provider_configs[provider].update(config)
                    self.debug(f"Updated provider config for '{provider}' with constructor values.")
                else:
                    # Add new provider config
                    self.provider_configs[provider] = config
                    self.debug(f"Added new provider config for '{provider}' from constructor.")

        self._started = False
        # Don't auto-initialize - use lazy initialization

        # --- Build final configuration ---
        # Priority: kwargs -> base_config
        self.config = base_config.copy()  # Start with base config
        self.config.update(kwargs)  # Apply constructor overrides
        # Ensure model is in the final config if determined
        if self._model:
            self.config["model"] = self._model

        # Use direct model value to avoid triggering validation
        model_display = self._model or "auto-select"
        self.info(f"Initialized LLMResource '{name}' with model '{model_display}'")
        self.debug(f"Final LLM config keys: {list(self.config.keys())}")

        # Mocking setup
        self._mock_llm_call: bool | Callable[[dict[str, Any]], dict[str, Any]] | None = None

    @property
    def model(self) -> str | None:
        """The currently selected LLM model name."""
        return self._model

    @property
    def physical_model_name(self) -> str | None:
        """The physical model name to send to AISuite."""
        if self._model == "local":
            # For local models, get the actual model name from provider config
            local_config = self.provider_configs.get("local", {})
            return local_config.get("model_name", "local")
        elif self._model and self._model.startswith("vllm:"):
            # Handle vLLM model name transformation
            base_name = self._model.replace("vllm:", "openai:", 1)
            # Check for environment variable override
            physical_override = os.getenv("VLLM_API_MODEL_NAME")
            if physical_override:
                return f"openai:{physical_override}"
            return base_name
        return self._model

    @property
    def aisuite_model_name(self) -> str | None:
        """The model name to send to AISuite in API calls."""
        if self._model == "local":
            # For local models, use api_type from config (default to "openai")
            local_config = self.provider_configs.get("local", {})
            api_type = local_config.get("api_type", "openai")
            physical_model = local_config.get("model_name", "local")
            return f"{api_type}:{physical_model}"
        elif self._model and self._model.startswith("vllm:"):
            # Handle vLLM model name transformation
            base_name = self._model.replace("vllm:", "openai:", 1)
            # Check for environment variable override
            physical_override = os.getenv("VLLM_API_MODEL_NAME")
            if physical_override:
                return f"openai:{physical_override}"
            return base_name
        return self._model

    @model.setter
    def model(self, value: str) -> None:
        """Set the model and force reinitialization with new provider config."""
        if value != self._model:
            self._model = value
            self._config_manager.selected_model = value  # Keep config manager in sync
            self.config["model"] = value
            self.info(f"LLM model set to: {self._model}")

            # Force reinitialization when model changes
            self._client = None
            self._started = False
            self._is_available = False

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
            self._mock_llm_call is True or callable(self._mock_llm_call) or os.environ.get("DANA_MOCK_LLM", "").lower() == "true"
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
        """Initialize the AISuite client with the current model's provider configuration."""
        if not self._client:
            self.debug("Initializing AISuite client...")

            # Explicitly apply the AISuite patch to fix the proxies issue
            if not is_patch_applied():
                self.debug("Applying AISuite patch for proxies issue...")
                patch_success = apply_aisuite_patch()
                if patch_success:
                    self.debug("AISuite patch applied successfully")
                else:
                    self.warning("Failed to apply AISuite patch - may encounter proxies issue")
            else:
                self.debug("AISuite patch already applied")

            # Get provider configuration for current model
            provider_configs = self._get_provider_config_for_current_model()

            if not provider_configs:
                self.error("No valid provider configuration found for current model")
                self._is_available = False
                return

            try:
                # Workaround for AISuite 0.1.11 proxies bug
                # Clean provider configs to remove unsupported parameters
                provider_configs = self._clean_provider_configs_for_aisuite(provider_configs)

                self.debug(f"Initializing AISuite client with provider_configs: {provider_configs}")

                self._client = ai.Client(provider_configs=provider_configs)
                self.debug("AISuite client initialized successfully.")
                self._query_executor.client = self._client
                self._query_executor.model = self.aisuite_model_name  # Use AISuite-compatible model name
                if self.model:
                    self.info("LLM client initialized successfully for model: %s", self.model)
                    self._is_available = True
                else:
                    self.warning("LLM client initialized without a model")
                    self._is_available = False
            except Exception as e:
                error_msg = str(e)
                if "proxies" in error_msg:
                    self.error(f"AISuite proxies error (patch may not be working): {e}")
                    self.error("Try restarting the application or check AISuite/Anthropic versions")
                else:
                    self.error(f"Failed to initialize AISuite client: {e}")
                self._is_available = False

    def _clean_provider_configs_for_aisuite(self, provider_configs: dict[str, Any]) -> dict[str, Any]:
        """Clean provider configs to remove AISuite-unsupported parameters.

        Args:
            provider_configs: Original provider configurations

        Returns:
            Provider configurations with unsupported parameters removed
        """
        # Remove problematic parameters that AISuite doesn't support
        cleaned_configs = {}
        unsupported_params = {"proxies", "model_name", "api_type", "http_client"}

        for provider, config in provider_configs.items():
            if isinstance(config, dict):
                # Filter out unsupported parameters
                cleaned_config = {k: v for k, v in config.items() if k not in unsupported_params}
                cleaned_configs[provider] = cleaned_config

                # Log if we removed any parameters
                removed_params = set(config.keys()) - set(cleaned_config.keys())
                if removed_params:
                    self.debug(f"Removed unsupported parameters from {provider}: {removed_params}")
            else:
                cleaned_configs[provider] = config

        return cleaned_configs

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
        # self.info(f"LLMResource '{self.name}' shut down")

    def _ensure_started(self) -> None:
        """Ensure LLM resource is started before use"""
        if not self._started:
            self.startup()

    def can_handle(self, request: BaseRequest) -> bool:
        """Check if request contains prompt."""
        return request and "prompt" in request.arguments

    def with_mock_llm_call(self, mock_llm_call: bool | Callable[[dict[str, Any]], dict[str, Any]]) -> "LegacyLLMResource":
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
        self._query_executor.model = self.aisuite_model_name  # Use AISuite-compatible model name
        self._query_executor.query_strategy = self.get_query_strategy()
        self._query_executor.query_max_iterations = self.get_query_max_iterations()

        # Set mock if configured
        if self._mock_llm_call is not None:
            self._query_executor.set_mock_llm_call(self._mock_llm_call)

        # Delegate to query executor
        # Let query executor handle request parameter building (including Anthropic transformation)
        return await self._query_executor.query_iterative(request, tool_call_handler=self._call_requested_tools)

    async def _query_once(self, request: dict[str, Any]) -> dict[str, Any]:
        """Make a single call to the LLM with the given request.

        This method delegates to the query executor for actual execution.

        Args:
            request: Dictionary containing query parameters

        Returns:
            Dict[str, Any]: The LLM response object
        """
        # Update query executor with current settings
        self._query_executor.model = self.aisuite_model_name  # Use AISuite-compatible model name
        self._query_executor.client = self._client

        # Set mock if configured
        if self._mock_llm_call is not None:
            self._query_executor.set_mock_llm_call(self._mock_llm_call)

        # Delegate to query executor
        # Let query executor handle request parameter building (including Anthropic transformation)
        return await self._query_executor.query_once(request)

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
        # CRITICAL DISCOVERY: AISuite automatically handles Anthropic system message transformation
        # but creates conflicts if we also add system parameters. Let AISuite handle it.
        return self._tool_call_manager.build_request_params(request, self.aisuite_model_name, available_resources)

    def _get_openai_functions(self, resources: dict[str, BaseSysResource]) -> list[OpenAIFunctionCall]:
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

            self.info(f"  [{i + 1}] {role.upper()}: {content_preview}")

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
                    function_name = (
                        tool_call.function.name if hasattr(tool_call, "function") and hasattr(tool_call.function, "name") else "unknown"
                    )
                    self.info(f"    [{i + 1}] {function_name}")

        # Keep debug level for full response details
        self.debug("LLM response (full): %s", str(response))

    async def _call_tools(self, tool_calls: list[dict[str, Any]], available_resources: list[BaseSysResource]) -> list[BaseResponse]:
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
        """Check if model has required API key."""
        return self._config_manager._validate_model(model_name)

    def _find_first_available_model(self) -> str | None:
        """Find first available model from preferred list."""
        return self._config_manager._find_first_available_model()

    def get_available_models(self) -> list[str]:
        """Get list of models with API keys set."""
        self.debug("Delegating get_available_models to configuration manager")
        return self._config_manager.get_available_models()

    def _is_model_available(self, model_info: dict[str, Any]) -> bool:
        """Check if model is available based on API key."""
        model_name = model_info.get("name")
        return bool(model_name and self._config_manager._is_model_actually_available(model_name))

    def _resolve_env_vars_in_provider_configs(self, provider_configs: dict[str, Any]) -> dict[str, Any]:
        """Resolve environment variable references in provider configs.

        Converts values like "env:ANTHROPIC_API_KEY" to the actual environment variable value.

        Args:
            provider_configs: Provider configuration dictionary

        Returns:
            Provider configuration with environment variables resolved
        """
        resolved_configs = {}

        for provider, config in provider_configs.items():
            resolved_config = {}
            for key, value in config.items():
                if isinstance(value, str) and value.startswith("env:"):
                    # Extract environment variable name
                    env_var_name = value[4:]  # Remove "env:" prefix
                    env_value = os.getenv(env_var_name)
                    if env_value:
                        resolved_config[key] = env_value
                        self.debug(f"Resolved {provider}.{key} from environment variable {env_var_name}")
                    else:
                        self.debug(f"Environment variable {env_var_name} not set for {provider}.{key}")
                        # Don't include the key if env var is not set
                        continue
                else:
                    resolved_config[key] = value

            if resolved_config:  # Only include provider if it has valid config
                resolved_configs[provider] = resolved_config

        return resolved_configs

    def _get_provider_config_for_current_model(self) -> dict[str, Any]:
        """Get the provider configuration for the current model."""
        # Determine provider from model name
        if not self._model:
            self.warning("No model set")
            return {}

        provider = self._get_provider_from_model(self._model)

        if not provider:
            self.warning(f"Could not determine provider for model: {self._model}")
            return {}

        # Get provider config from configuration
        provider_config = self.provider_configs.get(provider, {})

        if not provider_config:
            self.warning(f"No provider configuration found for provider: {provider}")
            return {}

        # Resolve environment variables in provider config
        resolved_config = self._resolve_provider_config(provider_config)

        if not resolved_config:
            self.warning(f"No valid configuration after resolving environment variables for provider: {provider}")
            return {}

        # Use the consolidated helper method for all model-specific transformations
        self.info(f"Getting AISuite config for model: {self._model} with provider config: {resolved_config}")
        return self._get_aisuite_config_for_model(self._model, resolved_config)

    def _get_provider_from_model(self, model_name: str) -> str | None:
        """Extract provider name from model name."""
        if model_name == "local":
            return "local"
        elif ":" in model_name:
            return model_name.split(":", 1)[0]
        else:
            return None

    def _resolve_provider_config(self, provider_config: dict[str, Any]) -> dict[str, Any]:
        """Resolve environment variables in a single provider config."""
        resolved_config = {}

        for key, value in provider_config.items():
            # Don't filter parameters here - let _filter_aisuite_params handle provider-specific filtering
            if isinstance(value, str) and value.startswith("env:"):
                # Extract environment variable name
                env_var = value[4:]  # Remove "env:" prefix
                env_value = os.getenv(env_var)
                if env_value:
                    resolved_config[key] = env_value
                    self.debug(f"Resolved {key} from environment variable {env_var}")
                else:
                    # Don't include the config if env var is not set
                    self.debug(f"Environment variable {env_var} not set for {key}, skipping")
                    continue
            else:
                # Use value as-is
                resolved_config[key] = value

        return resolved_config

    def _get_aisuite_config_for_model(self, model_name: str, provider_config: dict[str, Any]) -> dict[str, Any]:
        """Single method to handle all model-specific AISuite config transformation."""
        if model_name == "local":
            # Local models use the api_type from config (default to "openai")
            api_type = provider_config.get("api_type", "openai")
            return {api_type: provider_config}
        elif model_name and model_name.startswith("vllm:"):
            # vLLM models use OpenAI provider in AISuite
            return {"openai": provider_config}
        else:
            # Standard provider:model format
            provider = model_name.split(":", 1)[0] if ":" in model_name else "openai"

            # Special handling for Azure: construct deployment URL dynamically
            if provider == "azure" and ":" in model_name:
                config_copy = provider_config.copy()
                deployment_name = model_name.split(":", 1)[1]  # Extract model name (e.g., "gpt-4o")
                base_url = config_copy.get("base_url", "")

                # Construct the full deployment URL if base_url doesn't already include deployment path
                if base_url and not base_url.endswith(f"/openai/deployments/{deployment_name}"):
                    # Remove trailing slash if present
                    base_url = base_url.rstrip("/")
                    # Construct deployment URL
                    deployment_url = f"{base_url}/openai/deployments/{deployment_name}"
                    config_copy["base_url"] = deployment_url
                    self.debug(f"Constructed Azure deployment URL: {deployment_url}")

                return {provider: config_copy}
            else:
                return {provider: provider_config}
