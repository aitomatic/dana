"""
Reason function for Dana standard library.

This module provides the primary reason function for LLM reasoning with POET (Prompt
Optimization and Enhancement Technology) enhancements. It includes both the legacy
implementation for backward compatibility and the new enhanced implementation.

The module provides two main implementations:
1. old_reason_function: Legacy synchronous LLM reasoning without enhancements
2. py_reason: New POET-enhanced reasoning with automatic prompt optimization

Key Features:
- Context-aware prompt enhancement based on expected return types
- Semantic coercion for type-compatible results
- Robust fallback mechanisms for reliability
- Comprehensive logging and error handling
- Support for multiple LLM providers and response formats

Usage:
    from dana.libs.corelib.py_wrappers.py_reason import py_reason

    # Basic usage
    result = py_reason(context, "What is 2+2?")

    # With options
    result = py_reason(context, "List prime numbers", {
        "temperature": 0.1,
        "format": "json",
        "system_message": "You are a math expert."
    })

Author: Dana AI Team
Version: 2.0.0
License: MIT
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


def _execute_reason_call(
    context: SandboxContext,
    prompt: str,
    options: dict[str, Any] | None = None,
    use_mock: bool | None = None,
) -> Any:
    """Execute the original reason function to make a synchronous LLM call.

    Legacy implementation providing basic LLM reasoning without POET enhancements.
    Kept for backward compatibility and as a fallback mechanism.

    Args:
        context: The sandbox context containing variables, scope, and system resources
        prompt: The prompt string to send to the LLM
        options: Optional parameters for the LLM call (temperature, max_tokens, format, etc.)
        use_mock: Force use of mock responses (True) or real LLM calls (False)

    Returns:
        The LLM's response to the prompt, processed according to the specified format

    Raises:
        SandboxError: If the function execution fails or parameters are invalid
    """
    logger = DANA_LOGGER.getLogger("dana.reason.legacy")
    options = options or {}

    # Input validation
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
        # Create fallback LLM resource with auto model selection instead of hardcoded OpenAI
        from dana.builtin_types.resource.builtins.llm_resource_type import LLMResourceType

        llm_resource = LLMResourceType.create_instance_from_values({"model": "auto"})
        context.set_system_llm_resource(llm_resource)

    logger.info(f"LLMResource: {llm_resource.name} (model: {llm_resource.model})")

    # Get resources from context once and reuse throughout the function
    resources = {}
    try:
        resources = context.get_resources(options.get("resources", None)) if context is not None else {}
    except Exception:
        pass

    try:
        # Log the actual prompt being sent to LLM
        logger.debug(f"LLM PROMPT: {prompt}")

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

        # Extract just the text content from the response
        if isinstance(result, dict):
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

        # Log the actual response from LLM
        logger.debug(f"LLM RESPONSE: {result}")
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

    New primary implementation providing context-aware prompt enhancement and
    semantic coercion based on execution context including docstrings, type hints,
    metadata comments, and other contextual information.

    **Context Detection:**
    Automatically detects various types of context from:
    - Function docstrings (Google/NumPy/Sphinx style)
    - Variable type annotations (e.g., `user_count: int = reason(...)`)
    - Inline comments (e.g., `# returns int`)
    - Metadata comments (e.g., `## type: dict`, `## domain: finance`)
    - Execution environment and scope information
    - Resource availability and constraints

    **Supported Context Patterns:**
    - Type information: `Returns: str`, `-> str`, `return str`, `returns string`
    - Domain context: `## domain: finance`, `## context: medical`
    - Format requirements: `## format: json`, `## output: table`
    - Constraints: `## max_length: 100`, `## precision: 2`
    - Type mapping: "string"→str, "integer"→int, "dictionary"→dict, etc.

    Args:
        context: The sandbox context containing variables, scope, and execution metadata
        prompt: The prompt string to send to the LLM (will be enhanced if possible)
        options: Optional parameters for the LLM call (temperature, max_tokens, format, etc.)
        use_mock: Force use of mock responses for testing and debugging

    Returns:
        The LLM's response, potentially enhanced and coerced to match expected return type

    Raises:
        SandboxError: If the function execution fails or parameters are invalid
        RuntimeError: If the underlying reason function is unavailable

    Example:
        >>> # Function with docstring context
        >>> def get_user_age():
        ...     \"\"\"Get user age. Returns: int\"\"\"
        ...     return py_reason(context, "What is the user's age?")  # Enhanced for int output
        >>>
        >>> # Type-annotated assignment
        >>> user_names: list = py_reason(context, "List user names")  # Enhanced for list output
    """
    logger = DANA_LOGGER.getLogger("dana.reason.poet")

    try:
        # Detect execution context
        from dana.core.lang.interpreter.context_detection import ContextDetector
        from dana.core.lang.interpreter.enhanced_coercion import SemanticCoercer
        from dana.core.lang.interpreter.prompt_enhancement import enhance_prompt_for_type

        context_detector = ContextDetector()
        logger.debug("Starting context detection...")
        execution_context = context_detector.detect_current_context(context)
        logger.debug(f"Context detection result: {execution_context}")

        # Log detected context information
        if execution_context:
            logger.debug(f"CONTEXT DETECTED: {execution_context}")
            # Enhance prompt based on detected context
            enhanced_prompt = enhance_prompt_for_type(prompt, execution_context)
            logger.debug(f"PROMPT ENHANCED: {enhanced_prompt}")
        else:
            logger.debug("NO CONTEXT DETECTED")
            enhanced_prompt = prompt

        # Log the actual prompt sent to LLM
        logger.debug(f"LLM PROMPT: {enhanced_prompt}")

        # Execute with enhanced prompt using original function
        result = _execute_reason_call(context, enhanced_prompt, options, use_mock)

        # Apply semantic coercion if type information is available
        if execution_context and execution_context.expected_type and result is not None:
            try:
                semantic_coercer = SemanticCoercer()
                coerced_result = semantic_coercer.coerce_value(
                    result, execution_context.expected_type, context=f"reason_function_{execution_context.expected_type}"
                )

                if coerced_result != result:
                    result = coerced_result

            except Exception:
                # Fall back to original result if coercion fails
                pass

        return result

    except Exception:
        # Fallback to original function on any error
        logger.debug(f"LLM PROMPT: {prompt}")
        return _execute_reason_call(context, prompt, options, use_mock)
