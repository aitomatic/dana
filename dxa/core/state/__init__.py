"""
State management for DXA.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass
class AgentState:
    """Maintains agent-specific state."""
    
    name: str = "agent"
    metadata: Dict[str, Any] = field(default_factory=dict)
    history: Dict[str, Any] = field(default_factory=dict)

@dataclass
class WorldState:
    """Maintains environment and domain state."""
    
    parameters: Dict[str, Any] = field(default_factory=dict)
    events: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ExecutionState:
    """Maintains execution state across workflow runs."""
    
    current_step: Optional[str] = None
    variables: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

__all__ = [
    'AgentState',
    'WorldState',
    'ExecutionState'
]