"""
Reason function for Dana standard library.

This module provides the reason function for LLM reasoning with POET enhancements.
"""

__all__ = ["py_reason"]

import json
import os
from typing import Any

from dana.common.exceptions import SandboxError
from dana.common.types import BaseRequest
from dana.common.utils.logging import DANA_LOGGER
from dana.core.lang.sandbox_context import SandboxContext

# ============================================================================
# Original Reason Function (Legacy Implementation)
# ============================================================================


def old_reason_function(
    context: SandboxContext,
    prompt: str,
    options: dict[str, Any] | None = None,
    use_mock: bool | None = None,
) -> Any:
    """Execute the original reason function to make a synchronous LLM call.

    This is the legacy implementation that provides basic LLM reasoning without
    POET enhancements. It's kept for backward compatibility and as a fallback.

    Args:
        context: The sandbox context
        prompt: The prompt string to send to the LLM
        options: Optional parameters for the LLM call, including:
            - system_message: Custom system message (default: helpful assistant)
            - temperature: Controls randomness (default: 0.7)
            - max_tokens: Limit on response length
            - format: Output format ("text" or "json")
        use_mock: Force use of mock responses (True) or real LLM calls (False).
                  If None, defaults to checking DANA_MOCK_LLM environment variable.

    Returns:
        The LLM's response to the prompt

    Raises:
        SandboxError: If the function execution fails or parameters are invalid
    """
    logger = DANA_LOGGER.getLogger("dana.reason.legacy")
    logger.debug(f"Legacy reason function called with prompt: '{prompt[:50]}...'")
    options = options or {}

    if not prompt:
        raise SandboxError("reason function requires a non-empty prompt")

    # Convert prompt to string if it's not already
    if not isinstance(prompt, str):
        prompt = str(prompt)

    # Check if we should use mock responses
    # Priority: function parameter > environment variable
    should_mock = use_mock if use_mock is not None else os.environ.get("DANA_MOCK_LLM", "").lower() == "true"

    # Get LLM resource from context using system resource access
    llm_resource = context.get_system_llm_resource(use_mock=should_mock)

    if llm_resource is None:
        # raise SandboxError("No LLM resource available in context")
        from dana.core.builtin_types.resource.builtins.llm_resource_type import LLMResourceType

        # llm_resource = LLMResourceType.create_instance_from_values({"model": "openai:gpt-4o"})
        llm_resource = LLMResourceType.create_default_instance()
        context.set_system_llm_resource(llm_resource)

    logger.info(f"LLMResource: {llm_resource.name} (model: {llm_resource.model})")

    # Get resources from context once and reuse throughout the function
    resources = {}
    try:
        resources = context.get_resources(options.get("resources", None)) if context is not None else {}
    except Exception as e:
        logger.debug(f"Could not get available resources: {e}")

    try:
        # Log what's happening
        logger.debug(f"Starting synchronous LLM call with prompt: {prompt[:500]}{'...' if len(prompt) > 500 else ''}")

        # Prepare system message
        system_message = options.get("system_message", "You are a helpful AI assistant. Respond concisely and accurately.")

        # Set up the messages
        messages = [{"role": "system", "content": system_message}, {"role": "user", "content": prompt}]

        # Prepare LLM parameters and execute the query
        request_params = {
            "messages": messages,
            "temperature": options.get("temperature", 0.7),
            "max_tokens": options.get("max_tokens", None),
        }

        # Add resources if available
        if resources:
            request_params["available_resources"] = resources

        request = BaseRequest(arguments=request_params)

        # Make the synchronous call
        response = llm_resource.query_sync(request)

        if not response.success:
            raise SandboxError(f"LLM call failed: {response.error}")

        # Process the response
        result = response.content
        logger.debug(f"Raw LLM response type: {type(result)}")

        # Extract just the text content from the response
        if isinstance(result, dict):
            logger.debug(f"Raw response keys: {result.keys()}")
            # Handle different LLM response structures
            if "choices" in result and result["choices"] and isinstance(result["choices"], list):
                # OpenAI/Anthropic style response
                first_choice = result["choices"][0]
                if hasattr(first_choice, "message") and hasattr(first_choice.message, "content"):
                    # Handle object-style responses
                    result = first_choice.message.content
                elif isinstance(first_choice, dict) and "message" in first_choice:
                    # Handle dict-style responses
                    message = first_choice["message"]
                    if hasattr(message, "content"):
                        result = message.content
                    elif isinstance(message, dict) and "content" in message:
                        result = message["content"]
            elif "response" in result:
                # Some providers use "response" field
                result = result["response"]
            elif "content" in result:
                # Some providers use "content" field directly
                result = result["content"]

        # Handle format conversion if needed
        format_type = options.get("format", "text")
        if format_type == "json" and isinstance(result, str):
            try:
                # Try to parse the result as JSON
                result = json.loads(result)
            except json.JSONDecodeError:
                logger.warning(f"Warning: Could not parse LLM response as JSON: {result[:100]}")

        return result

    except Exception as e:
        logger.error(f"Error during synchronous LLM call: {str(e)}")
        raise SandboxError(f"Error during synchronous LLM call: {str(e)}") from e


