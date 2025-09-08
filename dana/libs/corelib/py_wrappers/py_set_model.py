"""
Set model function for Dana standard library.

This module provides the set_model function for configuring LLM models.
"""

__all__ = ["py_set_model"]

import difflib
from typing import Any

from dana.common.config.config_loader import ConfigLoader
from dana.common.exceptions import LLMError, SandboxError
from dana.common.sys_resource.llm.llm_configuration_manager import LLMConfigurationManager
from dana.common.utils.logging import DANA_LOGGER
from dana.core.lang.sandbox_context import SandboxContext


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

        # Add from preferred_models (only check llm sublevel)
        preferred_models = config.get("llm", {}).get("preferred_models", [])

        for model in preferred_models:
            if isinstance(model, str):
                all_models.add(model)
            elif isinstance(model, dict) and model.get("name"):
                all_models.add(model["name"])

        # Add from all_models list (only check llm sublevel)
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

        # Return models preserving preference order, then fallback models
        # First, get models from config in preference order
        preference_ordered_models = []
        for model in preferred_models:
            model_name = model if isinstance(model, str) else model.get("name")
            if model_name and model_name in all_models:
                preference_ordered_models.append(model_name)
                all_models.remove(model_name)

        # Add any remaining models (from fallback list) alphabetically
        remaining_models = sorted(list(all_models))

        return preference_ordered_models + remaining_models
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
    """Find the closest matching model name using enhanced fuzzy matching.

    This function uses intelligent provider-aware matching to find the best model.

    Args:
        model_input: The user-provided model string
        available_models: List of available model names

    Returns:
        The closest matching model name, or None if no good match found.
    """
    if not model_input or not available_models:
        return None

    model_lower = model_input.lower()

    # Try exact match first (case insensitive)
    for model in available_models:
        if model.lower() == model_lower:
            return model

    # Smart provider matching - if user types just a provider name, return the best model
    def _get_best_openai_model(models: list[str]) -> str | None:
        """Get the best OpenAI model with proper priority matching."""
        if not models:
            return None
        # First try exact match for gpt-4o
        for model in models:
            if model.endswith(":gpt-4o"):
                return model
        # Then try other gpt-4o variants
        for model in models:
            if "gpt-4o" in model:
                return model
        return models[0]

    def _get_best_azure_model(models: list[str]) -> str | None:
        """Get the best Azure model with proper priority matching."""
        if not models:
            return None
        # First try exact match for gpt-4o
        for model in models:
            if model.endswith(":gpt-4o"):
                return model
        # Then try other gpt-4o variants
        for model in models:
            if "gpt-4o" in model:
                return model
        return models[0]

    provider_preferences = {
        "openai": _get_best_openai_model,
        "anthropic": lambda models: next((m for m in models if "claude-3-5-sonnet" in m), models[0] if models else None),
        "google": lambda models: next((m for m in models if "gemini-1.5-pro" in m), models[0] if models else None),
        "groq": lambda models: next((m for m in models if "llama-3" in m and "70b" in m), models[0] if models else None),
        "azure": _get_best_azure_model,
        "deepseek": lambda models: next((m for m in models if "deepseek-chat" in m), models[0] if models else None),
    }

    if model_lower in provider_preferences:
        provider_models = [m for m in available_models if m.startswith(f"{model_lower}:")]
        if provider_models:
            best_model = provider_preferences[model_lower](provider_models)
            if best_model:
                return best_model

    # Enhanced substring matching with provider preference
    substring_matches = []
    for model in available_models:
        if model_lower in model.lower() or model.lower() in model_lower:
            substring_matches.append(model)

    if substring_matches:
        if len(substring_matches) == 1:
            return substring_matches[0]

        # Smart provider preferences for common models
        if "gpt" in model_lower:
            # For GPT models, prefer OpenAI over Azure, then prefer latest versions
            openai_matches = [m for m in substring_matches if m.startswith("openai:")]
            if openai_matches:
                # Prefer gpt-4o over gpt-4o-mini, gpt-4 over gpt-3.5
                # Use proper priority matching to avoid substring issues
                priority_order = ["gpt-4o", "gpt-4", "gpt-3.5"]

                # First pass: look for exact matches
                for priority in priority_order:
                    exact_match = f"openai:{priority}"
                    if exact_match in openai_matches:
                        return exact_match

                # Second pass: look for variations (like gpt-4o-mini)
                for priority in priority_order:
                    for match in openai_matches:
                        model_name = match.split(":", 1)[-1]
                        # Only match if it starts with priority followed by a delimiter
                        if model_name.startswith(priority) and len(model_name) > len(priority):
                            next_char = model_name[len(priority)]
                            if next_char in ["-", "_", "."]:
                                return match

                return openai_matches[0]

            # Fallback to Azure if no OpenAI
            azure_matches = [m for m in substring_matches if m.startswith("azure:")]
            if azure_matches:
                return azure_matches[0]

        elif "claude" in model_lower:
            # For Claude models, prefer latest versions
            anthropic_matches = [m for m in substring_matches if m.startswith("anthropic:")]
            if anthropic_matches:
                # Prefer claude-3-5-sonnet over haiku
                for match in anthropic_matches:
                    if "sonnet" in match:
                        return match
                return anthropic_matches[0]

        elif "gemini" in model_lower:
            # For Gemini models, prefer pro over flash
            google_matches = [m for m in substring_matches if m.startswith("google:")]
            if google_matches:
                for match in google_matches:
                    if "pro" in match:
                        return match
                return google_matches[0]

        # Return first match if no smart preference applies
        return substring_matches[0]

    # Enhanced fuzzy matching with better threshold
    close_matches = difflib.get_close_matches(
        model_input,
        available_models,
        n=3,  # Get top 3 matches
        cutoff=0.5,  # Lower threshold for more flexibility
    )

    if close_matches:
        # Apply smart preferences to fuzzy matches too
        if "gpt" in model_lower:
            openai_matches = [m for m in close_matches if m.startswith("openai:")]
            if openai_matches:
                return openai_matches[0]
        elif "claude" in model_lower:
            anthropic_matches = [m for m in close_matches if m.startswith("anthropic:")]
            if anthropic_matches:
                return anthropic_matches[0]

        return close_matches[0]

    # Try matching just the model name part (after the colon)
    model_name_part = model_input.split(":")[-1] if ":" in model_input else model_input
    for model in available_models:
        model_part = model.split(":")[-1] if ":" in model else model
        if model_name_part.lower() in model_part.lower():
            return model

    return None


