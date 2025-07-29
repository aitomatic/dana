"""Embedding resource with flexible model selection and configuration.

Provides a unified interface for embedding generation, integrating with the
centralized ConfigLoader for base settings ('dana_config.json') and
allowing overrides through constructor arguments and request parameters.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import os
from typing import Any

from dana.common.config.config_loader import ConfigLoader
from dana.common.exceptions import ConfigurationError
from dana.common.mixins.tool_callable import ToolCallable
from dana.common.resource.base_resource import BaseResource
from dana.common.types import BaseRequest, BaseResponse
from dana.common.resource.embedding.embedding_configuration_manager import EmbeddingConfigurationManager
from dana.common.resource.embedding.embedding_query_executor import EmbeddingQueryExecutor


class EmbeddingResource(BaseResource):
    """Embedding resource with flexible model selection and configuration.

    Provides a unified interface for embedding generation, integrating with the
    centralized ConfigLoader for base settings ('dana_config.json') and
    allowing overrides through constructor arguments and request parameters.

    Configuration Hierarchy:
    1. Base configuration loaded by ConfigLoader (using its search order for 'dana_config.json').
    2. `preferred_models` list provided to constructor (overrides list from config).
    3. `model` provided to constructor (overrides automatic selection from preferred list or config default).
    4. `kwargs` provided to constructor (overrides default parameters like batch_size from config).
    5. Parameters in the `query` request (overrides constructor/config defaults for that specific query).

    Attributes:
        model: The selected embedding model name (can be set explicitly or determined automatically).
        preferred_models: List of preferred models used for automatic selection.
                          Format: `["provider:model_name", ...]`
        config: The final configuration dictionary used for embedding calls, incorporating
                defaults from ConfigLoader and constructor overrides.

    Instantiation Examples:

    1.  **Use Configuration File Defaults (Simplest Case):**
        ```python
        # Instantiating with no arguments uses the name "default_embedding".
        # Relies entirely on 'dana_config.json' found by ConfigLoader.
        # Requires 'preferred_models' or 'default_model' in the config.
        # Requires relevant API keys (e.g., OPENAI_API_KEY) in environment.
        embedding = EmbeddingResource() # Name defaults to "default_embedding"

        # You can still provide a custom name:
        # embedding = EmbeddingResource(name="my_specific_embedding")
        ```

    2.  **Explicitly Specify Model:**
        ```python
        # Overrides automatic selection and 'default_model' from config.
        # Still uses other parameters (e.g., batch_size) from config if not overridden.
        # Still requires API keys for the specified model in environment.
        embedding = EmbeddingResource(name="openai_embedding", model="openai:text-embedding-3-small")
        ```

    3.  **Override Preferred Models for Selection:**
        ```python
        # Uses a custom list for automatic selection, ignoring the list in the config.
        # Requires API keys for models in *this* list.
        custom_models = [
            "openai:text-embedding-3-large",
            "huggingface:BAAI/bge-small-en-v1.5"
        ]
        embedding = EmbeddingResource(name="custom_selection_embedding", preferred_models=custom_models)
        ```

    4.  **Override Specific Embedding Parameters:**
        ```python
        # Uses default model selection (from config or overridden preferred_models).
        # Overrides 'batch_size' and 'dimension' from the config file.
        embedding = EmbeddingResource(name="custom_embedding", batch_size=100, dimension=1536)
        ```

    5.  **Combine Overrides:**
        ```python
        # Explicit model, overrides preferred list, overrides batch_size.
        embedding = EmbeddingResource(name="specific_embedding",
                                    model="openai:text-embedding-3-large",
                                    batch_size=200)
        ```

    **Important:** For automatic model selection (`_find_first_available_model`)
    to work correctly, the environment variables for the models in the effective
    `preferred_models` list must be set.
    """

    def __init__(self, name: str = "default_embedding", model: str | None = None, preferred_models: list[str] | None = None, **kwargs):
        """Initializes the EmbeddingResource.

        Loads base configuration using ConfigLoader, applies overrides from
        constructor arguments, and determines the final embedding model to use.

        Args:
            name: The name of the resource instance. Defaults to "default_embedding".
            model: Explicitly sets the model to use, overriding automatic selection.
            preferred_models: Overrides the preferred models list from the config file.
                              Used for automatic model selection if `model` is not set.
                              Format: `["provider:model_name", ...]`
            **kwargs: Additional configuration parameters (e.g., batch_size, dimension)
                      that override values from the config file.
        """
        super().__init__(name)

        # Initialize configuration manager
        self._config_manager = EmbeddingConfigurationManager(explicit_model=model)

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
        elif "embedding" in base_config and "preferred_models" in base_config["embedding"]:
            self.preferred_models = base_config["embedding"]["preferred_models"]
            self.debug("Using preferred_models from config file (embedding section).")
        else:
            self.preferred_models = []
            self.warning("No preferred_models list found in config or arguments.")

        # --- Determine the model ---
        # Priority: constructor arg -> find available -> None (let user figure it out)
        if model:
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

        # Initialize query executor
        self._query_executor = EmbeddingQueryExecutor(
            model=self._model,
            batch_size=self.get_batch_size(),
        )

        # Load provider configs from base_config
        if "embedding" in base_config and "provider_configs" in base_config["embedding"]:
            raw_provider_configs = base_config["embedding"]["provider_configs"]
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
        self.info(f"EmbeddingResource '{self.name}' initialized with model: {model_display}")

    @property
    def model(self) -> str | None:
        """Get the current embedding model."""
        return self._model

    @model.setter
    def model(self, value: str) -> None:
        """Set the embedding model."""
        self._model = value
        self.config["model"] = value
        if self._query_executor:
            self._query_executor.model = value

    def get_batch_size(self) -> int:
        """Get the batch size for embedding generation."""
        return self.config.get("batch_size", 100)

    def get_dimension(self) -> int | None:
        """Get the expected dimension for embeddings."""
        return self.config.get("dimension")

    def _resolve_env_vars_in_provider_configs(self, raw_configs: dict[str, Any]) -> dict[str, Any]:
        """Resolve environment variables in provider configurations.

        Converts 'env:VAR_NAME' values to actual environment variable values.

        Args:
            raw_configs: Raw provider configurations from config file

        Returns:
            Resolved provider configurations with actual environment values
        """
        resolved_configs = {}

        for provider, config in raw_configs.items():
            resolved_config = {}
            for key, value in config.items():
                if isinstance(value, str) and value.startswith("env:"):
                    env_var = value[4:]  # Remove 'env:' prefix
                    env_value = os.getenv(env_var)
                    if env_value:
                        resolved_config[key] = env_value
                        self.debug(f"Resolved {provider}.{key} from environment variable {env_var}")
                    else:
                        self.warning(f"Environment variable {env_var} not found for {provider}.{key}")
                        resolved_config[key] = value  # Keep original value
                else:
                    resolved_config[key] = value
            resolved_configs[provider] = resolved_config

        return resolved_configs

    def _find_first_available_model(self) -> str | None:
        """Find the first available embedding model from preferred list.

        Checks each model in the preferred_models list to see if the required
        API keys are available in the environment.

        Returns:
            First available model name, or None if no models are available
        """
        for model in self.preferred_models:
            if self._is_model_available(model):
                self.debug(f"Found available model: {model}")
                return model

        self.debug("No available models found in preferred list")
        return None

    def _is_model_available(self, model: str) -> bool:
        """Check if a model is available by validating required API keys.

        Args:
            model: Model name in format "provider:model_name"

        Returns:
            True if model is available (API keys present), False otherwise
        """
        if ":" not in model:
            self.warning(f"Invalid model format: {model}. Expected 'provider:model_name'")
            return False

        provider = model.split(":", 1)[0]

        # Check provider-specific requirements
        if provider == "openai":
            return bool(os.getenv("OPENAI_API_KEY"))
        elif provider == "huggingface":
            # HuggingFace models can work without API key for local models
            return True
        elif provider == "cohere":
            return bool(os.getenv("COHERE_API_KEY"))
        else:
            self.warning(f"Unknown provider: {provider}")
            return False

    @ToolCallable.tool
    async def query(self, request: BaseRequest) -> BaseResponse:
        """Generate embeddings for input text(s).

        Args:
            request: Request containing text(s) to embed

        Returns:
            Response containing generated embeddings
        """
        try:
            # Initialize if not already done
            await self.initialize()

            # Extract text(s) from request
            if not hasattr(request, "arguments") or not request.arguments:
                return BaseResponse(success=False, error="No arguments provided")

            texts = request.arguments.get("texts") or request.arguments.get("text")
            if not texts:
                return BaseResponse(success=False, error="No text provided for embedding")

            # Ensure texts is a list
            if isinstance(texts, str):
                texts = [texts]
            elif not isinstance(texts, list):
                return BaseResponse(success=False, error="Text must be a string or list of strings")

            # Generate embeddings
            embeddings = await self._query_executor.generate_embeddings(texts, self.provider_configs)

            return BaseResponse(
                success=True,
                content={
                    "embeddings": embeddings,
                    "model": self._model,
                    "dimension": len(embeddings[0]) if embeddings else None,
                    "count": len(embeddings),
                },
            )

        except Exception as e:
            self.error(f"Error generating embeddings: {e}")
            return BaseResponse(success=False, error=str(e))

    async def initialize(self) -> None:
        """Initialize the embedding resource."""
        if self._started:
            return

        self.debug("Initializing EmbeddingResource...")

        # Validate that we have a model
        if not self._model:
            self._model = self._find_first_available_model()
            if not self._model:
                raise ConfigurationError("No embedding model available. Check API keys and configuration.")

        # Initialize query executor with provider configs
        await self._query_executor.initialize(self.provider_configs)

        self._started = True
        self.info(f"EmbeddingResource initialized successfully with model: {self._model}")

    async def cleanup(self) -> None:
        """Cleanup embedding resource."""
        if self._query_executor:
            await self._query_executor.cleanup()
        self._started = False
        self.debug("EmbeddingResource cleaned up")
