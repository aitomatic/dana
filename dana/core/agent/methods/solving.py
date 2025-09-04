from typing import Any

from dana.core.lang.sandbox_context import SandboxContext
from dana.core.workflow.workflow_system import WorkflowInstance


class SolvingMixin:
    def solve_sync(self, problem_or_workflow: str | WorkflowInstance, sandbox_context: SandboxContext | None = None, **kwargs) -> Any:
        """Synchronous agent solve method."""
        return self._solve_impl(problem_or_workflow, sandbox_context or SandboxContext(), **kwargs)

    def plan_sync(
        self, problem_or_workflow: str | WorkflowInstance, sandbox_context: SandboxContext | None = None, **kwargs
    ) -> WorkflowInstance:
        """Synchronous agent plan method."""
        return self._plan_impl(problem_or_workflow, sandbox_context or SandboxContext(), **kwargs)

    def _solve_impl(self, problem_or_workflow: str | WorkflowInstance, sandbox_context: SandboxContext, **kwargs) -> Any:
        """Implementation of solve functionality."""
        print(f"[DEBUG] agent.solve() called with: {type(problem_or_workflow)} = {problem_or_workflow}")
        print(f"[DEBUG] sandbox_context: {sandbox_context}")
        print(f"[DEBUG] kwargs: {kwargs}")

        # If this is a new user request (string), start a new conversation turn
        if isinstance(problem_or_workflow, str):
            print(f"[DEBUG] Starting new conversation turn for: {problem_or_workflow}")
            self._global_event_history.start_new_conversation_turn(problem_or_workflow)

        # Enhanced context assembly using Context Engineering Framework
        if isinstance(problem_or_workflow, str):
            try:
                from dana.frameworks.ctxeng import ContextEngine

                # Create context engine for this agent
                if self._context_engine is None:
                    self._context_engine = ContextEngine.from_agent(self)

                # Assemble rich context using ctxeng framework
                rich_prompt = self._context_engine.assemble(
                    problem_or_workflow,
                    template="problem_solving",  # Use problem-solving template
                )

                print(f"[DEBUG] Context Engine assembled rich prompt (length: {len(rich_prompt)})")
                print(f"[DEBUG] Rich prompt preview: {rich_prompt[:200]}...")

                # Use rich prompt instead of basic problem
                problem_or_workflow = rich_prompt

            except ImportError:
                print("[DEBUG] Context Engineering Framework not available, using basic problem")
            except Exception as e:
                print(f"[DEBUG] Context Engine failed: {e}, using basic problem")

        # Always create or reuse a workflow via plan(), then execute
        print("[DEBUG] Calling agent.plan()...")
        workflow = self.plan_sync(problem_or_workflow, sandbox_context=sandbox_context, **kwargs)
        print(f"[DEBUG] Plan returned workflow: {type(workflow)}")
        print(f"[DEBUG] Workflow values: {getattr(workflow, '_values', 'No _values')}")

        print("[DEBUG] Executing workflow...")
        result = workflow.execute(sandbox_context or self._create_sandbox_context(), **kwargs)
        print(f"[DEBUG] Workflow execution result: {type(result)} = {result}")

        return result

    def _plan_impl(self, problem_or_workflow: str | WorkflowInstance, sandbox_context: SandboxContext, **kwargs) -> WorkflowInstance:
        """Implementation of plan functionality."""
        print(f"[DEBUG] agent.plan() called with: {type(problem_or_workflow)} = {problem_or_workflow}")
        print(f"[DEBUG] sandbox_context: {sandbox_context}")
        print(f"[DEBUG] kwargs: {kwargs}")

        if isinstance(problem_or_workflow, str):
            # Create new workflow for string problem
            print("[DEBUG] Creating new workflow for string problem...")
            workflow = self._create_new_workflow(problem_or_workflow, sandbox_context=sandbox_context, **kwargs)
            print(f"[DEBUG] New workflow created: {type(workflow)}")
        else:
            # Use existing workflow
            print(f"[DEBUG] Using existing workflow: {type(problem_or_workflow)}")
            workflow = problem_or_workflow

        print(f"[DEBUG] Plan returning workflow: {type(workflow)}")
        return workflow
