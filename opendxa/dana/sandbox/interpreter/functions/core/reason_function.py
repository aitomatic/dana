"""
Copyright © 2025 Aitomatic, Inc.

This source code is licensed under the license found in the LICENSE file in the root directory of this source tree

Reason function implementation for the DANA interpreter.

This module provides the reason function, which handles reasoning in the DANA interpreter.
"""

import json
from typing import Any, Dict, Optional

from opendxa.common.resource.llm_resource import LLMResource
from opendxa.common.types import BaseRequest
from opendxa.common.utils.logging import DXA_LOGGER
from opendxa.dana.common.exceptions import SandboxError
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def reason_function(
    prompt: str,
    context: SandboxContext,
    options: Optional[Dict[str, Any]] = None,
) -> Any:
    """Execute the reason function to generate a response using an LLM.

    Args:
        prompt: The prompt string to send to the LLM (can be a string or a list with LiteralExpression)
        context: The sandbox context
        options: Optional parameters for the LLM call, including:
            - system_message: Custom system message (default: helpful assistant)
            - temperature: Controls randomness (default: 0.7)
            - max_tokens: Limit on response length
            - format: Output format ("text" or "json")

    Returns:
        The LLM's response to the prompt

    Raises:
        SandboxError: If the function execution fails or parameters are invalid
    """
    logger = DXA_LOGGER.getLogger("opendxa.dana.reason")
    options = options or {}

    if not prompt:
        raise SandboxError("reason function requires a non-empty prompt")

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

        request = BaseRequest(arguments=request_params)
        response = llm_resource.query_sync(request)

        if not response.success:
            raise SandboxError(f"LLM reasoning failed: {response.error}")

        # Process the response
        result = response.content
        if isinstance(result, dict) and "content" in result:
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
        logger.error(f"Error during LLM reasoning: {str(e)}")
        raise SandboxError(f"Error during reasoning: {str(e)}") from e
