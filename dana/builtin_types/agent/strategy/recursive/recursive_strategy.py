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

    def __init__(self, max_depth: int = 10):
        """Initialize the recursive strategy."""
        self.max_depth = max_depth
        self.computable_context = ComputableContext()

    def can_handle(self, problem: str, context: ProblemContext) -> bool:
        """Determine if this strategy can handle the problem."""
        # Recursive strategy can handle most problems
        # but check for obvious infinite loops
        return not self._detect_obvious_loop(problem, context)

    def create_workflow(self, problem: str, context: ProblemContext, agent_instance=None, sandbox_context=None) -> WorkflowInstance:
        """Create a workflow instance using LLM-generated Dana code."""

        print("[DEBUG] RecursiveStrategy.create_workflow() called")
        print(f"[DEBUG] problem: {problem}")
        print(f"[DEBUG] context: {context}")
        print(f"[DEBUG] agent_instance: {type(agent_instance)}")
        print(f"[DEBUG] sandbox_context: {sandbox_context}")

        # 1. Check recursion depth limits
        print("[DEBUG] Checking depth limits...")
        if not self._check_depth_limits(context):
            print("[DEBUG] Depth limit reached, creating base case workflow")
            return self._create_base_case_workflow(problem, context)

        # 2. Generate LLM prompt with rich computable context
        print("[DEBUG] Building analysis prompt...")
        prompt = self._build_enhanced_analysis_prompt(problem, context)
        print(f"[DEBUG] Built prompt: {prompt[:200]}...")

        # 3. Get LLM response (Dana code)
        print("[DEBUG] Getting LLM response...")
        dana_code = self._get_llm_response(prompt, agent_instance, sandbox_context)
        print(f"[DEBUG] LLM response: {dana_code[:200]}...")

        # 4. Validate and compile Dana code
        print("[DEBUG] Compiling Dana code...")
        compiled_function = self._compile_dana_code(dana_code, context)
        print(f"[DEBUG] Compiled function: {type(compiled_function)}")

        # 5. Create WorkflowInstance with parent reference
        print("[DEBUG] Creating workflow instance...")
        workflow = self._create_workflow_instance(problem, context, compiled_function)
        print(f"[DEBUG] Created workflow: {type(workflow)}")

        return workflow

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
        from .prompts import build_enhanced_prompt

        return build_enhanced_prompt(problem, context)

    def _build_basic_prompt(self, problem: str, context: ProblemContext) -> str:
        """Build a basic prompt when rich context is not available."""
        from .prompts import build_basic_prompt

        return build_basic_prompt(problem, context)

    def _get_llm_response(self, prompt: str, agent_instance=None, sandbox_context=None) -> str:
        """Get LLM response (Dana code)."""
        if not agent_instance:
            raise ValueError("Agent instance is required for RecursiveStrategy to work")

        # The LLM always makes the decision about how to solve the problem
        # Call the agent's LLM method with the prompt
        # Pass sandbox_context to agent_instance.llm() if available
        from .prompts import SYSTEM_MESSAGE

        if sandbox_context:
            response = agent_instance.llm({"system": SYSTEM_MESSAGE, "prompt": prompt}, sandbox_context=sandbox_context)
        else:
            response = agent_instance.llm({"system": SYSTEM_MESSAGE, "prompt": prompt})

        return str(response)

    # Mock response method removed - LLM client is required
    # def _generate_mock_response(self, prompt: str) -> str:
    #     """Generate a mock LLM response for testing."""
    #     # Simulate LLM decision-making based on problem content
    #     problem = prompt.split("PROBLEM:")[1].split("\n")[0].strip() if "PROBLEM:" in prompt else ""
    #
    #     if "trip" in problem.lower() and "mexico" in problem.lower():
    #         # Complex travel planning - needs Dana code
    #         return """
    # agent.reason("Planning a trip to Mexico requires multiple steps and research")
    # agent.reason("I'll break this down into manageable components")
    #
    # # Step 1: Research destinations
    # destinations = agent.solve("Research best cities to visit in Mexico",
    #                          "Find top tourist destinations and attractions",
    #                          workflow_instance=workflow_instance)
    #
    # # Step 2: Plan logistics
    # logistics = agent.solve("Plan travel logistics for Mexico trip",
    #                        "Book flights, hotels, transportation, and safety considerations",
    #                        workflow_instance=workflow_instance)
    #
    # # Step 3: Create itinerary
    # itinerary = agent.solve("Create detailed day-by-day itinerary for Mexico trip",
    #                        "Plan activities, schedule, and cultural experiences",
    #                        workflow_instance=workflow_instance)
    #
    # agent.output({
    #     "destinations": destinations,
    #     "logistics": logistics,
    #     "itinerary": itinerary,
    #     "summary": "Complete Mexico trip plan with destinations, logistics, and daily itinerary"
    # })
    # """
    #     elif "plan" in problem.lower() and "planning" in problem.lower():
    #         # Meta-planning - explain the planning process
    #         return """
    # agent.reason("The user wants me to explain my planning methodology")
    # agent.reason("I should demonstrate how I approach complex problem-solving")
    #
    # planning_method = {
    #     "step1": "Analyze problem complexity and requirements",
    #     "step2": "Break down into manageable sub-problems",
    #     "step3": "Research and gather information for each component",
    #     "step4": "Synthesize solutions into coherent plan",
    #     "step5": "Validate and refine the final solution"
    # }
    #
    # agent.reason(f"Here's my planning methodology: {planning_method}")
    #
    # agent.output({
    #     "planning_methodology": planning_method,
    #     "explanation": "I approach complex problems by breaking them down systematically, researching each component, and then synthesizing a comprehensive solution. This method ensures thorough coverage and manageable execution.",
    #     "example": "For trip planning, I'd research destinations, logistics, and create detailed itineraries - exactly as I demonstrated above."
    # })
    # """
    #     elif "simple" in problem.lower() or "calculate" in problem.lower():
    #         # Simple calculation - direct solution
    #         return """
    # agent.reason("This is a straightforward calculation that I can solve directly")
    # result = 42 * 2 + 10  # Example calculation
    # agent.output(result)
    # """
    #     else:
    #         # Default case - generate Dana code for execution
    #         return """
    # agent.reason("I'll solve this problem by breaking it down and executing step by step")
    # agent.reason("Let me analyze the requirements and create a solution plan")
    #
    # # Analyze the problem
    # analysis = agent.solve(f"Analyze the problem: {problem}",
    #                       "Break down requirements and identify solution approach",
    #                       workflow_instance=workflow_instance)
    #
    # # Execute the solution
    # solution = agent.solve(f"Execute solution for: {problem}",
    #                       "Implement the solution based on analysis",
    #                       workflow_instance=workflow_instance)
    #
    # agent.output({
    #     "analysis": analysis,
    #     "solution": solution,
    #     "summary": f"Solved: {problem}"
    # })
    # """

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
                print("[DEBUG] SimpleSandboxFunction.execute() called")
                print(f"[DEBUG] context: {context}")
                print(f"[DEBUG] args: {args}")
                print(f"[DEBUG] kwargs: {kwargs}")
                print(f"[DEBUG] dana_code: {self.dana_code[:200]}...")

                # Try to execute the Dana code for simple cases
                try:
                    # Clean up the Dana code - remove extra parentheses and whitespace
                    clean_code = self.dana_code.strip()

                    # Handle cases with extra parentheses like "(agent.output(4))"
                    if clean_code.startswith("(") and clean_code.endswith(")"):
                        clean_code = clean_code[1:-1].strip()

                    # For simple output statements like "agent.output(4)", extract the value
                    if clean_code.startswith("agent.output(") and clean_code.endswith(")"):
                        # Extract the content inside agent.output()
                        content = clean_code[13:-1]  # Remove "agent.output(" and ")"
                        print(f"[DEBUG] Extracted content: {content}")

                        # Try to evaluate the content (for simple expressions like "4", "15", "2+2")
                        try:
                            result = eval(content)
                            print(f"[DEBUG] Evaluated result: {result}")
                            return result
                        except Exception as eval_error:
                            print(f"[DEBUG] Could not evaluate content: {eval_error}")
                            # Fall back to returning the content as string
                            return content
                    else:
                        # For other Dana code, return as-is for now
                        # In the future, this could be a full Dana interpreter
                        return f"Executed Dana code: {self.dana_code[:100]}..."

                except Exception as e:
                    print(f"[DEBUG] Error executing Dana code: {e}")
                    # Fall back to mock implementation
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
