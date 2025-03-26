"""Execution results management."""

from collections import OrderedDict
from typing import Dict, Any, Optional

from .result_key import ResultKey
from .constants import (
    OODA_STEPS,
    MAX_RECENT_RESULTS,
    DEFAULT_TOKEN_BUDGET,
    RECENT_CONTEXT_RATIO,
    ResultDict,
    ContextDict
)


class ExecutionResults:
    """Manages execution results with smart context selection."""
    
    def __init__(self, max_recent_results: int = MAX_RECENT_RESULTS):
        """Initialize the results manager.
        
        Args:
            max_recent_results: Maximum number of recent results to keep
        """
        self._immediate: Dict[str, Any] = {}  # Current plan execution
        self._recent: OrderedDict[str, Any] = OrderedDict()  # Last N plan results
        self._historical: Dict[str, Any] = {}  # Important long-term results
        self._max_recent = max_recent_results
        self._current_plan_id: Optional[str] = None

    def set_current_plan(self, plan_id: str):
        """Set the current plan being executed."""
        self._current_plan_id = plan_id

    def store(self, key: ResultKey, result: str) -> None:
        """Store a result with proper context management."""
        key_str = str(key)
        
        # Rule 1: Move results from previous plan node to recent
        if self._current_plan_id and key.node_id != self._current_plan_id:
            # Move all results from previous plan to recent
            for k, v in list(self._immediate.items()):
                prev_key = ResultKey.from_str(k)
                if prev_key.node_id == self._current_plan_id:
                    self._recent[k] = v
                    del self._immediate[k]
            
            # Update current plan
            self._current_plan_id = key.node_id
        elif not self._current_plan_id:
            # First result, set current plan
            self._current_plan_id = key.node_id
        
        # Rule 2: Store workflow-level decisions in historical
        if key.is_workflow:
            self._historical[key_str] = result
            return
        
        # Rule 3: Store results from current plan or any plan in current graph in immediate
        if key.node_id == self._current_plan_id or key.node_id.startswith("PLAN_"):
            self._immediate[key_str] = result
            return
        
        # Rule 4: Store other results in recent
        self._recent[key_str] = result
        
        # Rule 5: Enforce size limits
        if len(self._recent) > self._max_recent:
            # Remove oldest result
            oldest_key = next(iter(self._recent))
            del self._recent[oldest_key]

    def get_relevant_context(self, current_key: ResultKey) -> Dict[str, Any]:
        """Get relevant context for a reasoning step."""
        print(f"\nGetting context for {current_key}")
        print(f"Current plan: {self._current_plan_id}")
        
        # Get immediate context (previous steps in current plan)
        immediate_context = self._get_immediate_context(current_key)
        print("\nImmediate storage contents:")
        for k in self._immediate.keys():
            print(f"- {k}")
        print("\nImmediate context (filtered for current plan):")
        for k in immediate_context.keys():
            print(f"- {k}")
        
        # Get recent context (other plan nodes)
        recent_context = self._get_relevant_recent_results(current_key)
        print("\nRecent storage contents:")
        for k in self._recent.keys():
            print(f"- {k}")
        print("\nRecent context (filtered for relevance):")
        for k in recent_context.keys():
            print(f"- {k}")
        
        # Get historical context (important historical steps)
        historical_context = self._get_relevant_historical_results(current_key)
        print("\nHistorical storage contents:")
        for k in self._historical.keys():
            print(f"- {k}")
        print("\nHistorical context (filtered for relevance):")
        for k in historical_context.keys():
            print(f"- {k}")
        
        # Return the context with usage instructions
        return {
            'immediate_context': {
                'results': immediate_context,
                'usage': "Use these results to maintain continuity with previous steps in the current plan."
            },
            'recent_context': {
                'results': recent_context,
                'usage': "Use these results to coordinate with other plan nodes and maintain consistency across the current graph execution."
            },
            'historical_context': {
                'results': historical_context,
                'usage': "Use these results to inform decisions based on historical precedents and workflow-level outcomes."
            }
        }

    def _get_immediate_context(self, current_key: ResultKey) -> ResultDict:
        """Get context from current plan's previous steps."""
        immediate = {}
        current_step_idx = OODA_STEPS.index(current_key.step)
        
        # Include all previous steps in current plan
        for step in OODA_STEPS[:current_step_idx]:
            key = ResultKey(node_id=current_key.node_id, step=step)
            if str(key) in self._immediate:
                immediate[str(key)] = self._immediate[str(key)]
        
        return immediate

    def _get_relevant_recent_results(self, current_key: ResultKey) -> Dict[str, Any]:
        """Get relevant recent results based on execution context.
        
        Rules for recent results:
        1. Include results from previous plan nodes in the current graph
        2. Include results from same OODA step from other nodes
        3. Include results from previous steps in the OODA cycle
        4. Limit to MAX_RECENT_RESULTS to prevent context bloat
        """
        relevant = {}
        
        # Rule 1: Include results from previous plan nodes in the current graph
        for k, v in self._immediate.items():
            key = ResultKey.from_str(k)
            # Include results from any node that's not the current one
            if key.node_id != current_key.node_id:
                relevant[k] = v
        
        # Rule 2: Include results from same OODA step from other nodes
        for k, v in self._recent.items():
            key = ResultKey.from_str(k)
            if key.step == current_key.step:
                relevant[k] = v
        
        # Rule 3: Include results from previous steps in the OODA cycle
        for k, v in self._recent.items():
            key = ResultKey.from_str(k)
            if key.node_id == current_key.node_id:
                # Get the index of current step
                current_idx = OODA_STEPS.index(current_key.step)
                # Get the index of the step in the result
                result_idx = OODA_STEPS.index(key.step)
                # Include if it's a previous step
                if result_idx < current_idx:
                    relevant[k] = v
        
        # Rule 4: Limit to MAX_RECENT_RESULTS
        if len(relevant) > self._max_recent:
            # Sort by recency (assuming keys are ordered by timestamp)
            sorted_keys = sorted(relevant.keys(), reverse=True)
            # Keep only the most recent results
            relevant = {k: relevant[k] for k in sorted_keys[:self._max_recent]}
        
        return relevant

    def _get_relevant_historical_results(
        self,
        current_key: ResultKey
    ) -> ResultDict:
        """Get relevant historical results using simple rules."""
        relevant = {}
        
        # Rule 1: Always include workflow-level decisions
        for k, v in self._historical.items():
            if ResultKey.from_str(k).is_workflow:
                relevant[k] = v

        # Rule 2: Include historical results from same step type
        if current_key.step in ['DECIDE', 'ACT']:
            for k, v in self._historical.items():
                if ResultKey.from_str(k).step == current_key.step:
                    relevant[k] = v

        # Rule 3: Include results from previous graph executions
        # Only include results that are actually in the historical store
        # and not from the current graph execution
        for k, v in self._historical.items():
            key = ResultKey.from_str(k)
            if key.node_id != current_key.node_id:
                relevant[k] = v

        return relevant

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

    def get_latest(self, node_id: str, step: str) -> Optional[Any]:
        """Get the most recent result for a node and step.
        
        Args:
            node_id: ID of the node
            step: OODA step
            
        Returns:
            The most recent result or None if not found
        """
        key = ResultKey(node_id=node_id, step=step)
        str_key = str(key)
        
        # Check immediate context first
        if str_key in self._immediate:
            return self._immediate[str_key]
            
        # Then check recent results
        if str_key in self._recent:
            return self._recent[str_key]
            
        # Finally check historical results
        if str_key in self._historical:
            return self._historical[str_key]
            
        return None 