"""Execution results management.

This module provides functionality for managing execution results across different
contexts and time periods.
"""

from collections import OrderedDict
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import logging

from .result_key import ResultKey

from .constants import (
    OODA_STEPS,
    RECENT_CONTEXT_RATIO,
    ResultDict,
    ContextDict
)

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResults:
    """Manages execution results with different contexts and time periods."""
    _immediate: Dict[str, Any] = field(default_factory=dict)
    _recent: Dict[str, Any] = field(default_factory=dict)
    _historical: Dict[str, Any] = field(default_factory=dict)
    _max_recent: int = 10
    _current_plan: Optional[str] = None

    def __post_init__(self):
        if self._immediate is None:
            self._immediate = {}
        if self._recent is None:
            self._recent = {}
        if self._historical is None:
            self._historical = {}

    def set_current_plan(self, plan_id: str):
        """Set the current plan ID for context management."""
        self._current_plan = plan_id

    def store(self, key: ResultKey, result: Any) -> None:
        """Store a result with the given key."""
        key_str = str(key)
        self._immediate[key_str] = result
        logger.info(f"Stored result for key: {key_str}")
        logger.info(f"Current plan: {self._current_plan}")
        logger.info(f"Immediate storage contents: {self._immediate}")

    def get_latest(self, node_id: str, step: str) -> Optional[Any]:
        """Get the latest result for a given node and step."""
        key_str = f"{node_id}.{step}"
        logger.info(f"Getting latest result for key: {key_str}")
        logger.info(f"Current plan: {self._current_plan}")
        
        # Check immediate storage first
        if key_str in self._immediate:
            logger.info(f"Found result in immediate storage: {self._immediate[key_str]}")
            return self._immediate[key_str]
        
        # Check recent storage
        if key_str in self._recent:
            logger.info(f"Found result in recent storage: {self._recent[key_str]}")
            return self._recent[key_str]
        
        # Check historical storage
        if key_str in self._historical:
            logger.info(f"Found result in historical storage: {self._historical[key_str]}")
            return self._historical[key_str]
        
        logger.info("No result found in any storage")
        return None

    def get_relevant_context(self, current_key: ResultKey) -> Dict[str, Any]:
        """Get relevant context for a given key.
        
        This includes:
        1. Immediate context (previous steps in current plan)
        2. Recent context (other plan nodes)
        3. Historical context (important historical steps)
        """
        context = {
            'immediate_context': self._get_immediate_context(current_key),
            'recent_context': self._get_recent_context(current_key),
            'historical_context': self._get_historical_context(current_key)
        }
        return context

    def _get_immediate_context(self, current_key: ResultKey) -> Dict[str, Any]:
        """Get context from immediate storage (previous steps in current plan)."""
        if not self._current_plan:
            return {'results': {}, 'usage': 'No current plan set'}
        
        # Get all results for the current plan
        current_plan_results = {}
        for key_str, result in self._immediate.items():
            node_id = key_str.split('.')[0]
            if node_id == self._current_plan:
                current_plan_results[key_str] = result
        
        return {
            'results': current_plan_results,
            'usage': 'Use these results to understand the current plan\'s progress'
        }

    def _get_recent_context(self, current_key: ResultKey) -> Dict[str, Any]:
        """Get context from recent storage (other plan nodes)."""
        if not self._current_plan:
            return {'results': {}, 'usage': 'No current plan set'}
        
        # Get results from other plan nodes
        other_plan_results = {}
        for key_str, result in self._recent.items():
            node_id = key_str.split('.')[0]
            if node_id != self._current_plan:
                other_plan_results[key_str] = result
        
        return {
            'results': other_plan_results,
            'usage': 'Use these results to understand related plan nodes'
        }

    def _get_historical_context(self, current_key: ResultKey) -> Dict[str, Any]:
        """Get context from historical storage (important historical steps)."""
        return {
            'results': self._historical,
            'usage': 'Use these results to understand historical context and patterns'
        }

    def move_to_recent(self) -> None:
        """Move immediate results to recent storage."""
        self._recent.update(self._immediate)
        self._immediate.clear()

    def move_to_historical(self) -> None:
        """Move recent results to historical storage."""
        self._historical.update(self._recent)
        self._recent.clear()

    def _get_previous_ooda_step(self, current_step: str) -> Optional[str]:
        """Get the previous step in the OODA cycle."""
        try:
            current_idx = OODA_STEPS.index(current_step)
            return OODA_STEPS[current_idx - 1] if current_idx > 0 else None
        except ValueError:
            return None

    def _trim_to_token_budget(
        self,
        context: ContextDict,
        max_tokens: int
    ) -> ContextDict:
        """Simple token budget management."""
        # Rule 1: Never trim immediate context
        immediate = context['immediate_context']
        
        # Rule 2: Allocate remaining budget between recent and historical
        remaining_budget = max_tokens - self._estimate_tokens(immediate)
        
        # Rule 3: Prioritize recent over historical
        recent_budget = int(remaining_budget * RECENT_CONTEXT_RATIO)
        historical_budget = remaining_budget - recent_budget
        
        return {
            'immediate_context': immediate,
            'recent_context': self._trim_results(
                context['recent_context'],
                recent_budget
            ),
            'historical_context': self._trim_results(
                context['historical_context'],
                historical_budget
            )
        }

    def _estimate_tokens(self, results: ResultDict) -> int:
        """Rough estimate of tokens in results."""
        # Simple estimation: 1 token ≈ 4 characters
        total_chars = sum(len(str(v)) for v in results.values())
        return total_chars // 4

    def _trim_results(
        self,
        results: ResultDict,
        max_tokens: int
    ) -> ResultDict:
        """Trim results to fit token budget."""
        if not results:
            return {}
            
        # Sort by key to ensure consistent trimming
        sorted_results = OrderedDict(sorted(results.items()))
        
        # Keep adding results until we hit the token budget
        trimmed = OrderedDict()
        current_tokens = 0
        
        for k, v in sorted_results.items():
            result_tokens = len(str(v)) // 4
            if current_tokens + result_tokens > max_tokens:
                break
            trimmed[k] = v
            current_tokens += result_tokens
            
        return trimmed 