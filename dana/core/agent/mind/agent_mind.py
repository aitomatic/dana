"""
AgentMind - Complete cognitive system including memory, understanding, and learning.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .memory import MemorySystem
from .models.world_model import DomainKnowledge, LocationContext, SystemContext, TimeContext, WorldModel, WorldState
from .models.user_model import UserProfile, ExpertiseLevel
from .learning.patterns import PatternLibrary, StrategyPattern, ContextPattern
from ..context import ProblemContext


# Move classes to separate modules for better organization


class AgentMind:
    """
    Complete cognitive system including memory, understanding, and learning.

    This class manages:
    - All memory types (conversation, working, episodic, semantic)
    - User profiles and preferences
    - World model and environment understanding
    - Strategy and context pattern learning
    - Adaptive selection and optimization

    Storage Structure:
    ~/.dana/memory/       # Memory storage
    ~/.models/            # Models and patterns
    ├── users/           # User profiles
    ├── strategies/      # Strategy patterns
    ├── contexts/        # Context patterns
    └── world/          # World model
    """

    def __init__(self, user_id: str = "default"):
        """Initialize the agent mind.

        Args:
            user_id: User identifier for personalization
        """
        # Memory systems (owned by mind)
        self.memory = MemorySystem()

        # Understanding models
        self.user_profile: UserProfile | None = None
        self.world_model = WorldModel()

        # Learning systems
        self.patterns = PatternLibrary()

        # Storage paths
        self.models_dir = Path("~/.models").expanduser()
        self.users_dir = self.models_dir / "users"
        self.strategies_dir = self.models_dir / "strategies"
        self.contexts_dir = self.models_dir / "contexts"
        self.world_dir = self.models_dir / "world"

        # Initialize for user
        self.initialize_mind(user_id)

    def initialize_mind(self, user_id: str = "default"):
        """Initialize the agent mind for a specific user."""
        # Load user profile
        self.user_profile = self._load_user_profile(user_id)

        # Load learned patterns into patterns library
        self.patterns.load_patterns(user_id)

        # Initialize world model
        self.world_model.initialize()

        # Ensure storage directories exist
        self._ensure_storage_directories()

    # Memory interface methods

    def recall(self, query: str, context: ProblemContext | None = None) -> dict[str, Any]:
        """Intelligent recall across all memory types.

        Args:
            query: What to recall
            context: Current problem context for relevance

        Returns:
            Dictionary with recalled information from relevant memory types
        """
        context_dict = context.to_dict() if context else {}
        return self.memory.recall(query, context_dict)

    def form_memory(self, experience: dict[str, Any]) -> None:
        """Process and store experience as memory.

        Args:
            experience: Experience data to store
        """
        # Determine memory type based on experience
        if experience.get("type") == "conversation":
            # Conversation memory is handled directly by its own interface
            pass
        elif experience.get("type") == "working":
            key = experience.get("key", "unknown")
            value = experience.get("value")
            importance = experience.get("importance", 0.5)
            self.memory.working.store(key, value, importance=importance)
        elif experience.get("type") == "episodic":
            identifier = experience.get("id", "unknown")
            exp_data = experience.get("data")
            self.memory.episodic.store_experience(identifier, exp_data, **experience.get("metadata", {}))
        elif experience.get("type") == "semantic":
            key = experience.get("key", "unknown")
            fact = experience.get("fact")
            domain = experience.get("domain", "general")
            self.memory.semantic.store_fact(key, fact, domain=domain)

    def recall_conversation(self, n_turns: int = 3) -> list[dict[str, Any]]:
        """Recall recent conversation turns.

        Args:
            n_turns: Number of turns to recall

        Returns:
            List of recent conversation turns
        """
        return self.memory.get_conversation_context(n_turns)

    def recall_relevant(self, problem: ProblemContext) -> dict[str, Any]:
        """Recall all relevant information for current problem.

        Args:
            problem: Current problem context

        Returns:
            Dictionary with relevant memories
        """
        relevant = {}

        # Get from different memory types
        query = problem.problem_statement if problem else ""

        # Working memory (current task context)
        relevant["working"] = self.memory.get_working_context()

        # Episodic memory (similar experiences)
        if problem:
            context_dict = problem.to_dict()
            similar_experiences = self.memory.episodic.recall_similar(query, context_dict)
            relevant["episodic"] = similar_experiences

        # Semantic memory (domain knowledge)
        if problem and hasattr(problem, "domain"):
            domain_knowledge = self.memory.semantic.get_domain_knowledge(problem.domain)
            relevant["semantic"] = domain_knowledge

        return relevant

    def get_user_context(self) -> dict[str, Any]:
        """Get current user context combining profile and preferences.

        Returns:
            Dictionary with user context
        """
        if not self.user_profile:
            return {}

        return {
            "user_id": self.user_profile.user_id,
            "expertise_level": self.user_profile.expertise_level.value,
            "domain_preferences": self.user_profile.domain_preferences,
            "urgency_patterns": self.user_profile.urgency_patterns,
            "template_preferences": self.user_profile.template_preferences,
        }

    def assess_context_needs(self, problem: ProblemContext | None, template: str = "general") -> dict[str, Any]:
        """Assess what context is most important for current situation.

        Args:
            problem: Current problem context
            template: Template being used

        Returns:
            Dictionary with context priorities and recommendations
        """
        priorities = {
            "turns": 3,  # default conversation turns
            "memory_depth": "standard",
            "include_world": False,
            "filters": [],
        }

        # Adjust based on problem complexity
        if problem:
            if problem.depth > 2:
                priorities["turns"] = 5
                priorities["memory_depth"] = "deep"

            if len(problem.constraints) > 3:
                priorities["include_world"] = True

        # Adjust based on template
        if template == "problem_solving":
            priorities["turns"] = 5
            priorities["filters"] = ["solution", "decision", "error"]
        elif template == "conversation":
            priorities["turns"] = 10
            priorities["memory_depth"] = "shallow"
        elif template == "analysis":
            priorities["include_world"] = True
            priorities["filters"] = ["data", "analysis", "conclusion"]

        # Adjust based on user preferences
        if self.user_profile:
            depth_pref = self.user_profile.context_depth_preferences.get(template, "standard")
            if depth_pref == "comprehensive":
                priorities["turns"] = 10
                priorities["memory_depth"] = "deep"
                priorities["include_world"] = True

        return priorities

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
