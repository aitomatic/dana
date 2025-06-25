"""
Copyright © 2025 Aitomatic, Inc.

This source code is licensed under the license found in the LICENSE file in the root directory of this source tree

Set model function implementation for the Dana interpreter.

This module provides the set_model function, which allows changing the LLM model
being used in the current sandbox context.
"""

from typing import Any

from opendxa.common.exceptions import LLMError
from opendxa.common.resource.llm_resource import LLMResource
from opendxa.common.utils.logging import DXA_LOGGER
from opendxa.dana.common.exceptions import SandboxError
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def set_model_function(
    context: SandboxContext,
    model: str,
    options: dict[str, Any] | None = None,
) -> str:
    """Execute the set_model function to change the LLM model in the current context.

    Args:
        context: The runtime context for variable resolution.
        model: The model name to set (e.g., "openai:gpt-4", "anthropic:claude-3-5-sonnet").
        options: Optional parameters for the function (currently unused).

    Returns:
        The name of the model that was set.

    Raises:
        SandboxError: If the function execution fails.
        LLMError: If the model is invalid or unavailable.

    Example:
        # Set model in Dana code
        set_model("openai:gpt-4o")
        set_model("anthropic:claude-3-5-sonnet-20241022")
    """
    logger = DXA_LOGGER.getLogger("opendxa.dana.set_model")

    if options is None:
        options = {}

    if not model:
        raise SandboxError("set_model function requires a non-empty model name")

    if not isinstance(model, str):
        raise SandboxError(f"Model name must be a string, got {type(model).__name__}")

    try:
        # Get the current LLM resource from context
        llm_resource = context.get("system:llm_resource")

        if llm_resource is None:
            # If no LLM resource exists, create a new one with the specified model
            logger.info(f"No existing LLM resource found, creating new one with model: {model}")
            llm_resource = LLMResource(name="dana_llm", model=model)
            context.set("system:llm_resource", llm_resource)
        else:
            # Update the existing LLM resource's model
            logger.info(f"Updating existing LLM resource model from '{llm_resource.model}' to '{model}'")
            llm_resource.model = model

        logger.info(f"Successfully set LLM model to: {model}")
        return model

    except LLMError as e:
        error_msg = f"Failed to set model '{model}': {e}"
        logger.error(error_msg)
        raise SandboxError(error_msg) from e
    except Exception as e:
        error_msg = f"Unexpected error setting model '{model}': {e}"
        logger.error(error_msg)
        raise SandboxError(error_msg) from e
