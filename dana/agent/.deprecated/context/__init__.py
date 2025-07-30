"""
Agent Context Management Package

This package provides implicit context management for Dana agents,
enabling seamless conversation continuity similar to Claude Code CLI.
"""

from .agent_context_manager import AgentContextManager
from .conversation_state import ConversationState, ConversationTurn

__all__ = ["AgentContextManager", "ConversationState", "ConversationTurn"]
