"""
Copyright © 2025 Aitomatic, Inc.

This source code is licensed under the license found in the LICENSE file in the root directory of this source tree

Reason function implementation for the Dana interpreter.

This module provides the reason function, which handles reasoning in the Dana interpreter.
With Phase 4: IPVReason Integration, this function now automatically optimizes prompts
using the IPV (Infer-Process-Validate) pattern for better results.
"""

import json
import os
from typing import Any

from opendxa.common.config.config_loader import ConfigLoader
from opendxa.common.resource.llm_resource import LLMResource
from opendxa.common.types import BaseRequest
from opendxa.common.utils.logging import DXA_LOGGER
from opendxa.common.utils.misc import Misc
from opendxa.dana.common.exceptions import SandboxError
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def reason_function(
    prompt: str,
    context: SandboxContext,
    options: dict[str, Any] | None = None,
    use_mock: bool | None = None,
) -> Any:
    """Execute the reason function to generate a response using an LLM.

    This function now automatically uses IPVReason for intelligent optimization,
    making 95% of users get better results without needing to know about IPV.

    Args:
        prompt: The prompt string to send to the LLM (can be a string or a list with LiteralExpression)
        context: The sandbox context
        options: Optional parameters for the LLM call, including:
            - system_message: Custom system message (default: helpful assistant)
            - temperature: Controls randomness (default: 0.7)
            - max_tokens: Limit on response length
            - format: Output format ("text" or "json")
            - enable_ipv: Enable IPV optimization (default: True)
            - use_original: Force use of original implementation (default: False)
            - model: Optional specific model name to use (e.g., "gpt-4").
                     If provided, the function will try to find a matching configured model.
            - raw_prompt: If True, bypasses IPV optimization and uses the prompt as-is.
        use_mock: Force use of mock responses (True) or real LLM calls (False).
                  If None, defaults to checking OPENDXA_MOCK_LLM environment variable.

    Returns:
        The LLM's response to the prompt, optimized through IPV when enabled (unless raw_prompt is True)

    Raises:
        SandboxError: If the function execution fails or parameters are invalid
    """
    logger = DXA_LOGGER.getLogger("opendxa.dana.reason")
    options = options or {}

    # Extract model and raw_prompt from options dictionary
    model_from_options = options.get("model")
    raw_prompt_from_options = options.get("raw_prompt", False)

    if not prompt:
        raise SandboxError("reason function requires a non-empty prompt")

    # Convert prompt to string if it's not already
    if not isinstance(prompt, str):
        prompt = str(prompt)

    # Check if IPV optimization should be used
    enable_ipv = options.get("enable_ipv", True)  # IPV enabled by default
    use_original = options.get("use_original", False)  # Original implementation available

    # If raw_prompt is true, always use original implementation
    if raw_prompt_from_options:  # Use extracted value
        logger.debug("raw_prompt is True, using original implementation directly.")
        return _reason_original_implementation(prompt, context, options, use_mock, model_from_options)  # Pass extracted model

    # Use IPV optimization unless explicitly disabled or use_original is True
    if enable_ipv and not use_original:
        try:
            return _reason_with_ipv(prompt, context, options, use_mock, model_from_options)  # Pass extracted model
        except Exception as e:
            # If IPV fails, fall back to original implementation
            logger.warning(f"IPV optimization failed, falling back to original implementation: {e}")
            return _reason_original_implementation(prompt, context, options, use_mock, model_from_options)  # Pass extracted model
    else:
        # Use original implementation directly
        return _reason_original_implementation(prompt, context, options, use_mock, model_from_options)  # Pass extracted model