# ============================================================================
# POET-Enhanced Reason Function (New Primary Implementation)
# ============================================================================


def py_reason(
    context: SandboxContext,
    prompt: str,
    options: dict[str, Any] | None = None,
    use_mock: bool | None = None,
) -> Any:
    """Execute the POET-enhanced reason function with automatic prompt optimization.

    This is the new primary implementation that provides context-aware prompt
    enhancement and semantic coercion based on expected return types.

    Args:
        context: The sandbox context
        prompt: The prompt string to send to the LLM
        options: Optional parameters for the LLM call
        use_mock: Force use of mock responses

    Returns:
        The LLM's response optimized for the expected return type

    Raises:
        SandboxError: If the function execution fails or parameters are invalid
    """
    from dana.core.lang.interpreter.context_detection import ContextDetector
    from dana.core.lang.interpreter.enhanced_coercion import SemanticCoercer
    from dana.core.lang.interpreter.prompt_enhancement import enhance_prompt_for_type

    logger = DANA_LOGGER.getLogger("dana.reason.poet")
    logger.debug(f"POET-enhanced reason called with prompt: '{prompt[:50]}...'")

    try:
        # Phase 1: Detect expected return type context
        context_detector = ContextDetector()
        type_context = context_detector.detect_current_context(context)

        if type_context:
            logger.debug(f"Detected type context: {type_context}")

            # Phase 2: Enhance prompt based on expected type
            enhanced_prompt = enhance_prompt_for_type(prompt, type_context)

            if enhanced_prompt != prompt:
                logger.debug(f"Enhanced prompt from {len(prompt)} to {len(enhanced_prompt)} chars")
                logger.debug(f"Enhancement for type: {type_context.expected_type}")
            else:
                logger.debug("No prompt enhancement applied")
        else:
            logger.debug("No type context detected, using original prompt")
            enhanced_prompt = prompt

        # Phase 3: Execute with enhanced prompt using original function
        result = old_reason_function(context, enhanced_prompt, options, use_mock)

        # Phase 4: Apply semantic coercion if type context is available
        if type_context and type_context.expected_type and result is not None:
            try:
                semantic_coercer = SemanticCoercer()
                coerced_result = semantic_coercer.coerce_value(
                    result, type_context.expected_type, context=f"reason_function_{type_context.expected_type}"
                )

                if coerced_result != result:
                    logger.debug(f"Applied semantic coercion: {type(result)} → {type(coerced_result)}")

                return coerced_result

            except Exception as coercion_error:
                logger.debug(f"Semantic coercion failed: {coercion_error}, returning original result")
                # Fall back to original result if coercion fails
                return result

        return result

    except Exception as e:
        logger.debug(f"POET enhancement failed: {e}, falling back to original function")
        # Fallback to original function on any error
        return old_reason_function(context, prompt, options, use_mock)
