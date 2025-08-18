"""
LLM function for Dana standard library.

This module provides the llm function for LLM interactions with Promise support.
"""

__all__ = ["py_llm"]

import json
import os
from typing import Any

from dana.common.exceptions import SandboxError
from dana.common.types import BaseRequest
from dana.common.utils.logging import DANA_LOGGER
from dana.core.concurrency.promise_factory import PromiseFactory
from dana.core.lang.sandbox_context import SandboxContext


def py_llm(
    context: SandboxContext,
    prompt: str,
    options: dict[str, Any] | None = None,
    use_mock: bool | None = None,
) -> Any:
    """Execute the llm function to make an async LLM call and return a Promise.

    This function is designed to demonstrate concurrency in Dana by making
    async LLM calls and returning a Promise that can be resolved later.

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
        A Promise that will resolve to the LLM's response to the prompt

    Raises:
        SandboxError: If the function execution fails or parameters are invalid
    """
    logger = DANA_LOGGER.getLogger("dana.llm")
    logger.debug(f"LLM function called with prompt: '{prompt[:50]}...'")
    options = options or {}

    if not prompt:
        raise SandboxError("llm function requires a non-empty prompt")

    # Convert prompt to string if it's not already
    if not isinstance(prompt, str):
        prompt = str(prompt)

    # Check if we should use mock responses
    # Priority: function parameter > environment variable
    should_mock = use_mock if use_mock is not None else os.environ.get("DANA_MOCK_LLM", "").lower() == "true"

    # Get LLM resource from context using system resource access
    llm_resource = context.get_system_llm_resource(use_mock=should_mock)

    if llm_resource is None:
        raise SandboxError("No LLM resource available in context")

    logger.info(f"LLMResource: {llm_resource.name} (model: {llm_resource.model})")

    # Get resources from context once and reuse throughout the function
    resources = {}
    try:
        resources = context.get_resources(options.get("resources", None)) if context is not None else {}
    except Exception as e:
        logger.debug(f"Could not get available resources: {e}")

    # Create an async function that will be wrapped in a Promise
    async def _async_llm_call():
        """Async function that performs the actual LLM call."""
        try:
            # Log what's happening
            logger.debug(f"Starting LLM call with prompt: {prompt[:500]}{'...' if len(prompt) > 500 else ''}")

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

            # Make the async call directly
            response = await llm_resource.query(request)

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

            logger.debug(f"LLM function returning result: {type(result)}")
            return result

        except Exception as e:
            logger.error(f"Error during LLM call: {str(e)}")
            raise SandboxError(f"Error during LLM call: {str(e)}") from e

    # Create and return an EagerPromise that wraps the async function
    # EagerPromise starts execution immediately in background
    logger.debug("Creating EagerPromise for LLM call")
    logger.debug(f"_async_llm_call type: {type(_async_llm_call)}")
    logger.debug(f"context type: {type(context)}")
    logger.debug(f"context class: {context.__class__.__name__}")

    # PromiseFactory.create_promise() handles DanaThreadPool internally
    return PromiseFactory.create_promise(_async_llm_call)
