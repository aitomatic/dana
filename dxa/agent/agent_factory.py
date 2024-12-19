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

from typing import List, Union
from dxa.core.planning import (
    BasePlanning,
    SequentialPlanning,
    HierarchicalPlanning,
    DynamicPlanning,
    HeuristicPlanning
)
from dxa.core.reasoning import (
    BaseReasoning,
    DirectReasoning,
    ChainOfThoughtReasoning,
    OODAReasoning,
    DANAReasoning
)
from dxa.core.capability import BaseCapability
from dxa.core.resource import BaseResource
from dxa.core.io import BaseIO

class AgentFactory:
    """Factory for creating configured agents."""
    
    PLANNING_TYPES = {
        "none": BasePlanning,
        "sequential": SequentialPlanning,
        "hierarchical": HierarchicalPlanning,
        "dynamic": DynamicPlanning,
        "heuristic": HeuristicPlanning
    }
    
    REASONING_TYPES = {
        "none": BaseReasoning,
        "direct": DirectReasoning,
        "cot": ChainOfThoughtReasoning,
        "ooda": OODAReasoning,
        "dana": DANAReasoning
    }

    @classmethod
    def create_planning(cls, planning_type: Union[str, BasePlanning] = None) -> BasePlanning:
        """Return the given planning type or a default one if not provided."""
        if planning_type is None:
            return BasePlanning()
        
        if isinstance(planning_type, BasePlanning):
            return planning_type
        
        if planning_type not in cls.PLANNING_TYPES:
            raise ValueError(f"Unknown planning type: {planning_type}")
        
        return cls.PLANNING_TYPES[planning_type]()
    
    @classmethod
    def create_reasoning(cls, reasoning_type: Union[str, BaseReasoning] = None) -> BaseReasoning:
        """Return the given reasoning type or a default one if not provided."""
        if reasoning_type is None:
            return BaseReasoning()
        
        if isinstance(reasoning_type, BaseReasoning):
            return reasoning_type
            
        if reasoning_type not in cls.REASONING_TYPES:
            raise ValueError(f"Unknown reasoning type: {reasoning_type}")
            
        return cls.REASONING_TYPES[reasoning_type]()

    @classmethod
    def create_capabilities(cls, capabilities: List[BaseCapability] = None) -> List[BaseCapability]:
        """Return the given capabilities or an empty list if not provided."""
        return capabilities or []

    @classmethod
    def create_resources(cls, resources: List[BaseResource] = None) -> List[BaseResource]:
        """Return the given resources or an empty list if not provided."""
        return resources or []

    @classmethod
    def create_io(cls, io: BaseIO = None) -> BaseIO:
        """Return the given IO instance or a default one if not provided."""
        return io or BaseIO()