def py_set_model(
    context: SandboxContext,
    model: str | None = None,
    options: dict[str, Any] | None = None,
) -> str:
    """Execute the set_model function to change the LLM model in the current context.

    This function supports fuzzy matching to find the closest available model name
    from the configuration if an exact match is not found.

    Args:
        context: The runtime context for variable resolution.
        model: The model name to set (e.g., "gpt-4", "claude", "openai:gpt-4o").
               Supports partial names that will be matched to available models.
               If None or not provided, displays current model and available options.
        options: Optional parameters for the function.
               - exact_match_only (bool): If True, disable fuzzy matching (default: False)

    Returns:
        The name of the model that was actually set (may be different from input if fuzzy matched),
        or the currently selected model if no model argument is provided.

    Raises:
        SandboxError: If the function execution fails or no suitable model is found.
        LLMError: If the model is invalid or unavailable.

    Example:
        # Display current model and available options
        set_model()

        # Set exact match
        set_model("openai:gpt-4o")

        # Fuzzy match examples
        set_model("gpt-4")          # matches "openai:gpt-4o"
        set_model("claude")         # matches "anthropic:claude-3-5-*")
        set_model("gemini")         # matches "google:gemini-1.5-pro"
    """
    logger = DANA_LOGGER.getLogger("dana.set_model")

    if options is None:
        options = {}

    # Get the current LLM resource from context using system resource access
    llm_resource = context.get_system_llm_resource()

    # If no model argument provided, display comprehensive information
    if model is None:
        # Get current model - only show model if it was explicitly set in context
        current_model = "None"
        if llm_resource is not None and llm_resource.model is not None:
            current_model = llm_resource.model

        # Get only available models (with API keys)
        config_manager = LLMConfigurationManager()
        available_models = config_manager.get_available_models()

        # Display concise information
        print(f"Current model: {current_model}")

        if available_models:
            print("Available models:")
            for model_name in available_models:
                marker = "✓" if model_name == current_model else " "
                print(f"  {marker} {model_name}")

            print("\nExamples:")
            print("  set_model('gpt-4')    # fuzzy match")
            print("  set_model('claude')   # fuzzy match")
            print("  set_model('openai')   # best provider model")
        else:
            print("No models available - check your API keys in environment variables")
            print("Common API keys: OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY")

        return current_model

    # Validate model argument
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

        if llm_resource is None:
            # If no LLM resource exists in context, create a new one with the specified model
            logger.info(f"No existing LLM resource found in context, creating new one with model: {model}")
            from dana.core.builtin_types.resource.builtins.llm_resource_type import LLMResourceType

            dana_llm = LLMResourceType.create_default_instance()
            dana_llm.model = model
            context.set_system_llm_resource(dana_llm)
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
