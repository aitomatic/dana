"""Embedding resource for generating text embeddings.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import os
from typing import Any

from dana.common.config.config_loader import ConfigLoader
from dana.common.exceptions import ConfigurationError
from dana.common.mixins.tool_callable import ToolCallable
from dana.common.sys_resource.base_sys_resource import BaseSysResource
from dana.common.sys_resource.embedding.embedding_query_executor import EmbeddingQueryExecutor
from dana.common.types import BaseRequest, BaseResponse


class EmbeddingResource(BaseSysResource):
    """Embedding resource for generating text embeddings.

    Loads configuration from dana_config.json and provides a unified interface
    for embedding generation across different providers (OpenAI, HuggingFace, Cohere).

    Args:
        name: Resource instance name (default: "default_embedding")
        model: Specific model to use (e.g., "openai:text-embedding-3-small")
        **kwargs: Configuration overrides (batch_size, dimension, etc.)
    """

    def __init__(self, name: str = "default_embedding", model: str | None = None, **kwargs):
        """Initialize the EmbeddingResource."""
        super().__init__(name)

        # Load configuration from dana_config.json
        try:
            base_config = ConfigLoader().get_default_config()
            embedding_config = base_config.get("embedding", {})
        except ConfigurationError as e:
            self.warning(f"Could not load config: {e}. Using defaults.")
            embedding_config = {}

        # Load and resolve provider configurations
        self.provider_configs = self._load_provider_configs(embedding_config, kwargs)

        # Get preferred models from config
        self.preferred_models = embedding_config.get("preferred_models", [])

        # Determine model to use
        self._model = model or self._select_available_model()

        # Build final configuration
        self.config = {**embedding_config, **kwargs}
        if self._model:
            self.config["model"] = self._model

        # Initialize query executor
        self._query_executor = EmbeddingQueryExecutor(
            model=self._model,
            batch_size=self.get_batch_size(),
        )

        self._started = False
        self.info(f"EmbeddingResource '{self.name}' initialized with model: {self._model or 'auto-detect'}")

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

    def _load_provider_configs(self, embedding_config: dict[str, Any], kwargs: dict[str, Any]) -> dict[str, Any]:
        """Load and resolve provider configurations."""
        provider_configs = {}

        # Load from config file
        raw_configs = embedding_config.get("provider_configs", {})
        for provider, config in raw_configs.items():
            resolved_config = {}
            for key, value in config.items():
                if isinstance(value, str) and value.startswith("env:"):
                    env_var = value[4:]  # Remove 'env:' prefix
                    resolved_config[key] = os.getenv(env_var, value)
                else:
                    resolved_config[key] = value
            provider_configs[provider] = resolved_config

        # Apply overrides from kwargs
        if "provider_configs" in kwargs:
            for provider, config in kwargs["provider_configs"].items():
                if provider in provider_configs:
                    provider_configs[provider].update(config)
                else:
                    provider_configs[provider] = config

        # Provide environment-based defaults when config entries are missing
        env_defaults: dict[str, dict[str, Any]] = {
            "ollama": {
                "base_url": os.getenv("LOCAL_EMBEDDING_BASE_URL") or os.getenv("LOCAL_BASE_URL"),
                "model_name": os.getenv("LOCAL_EMBEDDING_MODEL_NAME"),
                "batch_size": os.getenv("EMBEDDING_BATCH_SIZE"),
                "dimension": os.getenv("EMBEDDING_DIMENSIONS"),
            },
            "local": {
                "base_url": os.getenv("LOCAL_EMBEDDING_BASE_URL") or os.getenv("LOCAL_BASE_URL"),
                "model_name": os.getenv("LOCAL_EMBEDDING_MODEL_NAME"),
                "batch_size": os.getenv("EMBEDDING_BATCH_SIZE"),
                "dimension": os.getenv("EMBEDDING_DIMENSIONS"),
            },
            "openai": {
                "api_key": os.getenv("OPENAI_API_KEY"),
            },
            "azure": {
                "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
                "base_url": os.getenv("AZURE_OPENAI_API_URL"),
                "api_version": os.getenv("AZURE_OPENAI_API_VERSION"),
            },
            "cohere": {
                "api_key": os.getenv("COHERE_API_KEY"),
            },
            "huggingface": {
                "api_key": os.getenv("HF_TOKEN"),
            },
            "ibm_watsonx": {
                "api_key": os.getenv("WATSONX_API_KEY"),
                "project_id": os.getenv("WATSONX_PROJECT_ID"),
            },
        }

        for provider, defaults in env_defaults.items():
            cleaned: dict[str, Any] = {}
            for key, value in defaults.items():
                if value is None or value == "":
                    continue
                if key in {"batch_size", "dimension"}:
                    try:
                        cleaned[key] = int(value)
                    except (TypeError, ValueError):
                        cleaned[key] = value
                else:
                    cleaned[key] = value

            if not cleaned:
                continue

            if provider not in provider_configs:
                provider_configs[provider] = cleaned
            else:
                for key, value in cleaned.items():
                    provider_configs[provider].setdefault(key, value)

        return provider_configs

    def _select_available_model(self) -> str | None:
        """Select the first available model from preferred list."""
        for model in self.preferred_models:
            if self._is_model_available(model):
                return model
        return None

    def _is_model_available(self, model: str) -> bool:
        """Check if a model is available by validating configuration and credentials."""
        if ":" not in model:
            return False

        provider, _ = model.split(":", 1)
        provider_config = self.provider_configs.get(provider, {})

        def _resolve_env(value: Any) -> Any:
            if isinstance(value, str) and value.startswith("env:"):
                return os.getenv(value[4:])
            return value

        def _has_value(value: Any) -> bool:
            resolved = _resolve_env(value)
            return bool(resolved)

        if provider == "ollama":
            base_url = provider_config.get("base_url") or os.getenv("LOCAL_EMBEDDING_BASE_URL") or os.getenv("LOCAL_BASE_URL")
            model_name = provider_config.get("model_name") or os.getenv("LOCAL_EMBEDDING_MODEL_NAME")
            return _has_value(base_url) and _has_value(model_name)

        if provider == "local":
            base_url = provider_config.get("base_url") or os.getenv("LOCAL_EMBEDDING_BASE_URL") or os.getenv("LOCAL_BASE_URL")
            model_name = provider_config.get("model_name") or os.getenv("LOCAL_EMBEDDING_MODEL_NAME")
            return _has_value(base_url) and _has_value(model_name)

        if provider == "openai":
            api_key = provider_config.get("api_key") or os.getenv("OPENAI_API_KEY")
            return _has_value(api_key)

        if provider == "cohere":
            api_key = provider_config.get("api_key") or os.getenv("COHERE_API_KEY")
            return _has_value(api_key)

        if provider == "azure":
            api_key = provider_config.get("api_key") or os.getenv("AZURE_OPENAI_API_KEY")
            base_url = provider_config.get("base_url") or os.getenv("AZURE_OPENAI_API_URL")
            return _has_value(api_key) and _has_value(base_url)

        if provider == "ibm_watsonx":
            api_key = provider_config.get("apikey") or provider_config.get("api_key") or os.getenv("WATSONX_API_KEY")
            project_id = provider_config.get("project_id") or provider_config.get("projectId") or os.getenv("WATSONX_PROJECT_ID")
            return _has_value(api_key) and _has_value(project_id)

        if provider == "huggingface":
            # Public models can be used without token, but if a token is provided ensure it resolves
            token = provider_config.get("api_key") or os.getenv("HF_TOKEN")
            return token is None or _has_value(token)

        return False

    @ToolCallable.tool
    async def query(self, request: BaseRequest) -> BaseResponse:
        """Generate embeddings for input text(s)."""
        try:
            await self.initialize()

            # Extract text(s) from request
            if not hasattr(request, "arguments") or not request.arguments:
                return BaseResponse(success=False, error="No arguments provided")

            texts = request.arguments.get("texts") or request.arguments.get("text")
            if not texts:
                return BaseResponse(success=False, error="No text provided")

            # Ensure texts is a list
            if isinstance(texts, str):
                texts = [texts]

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

        # Select model if not already set
        if not self._model:
            self._model = self._select_available_model()
            if not self._model:
                raise ConfigurationError("No embedding model available. Check API keys and configuration.")

        # Initialize query executor
        await self._query_executor.initialize(self.provider_configs)

        self._started = True
        self.info(f"EmbeddingResource initialized with model: {self._model}")
