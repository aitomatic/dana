"""
Recursive Strategy Implementation

This strategy implements recursive problem solving where the agent:
1. Breaks down complex problems into smaller sub-problems
2. Recursively solves each sub-problem
3. Combines results to solve the original problem
4. Leverages rich context engineering for optimal LLM reasoning
"""

from typing import Any

from dana.builtin_types.agent.context import ComputableContext, ProblemContext
from dana.builtin_types.workflow.workflow_system import WorkflowInstance, WorkflowType

from ..base import BaseStrategy


class RecursiveStrategy(BaseStrategy):
    """Strategy that solves problems by breaking them down recursively."""

    def __init__(self, llm_client=None, max_depth: int = 10):
        """Initialize the recursive strategy."""
        self.llm_client = llm_client
        self.max_depth = max_depth
        self.computable_context = ComputableContext()

    def can_handle(self, problem: str, context: ProblemContext) -> bool:
        """Determine if this strategy can handle the problem."""
        # Recursive strategy can handle most problems
        # but check for obvious infinite loops
        return not self._detect_obvious_loop(problem, context)

    def create_workflow(self, problem: str, context: ProblemContext) -> WorkflowInstance:
        """Create a workflow instance using LLM-generated Dana code."""

        # 1. Check recursion depth limits
        if not self._check_depth_limits(context):
            return self._create_base_case_workflow(problem, context)

        # 2. Generate LLM prompt with rich computable context
        prompt = self._build_enhanced_analysis_prompt(problem, context)

        # 3. Get LLM response (Dana code)
        dana_code = self._get_llm_response(prompt)

        # 4. Validate and compile Dana code
        compiled_function = self._compile_dana_code(dana_code, context)

        # 5. Create WorkflowInstance with parent reference
        return self._create_workflow_instance(problem, context, compiled_function)

    def _check_depth_limits(self, context: ProblemContext) -> bool:
        """Check if recursion depth limits have been reached."""

        # Check absolute depth limit
        if context.depth >= self.max_depth:
            return False

        # Check for rapid depth increases
        if self._detect_rapid_depth_increase(context):
            return False

        return True

    def _detect_obvious_loop(self, problem: str, context: ProblemContext) -> bool:
        """Detect obvious infinite loops in problem solving."""

        # Check for identical problem statements
        if self._is_identical_problem(problem, context):
            return True

        # Check for circular problem patterns
        if self._has_circular_pattern(problem, context):
            return True

        return False

    def _detect_rapid_depth_increase(self, context: ProblemContext) -> bool:
        """Detect rapid depth increases that might indicate loops."""
        # Simple implementation - could be enhanced
        return False

    def _is_identical_problem(self, problem: str, context: ProblemContext) -> bool:
        """Check if this problem is identical to the current one."""
        return problem.lower().strip() == context.problem_statement.lower().strip()

    def _has_circular_pattern(self, problem: str, context: ProblemContext) -> bool:
        """Check for circular problem patterns."""
        # Simple implementation - could be enhanced
        return False

    def _build_enhanced_analysis_prompt(self, problem: str, context: ProblemContext) -> str:
        """Build the LLM analysis prompt with rich computable context."""

        # In simplified workflow system, fallback to basic prompt
        # since we don't have rich context data anymore
        return self._build_basic_prompt(problem, context)

        # Return basic prompt since we don't have rich context in simplified system
        return self._build_basic_prompt(problem, context)

    def _build_basic_prompt(self, problem: str, context: ProblemContext) -> str:
        """Build a basic prompt when rich context is not available."""

        # Include conversation history if available
        conversation_section = ""
        if "conversation_history" in context.constraints:
            conversation_section = f"""
CONVERSATION HISTORY:
{context.constraints["conversation_history"]}

"""

        return f"""
You are an AI agent solving problems using Dana code.

PROBLEM: {problem}
OBJECTIVE: {context.objective}
DEPTH: {context.depth}

{conversation_section}AVAILABLE FUNCTIONS:
- agent.output(result): Specify final result when problem is solved
- agent.solve(sub_problem, objective): Solve a sub-problem recursively
- agent.input(prompt): Get user input during problem solving
- agent.reason(thought): Express natural language reasoning

Generate Dana code that solves: {problem}
"""

    def _get_llm_response(self, prompt: str) -> str:
        """Get LLM response (Dana code)."""
        if self.llm_client:
            # Use actual LLM client
            return self.llm_client.generate(prompt)
        else:
            # Mock response for testing
            return self._generate_mock_response(prompt)

    def _generate_mock_response(self, prompt: str) -> str:
        """Generate a mock LLM response for testing."""
        if "complex" in prompt.lower() or "break down" in prompt.lower():
            return """
agent.reason("This is a complex problem that needs to be broken down")
sub_problem_1 = agent.solve("Analyze the problem structure", "Break down into components", workflow_instance=workflow_instance)
sub_problem_2 = agent.solve("Solve the main components", "Apply solution to components", workflow_instance=workflow_instance)
agent.output({"analysis": sub_problem_1, "solution": sub_problem_2})
"""
        else:
            return """
agent.reason("This is a straightforward problem")
result = "Solution to the problem"
agent.output(result)
"""

    def _compile_dana_code(self, dana_code: str, context: ProblemContext) -> Any:
        """Compile Dana code to a ComposedFunction."""
        # For now, return a simple function that can be called
        # In a real implementation, this would compile the Dana code
        return self._create_simple_function(dana_code)

    def _create_simple_function(self, dana_code: str):
        """Create a simple function from Dana code for testing."""
        from dana.core.lang.interpreter.functions.sandbox_function import SandboxFunction

        class SimpleSandboxFunction(SandboxFunction):
            def __init__(self, dana_code: str):
                super().__init__()
                self.dana_code = dana_code

            def execute(self, context, *args, **kwargs):
                # Mock implementation - in reality this would execute the Dana code
                return f"Executed Dana code: {self.dana_code[:100]}..."

            def restore_context(self, context, original_context):
                # Default implementation - no context restoration needed for mock
                pass

        return SimpleSandboxFunction(dana_code)

    def _create_workflow_instance(self, problem: str, context: ProblemContext, compiled_function: Any) -> WorkflowInstance:
        """Create a WorkflowInstance with the compiled function."""

        # Get parent workflow if this is a recursive call
        parent_workflow = getattr(context, "workflow_instance", None)

        # Create workflow type
        workflow_type = self._create_workflow_type(problem)

        # Create workflow instance with simplified fields
        workflow = WorkflowInstance(
            struct_type=workflow_type,
            values={
                "composed_function": compiled_function,
                "name": f"RecursiveWorkflow_{hash(problem) % 10000}",
            },
            parent_workflow=parent_workflow,
        )

        return workflow

    def _create_workflow_type(self, problem: str) -> WorkflowType:
        """Create a workflow type for the problem."""
        # Simple workflow type creation - only custom fields needed
        # Default workflow fields (name, composed_function, metadata) are added automatically
        return WorkflowType(
            name=f"RecursiveWorkflow_{hash(problem) % 10000}",
            fields={},  # No custom fields needed
            field_order=[],  # No custom field order needed
            docstring=f"Recursive workflow for solving: {problem}",
        )

    def _create_base_case_workflow(self, problem: str, context: ProblemContext) -> WorkflowInstance:
        """Create a workflow for base cases (max depth reached)."""

        # Create a simple output function
        base_function = self._create_base_case_function(problem, context)

        # Get parent workflow if this is a recursive call
        parent_workflow = getattr(context, "workflow_instance", None)

        # Create workflow instance with simplified fields
        workflow = WorkflowInstance(
            struct_type=self._create_workflow_type(problem),
            values={
                "composed_function": base_function,
                "name": f"BaseCaseWorkflow_{hash(problem) % 10000}",
            },
            parent_workflow=parent_workflow,
        )

        return workflow

    def _create_base_case_function(self, problem: str, context: ProblemContext):
        """Create a simple function for base cases."""

        def base_case_function(*args, **kwargs):
            return f"Base case reached for: {problem}. Maximum recursion depth ({self.max_depth}) exceeded."

        return base_case_function

    def _format_recent_actions(self, actions) -> str:
        """Format recent actions for the prompt."""
        if not actions:
            return "No recent actions"

        formatted = []
        for action in actions[-3:]:  # Last 3 actions
            formatted.append(f"- {action.action_type}: {action.description}")

        return "\n".join(formatted)
