"""
Copyright © 2025 Aitomatic, Inc.

This source code is licensed under the license found in the LICENSE file in the root directory of this source tree

Reason function implementation for the Dana interpreter.

This module provides the reason function, which handles reasoning in the Dana interpreter.
"""

import json
import os
from typing import Any

from opendxa.common.mixins.queryable import QueryStrategy
from opendxa.common.resource.llm_resource import LLMResource
from opendxa.common.types import BaseRequest
from opendxa.common.utils.logging import DXA_LOGGER
from opendxa.dana.common.exceptions import SandboxError

# Import POET decorator
from opendxa.dana.poet import poet
from opendxa.dana.sandbox.sandbox_context import SandboxContext


@poet(domain="llm_optimization", timeout=30, retries=3)
def reason_function(
    context: SandboxContext,
    prompt: str,
    options: dict[str, Any] | None = None,
    use_mock: bool | None = None,
) -> Any:
    """Execute the reason function to generate a response using an LLM.

    Args:
        context: The sandbox context
        prompt: The prompt string to send to the LLM (can be a string or a list with LiteralExpression)
        options: Optional parameters for the LLM call, including:
            - system_message: Custom system message (default: helpful assistant)
            - temperature: Controls randomness (default: 0.7)
            - max_tokens: Limit on response length
            - format: Output format ("text" or "json")
        use_mock: Force use of mock responses (True) or real LLM calls (False).
                  If None, defaults to checking OPENDXA_MOCK_LLM environment variable.

    Returns:
        The LLM's response to the prompt

    Raises:
        SandboxError: If the function execution fails or parameters are invalid
    """
    logger = DXA_LOGGER.getLogger("opendxa.dana.reason")
    options = options or {}

    if not prompt:
        raise SandboxError("reason function requires a non-empty prompt")

    # Convert prompt to string if it's not already
    if not isinstance(prompt, str):
        prompt = str(prompt)

    # Check if we should use mock responses
    # Priority: function parameter > environment variable
    should_mock = use_mock if use_mock is not None else os.environ.get("OPENDXA_MOCK_LLM", "").lower() == "true"

    # Get LLM resource from context (assume it's available)
    if hasattr(context, "llm_resource") and context.llm_resource:
        llm_resource = context.llm_resource
    else:
        # Try to get from system.llm_resource
        try:
            llm_resource = context.get("system.llm_resource")
            if not llm_resource:
                llm_resource = LLMResource()
        except Exception:
            llm_resource = LLMResource()

    # Apply mocking if needed
    if should_mock:
        logger.info(f"Using mock LLM response (prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''})")
        llm_resource = llm_resource.with_mock_llm_call(True)

    try:
        # Log what's happening
        logger.debug(f"Starting LLM reasoning with prompt: {prompt[:500]}{'...' if len(prompt) > 500 else ''}")

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
        # Get resources from context and filter by included_resources
        try:
            resources = context.get_resources(options.get("resources", None)) if context is not None else {}
        except Exception as e:
            self.warning(f"Error getting resources from context: {e}")
            resources = {}

        # Set query strategy and max iterations to iterative and 5 respectively to ultilize tools calls
        previous_query_strategy = llm_resource._query_strategy
        previous_query_max_iterations = llm_resource._query_max_iterations
        if resources:
            request_params["available_resources"] = resources
            llm_resource._query_strategy = QueryStrategy.ITERATIVE
            llm_resource._query_max_iterations = options.get("max_iterations", 5)

        request = BaseRequest(arguments=request_params)

        response = llm_resource.query_sync(request)

        # Reset query strategy and max iterations
        llm_resource._query_strategy = previous_query_strategy
        llm_resource._query_max_iterations = previous_query_max_iterations

        if not response.success:
            raise SandboxError(f"LLM reasoning failed: {response.error}")

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
                    logger.debug(f"Extracted content from object attributes: {result[:100]}...")
                elif isinstance(first_choice, dict):
                    if "message" in first_choice:
                        message = first_choice["message"]
                        if isinstance(message, dict) and "content" in message:
                            result = message["content"]
                            logger.debug(f"Extracted content from choices[0].message.content: {result[:100]}...")
                        elif hasattr(message, "content"):
                            result = message.content
                            logger.debug(f"Extracted content from message.content attribute: {result[:100]}...")
                    elif "text" in first_choice:
                        # Some LLMs use 'text' instead of 'message.content'
                        result = first_choice["text"]
                        logger.debug(f"Extracted content from choices[0].text: {result[:100]}...")
            # Simpler response format with direct content
            elif "content" in result:
                result = result["content"]
                logger.debug(f"Extracted content directly from content field: {result[:100]}...")

        # If result is still a complex object, try to get its string representation
        if not isinstance(result, (str, int, float, bool, list, dict)) and hasattr(result, "__str__"):
            result = str(result)
            logger.debug(f"Converted complex object to string: {result[:100]}...")

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
        logger.error(f"Error during LLM reasoning: {str(e)}")
        raise SandboxError(f"Error during reasoning: {str(e)}") from e
