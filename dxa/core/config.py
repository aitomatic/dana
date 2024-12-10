"""Core configuration classes for DXA framework."""

from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class LLMConfig:
    """Configuration for Language Learning Models.
    
    Combines both resource-specific and model-specific parameters.
    
    Attributes:
        name: Name identifier for this LLM instance
        model_name: Name of the model to use (e.g., "gpt-4")
        description: Description of this LLM instance
        api_key: API key for model access
        temperature: Controls randomness in output (0.0-1.0)
        max_tokens: Maximum tokens in model response
        top_p: Controls diversity via nucleus sampling (0.0-1.0)
        additional_params: Optional additional model parameters
    """
    name: str
    model_name: str
    description: str = "LLM Resource"
    api_key: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    additional_params: Dict[str, Any] = None 

    @property
    def system_prompt(self) -> str:
        """Get the system prompt."""
        return self.additional_params.get("system_prompt")

    @system_prompt.setter
    def set_system_prompt(self, system_prompt: str) -> None:
        """Set the system prompt."""
        self.additional_params["system_prompt"] = system_prompt
