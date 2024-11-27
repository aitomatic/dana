"""Factory functions for creating DXA agents.

This module provides factory functions for creating and managing different types of DXA agents.
It handles resource initialization, cleanup, and proper error handling for all agent types.

The main function `create_agent` is provided as a context manager to ensure proper cleanup:

Example:
    >>> config = {
    ...     "api_key": "your-api-key",
    ...     "resources": ["math_expert"],
    ...     "model": "gpt-4"
    ... }
    >>> async with create_agent("interactive", config) as agent:
    ...     result = await agent.run(task)

Supported agent types:
    - interactive: Console-based interactive agents
    - websocket: Network-based WebSocket agents
    - automation: Workflow automation agents

Configuration:
    The config dictionary can include:
    - api_key: OpenAI API key (required)
    - model: Model name (default: "gpt-4")
    - resources: List of required resources
    - reasoning: Reasoning engine configuration
    - websocket_url: Required for WebSocket agents
    - workflow: Required for Automation agents

Error Handling:
    - ConfigurationError: Invalid configuration
    - ResourceError: Resource initialization failure
    - ReasoningError: Reasoning system failure
    - AgentError: Agent initialization/execution failure
    - ValueError: Invalid parameters
"""

from contextlib import asynccontextmanager
from typing import Dict, Any, AsyncIterator
import logging
from dxa.agents.interactive import InteractiveAgent
from dxa.agents.websocket import WebSocketAgent
from dxa.agents.automation import AutomationAgent
from dxa.core.reasoning.cot import ChainOfThoughtReasoning
from dxa.experts.math import create_math_expert
from dxa.agents.base_agent import BaseAgent
from dxa.agents.config import AgentConfig, LLMConfig
from dxa.common.errors import (
    ConfigurationError,
    ResourceError,
    AgentError,
    ReasoningError
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def create_agent(agent_type: str, config: Dict[str, Any]) -> AsyncIterator[BaseAgent]:
    """Create and manage an agent's lifecycle.
    
    Args:
        agent_type: Type of agent to create ("interactive", "websocket", "automation")
        config: Configuration dictionary containing agent settings
        
    Yields:
        Initialized agent instance
        
    Raises:
        ConfigurationError: If agent configuration is invalid
        ResourceError: If resource initialization fails
        ReasoningError: If reasoning system fails
        AgentError: If agent initialization fails
        ValueError: If required parameters are missing or invalid
        
    Example:
        async with create_agent("interactive", config) as agent:
            result = await agent.run(task)
    """
    # Initialize components
    try:
        reasoning = ChainOfThoughtReasoning()
        await reasoning.initialize()
    except (ValueError, ResourceError) as e:
        raise ReasoningError("Failed to initialize reasoning system") from e
    
    # Create agent-specific resources
    resources = {}
    if "math_expert" in config.get("resources", []):
        try:
            resources["math_expert"] = create_math_expert(config["api_key"])
            await resources["math_expert"].initialize()
        except (ValueError, ResourceError) as e:
            raise ResourceError("Failed to initialize math expert") from e

    try:
        # Create agent config
        llm_config = LLMConfig(
            model_name=config.get("model", "gpt-4"),
            temperature=config.get("temperature", 0.7),
            additional_params={"api_key": config["api_key"]}
        )
        
        agent_config = AgentConfig(
            name=config.get("name", f"{agent_type}_agent"),
            llm_config=llm_config,
            reasoning_config=config.get("reasoning", {}),
            resources_config=resources
        )

        # Create agent based on type
        if agent_type == "interactive":
            agent = InteractiveAgent(
                config=agent_config,
                reasoning=reasoning
            )
        elif agent_type == "websocket":
            if "websocket_url" not in config:
                raise ConfigurationError("websocket_url is required for WebSocket agent")
            agent = WebSocketAgent(
                name=agent_config.name,
                config=agent_config,
                reasoning=reasoning,
                websocket_url=config["websocket_url"]
            )
        elif agent_type == "automation":
            if "workflow" not in config:
                raise ConfigurationError("workflow is required for Automation agent")
            agent = AutomationAgent(
                name=agent_config.name,
                llm_config=llm_config.__dict__,
                workflow=config["workflow"]
            )
        else:
            raise ConfigurationError(f"Unknown agent type: {agent_type}")

        # Initialize agent
        try:
            await agent.initialize()
        except (ValueError, ResourceError) as e:
            raise AgentError(f"Failed to initialize {agent_type} agent") from e
        
        yield agent
        
    except (ValueError, KeyError) as e:
        raise ConfigurationError(f"Invalid configuration: {str(e)}") from e
        
    finally:
        # Cleanup everything
        for resource in resources.values():
            try:
                await resource.cleanup()
            except (ValueError, ResourceError) as e:
                logger.warning("Failed to cleanup resource: %s", str(e))
        try:
            await reasoning.cleanup()
        except (ValueError, ResourceError) as e:
            logger.warning("Failed to cleanup reasoning: %s", str(e))
        if "agent" in locals():
            try:
                await agent.cleanup()
            except (ValueError, ResourceError) as e:
                logger.warning("Failed to cleanup agent: %s", str(e)) 