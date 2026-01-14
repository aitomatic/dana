"""
LlamaStack client manager.

Manages a singleton LlamaStackClient instance for all LlamaStack APIs
(Inference, Agent, Storage, Conversation). This is a wrapper around the
actual LlamaStackClient from llama_stack_client library.

We create this outside of llm/providers/llamastack.py because there will be
multiple plug-ins that need to use the same client instance.
"""

import structlog

from ..config import config_manager

# Optional import - llama-stack may not be installed in all environments
try:
    from llama_stack_client import LlamaStackClient
except ImportError:
    LlamaStackClient = None  # type: ignore


logger = structlog.get_logger()


class LlamaStackClientManager:
    """
    Manages the shared LlamaStackClient singleton instance.

    This is NOT the client itself - it's a manager/factory that provides
    access to the underlying LlamaStackClient instance, handling URL
    resolution and ensuring only one client is created.
    """

    _instance = None
    _client = None
    _base_url = None

    @classmethod
    def get_client(cls) -> "LlamaStackClient":
        """
        Get or create LlamaStack client instance.
        Resolves base URL from config, env, or defaults to localhost:8321.

        Returns:
            Shared LlamaStackClient instance

        Raises:
            ImportError: If llama-stack package is not installed
        """
        if LlamaStackClient is None:
            raise ImportError(
                "llama-stack package is not installed. "
                "Install it with: pip install llama-stack>=0.3.0 "
                "or: uv add llama-stack>=0.3.0"
            )
        
        if cls._client is None:
            base_url = config_manager.get_provider_base_url("llamastack")
            if not base_url:
                base_url = "http://localhost:8321"  # Default for uv run
            logger.info("Creating LlamaStack client", base_url=base_url)
            cls._client = LlamaStackClient(base_url=base_url)
            cls._base_url = base_url
        return cls._client

    @classmethod
    def reset(cls):
        """Reset client instance (useful for testing)."""
        cls._client = None
        cls._base_url = None
