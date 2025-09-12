"""
Simple Helpful Solver - A non-recursive solver that provides useful responses.

This solver is designed to be helpful without the complexity and recursion issues
of the PlannerExecutorSolverMixin. It focuses on providing useful responses
for common queries and problems.
"""

from typing import Any, TYPE_CHECKING
from dana.core.lang.sandbox_context import SandboxContext
from dana.core.workflow.workflow_system import WorkflowInstance
from .base import BaseSolver
from .prompts import (
    SIMPLE_HELPFUL_SYSTEM_PROMPT,
)
if TYPE_CHECKING:
    from dana.core.agent.agent_instance import AgentInstance


class SimpleHelpfulSolver(BaseSolver):
    """
    Simple solver that provides helpful responses without complex recursion.

    This solver focuses on being useful and responsive rather than complex planning.
    It can handle common queries, provide information, and give helpful responses.
    """

    def __init__(self, agent: "AgentInstance"):
        super().__init__(agent)

    def solve_sync(
        self,
        problem_or_workflow: str | WorkflowInstance,
        artifacts: dict[str, Any] | None = None,
        sandbox_context: SandboxContext | None = None,
        **kwargs: Any,
    ) -> Any:
        """Simple, helpful problem solving without recursion."""
        # Debug print for solver entry
        print("=" * 80)
        print("🤖 [DEBUG] SIMPLE_HELPFUL_SOLVER SOLVE_SYNC")
        print("=" * 80)
        print(f"📥 Input type: {type(problem_or_workflow).__name__}")
        print(f"📝 Input content: '{problem_or_workflow}'")
        print(f"📦 Artifacts: {artifacts}")
        print(f"🏗️ Sandbox context: {sandbox_context is not None}")

        artifacts = artifacts or {}

        # Check for conversation termination commands first
        if isinstance(problem_or_workflow, str) and self._is_conversation_termination(problem_or_workflow):
            print("🚪 Conversation termination detected")
            print("=" * 80)
            return "Goodbye! Have a great day!"

        # Handle WorkflowInstance directly
        if isinstance(problem_or_workflow, WorkflowInstance):
            print("🔄 Handling WorkflowInstance directly")
            result = self._handle_workflow_instance(problem_or_workflow, sandbox_context, artifacts)
            print(f"✅ WorkflowInstance result: {type(result).__name__}")
            print("=" * 80)
            return result

        # Handle string problems
        problem = str(problem_or_workflow).strip()
        print(f"📝 Processing string problem: '{problem}'")

        # Provide helpful responses based on the problem
        print("🔍 Generating helpful response...")
        response = self._generate_helpful_response(problem, artifacts, sandbox_context)
        print(f"✅ Generated response: {type(response).__name__}")
        print(f"📄 Response preview: {str(response)[:100]}{'...' if len(str(response)) > 100 else ''}")
        print("=" * 80)

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
                "artifacts": artifacts,
                "result": result,
            }
        except Exception as e:
            return {
                "type": "error",
                "mode": "workflow",
                "artifacts": artifacts,
                "error": str(e),
            }

    def _generate_helpful_response(self, problem: str, artifacts: dict[str, Any], sandbox_context: SandboxContext | None) -> str:
        """Generate a helpful response for the given problem using LLM with conversation context."""
        print("🔍 [DEBUG] _generate_helpful_response")
        print(f"📝 Problem: '{problem}'")
        print(f"📦 Artifacts: {artifacts}")

        # Always try LLM first - it's much better at understanding context and nuance
        print("🤖 Attempting LLM response...")
        llm_response = self._try_llm_response(problem, artifacts)
        if llm_response:
            print(f"✅ LLM response successful: {type(llm_response).__name__}")
            return llm_response

        # Fallback to simple response if LLM is not available
        print("⚠️ LLM not available, using fallback response")
        fallback_response = f"I understand you're asking about '{problem}'. I'm here to help! Could you provide more details about what you'd like me to assist you with?"
        print(f"📄 Fallback response: {fallback_response}")
        return fallback_response

    def _try_llm_response(self, problem: str, artifacts: dict[str, Any]) -> str | None:
        """Try to get a response from LLM if available."""
        print("🤖 [DEBUG] _try_llm_response")
        print(f"📝 Problem: '{problem}'")
        print(f"📦 Artifacts: {artifacts}")
        print("🔧 Calling _generate_llm_response_with_context...")

        # Use the user message directly as the prompt, with all instructions in the system prompt
        result = self._generate_llm_response_with_context(
            prompt=problem, system_prompt=SIMPLE_HELPFUL_SYSTEM_PROMPT
        )

        print(f"📊 LLM result: {type(result).__name__ if result else 'None'}")
        if result:
            print(f"📄 Result preview: {str(result)[:100]}{'...' if len(str(result)) > 100 else ''}")

        return result
