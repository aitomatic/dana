"""Reason function implementation for the DANA interpreter.

This module provides the ReasonFunction class, which implements the reason() function
that allows DANA programs to perform reasoning using LLMs.
"""

from typing import Any, Dict, Optional

from opendxa.dana.exceptions import RuntimeError
from opendxa.dana.runtime.context import RuntimeContext
from opendxa.dana.runtime.executor.llm_integration import LLMIntegration


class ReasonFunction:
    """Handles the reason() function in DANA.

    This class provides the implementation for the reason() function, which
    allows DANA programs to perform reasoning using LLMs.
    """

    @staticmethod
    def execute(
        prompt: str,
        context: RuntimeContext,
        llm_integration: LLMIntegration,
        options: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Execute a synchronous reasoning operation.

        Args:
            prompt: The evaluated prompt string
            context: The runtime context for variable resolution
            llm_integration: The LLM integration instance to use
            options: Optional parameters for the LLM query

        Returns:
            The reasoning result from the LLM

        Raises:
            RuntimeError: If the LLM resource is not available or if the query fails
        """
        try:
            # Get the LLM resource
            llm_resource = llm_integration._get_llm_resource()
            if not llm_resource:
                raise RuntimeError("No LLM resource available for reasoning")

            # Log what's happening
            llm_integration.debug(f"Starting LLM reasoning with prompt: {prompt[:500]}{'...' if len(prompt) > 500 else ''}")

            # Prepare the context data
            context_data = llm_integration._prepare_context_data(context)

            # Build the combined prompt with context
            enriched_prompt = llm_integration._build_enriched_prompt(prompt, context_data)

            # Prepare the system message
            system_message = llm_integration._build_system_message(options)

            # Set up the messages
            messages = [{"role": "system", "content": system_message}, {"role": "user", "content": enriched_prompt}]

            # Prepare LLM parameters and execute the query
            request = llm_integration._prepare_llm_params(messages, options)
            response = llm_resource.query_sync(request)
            if not response.success:
                raise RuntimeError(f"LLM reasoning failed: {response.error}")

            # Process the response
            result = llm_integration._process_llm_response(response.content)

            # Handle format conversion if needed
            format_type = options.get("format", "text") if options else "text"
            if format_type == "json" and isinstance(result, str):
                try:
                    # Try to parse the result as JSON
                    import json

                    result = json.loads(result)
                except json.JSONDecodeError:
                    llm_integration.warning(f"Warning: Could not parse LLM response as JSON: {result[:100]}")

            return result

        except Exception as e:
            llm_integration.error(f"Error during LLM reasoning: {str(e)}")
            raise RuntimeError(f"Error during reasoning: {str(e)}") from e
