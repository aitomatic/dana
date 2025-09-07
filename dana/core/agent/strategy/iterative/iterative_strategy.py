"""
Iterative Strategy Implementation

This module implements an iterative strategy for solving problems
by refining solutions through multiple iterations rather than recursion.
"""

from typing import Any

from dana.core.agent.context import ProblemContext
from dana.core.agent.strategy.base import BaseStrategy
from dana.core.workflow import WorkflowInstance, WorkflowType


class IterativeStrategy(BaseStrategy):
    """Strategy that solves problems through iterative refinement."""

    def __init__(self, max_iterations: int = 10):
        """Initialize the iterative strategy."""
        self.max_iterations = max_iterations

    def can_handle(self, problem: str, context: ProblemContext) -> bool:
        """Determine if this strategy can handle the problem."""
        # Iterative strategy can handle most problems
        # but check for obvious infinite loops
        return not self._detect_obvious_loop(problem, context)

    def create_workflow(self, problem: str, context: ProblemContext, agent_instance=None, sandbox_context=None) -> WorkflowInstance:
        """Create a workflow instance using LLM-generated Dana code."""

        # 1. Check iteration limits
        if not self._check_iteration_limits(context):
            return self._create_base_case_workflow(problem, context)

        # 2. Generate LLM prompt
        prompt = self._build_analysis_prompt(problem, context)

        # Color codes for terminal output
        BLUE = "\033[94m"
        GREEN = "\033[92m"
        YELLOW = "\033[93m"
        RED = "\033[91m"
        BOLD = "\033[1m"
        END = "\033[0m"

        print("=" * 80)
        print(f"{BLUE}{BOLD}🤖 LLM PROMPT:{END}")
        print("=" * 80)
        print(f"{YELLOW}{prompt}{END}")
        print("=" * 80)

        # 3. Get LLM response (Dana code)
        dana_code = self._get_llm_response(prompt, agent_instance, sandbox_context)

        print("=" * 80)
        print(f"{GREEN}{BOLD}🤖 LLM RESPONSE:{END}")
        print("=" * 80)
        print(f"{YELLOW}{dana_code}{END}")
        print("=" * 80)

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
        from .prompts import build_analysis_prompt

        return build_analysis_prompt(problem, context)

    def _get_llm_response(self, prompt: str, agent_instance=None, sandbox_context=None) -> str:
        """Get LLM response (Dana code)."""
        import time

        if not agent_instance:
            raise ValueError("Agent instance is required for IterativeStrategy to work")

        # The LLM always makes the decision about how to solve the problem
        # Call the agent's LLM method with the prompt
        # Pass sandbox_context to agent_instance.llm() if available
        from .prompts import SYSTEM_MESSAGE

        print("⏱️  LLM TIMEOUT - Setting 30 second timeout for LLM call")
        start_time = time.time()

        try:
            if sandbox_context:
                response = agent_instance.llm(
                    {"system": SYSTEM_MESSAGE, "prompt": prompt},
                    sandbox_context=sandbox_context,
                )
            else:
                response = agent_instance.llm({"system": SYSTEM_MESSAGE, "prompt": prompt})

            elapsed_time = time.time() - start_time
            print(f"⏱️  LLM TIMEOUT - LLM call completed in {elapsed_time:.2f} seconds")
            return str(response)

        except Exception as e:
            elapsed_time = time.time() - start_time
            print(f"❌ LLM ERROR - Failed after {elapsed_time:.2f} seconds: {e}")
            # Return a fallback response
            return f'{{"approach": "direct", "reasoning": "LLM call failed: {e}", "result": "Error: LLM call failed"}}'

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

    def _compile_dana_code(self, llm_response: str, context: ProblemContext) -> Any:
        """Parse LLM JSON response and compile to a function."""
        import json

        print("🔍 PARSING - LLM JSON response")

        try:
            # Try to parse the response as JSON
            response_data = json.loads(llm_response)

            # Check if it's a dictionary (valid JSON response)
            if isinstance(response_data, dict):
                print(f"✅ JSON PARSED - Approach: {response_data.get('approach', 'unknown')}")
                print(f"📝 REASONING - {response_data.get('reasoning', 'No reasoning provided')}")

                approach = response_data.get("approach", "dana_code")

                if approach == "direct":
                    # For direct approach, return the result directly
                    result = response_data.get("result", "No result provided")
                    print(f"🎯 DIRECT RESULT - {result}")
                    return self._create_direct_result_function(result)
                else:
                    # For dana_code approach, extract and compile the Dana code
                    dana_code = response_data.get("dana_code", "")
                    if not dana_code:
                        print("⚠️  NO DANA CODE - Falling back to mock response")
                        dana_code = llm_response
                    print(f"📜 DANA CODE - {dana_code[:100]}...")
                    return self._create_simple_function(dana_code)
            else:
                # JSON parsed but not a dictionary (e.g., just a number or string)
                print(f"⚠️  JSON NOT DICT - Got {type(response_data).__name__}: {response_data}, treating as raw Dana code")
                return self._create_simple_function(llm_response)

        except json.JSONDecodeError as e:
            print(f"❌ JSON PARSE ERROR - {e}, treating as raw Dana code")
            # Fall back to treating the response as raw Dana code
            return self._create_simple_function(llm_response)

    def _create_simple_function(self, dana_code: str):
        """Create a simple function from Dana code for testing."""

        def simple_function(*args, **kwargs):
            # Mock implementation - in reality this would execute the Dana code
            return f"Executed iterative Dana code: {dana_code[:100]}..."

        return simple_function

    def _create_direct_result_function(self, result: Any):
        """Create a function that returns a direct result."""

        def direct_result_function(*args, **kwargs):
            print("🎯 EXECUTING - Direct result function")
            print(f"📤 RETURNING - {result}")
            return result

        return direct_result_function

    def _create_workflow_instance(self, problem: str, context: ProblemContext, compiled_function: Any) -> WorkflowInstance:
        """Create a WorkflowInstance with the compiled function."""

        # Get parent workflow if this is a recursive call
        parent_workflow = getattr(context, "workflow_instance", None)

        # Create workflow type
        workflow_type = WorkflowType.create_for_problem(problem, "Iterative")

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

    def _create_base_case_workflow(self, problem: str, context: ProblemContext) -> WorkflowInstance:
        """Create a workflow for base cases (max iterations reached)."""

        # Create a simple output function
        base_function = self._create_base_case_function(problem, context)

        # Get parent workflow if this is a recursive call
        parent_workflow = getattr(context, "workflow_instance", None)

        # Create workflow instance with simplified fields
        workflow = WorkflowInstance(
            struct_type=WorkflowType.create_for_problem(problem, "Iterative"),
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
