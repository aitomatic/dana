"""DXA agent implementations.

This module provides different types of agents for various use cases. Each agent type
is specialized for specific interaction patterns and execution models.

Available Agent Types:
    - InteractiveAgent: Console-based interactive agent
    - WebSocketAgent: Network-based agent using WebSocket
    - AutomationAgent: Workflow automation agent
    - CollaborativeAgent: Multi-agent coordination

Supporting Components:
    - StateManager: Manages agent state and history
    - AgentProgress: Reports task progress
    - AgentConfig: Configuration management
"""

from dxa.agent.base_agent import BaseAgent
from dxa.agent.interactive_agent import InteractiveAgent
from dxa.agent.websocket_agent import WebSocketAgent
from dxa.agent.automation_agent import AutomationAgent
from dxa.agent.collaborative_agent import CollaborativeAgent
from dxa.agent.autonomous_agent import AutonomousAgent
from dxa.agent.state import (
    StateManager,
    Observation,
    AgentState,
    Message
)
from dxa.agent.progress import AgentProgress
from dxa.agent.config import AgentConfig, LLMConfig
from dxa.agent.agent_llm import AgentLLM

__all__ = [
    # Base classes
    'BaseAgent',
    'AgentLLM',
    
    # Agent implementations
    'InteractiveAgent',
    'WebSocketAgent',
    'AutomationAgent',
    'CollaborativeAgent',
    'AutonomousAgent',
    # State management
    'StateManager',
    'Observation',
    'AgentState',
    'Message',
    
    # Progress and configuration
    'AgentProgress',
    'AgentConfig',
    'LLMConfig'
]
