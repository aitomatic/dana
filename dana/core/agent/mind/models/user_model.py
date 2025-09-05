"""
User model and profile management.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ExpertiseLevel(Enum):
    """User expertise levels."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class UrgencyLevel(Enum):
    """Problem urgency levels."""

    QUICK = "quick"
    STANDARD = "standard"
    THOROUGH = "thorough"


@dataclass
class UserProfile:
    """User profile with preferences and settings."""

    user_id: str
    expertise_level: ExpertiseLevel = ExpertiseLevel.INTERMEDIATE
    domain_preferences: list[str] = field(default_factory=lambda: ["general"])
    urgency_patterns: dict[str, float] = field(default_factory=lambda: {"quick": 0.6, "standard": 0.3, "thorough": 0.1})
    template_preferences: dict[str, str] = field(
        default_factory=lambda: {"problem_solving": "problem_solving", "conversation": "conversation", "analysis": "analysis"}
    )
    context_depth_preferences: dict[str, str] = field(
        default_factory=lambda: {"general": "standard", "technical": "comprehensive", "business": "detailed"}
    )
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
