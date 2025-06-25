"""
Copyright © 2025 Aitomatic, Inc.

This source code is licensed under the license found in the LICENSE file in the root directory of this source tree

Set model function implementation for the Dana interpreter.

This module provides the set_model function, which allows changing the LLM model
being used in the current sandbox context with fuzzy matching support.
"""

import difflib
from typing import Any

from opendxa.common.config.config_loader import ConfigLoader
from opendxa.common.exceptions import LLMError
from opendxa.common.resource.llm_resource import LLMResource
from opendxa.common.utils.logging import DXA_LOGGER
from opendxa.dana.common.exceptions import SandboxError
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def _get_available_model_names() -> list[str]:
    """Get list of available model names from configuration.
    
    Returns:
        List of available model names from the LLM configuration.
    """
    try:
        config_loader = ConfigLoader()
        config = config_loader.get_default_config()
        
        # Get models from both preferred_models and all_models
        all_models = set()
        
        # Add from preferred_models (check both root level and llm sublevel)
        preferred_models = config.get("preferred_models", [])
        if not preferred_models:
            preferred_models = config.get("llm", {}).get("preferred_models", [])
        
        for model in preferred_models:
            if isinstance(model, str):
                all_models.add(model)
            elif isinstance(model, dict) and model.get("name"):
                all_models.add(model["name"])
        
        # Add from all_models list
        all_models_list = config.get("all_models", [])
        if not all_models_list:
            all_models_list = config.get("llm", {}).get("all_models", [])
        
        for model in all_models_list:
            if isinstance(model, str):
                all_models.add(model)
        
        # Add common model names as fallback
        fallback_models = [
            "openai:gpt-4o",
            "openai:gpt-4o-mini", 
            "openai:gpt-4-turbo",
            "anthropic:claude-3-5-sonnet-20241022",
            "anthropic:claude-3-5-haiku-20241022",
            "google:gemini-1.5-pro",
            "google:gemini-1.5-flash",
            "cohere:command-r-plus",
            "mistral:mistral-large-latest",
            "groq:llama-3.1-70b-versatile",
            "deepseek:deepseek-chat",
            "deepseek:deepseek-coder",
            "ollama:llama3.1",
            "ollama:mixtral",
            "together:meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
            "together:mistralai/Mixtral-8x7B-Instruct-v0.1",
            "huggingface:microsoft/DialoGPT-medium",
            "azure:gpt-4o",
            "azure:gpt-35-turbo",
        ]
        all_models.update(fallback_models)
        
        return sorted(list(all_models))
    except Exception:
        # Return fallback list if config loading fails
        return [
            "openai:gpt-4o",
            "openai:gpt-4o-mini", 
            "openai:gpt-4-turbo",
            "anthropic:claude-3-5-sonnet-20241022",
            "anthropic:claude-3-5-haiku-20241022",
            "google:gemini-1.5-pro",
            "google:gemini-1.5-flash",
            "cohere:command-r-plus",
            "mistral:mistral-large-latest",
            "groq:llama-3.1-70b-versatile",
            "deepseek:deepseek-chat",
            "deepseek:deepseek-coder",
            "ollama:llama3.1",
            "ollama:mixtral",
            "together:meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
            "together:mistralai/Mixtral-8x7B-Instruct-v0.1",
            "huggingface:microsoft/DialoGPT-medium",
            "azure:gpt-4o",
            "azure:gpt-35-turbo",
        ]


def _find_closest_model_match(model_input: str, available_models: list[str]) -> str | None:
    """Find the closest matching model name using fuzzy matching.
    
    Args:
        model_input: The user-provided model string
        available_models: List of available model names
        
    Returns:
        The closest matching model name, or None if no good match found.
    """
    if not model_input or not available_models:
        return None
    
    # Try exact match first (case insensitive)
    model_lower = model_input.lower()
    for model in available_models:
        if model.lower() == model_lower:
            return model
    
    # Try substring match (e.g., "gpt-4" matches "openai:gpt-4o")
    for model in available_models:
        if model_lower in model.lower() or model.lower() in model_lower:
            return model
    
    # Use fuzzy matching for close matches
    # Get close matches with a reasonable cutoff (0.6 = 60% similarity)
    close_matches = difflib.get_close_matches(
        model_input, 
        available_models, 
        n=1,  # Return only the best match
        cutoff=0.6  # 60% similarity threshold
    )
    
    if close_matches:
        return close_matches[0]
    
    # Try matching just the model name part (after the colon)
    model_name_part = model_input.split(":")[-1] if ":" in model_input else model_input
    for model in available_models:
        model_part = model.split(":")[-1] if ":" in model else model
        if model_name_part.lower() in model_part.lower():
            return model
    
    return None


def set_model_function(
    context: SandboxContext,
    model: str,
    options: dict[str, Any] | None = None,
) -> str:
    """Execute the set_model function to change the LLM model in the current context.

    This function supports fuzzy matching to find the closest available model name
    from the configuration if an exact match is not found.

    Args:
        context: The runtime context for variable resolution.
        model: The model name to set (e.g., "gpt-4", "claude", "openai:gpt-4o").
               Supports partial names that will be matched to available models.
        options: Optional parameters for the function.
               - exact_match_only (bool): If True, disable fuzzy matching (default: False)

    Returns:
        The name of the model that was actually set (may be different from input if fuzzy matched).

    Raises:
        SandboxError: If the function execution fails or no suitable model is found.
        LLMError: If the model is invalid or unavailable.

    Example:
        # Exact match
        set_model("openai:gpt-4o")
        
        # Fuzzy match examples
        set_model("gpt-4")          # matches "openai:gpt-4o"
        set_model("claude")         # matches "anthropic:claude-3-5-sonnet-20241022"
        set_model("gemini")         # matches "google:gemini-1.5-pro"
    """
    logger = DXA_LOGGER.getLogger("opendxa.dana.set_model")

    if options is None:
        options = {}

    if not model:
        raise SandboxError("set_model function requires a non-empty model name")

    if not isinstance(model, str):
        raise SandboxError(f"Model name must be a string, got {type(model).__name__}")

    # Check if exact matching is requested
    exact_match_only = options.get("exact_match_only", False)
    
    # Store the original input for logging
    original_input = model

    try:
        # Try to find the best matching model
        if not exact_match_only:
            available_models = _get_available_model_names()
            matched_model = _find_closest_model_match(model, available_models)
            
            if matched_model and matched_model != model:
                logger.info(f"Fuzzy matched '{original_input}' to '{matched_model}'")
                model = matched_model
            elif not matched_model:
                logger.warning(f"No close match found for '{original_input}', trying as-is")
        
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

        if original_input != model:
            logger.info(f"Successfully set LLM model to: {model} (matched from '{original_input}')")
        else:
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