def _reason_with_ipv(
    prompt: str,
    context: SandboxContext,
    options: dict[str, Any],
    use_mock: bool | None = None,
    model: str | None = None,
) -> Any:
    """Enhanced reason function using IPVReason for optimization."""
    logger = DXA_LOGGER.getLogger("opendxa.dana.reason.ipv")

    try:
        # Import IPVReason and IPVConfig
        from opendxa.dana.ipv import IPVConfig, IPVReason

        # Create IPV configuration from options
        ipv_config = IPVConfig(
            debug_mode=options.get("debug_mode", False),
            max_iterations=options.get("max_iterations", 3),
        )

        # Create IPVReason executor
        ipv_reason = IPVReason()

        # Prepare kwargs for IPV execution
        # Pass model and other llm_options through
        llm_options_for_ipv = options.copy()
        if model:
            llm_options_for_ipv["model"] = model  # Model goes into llm_options

        ipv_kwargs = {
            "config": ipv_config,
            "llm_options": llm_options_for_ipv,  # Use the modified llm_options
            "use_mock": use_mock,
            # "model": model, # Removed from here
        }

        # Execute with IPV optimization
        logger.debug(f"Using IPV optimization for prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
        result = ipv_reason.execute(prompt, context, **ipv_kwargs)

        logger.debug("IPV optimization completed successfully")
        return result

    except ImportError:
        # IPV not available, fall back to original
        logger.debug("IPV not available, using original implementation")
        return _reason_original_implementation(prompt, context, options, use_mock, model)
    except Exception as e:
        # IPV failed, fall back to original
        logger.warning(f"IPV optimization failed: {e}")
        raise


def _reason_original_implementation(
    prompt: str,
    context: SandboxContext,
    options: dict[str, Any],
    use_mock: bool | None = None,
    model: str | None = None,
) -> Any:
    """Original reason function implementation (pre-IPV)."""
    logger = DXA_LOGGER.getLogger("opendxa.dana.reason.original")

    # Check if we should use mock responses
    should_mock = use_mock if use_mock is not None else os.environ.get("OPENDXA_MOCK_LLM", "").lower() == "true"

    llm_resource: LLMResource | None = None

    if model:
        logger.debug(f"Attempting to use specified model: {model}")
        if not hasattr(context, "cached_llm_resources"):
            context.cached_llm_resources = {}

        # First check cache
        if model in context.cached_llm_resources:
            llm_resource = context.cached_llm_resources[model]
            logger.debug(f"Found cached LLMResource for model '{model}'")
        else:
            # Check system:llm_resources (plural) provided by sandbox
            system_llms = context.get("system:llm_resources", {})
            if isinstance(system_llms, dict):
                # Try exact match first
                if model in system_llms and isinstance(system_llms[model], LLMResource):
                    llm_resource = system_llms[model]
                    logger.info(f"Using pre-configured LLMResource for model: {model}")
                else:
                    # Try partial match
                    for key, res in system_llms.items():
                        if isinstance(res, LLMResource) and model.lower() in key.lower():
                            llm_resource = res
                            logger.info(f"Using pre-configured LLMResource '{key}' for model: {model}")
                            break

                if llm_resource:
                    context.cached_llm_resources[model] = llm_resource
                    logger.debug(f"Cached LLMResource for future use with model '{model}'")

            if not llm_resource:
                # Not found in system resources, try to create from config
                logger.debug(f"Model '{model}' not found in system:llm_resources, checking config")
                try:
                    config = ConfigLoader().get_default_config()
                    for model_entry in config.get("preferred_models", []):
                        if model.lower() in model_entry.get("name", "").lower():
                            model_id = model_entry["name"]
                            resource_name = f"llm_resource_{model_id.replace(':', '_').replace('/', '_')}"
                            llm_resource = LLMResource(name=resource_name, model=model_id)

                            if not llm_resource._is_available:
                                Misc.safe_asyncio_run(llm_resource.initialize)

                            if llm_resource._is_available:
                                context.cached_llm_resources[model] = llm_resource
                                logger.info(f"Created and cached new LLMResource for model: {model_id}")
                                break
                            else:
                                logger.warning(f"LLMResource for '{model_id}' not available (missing API keys?)")
                                llm_resource = None
                except Exception as e:
                    logger.error(f"Error creating LLMResource for '{model}': {e}")
                    llm_resource = None

    # Fallback to default if needed
    if not llm_resource:
        logger.debug("Using default LLM resource")
        # Try context.get first as it's the recommended way
        llm_resource = context.get("system:llm_resource")
        if not isinstance(llm_resource, LLMResource):
            # Fallback to direct attribute access
            llm_resource = getattr(context, "llm_resource", None)
            if not isinstance(llm_resource, LLMResource):
                # Last resort: create new default
                logger.debug("Creating new default LLMResource")
                llm_resource = LLMResource()

    # Prepare the request
    request = BaseRequest(
        arguments={
            "prompt": prompt,
            "messages": [{"role": "user", "content": prompt}],
            "system_message": options.get("system_message", "You are a helpful assistant."),
            "temperature": options.get("temperature", 0.7),
            "max_tokens": options.get("max_tokens"),
        }
    )

    # Execute the request
    try:
        response = Misc.safe_asyncio_run(llm_resource.query, request)
        return response.content if options.get("format") != "json" else json.loads(response.content)
    except Exception as e:
        raise SandboxError(f"LLM request failed: {e}")
