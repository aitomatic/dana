"""DXA agent module."""

from dxa.agent.agent_framework import (
    AgentConfig,
    AgentState,
    StateManager,
    AgentProgress,
    AgentRuntime,
    AgentLLM
)
from dxa.agent.base_agent import BaseAgent
from dxa.agent.interactive_agent import InteractiveAgent
from dxa.agent.autonomous_agent import AutonomousAgent
from dxa.agent.websocket_agent import WebSocketAgent
from dxa.agent.work_automation_agent import WorkAutomationAgent
from dxa.agent.collaborative_agent import CollaborativeAgent

__version__ = "0.1.0"

__all__ = [
    "AgentConfig",
    "AgentState", 
    "StateManager",
    "AgentProgress",
    "AgentRuntime",
    "AgentLLM",
    "BaseAgent",
    "InteractiveAgent",
    "AutonomousAgent", 
    "WebSocketAgent",
    "WorkAutomationAgent",
    "CollaborativeAgent"
]
