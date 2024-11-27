"""
This module contains configuration classes for LLM models and agents.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class LLMConfig:
    """Configuration for LLM models."""
    model_name: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    additional_params: Dict[str, Any] = None

@dataclass
class AgentConfig:
    """Configuration for agents."""
    name: str
    llm_config: LLMConfig
    reasoning_config: Optional[Dict[str, Any]] = None
    resources_config: Optional[Dict[str, Any]] = None 