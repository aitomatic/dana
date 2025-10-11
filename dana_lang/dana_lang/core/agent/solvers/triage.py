"""
Triage Solver for intelligent query routing.

This solver analyzes incoming queries and routes them to the most appropriate
specialized solver based on query content and intent.
"""

from typing import Any
from .base import BaseSolver
from .prompts import TRIAGE_SYSTEM_PROMPT, get_triage_prompt
from dana_lang.core.lang.sandbox_context import SandboxContext
from dana_lang.core.workflow.workflow_system import WorkflowInstance


class TriageSolver(BaseSolver):
    """Solver that intelligently routes queries to appropriate specialized solvers."""

    def __init__(self, agent):
        """Initialize triage solver for query classification."""
        super().__init__(agent)

    def solve_sync(
        self,
        problem_or_workflow: str | WorkflowInstance,
        artifacts: dict[str, Any] | None = None,
        sandbox_context: SandboxContext | None = None,
        **kwargs,
    ) -> Any:
        """Required by BaseSolver - delegates to classify_query."""
        if isinstance(problem_or_workflow, WorkflowInstance):
            # For WorkflowInstance, return a default classification
            return "planner_executor"
        return self.classify_query(problem_or_workflow)

    def classify_query(self, problem: str) -> str:
        """Classify query using LLM and return the appropriate solver name."""
        print("🔍 [TRIAGE] Analyzing query for solver selection...")
        print(f"📝 Query: '{problem}'")

        try:
            # Use LLM to classify the query with conversation context
            prompt = get_triage_prompt(problem)
            response = self._query_llm_with_prteng(prompt=prompt, system_prompt=TRIAGE_SYSTEM_PROMPT, max_turns=1)

            if response:
                # Clean up the response to get just the solver name
                solver_name = response.strip().lower()
                if solver_name in ["simple_helpful", "planner_executor", "reactive_support"]:
                    print(f"✅ [TRIAGE] LLM selected solver: {solver_name}")
                    return solver_name
                else:
                    print(f"⚠️ [TRIAGE] Invalid LLM response '{solver_name}', using fallback")
                    return self._classify_query_fallback(problem)
            else:
                print("⚠️ [TRIAGE] No LLM response, using fallback")
                return self._classify_query_fallback(problem)

        except Exception as e:
            print(f"❌ [TRIAGE] LLM classification failed: {e}, using fallback")
            return self._classify_query_fallback(problem)

    def _classify_query_fallback(self, problem: str) -> str:
        """Fallback classification when LLM fails - defaults to simple_helpful."""
        print("✅ [TRIAGE] Fallback: using simple_helpful solver")
        return "simple_helpful"
