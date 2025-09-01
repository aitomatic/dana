"""
Iterative Strategy Implementation

This module implements an iterative strategy for solving problems
by refining solutions through multiple iterations rather than recursion.
"""

from typing import Any

from dana.builtin_types.agent.context import ProblemContext
from dana.builtin_types.agent.strategy.base import BaseStrategy
from dana.builtin_types.workflow import WorkflowInstance, WorkflowType


class IterativeStrategy(BaseStrategy):
    """Strategy that solves problems through iterative refinement."""

    def __init__(self, llm_client=None, max_iterations: int = 10):
        """Initialize the iterative strategy."""
        self.llm_client = llm_client
        self.max_iterations = max_iterations

    def can_handle(self, problem: str, context: ProblemContext) -> bool:
        """Determine if this strategy can handle the problem."""
        # Iterative strategy can handle most problems
        # but check for obvious infinite loops
        return not self._detect_obvious_loop(problem, context)

    def create_workflow(self, problem: str, context: ProblemContext) -> WorkflowInstance:
        """Create a workflow instance using LLM-generated Dana code."""

        # 1. Check iteration limits
        if not self._check_iteration_limits(context):
            return self._create_base_case_workflow(problem, context)

        # 2. Generate LLM prompt
        prompt = self._build_analysis_prompt(problem, context)

        # 3. Get LLM response (Dana code)
        dana_code = self._get_llm_response(prompt)

        # 4. Validate and compile Dana code
        compiled_function = self._compile_dana_code(dana_code, context)

        # 5. Create WorkflowInstance
        return self._create_workflow_instance(problem, context, compiled_function)

    def _check_iteration_limits(self, context: ProblemContext) -> bool:
        """Check if iteration limits have been reached."""
        # For now, always allow iterations
        # In a real implementation, this would track iteration count
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

    def _is_identical_problem(self, problem: str, context: ProblemContext) -> bool:
        """Check if this problem is identical to the current one."""
        return problem.lower().strip() == context.problem_statement.lower().strip()

    def _has_circular_pattern(self, problem: str, context: ProblemContext) -> bool:
        """Check for circular problem patterns."""
        # Simple implementation - could be enhanced
        return False

    def _build_analysis_prompt(self, problem: str, context: ProblemContext) -> str:
        """Build the LLM analysis prompt."""

        # Include conversation history if available
        conversation_section = ""
        if "conversation_history" in context.constraints:
            conversation_section = f"""
CONVERSATION HISTORY:
{context.constraints["conversation_history"]}

"""

        return f"""
You are an AI agent solving problems using Dana code through iterative refinement.

PROBLEM: {problem}
OBJECTIVE: {context.objective}
DEPTH: {context.depth}

{conversation_section}AVAILABLE FUNCTIONS:
- agent.output(result): Specify final result when problem is solved
- agent.iterate(improvement_plan): Plan the next iteration
- agent.input(prompt): Get user input during problem solving
- agent.reason(thought): Express natural language reasoning

DECISION: You must decide whether to:
1. SOLVE DIRECTLY: If the problem is simple enough, solve it directly and output the result
2. GENERATE DANA CODE: If the problem requires iterative refinement, generate Dana code that will execute step by step

ITERATIVE STRATEGY (if generating Dana code):
- Break down the problem into manageable steps
- Execute each step and evaluate results
- Use agent.iterate() to plan improvements
- Continue until the problem is solved or max iterations reached

Choose the appropriate approach and implement it. For Dana code generation, use the available functions above.

Generate Dana code or solve directly for: {problem}
"""

    def _get_llm_response(self, prompt: str) -> str:
        """Get LLM response (Dana code)."""
        if not self.llm_client:
            raise ValueError("LLM client is required for IterativeStrategy to work")

        # The LLM always makes the decision about how to solve the problem
        return self.llm_client.generate(prompt)

    # Mock response method removed - LLM client is required
    # def _generate_mock_response(self, prompt: str) -> str:
    #     """Generate a mock LLM response for testing."""
    #     # Simulate LLM decision-making based on problem content
    #     problem = prompt.split("PROBLEM:")[1].split("\n")[0].strip() if "PROBLEM:" in prompt else ""
    #
    #     if "trip" in problem.lower() and "mexico" in problem.lower():
    #         # Complex travel planning - needs iterative refinement
    #         return """
    # agent.reason("Planning a trip to Mexico requires iterative refinement")
    # agent.reason("I'll start with initial research and improve the plan step by step")
    #
    # # Iteration 1: Initial research
    # agent.reason("Starting with basic destination research")
    # destinations = ["Mexico City", "Cancun", "Guadalajara"]
    # agent.reason(f"Initial destinations: {destinations}")
    #
    # # Iteration 2: Refine based on feedback
    # improvement_plan = agent.iterate("Research safety considerations and cultural aspects")
    # agent.reason("Refining destinations based on safety and culture")
    # refined_destinations = ["Mexico City (cultural hub)", "Oaxaca (safe, authentic)", "Merida (colonial charm)"]
    #
    # # Iteration 3: Final logistics
    # agent.reason("Final iteration: planning logistics and itinerary")
    # final_plan = {
    #     "destinations": refined_destinations,
    #     "logistics": "Book flights, hotels, local transport",
    #     "itinerary": "7-day cultural exploration route"
    # }
    #
    # agent.output(final_plan)
    # """
    #     elif "plan" in problem.lower() and "planning" in problem.lower():
    #         # Meta-planning - explain iterative approach
    #         return """
    # agent.reason("The user wants me to explain my iterative methodology")
    # agent.reason("I should demonstrate how I approach complex problem-solving")
    #
    # iterative_method = {
    #     "iteration1": "Initial analysis and basic solution",
    #     "iteration2": "Identify areas for improvement",
    #     "iteration3": "Refine based on feedback and constraints",
    #     "iteration4": "Validate and finalize solution"
    # }
    #
    # agent.reason(f"Here's my iterative methodology: {iterative_method}")
    #
    # agent.output({
    #     "iterative_methodology": iterative_method,
    #     "explanation": "I solve complex problems through multiple iterations, starting with basic solutions and refining them based on feedback, constraints, and deeper analysis.",
    #     "example": "For trip planning, I'd start with basic research, then refine destinations, then logistics, then create detailed itineraries."
    # })
    # """
    #     else:
    #         # Default case - iterative approach
    #         return """
    # agent.reason("I'll solve this problem through iterative refinement")
    # agent.reason("Starting with initial analysis and improving step by step")
    #
    # # Iteration 1: Initial analysis
    # agent.reason("First iteration: basic problem analysis")
    # initial_analysis = analyze_problem_basics()
    # agent.reason(f"Initial analysis: {initial_analysis}")
    #
    # # Iteration 2: Refine approach
    # improvement_plan = agent.iterate("Identify areas for improvement")
    # agent.reason("Second iteration: refining the approach")
    # refined_approach = apply_improvements(initial_analysis, improvement_plan)
    #
    # # Iteration 3: Final solution
    # agent.reason("Final iteration: implementing refined solution")
    # final_solution = implement_solution(refined_approach)
    #
    # agent.output({
    #     "iterations": 3,
    #     "final_solution": final_solution,
    #     "improvement_path": "Basic analysis → Refinement → Implementation"
    # })
    # """

    def _compile_dana_code(self, dana_code: str, context: ProblemContext) -> Any:
        """Compile Dana code to a function."""
        # For now, return a simple function that can be called
        # In a real implementation, this would compile the Dana code
        return self._create_simple_function(dana_code)

    def _create_simple_function(self, dana_code: str):
        """Create a simple function from Dana code for testing."""

        def simple_function(*args, **kwargs):
            # Mock implementation - in reality this would execute the Dana code
            return f"Executed iterative Dana code: {dana_code[:100]}..."

        return simple_function

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
                "name": f"IterativeWorkflow_{hash(problem) % 10000}",
            },
            parent_workflow=parent_workflow,
        )

        return workflow

    def _create_workflow_type(self, problem: str) -> WorkflowType:
        """Create a workflow type for the problem."""
        # Simple workflow type creation - only custom fields needed
        # Default workflow fields (name, composed_function, metadata) are added automatically
        return WorkflowType(
            name=f"IterativeWorkflow_{hash(problem) % 10000}",
            fields={},  # No custom fields needed
            field_order=[],  # No custom field order needed
            docstring=f"Iterative workflow for solving: {problem}",
        )

    def _create_base_case_workflow(self, problem: str, context: ProblemContext) -> WorkflowInstance:
        """Create a workflow for base cases (max iterations reached)."""

        # Create a simple output function
        base_function = self._create_base_case_function(problem, context)

        # Get parent workflow if this is a recursive call
        parent_workflow = getattr(context, "workflow_instance", None)

        # Create workflow instance with simplified fields
        workflow = WorkflowInstance(
            struct_type=self._create_workflow_type(problem),
            values={
                "composed_function": base_function,
                "name": f"BaseCaseIterativeWorkflow_{hash(problem) % 10000}",
            },
            parent_workflow=parent_workflow,
        )

        return workflow

    def _create_base_case_function(self, problem: str, context: ProblemContext):
        """Create a simple function for base cases."""

        def base_case_function(*args, **kwargs):
            return f"Base case reached for: {problem}. Maximum iterations ({self.max_iterations}) exceeded."

        return base_case_function
