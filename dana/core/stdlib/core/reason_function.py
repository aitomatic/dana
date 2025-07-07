"""
Copyright © 2025 Aitomatic, Inc.

This source code is licensed under the license found in the LICENSE file in the root directory of this source tree

Reason function implementation for the Dana interpreter.

This module provides the reason function, which handles reasoning in the Dana interpreter.
"""

import json
import os
from typing import Any

from dana.common.exceptions import SandboxError
from dana.common.mixins.queryable import QueryStrategy
from dana.common.resource.llm.llm_resource import LLMResource
from dana.common.types import BaseRequest
from dana.common.utils.logging import DANA_LOGGER

# Import POET decorator
from dana.core.lang.sandbox_context import SandboxContext


def old_reason_function(
    context: SandboxContext,
    prompt: str,
    options: dict[str, Any] | None = None,
    use_mock: bool | None = None,
) -> Any:
    """Execute the original reason function to generate a response using an LLM.

    This is the legacy implementation preserved for inspection and fallback.

    Args:
        context: The sandbox context
        prompt: The prompt string to send to the LLM (can be a string or a list with LiteralExpression)
        options: Optional parameters for the LLM call, including:
            - system_message: Custom system message (default: helpful assistant)
            - temperature: Controls randomness (default: 0.7)
            - max_tokens: Limit on response length
            - format: Output format ("text" or "json")
        use_mock: Force use of mock responses (True) or real LLM calls (False).
                  If None, defaults to checking DANA_MOCK_LLM environment variable.

        Note: A2A agents can be provided via options['agents']. This can be an A2AAgent,
              AgentPool, or list of A2AAgent instances. If provided, agent selection
              will be performed based on the task and available resources.

    Returns:
        The LLM's response to the prompt

    Raises:
        SandboxError: If the function execution fails or parameters are invalid
    """
    logger = DANA_LOGGER.getLogger("dana.reason")
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

    # Get LLM resource from context (assume it's available)
    if hasattr(context, "llm_resource") and context.llm_resource:
        llm_resource = context.llm_resource
    else:
        # Try to get from system:llm_resource
        try:
            llm_resource = context.get("system:llm_resource")
            if not llm_resource:
                llm_resource = LLMResource()
        except Exception:
            llm_resource = LLMResource()

    # Apply mocking if needed
    if should_mock:
        logger.info(f"Using mock LLM response (prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''})")
        llm_resource = llm_resource.with_mock_llm_call(True)

    # Get resources from context once and reuse throughout the function
    resources = {}
    try:
        resources = context.get_resources(options.get("resources", None)) if context is not None else {}
    except Exception as e:
        logger.debug(f"Could not get available resources: {e}")

    # Handle agent integration if agents are provided via options
    actual_agents = options.get("agents")
    if actual_agents is not None:
        try:
            # Check if agents is an A2AAgent, AgentPool, or list of agents
            from dana.agent.abstract_dana_agent import AbstractDanaAgent
            from dana.integrations.agent_to_agent.pool import AgentPool

            agent_pool = None

            if isinstance(actual_agents, AgentPool):
                # Agent pool: use it directly
                agent_pool = actual_agents
                logger.info(f"Using DANA agent pool for reasoning with {len(actual_agents.get_agent_cards())} agents")

            elif isinstance(actual_agents, AbstractDanaAgent):
                # Single agent: create a temporary pool with just this agent
                agent_pool = AgentPool(
                    name="temp_pool_single_agent",
                    description="Temporary pool for single agent reasoning",
                    agents=[actual_agents],
                    context=context,
                )
                logger.info(f"Using single DANA agent for reasoning: {actual_agents}")

            elif isinstance(actual_agents, list):
                # List of agents: create a temporary pool
                if all(isinstance(agent, AbstractDanaAgent) for agent in actual_agents):
                    agent_pool = AgentPool(
                        name="temp_pool_multiple_agents",
                        description="Temporary pool for multiple agent reasoning",
                        agents=actual_agents,
                        context=context,
                    )
                    logger.info(f"Using DANA agent list for reasoning with {len(actual_agents)} agents")
                else:
                    logger.warning("Invalid agents list: all items must be AbstractDanaAgent instances")

            else:
                logger.warning(
                    f"Invalid agents parameter type: {type(actual_agents)}, expected AbstractDanaAgent, AgentPool, or list of AbstractDanaAgent"
                )

            # If we have a valid agent pool, select and use an agent
            if agent_pool:
                # Select best agent considering available resources (already retrieved above)
                selected_agent = agent_pool.select_agent(prompt, included_resources=list(resources.keys()))  # type: ignore

                if selected_agent:
                    logger.info(f"Selected agent '{selected_agent.name}' for reasoning task")
                    try:
                        import inspect

                        from dana.common.utils.misc import Misc

                        # Check if solve method is async
                        if inspect.iscoroutinefunction(selected_agent.solve):
                            # Use safe_asyncio_run for better async handling
                            response = Misc.safe_asyncio_run(selected_agent.solve, prompt)
                        else:
                            response = selected_agent.solve(prompt)
                        logger.debug(
                            f"Agent '{selected_agent.name}' provided response: {str(response)[:100]}{'...' if len(str(response)) > 100 else ''}"
                        )
                        return response
                    except Exception as e:
                        logger.warning(f"Agent '{selected_agent.name}' solve() failed: {e}, falling back to local LLM")
                else:
                    logger.debug("Local agent is selected or no suitable agent found in agent pool => using local LLM")

        except ImportError:
            logger.warning("DANA agent dependencies not available, falling back to local LLM reasoning")
        except Exception as e:
            logger.warning(f"Error using DANA agents for reasoning: {e}, falling back to local LLM")

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

        # Set query strategy and max iterations to iterative and 5 respectively to utilize tool calls
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
        if not isinstance(result, str | int | float | bool | list | dict) and hasattr(result, "__str__"):
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


# ============================================================================
# POET-Enhanced Reason Function (New Primary Implementation)
# ============================================================================


def reason_function(
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
