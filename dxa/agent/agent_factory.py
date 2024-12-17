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

from typing import Dict, Any, Union
from dxa.agent.agent import Agent
from dxa.core.reasoning import (
    BaseReasoning,
    DirectReasoning,
    ChainOfThoughtReasoning,
    OODAReasoning,
    DANAReasoning
)

class AgentFactory:
    """Factory for creating configured agents."""
    
    REASONING_TYPES = {
        "direct": DirectReasoning,
        "cot": ChainOfThoughtReasoning,
        "ooda": OODAReasoning,
        "dana": DANAReasoning
    }

    @classmethod
    def create_reasoning(cls, reasoning_type: Union[str, BaseReasoning]) -> BaseReasoning:
        """Create reasoning instance from type."""
        if isinstance(reasoning_type, BaseReasoning):
            return reasoning_type
            
        if reasoning_type not in cls.REASONING_TYPES:
            raise ValueError(f"Unknown reasoning type: {reasoning_type}")
            
        return cls.REASONING_TYPES[reasoning_type]()

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> Agent:
        """Create an agent from configuration dictionary."""
        # Create base agent
        agent = Agent(
            name=config["name"],
            config=config
        )
        
        # Configure reasoning
        if "reasoning" in config:
            reasoning = cls.create_reasoning(config["reasoning"])
            agent.with_reasoning(reasoning)
            
        # Add resources
        if "resources" in config:
            agent.with_resources(config["resources"])
            
        # Add capabilities
        if "capabilities" in config:
            agent.with_capabilities(config["capabilities"])
            
        return agent