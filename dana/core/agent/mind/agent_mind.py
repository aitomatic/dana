"""
AgentMind Mixin

Provides intelligent agent capabilities including user profile management,
strategy and context pattern learning, and adaptive selection.

This mixin can be added to any agent to provide intelligent learning
and adaptation capabilities.
"""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

from .world_model import DomainKnowledge, LocationContext, SystemContext, TimeContext, WorldModel, WorldState


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


@dataclass
class StrategyPattern:
    """Learned strategy pattern for problem solving."""

    pattern_id: str
    strategy_type: str
    success_rate: float
    execution_time: float
    user_satisfaction: float
    usage_count: int = 0
    last_used: datetime | None = None
    context_requirements: list[str] = field(default_factory=list)
    fallback_strategies: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class ContextPattern:
    """Learned context pattern for optimal LLM performance."""

    pattern_id: str
    template: str
    scope: str
    priority: str
    token_efficiency: float
    llm_performance: float
    usage_count: int = 0
    last_used: datetime | None = None
    context_keys_used: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)


class AgentMind:
    """
    AgentMind mixin providing intelligent agent capabilities.

    This mixin manages:
    - User profiles and preferences
    - Strategy and context pattern learning
    - Adaptive selection and optimization
    - Pattern storage and retrieval

    Storage Structure:
    ~/.models/
    ├── users/           # User profiles
    ├── strategies/      # Strategy patterns
    ├── contexts/        # Context patterns
    └── world/          # Future: World model
    """

    def __init__(self):
        """Initialize the agent mind."""
        self.user_profile: UserProfile | None = None
        self.strategy_patterns: dict[str, StrategyPattern] = {}
        self.context_patterns: dict[str, ContextPattern] = {}
        self.world_model = WorldModel()  # World model for shared knowledge

        # Storage paths
        self.models_dir = Path("~/.models").expanduser()
        self.users_dir = self.models_dir / "users"
        self.strategies_dir = self.models_dir / "strategies"
        self.contexts_dir = self.models_dir / "contexts"
        self.world_dir = self.models_dir / "world"

    def initialize_mind(self, user_id: str = "default"):
        """Initialize the agent mind for a specific user."""
        # Load user profile
        self.user_profile = self._load_user_profile(user_id)

        # Load learned patterns
        self.strategy_patterns = self._load_strategy_patterns(user_id)
        self.context_patterns = self._load_context_patterns(user_id)

        # Initialize world model
        self.world_model.initialize()

        # Ensure storage directories exist
        self._ensure_storage_directories()

    def get_user_preferences(self) -> UserProfile | None:
        """Get current user preferences."""
        return self.user_profile

    def get_strategy_patterns(self) -> dict[str, StrategyPattern]:
        """Get learned strategy patterns."""
        return self.strategy_patterns.copy()

    def get_context_patterns(self) -> dict[str, ContextPattern]:
        """Get learned context patterns."""
        return self.context_patterns.copy()

    def select_optimal_strategy(self, problem: str, context: dict[str, Any]) -> str | None:
        """
        Select the optimal strategy based on learned patterns.

        Args:
            problem: The problem statement
            context: Current problem context

        Returns:
            Strategy type name or None if no suitable pattern found
        """
        if not self.strategy_patterns:
            return None

        # Score patterns based on problem characteristics
        scored_patterns = []
        for pattern_id, pattern in self.strategy_patterns.items():
            score = self._calculate_strategy_score(pattern, problem, context)
            scored_patterns.append((pattern_id, score))

        # Return highest scoring pattern
        if scored_patterns:
            scored_patterns.sort(key=lambda x: x[1], reverse=True)
            return scored_patterns[0][0]

        return None

    def select_optimal_context(self, problem: str, strategy: str) -> dict[str, Any] | None:
        """
        Select optimal context configuration based on learned patterns.

        Args:
            problem: The problem statement
            strategy: Selected strategy type

        Returns:
            Context configuration dict or None if no suitable pattern found
        """
        if not self.context_patterns:
            return None

        # Find patterns that work well with this strategy
        strategy_patterns = {k: v for k, v in self.context_patterns.items() if v.usage_count > 0 and v.llm_performance > 0.7}

        if not strategy_patterns:
            return None

        # Score patterns based on problem characteristics
        scored_patterns = []
        for pattern_id, pattern in strategy_patterns.items():
            score = self._calculate_context_score(pattern, problem, strategy)
            scored_patterns.append((pattern_id, score))

        # Return highest scoring pattern configuration
        if scored_patterns:
            scored_patterns.sort(key=lambda x: x[1], reverse=True)
            best_pattern = strategy_patterns[scored_patterns[0][0]]
            return {
                "template": best_pattern.template,
                "scope": best_pattern.scope,
                "priority": best_pattern.priority,
                "context_keys": best_pattern.context_keys_used,
            }

        return None

    def learn_from_execution(
        self, strategy: str, context_config: dict[str, Any], success: bool, execution_time: float, user_satisfaction: float = None
    ):
        """
        Learn from execution results to improve future selections.

        Args:
            strategy: Strategy type used
            context_config: Context configuration used
            success: Whether execution was successful
            execution_time: Time taken for execution
            user_satisfaction: User satisfaction rating (0.0-1.0)
        """
        # Update strategy pattern
        strategy_key = f"{strategy}_{self._generate_pattern_id(context_config)}"
        if strategy_key in self.strategy_patterns:
            pattern = self.strategy_patterns[strategy_key]
            pattern.usage_count += 1
            pattern.last_used = datetime.now()
            pattern.last_updated = datetime.now()

            # Update success rate (exponential moving average)
            alpha = 0.1
            pattern.success_rate = alpha * (1.0 if success else 0.0) + (1 - alpha) * pattern.success_rate

            # Update execution time
            pattern.execution_time = alpha * execution_time + (1 - alpha) * pattern.execution_time

            if user_satisfaction is not None:
                pattern.user_satisfaction = alpha * user_satisfaction + (1 - alpha) * pattern.user_satisfaction
        else:
            # Create new strategy pattern
            self.strategy_patterns[strategy_key] = StrategyPattern(
                pattern_id=strategy_key,
                strategy_type=strategy,
                success_rate=1.0 if success else 0.0,
                execution_time=execution_time,
                user_satisfaction=user_satisfaction or 0.5,
                usage_count=1,
                last_used=datetime.now(),
                context_requirements=list(context_config.keys()),
            )

        # Update context pattern
        context_key = f"{context_config.get('template', 'unknown')}_{self._generate_pattern_id(context_config)}"
        if context_key in self.context_patterns:
            pattern = self.context_patterns[context_key]
            pattern.usage_count += 1
            pattern.last_used = datetime.now()
            pattern.last_updated = datetime.now()

            # Update performance metrics
            alpha = 0.1
            pattern.llm_performance = alpha * (1.0 if success else 0.0) + (1 - alpha) * pattern.llm_performance
        else:
            # Create new context pattern
            self.context_patterns[context_key] = ContextPattern(
                pattern_id=context_key,
                template=context_config.get("template", "general"),
                scope=context_config.get("scope", "standard"),
                priority=context_config.get("priority", "relevant"),
                token_efficiency=0.8,  # Default value
                llm_performance=1.0 if success else 0.0,
                usage_count=1,
                last_used=datetime.now(),
                context_keys_used=list(context_config.keys()),
            )

        # Save updated patterns
        self._save_patterns()

    def update_user_preferences(self, **preferences):
        """Update user preferences."""
        if not self.user_profile:
            return

        for key, value in preferences.items():
            if hasattr(self.user_profile, key):
                setattr(self.user_profile, key, value)

        self.user_profile.last_updated = datetime.now()
        self._save_user_profile()

    def cleanup_expired_patterns(self, max_age_days: int = 30):
        """Remove patterns that haven't been used recently."""
        cutoff_date = datetime.now() - timedelta(days=max_age_days)

        # Clean strategy patterns
        expired_strategies = [
            k for k, v in self.strategy_patterns.items() if v.last_used and v.last_used < cutoff_date and v.usage_count < 5
        ]
        for key in expired_strategies:
            del self.strategy_patterns[key]

        # Clean context patterns
        expired_contexts = [k for k, v in self.context_patterns.items() if v.last_used and v.last_used < cutoff_date and v.usage_count < 5]
        for key in expired_contexts:
            del self.context_patterns[key]

        # Save cleaned patterns
        if expired_strategies or expired_contexts:
            self._save_patterns()

    def _ensure_storage_directories(self):
        """Ensure all storage directories exist."""
        for directory in [self.users_dir, self.strategies_dir, self.contexts_dir, self.world_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def _load_user_profile(self, user_id: str) -> UserProfile:
        """Load user profile from ~/.models/users/{user_id}.json"""
        profile_file = self.users_dir / f"{user_id}.json"
        if profile_file.exists():
            try:
                with open(profile_file) as f:
                    data = json.load(f)
                    # Convert string enums back to enum values
                    if "expertise_level" in data:
                        data["expertise_level"] = ExpertiseLevel(data["expertise_level"])
                    if "created_at" in data:
                        data["created_at"] = datetime.fromisoformat(data["created_at"])
                    if "last_updated" in data:
                        data["last_updated"] = datetime.fromisoformat(data["last_updated"])
                    return UserProfile(**data)
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                print(f"Error loading user profile: {e}")

        # Return default profile
        return UserProfile(user_id=user_id)

    def _load_strategy_patterns(self, user_id: str) -> dict[str, StrategyPattern]:
        """Load strategy patterns from ~/.models/strategies/{user_id}.json"""
        patterns_file = self.strategies_dir / f"{user_id}.json"
        if patterns_file.exists():
            try:
                with open(patterns_file) as f:
                    data = json.load(f)
                    patterns = {}
                    for pattern_id, pattern_data in data.items():
                        # Convert datetime strings back to datetime objects
                        if "created_at" in pattern_data:
                            pattern_data["created_at"] = datetime.fromisoformat(pattern_data["created_at"])
                        if "last_updated" in pattern_data:
                            pattern_data["last_updated"] = datetime.fromisoformat(pattern_data["last_updated"])
                        if "last_used" in pattern_data and pattern_data["last_used"]:
                            pattern_data["last_used"] = datetime.fromisoformat(pattern_data["last_used"])
                        patterns[pattern_id] = StrategyPattern(**pattern_data)
                    return patterns
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                print(f"Error loading strategy patterns: {e}")

        return {}

    def _load_context_patterns(self, user_id: str) -> dict[str, ContextPattern]:
        """Load context patterns from ~/.models/contexts/{user_id}.json"""
        patterns_file = self.contexts_dir / f"{user_id}.json"
        if patterns_file.exists():
            try:
                with open(patterns_file) as f:
                    data = json.load(f)
                    patterns = {}
                    for pattern_id, pattern_data in data.items():
                        # Convert datetime strings back to datetime objects
                        if "created_at" in pattern_data:
                            pattern_data["created_at"] = datetime.fromisoformat(pattern_data["created_at"])
                        if "last_updated" in pattern_data:
                            pattern_data["last_updated"] = datetime.fromisoformat(pattern_data["last_updated"])
                        if "last_used" in pattern_data and pattern_data["last_used"]:
                            pattern_data["last_used"] = datetime.fromisoformat(pattern_data["last_used"])
                        patterns[pattern_id] = ContextPattern(**pattern_data)
                    return patterns
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                print(f"Error loading context patterns: {e}")

        return {}

    def _save_user_profile(self):
        """Save user profile to ~/.models/users/{user_id}.json"""
        os.makedirs(self.users_dir, exist_ok=True)
        profile_file = self.users_dir / f"{self.user_profile.user_id}.json"

        # Convert to serializable format
        data = {
            "user_id": self.user_profile.user_id,
            "expertise_level": self.user_profile.expertise_level.value,
            "domain_preferences": self.user_profile.domain_preferences,
            "urgency_patterns": self.user_profile.urgency_patterns,
            "template_preferences": self.user_profile.template_preferences,
            "context_depth_preferences": self.user_profile.context_depth_preferences,
            "created_at": self.user_profile.created_at.isoformat(),
            "last_updated": self.user_profile.last_updated.isoformat(),
        }

        with open(profile_file, "w") as f:
            json.dump(data, f, indent=2)

    def _save_patterns(self):
        """Save strategy and context patterns to storage under ~/.models/."""
        # Save strategy patterns
        os.makedirs(self.strategies_dir, exist_ok=True)
        strategy_file = self.strategies_dir / f"{self.user_profile.user_id}.json"

        # Convert to serializable format
        strategy_data = {}
        for pattern_id, pattern in self.strategy_patterns.items():
            strategy_data[pattern_id] = {
                "pattern_id": pattern.pattern_id,
                "strategy_type": pattern.strategy_type,
                "success_rate": pattern.success_rate,
                "execution_time": pattern.execution_time,
                "user_satisfaction": pattern.user_satisfaction,
                "usage_count": pattern.usage_count,
                "last_used": pattern.last_used.isoformat() if pattern.last_used else None,
                "context_requirements": pattern.context_requirements,
                "fallback_strategies": pattern.fallback_strategies,
                "created_at": pattern.created_at.isoformat(),
                "last_updated": pattern.last_updated.isoformat(),
            }

        with open(strategy_file, "w") as f:
            json.dump(strategy_data, f, indent=2, default=str)

        # Save context patterns
        os.makedirs(self.contexts_dir, exist_ok=True)
        context_file = self.contexts_dir / f"{self.user_profile.user_id}.json"

        # Convert to serializable format
        context_data = {}
        for pattern_id, pattern in self.context_patterns.items():
            context_data[pattern_id] = {
                "pattern_id": pattern.pattern_id,
                "template": pattern.template,
                "scope": pattern.scope,
                "priority": pattern.priority,
                "token_efficiency": pattern.token_efficiency,
                "llm_performance": pattern.llm_performance,
                "usage_count": pattern.usage_count,
                "last_used": pattern.last_used.isoformat() if pattern.last_used else None,
                "context_keys_used": pattern.context_keys_used,
                "created_at": pattern.created_at.isoformat(),
                "last_updated": pattern.last_updated.isoformat(),
            }

        with open(context_file, "w") as f:
            json.dump(context_data, f, indent=2, default=str)

    def _calculate_strategy_score(self, pattern: StrategyPattern, problem: str, context: dict[str, Any]) -> float:
        """Calculate score for a strategy pattern based on current problem and context."""
        score = 0.0

        # Base score from success rate
        score += pattern.success_rate * 0.4

        # Recency bonus (recently used patterns get slight boost)
        if pattern.last_used:
            days_since = (datetime.now() - pattern.last_used).days
            if days_since < 7:
                score += 0.1
            elif days_since < 30:
                score += 0.05

        # Usage count bonus (well-tested patterns get boost)
        if pattern.usage_count > 10:
            score += 0.1
        elif pattern.usage_count > 5:
            score += 0.05

        # User satisfaction bonus
        score += pattern.user_satisfaction * 0.2

        # Execution time bonus (faster is better, but not too much weight)
        if pattern.execution_time < 1.0:
            score += 0.1
        elif pattern.execution_time < 2.0:
            score += 0.05

        return min(score, 1.0)  # Cap at 1.0

    def _calculate_context_score(self, pattern: ContextPattern, problem: str, strategy: str) -> float:
        """Calculate score for a context pattern based on current problem and strategy."""
        score = 0.0

        # Base score from LLM performance
        score += pattern.llm_performance * 0.5

        # Token efficiency bonus
        score += pattern.token_efficiency * 0.2

        # Recency bonus
        if pattern.last_used:
            days_since = (datetime.now() - pattern.last_used).days
            if days_since < 7:
                score += 0.1
            elif days_since < 30:
                score += 0.05

        # Usage count bonus
        if pattern.usage_count > 10:
            score += 0.1
        elif pattern.usage_count > 5:
            score += 0.05

        return min(score, 1.0)  # Cap at 1.0

    def _generate_pattern_id(self, config: dict[str, Any]) -> str:
        """Generate a pattern ID from configuration."""
        # Simple hash-based ID generation
        config_str = str(sorted(config.items()))
        return str(hash(config_str))[-8:]  # Last 8 characters of hash

    # World Model Integration Methods

    def get_world_context(self) -> WorldState:
        """Get current world context."""
        return self.world_model.get_current_state()

    def get_temporal_context(self) -> TimeContext:
        """Get current temporal context."""
        return self.world_model.get_temporal_context()

    def get_location_context(self) -> LocationContext:
        """Get current location context."""
        return self.world_model.get_location_context()

    def get_system_context(self) -> SystemContext:
        """Get current system context."""
        return self.world_model.get_system_context()

    def get_domain_knowledge(self, domain: str) -> DomainKnowledge | None:
        """Get knowledge for a specific domain."""
        return self.world_model.get_domain_knowledge(domain)

    def update_domain_knowledge(self, domain: str, knowledge: DomainKnowledge):
        """Update domain knowledge."""
        self.world_model.update_domain_knowledge(domain, knowledge)

    def get_shared_patterns(self, pattern_type: str | None = None) -> dict[str, Any]:
        """Get shared patterns from world model."""
        return self.world_model.get_shared_patterns(pattern_type)

    def add_shared_pattern(self, pattern_type: str, pattern_id: str, pattern_data: dict[str, Any]):
        """Add a new shared pattern to world model."""
        self.world_model.add_shared_pattern(pattern_type, pattern_id, pattern_data)

    def is_business_hours(self) -> bool:
        """Check if current time is during business hours."""
        return self.get_temporal_context().is_business_hours

    def is_holiday(self) -> bool:
        """Check if current date is a holiday."""
        return self.get_temporal_context().is_holiday

    def get_current_season(self) -> str:
        """Get current season."""
        return self.get_temporal_context().season

    def get_time_period(self) -> str:
        """Get current time period of day."""
        return self.get_temporal_context().time_period

    def get_system_health(self) -> str:
        """Get current system health status."""
        return self.get_system_context().system_health

    def is_system_healthy(self) -> bool:
        """Check if system is healthy."""
        return self.get_system_context().system_health == "healthy"

    def get_available_resources(self) -> dict[str, Any]:
        """Get available system resources."""
        return self.get_system_context().available_resources

    def get_location_info(self) -> dict[str, str]:
        """Get current location information."""
        location = self.get_location_context()
        return {
            "country": location.country,
            "region": location.region,
            "city": location.city,
            "timezone": location.timezone,
            "environment": location.environment,
            "network": location.network,
        }

    def should_use_lightweight_processing(self) -> bool:
        """Determine if lightweight processing should be used based on system health."""
        system_health = self.get_system_health()
        return system_health in ["degraded", "critical"]

    def get_optimal_concurrency_level(self) -> int:
        """Get optimal concurrency level based on system health and resources."""
        if self.should_use_lightweight_processing():
            return 1

        # Check available CPU resources
        resources = self.get_available_resources()
        cpu_info = resources.get("cpu", {})
        available_cpu = cpu_info.get("available", 1)

        # Check memory usage
        memory_usage = self.get_system_context().memory_usage

        # Determine concurrency based on available resources
        if memory_usage > 80:
            return max(1, int(available_cpu * 0.5))
        elif memory_usage > 60:
            return max(1, int(available_cpu * 0.8))
        else:
            return max(1, int(available_cpu))

    def get_localization_settings(self) -> dict[str, str]:
        """Get localization settings based on current location."""
        location = self.get_location_context()

        # Default settings
        settings = {"date_format": "MM/DD/YYYY", "time_format": "12-hour", "currency": "USD", "language": "en"}

        # Override based on location
        if location.country == "US":
            settings.update({"date_format": "MM/DD/YYYY", "time_format": "12-hour", "currency": "USD"})
        elif location.country in ["UK", "GB"]:
            settings.update({"date_format": "DD/MM/YYYY", "time_format": "24-hour", "currency": "GBP"})
        elif location.country in ["DE", "FR", "IT", "ES"]:
            settings.update({"date_format": "DD/MM/YYYY", "time_format": "24-hour", "currency": "EUR"})

        return settings
