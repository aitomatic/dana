"""Core types and enums for the MUA system."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List
from datetime import datetime

class OODAPhase(Enum):
    """Enumeration of phases in the OODA loop decision cycle."""
    OBSERVE = "observe"
    ORIENT = "orient"
    DECIDE = "decide"
    ACT = "act"

@dataclass
class ChatHistory:
    """Manages the conversation history."""
    messages: List[Dict] = field(default_factory=list)

    def add_message(self, role: str, content: str):
        """Add a new message to the history."""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().timestamp()
        })

@dataclass
class Observation:
    """Class representing a single observation with timestamp and associated data."""
    data: Dict
    source: str
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())

@dataclass
class ExpertResponse:
    """Structured response from a domain expert."""
    confidence: float
    analysis: Dict
    recommendations: List[Dict]
    follow_up: List[str]
    metadata: Dict = field(default_factory=dict)

    @classmethod
    def create_fallback(cls, content: str, error: str = "Response format error") -> 'ExpertResponse':
        """Create a fallback response when parsing fails."""
        return cls(
            confidence=0.0,
            analysis={
                'main_points': [],
                'details': content,
                'assumptions': [],
                'limitations': [error]
            },
            recommendations=[],
            follow_up=["Please provide response in the correct format"],
            metadata={'error': error}
        )

@dataclass
class AgentState:
    """Class representing the current state of the Model-Using Agent in the OODA loop."""
    current_phase: OODAPhase
    observations: List[Observation]
    context_window: List[Dict]
    problem_statement: str
    working_memory: Dict
    agent_history: ChatHistory = field(default_factory=ChatHistory)
