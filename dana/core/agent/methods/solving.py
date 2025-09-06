from typing import Any

from dana.core.lang.sandbox_context import SandboxContext
from dana.core.workflow.workflow_system import WorkflowInstance
from dana.frameworks.ctxeng import ContextEngineerMixin


class SolvingMixin(ContextEngineerMixin):
    def solve_sync(self, problem_or_workflow: str | WorkflowInstance, sandbox_context: SandboxContext | None = None, **kwargs) -> Any:
        """Implementation of solve functionality."""
        print(f"🔧 AGENT.SOLVE() - Input: {type(problem_or_workflow).__name__} = {str(problem_or_workflow)[:100]}...")

        # If this is a new user request (string), start a new conversation turn
        if isinstance(problem_or_workflow, str):
            print("🔄 STATE TRANSITION - Starting new conversation turn")
            # Use centralized state
            self.state.start_new_conversation_turn(problem_or_workflow)
            # Set problem context in centralized state
            from ..context import ProblemContext

            self.state.set_problem_context(ProblemContext(problem_statement=problem_or_workflow))

        # Enhanced context assembly using Context Engineering Framework
        if isinstance(problem_or_workflow, str):
            try:
                # Assemble rich context using ctxeng framework
                rich_prompt = self.assemble_context(problem_or_workflow, template="problem_solving")
                print(f"📝 CONTEXT ENGINE - Assembled rich prompt ({len(rich_prompt)} chars)")
                # Use rich prompt instead of basic problem
                problem_or_workflow = rich_prompt
            except ImportError:
                print("⚠️  CONTEXT ENGINE - Framework not available, using basic problem")
            except Exception as e:
                print(f"❌ CONTEXT ENGINE - Failed: {e}, using basic problem")

        # Always create or reuse a workflow via plan(), then execute
        print("🎯 STATE TRANSITION - Planning workflow...")
        workflow = self.plan_sync(problem_or_workflow, sandbox_context=sandbox_context, **kwargs)

        print("⚡ STATE TRANSITION - Executing workflow...")
        try:
            result = workflow.execute(sandbox_context or self._create_sandbox_context(), **kwargs)
            print(f"✅ WORKFLOW COMPLETE - Result: {type(result).__name__} = {str(result)[:100]}...")
            return result
        except Exception as e:
            print(f"❌ WORKFLOW ERROR - {e}")
            # Return error message instead of re-raising
            return f"Error executing workflow: {str(e)}"

    def plan_sync(
        self, problem_or_workflow: str | WorkflowInstance, sandbox_context: SandboxContext | None = None, **kwargs
    ) -> WorkflowInstance:
        """Implementation of plan functionality."""
        if isinstance(problem_or_workflow, str):
            # Create new workflow for string problem
            print("🏗️  PLANNING - Creating new workflow for string problem")
            workflow = self._create_new_workflow(problem_or_workflow, sandbox_context=sandbox_context, **kwargs)
        else:
            # Use existing workflow
            print(f"♻️  PLANNING - Reusing existing workflow: {type(problem_or_workflow).__name__}")
            workflow = problem_or_workflow

        return workflow

    def _create_new_workflow(self, problem: str, sandbox_context: SandboxContext | None = None, **kwargs) -> WorkflowInstance:
        """Create a new workflow for a string problem using auto strategy selection."""
        from dana.core.workflow.workflow_system import WorkflowInstance

        print("🎲 STRATEGY SELECTION - Auto-selecting strategy for problem")
        workflow = WorkflowInstance.create_with_strategy(
            problem=problem, strategy_type="auto", agent_instance=self, sandbox_context=sandbox_context, **kwargs
        )
        print(f"✅ WORKFLOW CREATED - {type(workflow).__name__}")

        return workflow
