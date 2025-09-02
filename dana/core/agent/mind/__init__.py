"""
Agent Mind Module

This module provides intelligent agent capabilities including:
- User profile management
- Strategy and context pattern learning
- Adaptive selection and optimization
- Pattern storage and retrieval
- World model awareness (time, location, system state)

The AgentMind mixin can be added to any agent to provide
intelligent learning and adaptation capabilities.
"""

from .agent_mind import AgentMind, ContextPattern, ExpertiseLevel, StrategyPattern, UrgencyLevel, UserProfile
from .world_model import (
    DomainKnowledge,
    DomainKnowledgeProvider,
    LocationContext,
    LocationProvider,
    SharedPatternsProvider,
    StateProvider,
    SystemContext,
    SystemProvider,
    TimeContext,
    TimeProvider,
    WorldModel,
    WorldState,
)

__all__ = [
    # AgentMind classes
    "AgentMind",
    "UserProfile",
    "StrategyPattern",
    "ContextPattern",
    "ExpertiseLevel",
    "UrgencyLevel",
    # World model classes
    "WorldModel",
    "WorldState",
    "TimeContext",
    "LocationContext",
    "SystemContext",
    "DomainKnowledge",
    "StateProvider",
    "TimeProvider",
    "LocationProvider",
    "SystemProvider",
    "DomainKnowledgeProvider",
    "SharedPatternsProvider",
]
