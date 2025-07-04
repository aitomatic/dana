"""
Copyright © 2025 Aitomatic, Inc.

This source code is licensed under the license found in the LICENSE file in the root directory of this source tree

List models function implementation for the Dana interpreter.

This module provides the list_models function, which lists all available LLM models
in preferred order from the configuration.
"""

from typing import Any

from dana.common.utils.logging import DXA_LOGGER
from opendxa.dana.common.exceptions import SandboxError
from dana.core.lang.interpreter.functions.core.set_model_function import _get_available_model_names
from dana.core.lang.sandbox_context import SandboxContext


def list_models_function(
    context: SandboxContext,
    options: dict[str, Any] | None = None,
) -> list[str]:
    """Execute the list_models function to get all available LLM models in preferred order.

    Args:
        context: The runtime context for variable resolution.
        options: Optional parameters for the function.
               - provider (str): Filter by provider (e.g., "openai", "anthropic")
               - show_details (bool): If True, return detailed info (default: False)

    Returns:
        List of available model names in preferred order.

    Raises:
        SandboxError: If the function execution fails.

    Example:
        # List all models in Dana code
        models = list_models()

        # Filter by provider
        openai_models = list_models({"provider": "openai"})
    """
    logger = DXA_LOGGER.getLogger("opendxa.dana.list_models")

    if options is None:
        options = {}

    try:
        # Get all available models in preferred order
        all_models = _get_available_model_names()

        # Filter by provider if specified
        provider_filter = options.get("provider")
        if provider_filter:
            provider_filter = provider_filter.lower()
            filtered_models = []
            for model in all_models:
                if ":" in model:
                    model_provider = model.split(":", 1)[0].lower()
                    if model_provider == provider_filter:
                        filtered_models.append(model)
                elif provider_filter in model.lower():
                    filtered_models.append(model)
            models = filtered_models
        else:
            models = all_models

        logger.info(f"Listed {len(models)} available models" + (f" (filtered by provider: {provider_filter})" if provider_filter else ""))

        return models

    except Exception as e:
        error_msg = f"Unexpected error listing models: {e}"
        logger.error(error_msg)
        raise SandboxError(error_msg) from e
