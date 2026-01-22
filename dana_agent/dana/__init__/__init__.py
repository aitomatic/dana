"""
Dana Agent - Domain-Aware Neurosymbolic Agents

This package provides the core agent framework for building and managing
specialized AI agents with domain-specific knowledge and capabilities.
"""

########################################################
# Initialize environment
from .init_environment import init_environment


init_environment()

########################################################
# Export main components
from dana.common.llm.llm import LLM, LLMMessage, LLMResponse
from dana.core.agent.star_agent import STARAgent


########################################################
# Export all components
__all__ = ["LLM", "LLMMessage", "LLMResponse", "STARAgent"]
