"""Factory functions for creating DXA agents.

This module provides factory functions for creating and managing DXA agents with proper
lifecycle management and error handling.

Examples:
    Basic usage with default settings:
        ```python
        async with create_agent({"name": "basic_agent"}) as agent:
            result = await agent.run("Analyze this data")
        ```

    Research agent with Chain of Thought reasoning:
        ```python
        from dxa.core.resource import LLMResource
        from dxa.core.io import ConsoleIO

        config = {
            "name": "researcher",
            "reasoning": "cot",
            "capabilities": ["research", "analysis"],
            "resources": {
                "llm": LLMResource(model="gpt-4"),
                "search": SearchResource(),
                "database": DatabaseResource()
            }
        }

        async with create_agent(config) as agent:
            result = await agent.run("Research quantum computing trends")
        ```

    Interactive agent with WebSocket I/O:
        ```python
        from dxa.core.io import WebSocketIO

        config = {
            "name": "interactive",
            "reasoning": "ooda",
            "io": WebSocketIO("wss://your-server/agent"),
            "capabilities": ["interaction", "streaming"],
            "resources": {
                "llm": LLMResource(model="gpt-4")
            }
        }

        async with create_agent(config) as agent:
            result = await agent.run("Help user with task")
        ```

Configuration Options:
    - name (str): Agent identifier
    - reasoning (str|BaseReasoning): "cot", "ooda", or custom reasoning
    - capabilities (List[str]): Agent capabilities
    - resources (Dict[str, BaseResource]): Available resources
    - io (BaseIO): I/O handler for interaction

The factory handles:
    - Agent lifecycle management
    - Resource initialization
    - Error handling
    - Proper cleanup
"""

from contextlib import asynccontextmanager
from typing import Dict, Any, AsyncIterator
import logging

from dxa.agent.agent import Agent
from dxa.core.reasoning import ChainOfThoughtReasoning, OODAReasoning
from dxa.core.io import ConsoleIO, WebSocketIO, BaseIO
from dxa.common.errors import ConfigurationError
from dxa.core.reasoning import BaseReasoning

logger = logging.getLogger(__name__)

def get_reasoning(reasoning_type: str) -> BaseReasoning:
    """Get reasoning implementation by type."""
    reasonings = {
        "cot": ChainOfThoughtReasoning(),
        "ooda": OODAReasoning()
    }
    if reasoning_type not in reasonings:
        raise ConfigurationError(f"Unknown reasoning type: {reasoning_type}")
    return reasonings[reasoning_type]

def get_io_handler(io_config: Dict[str, Any]) -> BaseIO:
    """Get IO handler from configuration."""
    io_type = io_config.get("type", "console")
    if io_type == "console":
        return ConsoleIO()
    elif io_type == "websocket":
        if "url" not in io_config:
            raise ConfigurationError("WebSocket IO requires 'url' parameter")
        return WebSocketIO(io_config["url"])
    raise ConfigurationError(f"Unknown IO type: {io_type}")

@asynccontextmanager
async def create_agent(config: Dict[str, Any]) -> AsyncIterator[Agent]:
    """Create and manage an agent's lifecycle.
    
    Args:
        config: Configuration dictionary containing agent settings
        
    Example:
        async with create_agent({
            "name": "researcher",
            "reasoning": "cot",
            "capabilities": ["research", "analysis"],
            "resources": {
                "llm": LLMResource(model="gpt-4")
            }
        }) as agent:
            result = await agent.run("Research quantum computing")
    """
    agent = None
    try:
        # Create base agent
        agent = Agent(name=config.get("name"))
        
        # Configure using with_* methods
        if "reasoning" in config:
            reasoning = (
                config["reasoning"] if isinstance(config["reasoning"], BaseReasoning)
                else get_reasoning(config["reasoning"])
            )
            agent.with_reasoning(reasoning)
            
        if "resources" in config:
            agent.with_resources(config["resources"])
            
        if "capabilities" in config:
            agent.with_capabilities(config["capabilities"])
            
        if "io" in config:
            io_handler = (
                config["io"] if isinstance(config["io"], BaseIO)
                else get_io_handler(config["io"])
            )
            agent.with_io(io_handler)
            
        yield agent
        
    except Exception as e:
        raise ConfigurationError(f"Failed to create agent: {str(e)}") from e
        
    finally:
        if agent:
            try:
                await agent.cleanup()
            # pylint: disable=broad-exception-caught
            except Exception as e:
                logger.warning("Failed to cleanup agent: %s", str(e)) 