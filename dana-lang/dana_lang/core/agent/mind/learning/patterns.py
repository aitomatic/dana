"""
Pattern library for learned strategies and contexts.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


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


class PatternLibrary:
    """Library for managing learned patterns."""

    def __init__(self, storage_dir: str | None = None):
        """Initialize pattern library.

        Args:
            storage_dir: Directory for pattern storage
        """
        self.storage_dir = Path(storage_dir) if storage_dir else Path("~/.models").expanduser()
        self.strategies_dir = self.storage_dir / "strategies"
        self.contexts_dir = self.storage_dir / "contexts"

        self.strategy_patterns: dict[str, StrategyPattern] = {}
        self.context_patterns: dict[str, ContextPattern] = {}

        # Ensure directories exist
        self.strategies_dir.mkdir(parents=True, exist_ok=True)
        self.contexts_dir.mkdir(parents=True, exist_ok=True)

    def load_patterns(self, user_id: str) -> None:
        """Load patterns for a specific user.

        Args:
            user_id: User identifier
        """
        self.strategy_patterns = self._load_strategy_patterns(user_id)
        self.context_patterns = self._load_context_patterns(user_id)

    def save_patterns(self, user_id: str) -> None:
        """Save patterns for a specific user.

        Args:
            user_id: User identifier
        """
        self._save_strategy_patterns(user_id)
        self._save_context_patterns(user_id)

    def add_strategy_pattern(self, pattern: StrategyPattern) -> None:
        """Add a strategy pattern to the library.

        Args:
            pattern: Strategy pattern to add
        """
        self.strategy_patterns[pattern.pattern_id] = pattern

    def add_context_pattern(self, pattern: ContextPattern) -> None:
        """Add a context pattern to the library.

        Args:
            pattern: Context pattern to add
        """
        self.context_patterns[pattern.pattern_id] = pattern

    def get_strategy_patterns(self) -> dict[str, StrategyPattern]:
        """Get all strategy patterns."""
        return self.strategy_patterns.copy()

    def get_context_patterns(self) -> dict[str, ContextPattern]:
        """Get all context patterns."""
        return self.context_patterns.copy()

    def find_best_strategy(self, problem_type: str, context: dict[str, Any]) -> StrategyPattern | None:
        """Find the best strategy pattern for given context.

        Args:
            problem_type: Type of problem
            context: Current context

        Returns:
            Best matching strategy pattern or None
        """
        candidates = []

        for pattern in self.strategy_patterns.values():
            if pattern.strategy_type == problem_type or problem_type in pattern.context_requirements:
                score = self._calculate_strategy_score(pattern, context)
                candidates.append((pattern, score))

        if not candidates:
            return None

        # Return highest scoring pattern
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]

    def find_best_context(self, template: str, problem: str) -> ContextPattern | None:
        """Find the best context pattern for given template and problem.

        Args:
            template: Template name
            problem: Problem description

        Returns:
            Best matching context pattern or None
        """
        candidates = []

        for pattern in self.context_patterns.values():
            if pattern.template == template:
                score = self._calculate_context_score(pattern, problem)
                candidates.append((pattern, score))

        if not candidates:
            return None

        # Return highest scoring pattern
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]

    def _calculate_strategy_score(self, pattern: StrategyPattern, context: dict[str, Any]) -> float:
        """Calculate score for strategy pattern based on context."""
        score = 0.0

        # Base score from success rate and user satisfaction
        score += pattern.success_rate * 0.4
        score += pattern.user_satisfaction * 0.3

        # Recent usage bonus
        if pattern.last_used:
            days_since = (datetime.now() - pattern.last_used).days
            if days_since < 7:
                score += 0.2
            elif days_since < 30:
                score += 0.1

        # Usage count bonus (well-tested patterns)
        if pattern.usage_count > 10:
            score += 0.1

        return min(score, 1.0)

    def _calculate_context_score(self, pattern: ContextPattern, problem: str) -> float:
        """Calculate score for context pattern."""
        score = 0.0

        # Base score from performance metrics
        score += pattern.llm_performance * 0.5
        score += pattern.token_efficiency * 0.2

        # Recent usage bonus
        if pattern.last_used:
            days_since = (datetime.now() - pattern.last_used).days
            if days_since < 7:
                score += 0.2
            elif days_since < 30:
                score += 0.1

        # Usage count bonus
        if pattern.usage_count > 5:
            score += 0.1

        return min(score, 1.0)

    def _load_strategy_patterns(self, user_id: str) -> dict[str, StrategyPattern]:
        """Load strategy patterns from storage."""
        patterns_file = self.strategies_dir / f"{user_id}.json"

        if not patterns_file.exists():
            return {}

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
        """Load context patterns from storage."""
        patterns_file = self.contexts_dir / f"{user_id}.json"

        if not patterns_file.exists():
            return {}

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

    def _save_strategy_patterns(self, user_id: str) -> None:
        """Save strategy patterns to storage."""
        patterns_file = self.strategies_dir / f"{user_id}.json"

        # Convert to serializable format
        data = {}
        for pattern_id, pattern in self.strategy_patterns.items():
            data[pattern_id] = {
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

        try:
            with open(patterns_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving strategy patterns: {e}")

    def _save_context_patterns(self, user_id: str) -> None:
        """Save context patterns to storage."""
        patterns_file = self.contexts_dir / f"{user_id}.json"

        # Convert to serializable format
        data = {}
        for pattern_id, pattern in self.context_patterns.items():
            data[pattern_id] = {
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

        try:
            with open(patterns_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving context patterns: {e}")
