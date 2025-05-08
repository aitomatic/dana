"""LLM integration for the DANA interpreter.

This module provides the LLMIntegration class, which is responsible for
handling interactions with Large Language Models during execution.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional

from opendxa.common.resource.llm_resource import LLMResource
from opendxa.common.types import BaseRequest
from opendxa.common.utils.misc import Misc
from opendxa.dana.exceptions import RuntimeError, StateError
from opendxa.dana.runtime.executor.base_executor import BaseExecutor
from opendxa.dana.runtime.executor.context_manager import ContextManager


class LLMIntegration(BaseExecutor):
    """Handles LLM integration for the DANA interpreter.

    Responsibilities:
    - Initialize and manage LLM resources
    - Construct prompts and context
    - Execute LLM reasoning operations
    - Process and validate LLM responses
    """

    def __init__(self, context_manager: ContextManager):
        """Initialize the LLM integration.

        Args:
            context_manager: The context manager for variable resolution and resource management
        """
        super().__init__()
        self.context_manager = context_manager

    async def perform_reasoning(
        self, prompt: str, context_vars: Optional[List[str]] = None, options: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute a reasoning operation by calling the LLM.

        Args:
            prompt: The reasoning prompt to send to the LLM
            context_vars: Optional list of variable names to include as context
            options: Optional parameters for the LLM call (temperature, format, etc.)

        Returns:
            The reasoning result from the LLM

        Raises:
            RuntimeError: If the LLM resource is not available or if the query fails
        """
        # Get or initialize the LLM resource
        llm = self._get_llm_resource()

        # Log what's happening
        self.debug(f"Starting LLM reasoning with prompt: {prompt[:50]}{'...' if len(prompt) > 50 else ''}")

        # Prepare the context data
        context_data = self._prepare_context_data(context_vars)

        # Build the combined prompt with context
        enriched_prompt = self._build_enriched_prompt(prompt, context_data)

        # Prepare the system message
        system_message = self._build_system_message(options)

        # Set up the messages
        messages = [{"role": "system", "content": system_message}, {"role": "user", "content": enriched_prompt}]

        # Prepare LLM parameters
        params = self._prepare_llm_params(messages, options)

        # Make the LLM call
        return await self._execute_llm_query(llm, params, options)

    def _get_llm_resource(self) -> Any:
        """Get or initialize the LLM resource.

        Returns:
            The LLM resource to use for reasoning

        Raises:
            RuntimeError: If no LLM resource can be found or initialized
        """
        try:
            # Try to get an existing resource
            try:
                return self.context_manager.get_resource("reason_llm")
            except StateError:
                try:
                    return self.context_manager.get_resource("llm")
                except StateError:
                    # Create a default LLM resource
                    self.warning("No LLM resource found, creating a default one")
                    llm = LLMResource(name="reason_llm")
                    self.context_manager.register_resource("reason_llm", llm)
                    self.info("reason_llm resource registered")
                    return llm
        except Exception as e:
            error_msg = (
                "No LLM resource found and could not create one. "
                "Please configure one before using reason() statements:\n"
                "1. Set environment variables (e.g., OPENAI_API_KEY, ANTHROPIC_API_KEY)\n"
                "2. Or register an LLM resource with the context"
            )
            self.error(error_msg)
            raise RuntimeError(error_msg) from e

    def _prepare_context_data(self, context_vars: Optional[List[str]]) -> Dict[str, Any]:
        """Prepare context data to include with the prompt.

        Args:
            context_vars: List of variable names to include in the context

        Returns:
            A dictionary of context data
        """
        context_data = {}
        if context_vars:
            for var_name in context_vars:
                try:
                    # Get the variable value from context
                    value = self.context_manager.get_variable(var_name)
                    # Add it to the context data
                    context_data[var_name] = value
                except StateError:
                    self.warning(f"Warning: Context variable '{var_name}' not found")
        return context_data

    def _build_enriched_prompt(self, prompt: str, context_data: Dict[str, Any]) -> str:
        """Build an enriched prompt with context data.

        Args:
            prompt: The base prompt
            context_data: Context data to include

        Returns:
            The enriched prompt with context
        """
        if not context_data:
            return prompt

        # Format the context as JSON for inclusion in the prompt
        context_str = json.dumps(context_data, indent=2, default=str)
        return f"{prompt}\n\nContext:\n{context_str}"

    def _build_system_message(self, options: Optional[Dict[str, Any]]) -> str:
        """Build the system message for the LLM.

        Args:
            options: Optional parameters that may affect the system message

        Returns:
            The system message to use
        """
        system_message = "You are a reasoning engine. Analyze the query and provide a thoughtful, accurate response."

        # Add any format-specific instructions
        format_type = options.get("format", "text") if options else "text"
        if format_type == "json":
            system_message += " Return your answer in valid JSON format."

        return system_message

    def _prepare_llm_params(self, messages: List[Dict[str, str]], options: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare parameters for the LLM query.

        Args:
            messages: The messages to send to the LLM
            options: Optional parameters to include

        Returns:
            A dictionary of parameters for the LLM query
        """
        # Set up basic parameters
        params = {
            "messages": messages,
            "temperature": options.get("temperature", 0.7) if options else 0.7,
        }

        # Add max_tokens if specified
        if options and "max_tokens" in options:
            params["max_tokens"] = options["max_tokens"]

        return params

    async def _execute_llm_query(self, llm: Any, params: Dict[str, Any], options: Optional[Dict[str, Any]]) -> Any:
        """Execute the LLM query.

        Args:
            llm: The LLM resource to use
            params: The parameters for the query
            options: Optional parameters that may affect result processing

        Returns:
            The result from the LLM

        Raises:
            RuntimeError: If the query fails
        """
        try:
            # Initialize the LLM if needed
            try:
                await llm.initialize()
            except Exception:
                # Ignore initialization errors (it might already be initialized)
                pass

            # Log the start of the query
            self.info("Starting LLM query - this may take some time...")

            # Make the asynchronous LLM query
            response = await llm.query(BaseRequest(arguments=params))

            if not response.success:
                raise RuntimeError(f"LLM reasoning failed: {response.error}")

            # Extract the content from the response
            content = response.content

            # Process the response based on its structure
            result = self._process_llm_response(content)

            # Handle format conversion if needed
            format_type = options.get("format", "text") if options else "text"
            if format_type == "json" and isinstance(result, str):
                try:
                    # Try to parse the result as JSON
                    result = json.loads(result)
                except json.JSONDecodeError:
                    self.warning(f"Warning: Could not parse LLM response as JSON: {result[:100]}")

            return result

        except Exception as e:
            self.error(f"Error during LLM reasoning: {str(e)}")
            raise RuntimeError(f"Error during reasoning: {str(e)}") from e

    def _process_llm_response(self, content: Any) -> Any:
        """Process the raw LLM response to extract the result.

        Args:
            content: The raw content from the LLM response

        Returns:
            The extracted result
        """
        # If it's a completion-style response with choices
        if isinstance(content, dict) and "choices" in content:
            result = content["choices"][0]
            result = Misc.get_field(result, "message")
            result = Misc.get_field(result, "content")
            return result

        # If it's a direct content response
        elif isinstance(content, dict) and "content" in content:
            return Misc.get_field(content, "content", content)

        # Fallback for other formats
        return str(content)

    def execute_direct_synchronous_reasoning(
        self, prompt: str, context_vars: Optional[List[str]] = None, options: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute a synchronous reasoning operation.

        This method is a wrapper around the asynchronous perform_reasoning method
        that runs it synchronously for environments that don't support async/await.

        Args:
            prompt: The reasoning prompt to send to the LLM
            context_vars: Optional list of variable names to include as context
            options: Optional parameters for the LLM call

        Returns:
            The reasoning result from the LLM

        Raises:
            RuntimeError: If the LLM resource is not available or if the query fails
        """
        try:
            # Import event loop functions for manual async handling
            from asyncio import new_event_loop, set_event_loop

            # Create a new event loop for this operation
            loop = new_event_loop()
            set_event_loop(loop)

            # Set a longer timeout for the event loop (2 minutes)
            loop.slow_callback_duration = 120.0  # seconds

            # Run the query with a large timeout
            result = loop.run_until_complete(asyncio.wait_for(self.perform_reasoning(prompt, context_vars, options), timeout=120))

            # Clean up resources
            loop.close()

            return result

        except Exception as e:
            self.error(f"Error in synchronous LLM query: {e}")
            raise RuntimeError(f"Error during reasoning: {str(e)}") from e
