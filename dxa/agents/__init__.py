"""DXA agent implementations.

This module provides different types of agents for various use cases. Each agent type
is specialized for specific interaction patterns and execution models.

Available Agent Types:
    - ConsoleAgent: Interactive console-based agent
    - WebSocketAgent: Network-based agent using WebSocket
    - AutomationAgent: Workflow automation agent
    - CollaborativeAgent: Multi-agent coordination

Supporting Components:
    - StateManager: Manages agent state and history
    - AgentProgress: Reports task progress
    - AgentConfig: Configuration management
    
Example:
    ```python
    from dxa.agents import ConsoleAgent
    from dxa.agents.state import StateManager
    from dxa.agents.config import AgentConfig, LLMConfig
    
    # Create agent configuration
    config = AgentConfig(
        name="math_tutor",
        llm_config=LLMConfig(
            model_name="gpt-4",
            temperature=0.7
        )
    )
    
    # Create and use agent
    agent = ConsoleAgent(
        config=config,
        reasoning=ChainOfThoughtReasoning()
    )
    
    result = await agent.run({"task": "solve_equation"})
    ```
"""

from dxa.agents.base_agent import BaseAgent
from dxa.agents.state import (
    StateManager,
    Observation,
    AgentState,
    Message
)

__all__ = [
    # Agent implementations
    'BaseAgent',
    
    # State management
    'StateManager',
    'Observation',
    'AgentState',
    'Message'
]
