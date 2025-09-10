"""
Simple Helpful Solver - A non-recursive solver that provides useful responses.

This solver is designed to be helpful without the complexity and recursion issues
of the PlannerExecutorSolverMixin. It focuses on providing useful responses
for common queries and problems.
"""

from typing import Any
from dana.core.lang.sandbox_context import SandboxContext
from dana.core.workflow.workflow_system import WorkflowInstance
from .base import BaseSolverMixin


class SimpleHelpfulSolverMixin(BaseSolverMixin):
    """
    Simple solver that provides helpful responses without complex recursion.

    This solver focuses on being useful and responsive rather than complex planning.
    It can handle common queries, provide information, and give helpful responses.
    """

    MIXIN_NAME = "simple_helpful"

    def solve_sync(
        self,
        problem_or_workflow: str | WorkflowInstance,
        artifacts: dict[str, Any] | None = None,
        sandbox_context: SandboxContext | None = None,
        **kwargs: Any,
    ) -> Any:
        """Simple, helpful problem solving without recursion."""
        artifacts = artifacts or {}

        # Check for conversation termination commands first
        if isinstance(problem_or_workflow, str) and self._is_conversation_termination(problem_or_workflow):
            return "Goodbye! Have a great day!"

        # Handle WorkflowInstance directly
        if isinstance(problem_or_workflow, WorkflowInstance):
            return self._handle_workflow_instance(problem_or_workflow, sandbox_context, artifacts)

        # Handle string problems
        problem = str(problem_or_workflow).strip()

        # Provide helpful responses based on the problem
        response = self._generate_helpful_response(problem, artifacts, sandbox_context)

        # Return just the helpful text for clean conversation
        return response

    def _handle_workflow_instance(
        self, workflow: WorkflowInstance, sandbox_context: SandboxContext | None, artifacts: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle WorkflowInstance execution."""
        try:
            result = self._run_workflow_instance(workflow, sandbox_context)
            return {
                "type": "answer",
                "mode": "workflow",
                "telemetry": {"mixin": self.MIXIN_NAME, "selected": "direct"},
                "artifacts": artifacts,
                "result": result,
            }
        except Exception as e:
            return {
                "type": "error",
                "mode": "workflow",
                "telemetry": {"mixin": self.MIXIN_NAME, "selected": "direct"},
                "artifacts": artifacts,
                "error": str(e),
            }

    def _generate_helpful_response(self, problem: str, artifacts: dict[str, Any], sandbox_context: SandboxContext | None) -> str:
        """Generate a helpful response for the given problem using LLM with conversation context."""

        # Always try LLM first - it's much better at understanding context and nuance
        llm_response = self._try_llm_response(problem, artifacts)
        if llm_response:
            return llm_response

        # Fallback to simple response if LLM is not available
        return f"I understand you're asking about '{problem}'. I'm here to help! Could you provide more details about what you'd like me to assist you with?"

    def _try_llm_response(self, problem: str, artifacts: dict[str, Any]) -> str | None:
        """Try to get a response from LLM if available."""
        # Simple, clean prompt - let the LLM do the heavy lifting
        prompt = f"""You are a helpful AI assistant. Respond naturally and helpfully to the user's message.

Current message: {problem}

If the user is asking about what they said previously, look at the conversation history above and tell them what they said. Be specific and helpful.

Respond:"""

        return self._generate_llm_response_with_context(
            prompt=prompt, system_prompt="You are a helpful AI assistant. Be conversational and provide useful responses."
        )
