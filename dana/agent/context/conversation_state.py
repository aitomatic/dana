"""
Conversation State Management for Dana Agents

This module provides classes for tracking conversation state and context
across multiple agent interactions within a session.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from collections import deque


@dataclass
class ConversationTurn:
    """Represents a single turn in a conversation"""

    timestamp: datetime
    user_input: str
    agent_response: str
    context_used: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationState:
    """Manages the state of a conversation session"""

    # Session identification
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = ""
    instance_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # Conversation tracking
    conversation_history: deque = field(default_factory=lambda: deque(maxlen=50))
    current_turn: ConversationTurn | None = None

    # Context extraction
    extracted_facts: dict[str, Any] = field(default_factory=dict)
    user_preferences: dict[str, Any] = field(default_factory=dict)
    topics_discussed: list[str] = field(default_factory=list)

    # Session metadata
    session_start: datetime = field(default_factory=datetime.now)
    last_interaction: datetime = field(default_factory=datetime.now)
    interaction_count: int = 0

    def add_turn(self, user_input: str, agent_response: str, context_used: dict[str, Any] = None):
        """Add a new conversation turn"""
        turn = ConversationTurn(
            timestamp=datetime.now(), user_input=user_input, agent_response=agent_response, context_used=context_used or {}, metadata={}
        )

        self.conversation_history.append(turn)
        self.current_turn = turn
        self.last_interaction = datetime.now()
        self.interaction_count += 1

    def get_recent_history(self, n: int = 5) -> list[ConversationTurn]:
        """Get the n most recent conversation turns"""
        return list(self.conversation_history)[-n:]

    def get_conversation_context(self) -> str:
        """Get formatted conversation context for prompt injection"""
        recent_turns = self.get_recent_history(5)
        if not recent_turns:
            return ""

        context_parts = []
        for turn in recent_turns:
            context_parts.append(f"User: {turn.user_input}")
            context_parts.append(f"Agent: {turn.agent_response}")

        return "\n".join(context_parts)

    def extract_user_info(self, text: str) -> dict[str, Any]:
        """Extract user information from text (basic implementation)"""
        # Simple extraction - in real implementation, would use LLM
        extracted = {}

        # Extract names (basic pattern matching)
        import re

        name_patterns = [r"I'm ([A-Z][a-z]+)", r"My name is ([A-Z][a-z]+)", r"I am ([A-Z][a-z]+)", r"Call me ([A-Z][a-z]+)"]

        for pattern in name_patterns:
            match = re.search(pattern, text)
            if match:
                extracted["name"] = match.group(1)
                break

        # Extract email addresses
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        email_match = re.search(email_pattern, text)
        if email_match:
            extracted["email"] = email_match.group(0)

        # Store extracted info
        if extracted:
            self.extracted_facts.update(extracted)

        return extracted

    def get_user_context(self) -> dict[str, Any]:
        """Get user context for prompt enhancement"""
        context = {}

        # Add extracted facts
        if self.extracted_facts:
            context["user_info"] = self.extracted_facts

        # Add conversation summary
        if self.conversation_history:
            context["conversation_summary"] = self._generate_conversation_summary()

        return context

    def _generate_conversation_summary(self) -> str:
        """Generate a brief summary of the conversation"""
        if not self.conversation_history:
            return ""

        # Simple summary - just the main topics
        summary_parts = []

        if self.extracted_facts.get("name"):
            summary_parts.append(f"User name: {self.extracted_facts['name']}")

        if len(self.conversation_history) > 1:
            summary_parts.append(f"Conversation has {len(self.conversation_history)} turns")

        # Add recent topics (basic implementation)
        recent_turns = self.get_recent_history(3)
        if recent_turns:
            last_user_input = recent_turns[-1].user_input
            summary_parts.append(f"Current topic: {last_user_input[:50]}...")

        return "; ".join(summary_parts)

    def should_include_context(self) -> bool:
        """Determine if context should be included in next response"""
        # Include context if we have previous conversation or extracted facts
        return len(self.conversation_history) > 0 or len(self.extracted_facts) > 0

    def clear_session(self):
        """Clear session data (for testing)"""
        self.conversation_history.clear()
        self.extracted_facts.clear()
        self.user_preferences.clear()
        self.topics_discussed.clear()
        self.interaction_count = 0
        self.current_turn = None
