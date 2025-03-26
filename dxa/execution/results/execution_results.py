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

    def store(self, key: ResultKey, value: Any):
        """Store a result with smart categorization.
        
        Args:
            key: Unique identifier for the result
            value: The result value to store
        """
        str_key = str(key)
        print(f"\nStoring result for {str_key}")
        print(f"Current plan: {self._current_plan_id}")
        
        # 1. If this is a new plan node, move previous plan results to recent
        if (key.node_id.startswith("PLAN_") and self._current_plan_id and key.node_id != self._current_plan_id):
            print(f"Moving results from previous plan {self._current_plan_id} to recent")
            # Move all results from previous plan to recent
            for k, v in list(self._immediate.items()):
                prev_key = ResultKey.from_str(k)
                if prev_key.node_id.startswith("PLAN_"):
                    print(f"Moving {k} to recent")
                    self._recent[k] = v
                    del self._immediate[k]
                    if len(self._recent) > self._max_recent:
                        self._recent.popitem(last=False)  # Remove oldest
        
        # 2. Store in immediate if part of current plan or any plan in the current graph
        if key.node_id == self._current_plan_id or key.node_id.startswith("PLAN_"):
            print(f"Storing {str_key} in immediate")
            self._immediate[str_key] = value
            return

        # 3. Store in historical if it's a key decision point
        # Rules for historical storage:
        # - Workflow-level decisions (DECIDE/ACT) that affect future executions
        # - Final outcomes of completed workflows
        # - Critical decisions that establish precedents
        if (key.is_workflow and key.step in ['DECIDE', 'ACT']):
            print(f"Storing {str_key} in historical")
            self._historical[str_key] = value
            return

        # 4. Otherwise store in recent, maintaining size limit
        print(f"Storing {str_key} in recent")
        self._recent[str_key] = value
        if len(self._recent) > self._max_recent:
            self._recent.popitem(last=False)  # Remove oldest

    def get_relevant_context(
        self,
        current_key: ResultKey,
        max_tokens: int = DEFAULT_TOKEN_BUDGET
    ) -> ContextDict:
        """Get relevant context using explicit rules for each context type.
        
        Args:
            current_key: Key for the current execution step
            max_tokens: Maximum token budget for context
            
        Returns:
            Dictionary containing immediate, recent, and historical context with usage instructions
        """
        print(f"\nGetting context for {current_key}")
        print(f"Current plan: {self._current_plan_id}")
        print(f"Immediate results: {list(self._immediate.keys())}")
        print(f"Recent results: {list(self._recent.keys())}")
        print(f"Historical results: {list(self._historical.keys())}")
        
        context = {
            'immediate_context': {
                'results': self._get_immediate_context(current_key),
                'usage': 'Use these results to maintain continuity within the current plan node. '
                         'Each step should build upon the previous steps in sequence.'
            },
            'recent_context': {
                'results': self._get_relevant_recent_results(current_key),
                'usage': 'Use these results to coordinate with parallel plan nodes and maintain '
                         'consistency across the current execution. Reference specific results when '
                         'they directly influence the current step.'
            },
            'historical_context': {
                'results': self._get_relevant_historical_results(current_key),
                'usage': 'Use these results as established precedents and constraints. '
                         'Reference specific decisions when they set boundaries or requirements '
                         'for the current step.'
            }
        }
        
        print("\nContext returned:")
        print(f"Immediate context: {list(context['immediate_context']['results'].keys())}")
        print(f"Recent context: {list(context['recent_context']['results'].keys())}")
        print(f"Historical context: {list(context['historical_context']['results'].keys())}")
        
        return self._trim_to_token_budget(context, max_tokens)

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
            # Include results from any plan node that's not the current one
            if key.node_id.startswith("PLAN_") and key.node_id != current_key.node_id:
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
        for k, v in self._immediate.items():
            key = ResultKey.from_str(k)
            if (key.node_id != current_key.node_id and not key.node_id.startswith("PLAN_")):
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