"""DXA agent implementations.

This module provides different types of agents for various use cases. Each agent type
is specialized for specific interaction patterns and execution models.

Class Hierarchy:
    BaseAgent
    ├── AutonomousAgent
    ├── InteractiveAgent
    ├── WebSocketAgent
    ├── WorkAutomationAgent
    └── CollaborativeAgent

Available Agent Types:
    - BaseAgent: Abstract base class with common functionality
        - Default Chain of Thought reasoning
        - Resource management
        - Error handling
        
    - InteractiveAgent: Console-based interactive agent
        - Real-time user interaction
        - Progress monitoring
        - Decision points
        
    - WebSocketAgent: Network-based agent using WebSocket
        - Remote communication
        - Connection management
        - State synchronization
        
    - WorkAutomationAgent: Workflow automation agent
        - Step-by-step execution
        - Process validation
        - Default OODA reasoning
        
    - CollaborativeAgent: Multi-agent coordination
        - Agent-to-agent communication
        - Task delegation
        - Result aggregation

Supporting Components:
    - StateManager: Manages agent state and history
    - AgentProgress: Reports task progress
    - AgentConfig: Configuration management
"""

from dxa.agent.base_agent import BaseAgent
from dxa.agent.interactive_agent import InteractiveAgent
from dxa.agent.websocket_agent import WebSocketAgent
from dxa.agent.work_automation_agent import WorkAutomationAgent
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
    'WorkAutomationAgent',
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
