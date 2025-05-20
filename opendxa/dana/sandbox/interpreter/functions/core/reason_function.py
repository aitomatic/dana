"""
Copyright © 2025 Aitomatic, Inc.

This source code is licensed under the license found in the LICENSE file in the root directory of this source tree

Reason function implementation for the DANA interpreter.

This module provides the reason function, which handles reasoning in the DANA interpreter.
"""

import json
from typing import Any, Dict, Optional

from opendxa.common.types import BaseRequest
from opendxa.common.utils.logging import DXA_LOGGER
from opendxa.dana.common.exceptions import SandboxError
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def reason_function(
    prompt: str,
    context: SandboxContext,
    options: Optional[Dict[str, Any]] = None,
) -> Any:
    """Execute the reason function.

    Args:
        prompt: The reasoning prompt.
        context: The runtime context for variable resolution.
        options: Optional parameters for the function.

    Returns:
        The result of the reasoning operation.

    Raises:
        SandboxError: If the function execution fails.
    """
    logger = DXA_LOGGER.getLogger("opendxa.dana.reason")

    if options is None:
        options = {}

    prompt = options.get("prompt", prompt)
    llm_resource = context.llm_resource

    try:
        # Log what's happening
        logger.debug(f"Starting LLM reasoning with prompt: {prompt[:500]}{'...' if len(prompt) > 500 else ''}")

        # Extract variables from context for prompt enrichment
        context_vars = {}
        try:
            # Get all variables from local scope
            local_scope = context._state.get("local", {})
            for key, value in local_scope.items():
                # Only add simple types to context
                if isinstance(value, (str, int, float, bool, list, dict)):
                    context_vars[key] = value
        except (AttributeError, KeyError):
            pass  # If we can't access local scope, use empty context

        # Build the combined prompt with context
        if context_vars:
            # Only include context if there are variables to include
            context_section = "Available variables:\n"
            for key, value in context_vars.items():
                context_section += f"  {key}: {value}\n"
            enriched_prompt = f"{context_section}\n{prompt}"
        else:
            enriched_prompt = prompt

        # Prepare system message
        system_message = options.get("system_message", "You are a helpful AI assistant. Respond concisely and accurately.")

        # Set up the messages
        messages = [{"role": "system", "content": system_message}, {"role": "user", "content": enriched_prompt}]

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
