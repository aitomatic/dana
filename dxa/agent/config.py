"""Configuration classes for DXA agents.

This module provides dataclasses for configuring agents and their components.
It ensures type safety and provides a standardized way to configure different
agent types and their Language Learning Models (LLMs).

Example:
    ```python
    llm_config = LLMConfig(
        model_name="gpt-4",
        temperature=0.7,
        additional_params={"api_key": "your-key"}
    )
    
    agent_config = AgentConfig(
        name="research_agent",
        llm_config=llm_config,
        reasoning_config={"strategy": "chain-of-thought"}
    )
    ```
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class LLMConfig:
    """Configuration for Language Learning Models.
    
    This class defines the configuration parameters for LLMs used by agents.
    It includes both required and optional parameters for model behavior.
    
    Attributes:
        model_name: Identifier of the LLM model to use (e.g., "gpt-4")
        temperature: Controls randomness in output (0.0-1.0)
        max_tokens: Maximum tokens in model response (None for model default)
        top_p: Controls diversity via nucleus sampling (0.0-1.0)
        additional_params: Optional additional model parameters
        
    Example:
        ```python
        config = LLMConfig(
            model_name="gpt-4",
            temperature=0.7,
            max_tokens=2000,
            additional_params={
                "api_key": "your-key",
                "organization": "your-org"
            }
        )
        ```
    """
    model_name: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    additional_params: Dict[str, Any] = None

@dataclass
class AgentConfig:
    """Configuration for DXA agents.
    
    This class defines the complete configuration for an agent, including
    its LLM settings, reasoning system, and available resources.
    
    Attributes:
        name: Agent identifier
        llm_config: Configuration for the agent's LLM
        reasoning_config: Optional reasoning system configuration
        resources_config: Optional resource configuration
        
    Example:
        ```python
        config = AgentConfig(
            name="research_agent",
            llm_config=LLMConfig(...),
            reasoning_config={
                "strategy": "chain-of-thought",
                "max_steps": 5
            },
            resources_config={
                "math_expert": {"capability": "mathematics"},
                "web_access": {"urls": ["allowed.com"]}
            }
        )
        ```
    """
    name: str
    llm_config: LLMConfig
    reasoning_config: Optional[Dict[str, Any]] = None
    resources_config: Optional[Dict[str, Any]] = None 