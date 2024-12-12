"""Core types for DXA agents.

This module provides the foundational dataclass definitions for building agents:
- Configuration management
- State tracking and observations
- Progress monitoring
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from dxa.core.reasoning.base_reasoning import BaseReasoning

@dataclass
class AgentConfig:
    """Configuration for DXA agents."""
    name: str
    llm_config: Dict[str, Any]
    reasoning: BaseReasoning
    additional_params: Optional[Dict[str, Any]] = None