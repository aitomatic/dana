"""
Plan-Then-Execute Strategy Implementation

This strategy implements the current approach where the agent:
1. Plans the solution using LLM reasoning
2. Executes based on the determined plan type
"""

from typing import Any, Union

import yaml

from dana.builtin_types.agent.agent_instance import AgentInstance
from dana.builtin_types.workflow.workflow_system import WorkflowInstance, WorkflowType
from dana.core.lang.sandbox_context import SandboxContext

from ..base import BaseStrategy
from ..enums import PlanType, parse_plan_type
from ..plan import StrategyPlan
from .prompts import (
    clean_code_block,
    create_analysis_prompt,
    create_manual_solution_prompt,
    default_system_message,
    extract_yaml_content,
)

# Type aliases for better readability
PlanDict = dict[str, PlanType | str]
ProblemContext = dict[str, Any] | None


class PlannerStrategy(BaseStrategy):
    """Strategy that plans first, then executes based on plan type."""

    def __init__(self):
        """Initialize the planner strategy."""
        self._name = "planner"

    @property
    def name(self) -> str:
        """Strategy identifier."""
        return self._name

    def can_handle(self, problem: str, context: dict[str, Any] | None = None) -> float:
        """Return confidence score for handling this problem."""
        # This strategy can handle most problems, but may not be optimal for all
        is_experimental = True
        return 1.0 if is_experimental else 0.7

    def create_plan(
        self,
        agent_instance: AgentInstance,
        problem: str,
        sandbox_context: SandboxContext | None = None,
        problem_context: dict[str, Any] | None = None,
    ) -> StrategyPlan:
        """Create a plan that supports all current return types."""
        plan_data = self._create_plan(agent_instance, problem, sandbox_context, problem_context)

        # Determine plan type from content
        if isinstance(plan_data, dict):
            plan_type = plan_data.get("type", PlanType.MANUAL)
            if isinstance(plan_type, str):
                plan_type = PlanType(plan_type)
        elif isinstance(plan_data, str):
            plan_type = parse_plan_type(plan_data)
        else:
            plan_type = PlanType.MANUAL

        # Extract metadata
        metadata = self._extract_plan_metadata(plan_data, problem, problem_context)

        return StrategyPlan(
            strategy_name=self.name,
            confidence=self.can_handle(problem, problem_context),
            plan_type=plan_type,  # type: ignore
            content=plan_data,
            reasoning=metadata.get("reasoning", ""),
            complexity=metadata.get("complexity", "moderate"),
            estimated_duration=metadata.get("estimated_duration", "unknown"),
            metadata=metadata,
        )

    def execute_plan(
        self,
        agent_instance: AgentInstance,
        plan: StrategyPlan,
        problem: str,
        sandbox_context: SandboxContext | None = None,
        problem_context: dict[str, Any] | None = None,
    ) -> Any:
        """Execute a plan using the existing execution logic."""
        return self._execute_plan(agent_instance, plan.content, problem, sandbox_context, problem_context)

    def _deprecated_determine_plan_type(self, plan_data: Any) -> PlanType:
        """Determine plan type from the plan data."""
        if plan_data is None:
            return PlanType.MANUAL
        elif isinstance(plan_data, str):
            if plan_data.startswith("agent:"):
                return PlanType.DELEGATE
            elif plan_data == "TYPE_ESCALATE":
                return PlanType.ESCALATE
            else:
                return PlanType.DIRECT
        elif isinstance(plan_data, dict):
            plan_type_str = plan_data.get("type", "").lower()
            if "code" in plan_type_str:
                return PlanType.CODE
            elif "workflow" in plan_type_str:
                return PlanType.WORKFLOW
            else:
                return PlanType.DIRECT
        elif hasattr(plan_data, "execute"):
            return PlanType.WORKFLOW
        elif hasattr(plan_data, "input"):
            return PlanType.INPUT
        else:
            return PlanType.MANUAL

    def _extract_plan_metadata(self, plan_data: Any, problem: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Extract metadata from plan data."""
        metadata = {}

        if isinstance(plan_data, dict):
            metadata.update(
                {
                    "reasoning": plan_data.get("reasoning", ""),
                    "complexity": plan_data.get("complexity", "moderate"),
                    "estimated_duration": plan_data.get("estimated_duration", "unknown"),
                    "confidence": plan_data.get("confidence", 0.0),
                    "details": plan_data.get("details", {}),
                }
            )
        elif isinstance(plan_data, str):
            # For string plans, try to extract basic metadata
            if plan_data.startswith("agent:"):
                metadata["reasoning"] = f"Delegating to specialist agent: {plan_data}"
                metadata["complexity"] = "moderate"
            elif plan_data == "TYPE_ESCALATE":
                metadata["reasoning"] = "Escalating to human intervention"
                metadata["complexity"] = "critical"
            else:
                metadata["reasoning"] = "Direct solution provided"
                metadata["complexity"] = "simple"

        return metadata

    # ============================================================================
    # CORE SOLVING METHODS (Most Significant)
    # ============================================================================

    def _create_plan(
        self,
        agent_instance: AgentInstance,
        task: str,
        sandbox_context: SandboxContext | None = None,
        problem_context: ProblemContext = None,
    ) -> Union[PlanDict, str, WorkflowInstance]:
        """Analyze problem and determine the best plan using agent reasoning.

        Called by: create_plan method
        """

        agent_instance.debug(f"PLAN: Analyzing problem: '{task}'")

        # Use the centralized prompt template
        analysis_prompt = create_analysis_prompt(task, problem_context)

        # Use the agent's reason method
        for _ in range(3):  # try 3 times to get a valid plan
            analysis = agent_instance.reason(
                analysis_prompt, sandbox_context, {"problem": task, "context": problem_context}, default_system_message, is_sync=True
            )
            agent_instance.error(f"CTN PLAN: Analysis result: {analysis}")

            plan = self._parse_analysis(agent_instance, analysis, task, sandbox_context, problem_context)
            if plan is not None:
                break

        agent_instance.debug(f"PLAN: Determined plan: {type(plan).__name__}")

        return plan

    def _execute_plan(
        self,
        agent_instance: AgentInstance,
        plan: Union[PlanDict, str, WorkflowInstance, None],
        problem: str,
        sandbox_context: SandboxContext | None = None,
        problem_context: ProblemContext = None,
    ) -> str:
        """Execute different types of plans based on plan type.

        Called by: execute_plan method
        """

        # Handle None plan
        if plan is None:
            agent_instance.debug("EXECUTE_PLAN: No plan returned, using direct solution")
            return self._solve_manually(agent_instance, problem, sandbox_context, problem_context)

        # Handle string plans
        if isinstance(plan, str):
            # Check if it's a delegation or escalation string
            if plan.startswith("agent:") or plan == "TYPE_ESCALATE":
                return self._route_string(agent_instance, plan, problem, problem_context)
            else:
                # This is a direct solution from the LLM
                agent_instance.debug("EXECUTE_PLAN: Using direct solution from LLM")
                return plan

        # Handle workflow plans
        if hasattr(plan, "execute") and callable(plan.execute):
            agent_instance.debug("EXECUTE_PLAN: Executing workflow")
            return self._execute_workflow(agent_instance, plan, problem, sandbox_context, problem_context)

        # Handle dict plans
        if isinstance(plan, dict):
            agent_instance.debug(f"EXECUTE_PLAN: Routing dict plan with keys: {list(plan.keys())}")
            return self._route_dict(agent_instance, plan, problem, sandbox_context, problem_context)

        # Handle other types "manually"
        agent_instance.debug("EXECUTE_PLAN: Treating as manual solution")
        return self._solve_manually(agent_instance, problem, sandbox_context, problem_context)

    # ============================================================================
    # ANALYSIS & PLAN CREATION
    # ============================================================================

    def _parse_analysis(
        self,
        agent_instance: AgentInstance,
        analysis: str,
        problem: str,
        sandbox_context: SandboxContext | None = None,
        problem_context: ProblemContext = None,
    ) -> Union[PlanDict, str, WorkflowInstance]:
        """Convert analysis result into an appropriate plan object.

        Called by: _create_plan
        """

        agent_instance.debug("ANALYSIS: Converting analysis to plan")

        # Extract and parse YAML content
        try:
            yaml_content = extract_yaml_content(str(analysis))
            agent_instance.debug(f"ANALYSIS: Extracted YAML content: {repr(yaml_content)}")
            parsed_analysis = yaml.safe_load(yaml_content)
            plan_str = parsed_analysis.get("plan", "")
            agent_instance.debug(f"ANALYSIS: Parsed YAML response: {parsed_analysis}")
            agent_instance.debug(f"ANALYSIS: Raw solution field: {repr(parsed_analysis.get('solution', ''))}")
        except Exception as e:
            agent_instance.debug(f"ANALYSIS: YAML parsing failed, using fallback: {e}")
            plan_str = str(analysis)
            parsed_analysis = {}

        # Parse plan type and extract solution
        plan_type = parse_plan_type(plan_str)
        solution = parsed_analysis.get("solution", "") if isinstance(parsed_analysis, dict) else ""
        solution = str(solution)

        # Extract additional metadata for logging
        confidence = parsed_analysis.get("confidence", 0.0) if isinstance(parsed_analysis, dict) else 0.0
        reasoning = parsed_analysis.get("reasoning", "") if isinstance(parsed_analysis, dict) else ""
        details = parsed_analysis.get("details", {}) if isinstance(parsed_analysis, dict) else {}

        agent_instance.info(f"ANALYSIS: Parsed plan type: {plan_type}")
        agent_instance.info(f"ANALYSIS: Confidence: {confidence}")
        agent_instance.info(f"ANALYSIS: Reasoning: {reasoning[:100]}...")
        agent_instance.info(f"ANALYSIS: Complexity: {details.get('complexity', 'UNKNOWN')}")
        agent_instance.info(f"ANALYSIS: Estimated duration: {details.get('estimated_duration', 'UNKNOWN')}")
        agent_instance.info(f"ANALYSIS: Extracted solution: {solution[:100]}...")

        # Route to appropriate plan handler based on type
        return self._complete_plan(agent_instance, plan_type, solution, problem, parsed_analysis or {})

    def _complete_plan(
        self, agent_instance: AgentInstance, plan_type: PlanType, solution: str, problem: str, metadata: dict | None = None
    ) -> Union[PlanDict, str, WorkflowInstance]:
        """Create appropriate plan object based on plan type.

        Called by: _parse_analysis
        """

        agent_instance.debug(f"ANALYSIS: Creating {plan_type.value} plan")

        if isinstance(solution, str):
            solution = solution.strip()

        if plan_type == PlanType.DIRECT:
            # LLM already provided the solution, use it directly
            if solution:
                return solution  # Return the solution directly

        elif plan_type == PlanType.CODE:
            # LLM already provided the code, use it directly
            if solution:
                # Clean up the solution by removing code block markers
                cleaned_solution = clean_code_block(solution)
                agent_instance.debug(f"COMPLETE_PLAN: Creating CODE plan with content length: {len(cleaned_solution)}")
                agent_instance.debug(f"COMPLETE_PLAN: Cleaned solution preview: {cleaned_solution[:100]}...")
                return {"type": PlanType.CODE, "content": cleaned_solution}

        elif plan_type == PlanType.INPUT:
            return {"type": PlanType.INPUT, "content": solution}

        elif plan_type == PlanType.WORKFLOW:
            if solution:
                # Try to parse workflow from LLM output
                try:
                    from dana.builtin_types.workflow.factory import WorkflowFactory

                    factory = WorkflowFactory()
                    workflow_instance = factory.create_from_yaml(solution)
                    return workflow_instance
                except Exception as e:
                    agent_instance.error(f"Failed to parse workflow from LLM output: {e}")
                    # Fallback to simple workflow dict
                    # return {"type": PlanType.WORKFLOW, "content": solution}
                    # Return None so caller can retry
                    return None  # type: ignore
            else:
                workflow_type = self._create_workflow_type(agent_instance, problem)
                return WorkflowInstance(workflow_type, {})

        elif plan_type == PlanType.DELEGATE:
            return {"type": PlanType.DELEGATE, "content": solution}

        elif plan_type == PlanType.ESCALATE:
            return {"type": PlanType.ESCALATE, "content": solution}

        # Fail-over to manual solution
        agent_instance.debug("ANALYSIS: Default to 'manual' solution")
        if solution:
            return solution  # Use LLM's solution directly, whatever it is
        else:
            return {"type": PlanType.MANUAL, "content": "Manual handling"}

    # ============================================================================
    # PLAN EXECUTION - SPECIFIC HANDLERS
    # ============================================================================

    def _solve_manually(
        self,
        agent_instance: AgentInstance,
        problem: str,
        sandbox_context: SandboxContext | None = None,
        problem_context: ProblemContext = None,
    ) -> str:
        """Fallback handler for direct problem solving using agent reasoning.

        Called by: _execute_plan, _route_string, _route_dict
        """
        agent_instance.debug(f"Using direct reasoning for: '{problem}'")

        # Safely serialize context for YAML
        context_str = "{}"
        if problem_context is not None:
            try:
                # Convert context to a serializable format
                if hasattr(problem_context, "__dict__"):
                    context_str = str(problem_context.__dict__)
                else:
                    context_str = str(problem_context)
            except Exception:
                context_str = "{}"

        # Use the centralized prompt template
        manual_prompt = create_manual_solution_prompt(problem, context_str)

        solution = agent_instance.reason(manual_prompt, sandbox_context, problem_context, default_system_message)
        return f"Manual solution: {solution}"

    def _execute_python(
        self,
        agent_instance: AgentInstance,
        plan: PlanDict,
        problem: str,
        sandbox_context: SandboxContext | None = None,
        problem_context: ProblemContext = None,
    ) -> str:
        """Handle python code execution plan.

        Called by: _execute_plan
        """
        agent_instance.debug(f"TYPE_CODE: Executing Python code for: '{problem}'")

        python_code = plan.get("content", "")
        if not python_code:
            return f"No code provided for '{problem}'"

        try:
            # Use the coding resource to execute Python code
            from dana.common.sys_resource.coding.coding_resource import CodingResource

            # Create a coding resource instance
            coding_resource = CodingResource()

            # Execute the Python code
            result = coding_resource._execute_python_code(python_code, timeout=30)  # type: ignore

            return result

        except Exception as e:
            agent_instance.debug(f"TYPE_CODE: Execution failed: {e}")
            return f"Python code execution failed for '{problem}': {str(e)}\n\nCode was:\n{python_code}"

    def _execute_workflow(
        self,
        agent_instance: AgentInstance,
        workflow: Union[WorkflowInstance, PlanDict],
        problem: str,
        sandbox_context: SandboxContext | None = None,
        problem_context: ProblemContext = None,
    ) -> str:
        """Handle workflow execution plan.

        Called by: _execute_plan, _route_dict
        """
        agent_instance.debug(f"WORKFLOW: Executing workflow for: '{problem}'")

        try:
            # Prepare workflow data
            workflow_data = {"problem": problem, "context": problem_context or {}}

            # Execute the workflow
            if hasattr(workflow, "execute") and callable(workflow.execute):
                result = workflow.execute(agent_instance, sandbox_context, workflow_data)
                return f"Workflow execution completed for '{problem}': {result}"
            else:
                return f"Workflow plan for '{problem}' (workflow object: {type(workflow).__name__})"

        except Exception as e:
            return f"Workflow execution failed for '{problem}': {str(e)}"

    def _delegate_to_agent(self, agent_instance: AgentInstance, agent_id: str, problem: str, problem_context: ProblemContext = None) -> str:
        """Handle agent delegation plan.

        Called by: _route_string
        """
        agent_instance.debug(f"DELEGATE: Delegating to agent: {agent_id}")

        # Extract agent name from "agent:name" format
        agent_name = agent_id.replace("agent:", "")
        return f"Delegated problem '{problem}' to agent: {agent_name}"

    def _input_from_user(
        self,
        agent_instance: AgentInstance,
        plan: PlanDict,
        request: str,
        sandbox_context: SandboxContext | None = None,
        problem_context: ProblemContext = None,
    ) -> str:
        """Handle user input plan.

        Called by: _route_dict
        """
        response = agent_instance.input(f"'{request}'")

        return f"User response is '{response}'"

    def _escalate_to_human(self, agent_instance: AgentInstance, problem: str, problem_context: ProblemContext = None) -> str:
        """Handle escalation to human plan.

        Called by: _route_string
        """
        agent_instance.debug(f"ESCALATE: Escalating to human: '{problem}'")

        return f"Problem '{problem}' escalated to human for manual intervention"

    # ============================================================================
    # PLAN EXECUTION - HELPERS
    # ============================================================================

    def _route_string(self, agent_instance: AgentInstance, plan: str, problem: str, problem_context: ProblemContext) -> str:
        """Route string-based plans (escalate, delegate, or direct).

        Called by: _execute_plan
        """
        if plan == "TYPE_ESCALATE":
            return self._escalate_to_human(agent_instance, problem, problem_context)
        elif plan.startswith("agent:"):
            return self._delegate_to_agent(agent_instance, plan, problem, problem_context)
        else:
            return self._solve_manually(agent_instance, problem, problem_context, None)  # type: ignore

    def _route_dict(
        self,
        agent_instance: AgentInstance,
        plan: PlanDict,
        problem: str,
        sandbox_context: SandboxContext | None = None,
        problem_context: ProblemContext = None,
    ) -> str:
        """Route dictionary-based plans.

        Called by: _execute_plan
        """
        plan_type = plan.get("type", PlanType.MANUAL)
        content = plan.get("content", "")

        agent_instance.debug(f"ROUTE_DICT: Plan type: '{plan_type}' (expected: '{PlanType.CODE.value.lower()}')")
        agent_instance.debug(f"ROUTE_DICT: Content length: {len(content)}")  # type: ignore
        agent_instance.debug(f"ROUTE_DICT: Content preview: {content[:100]}...")  # type: ignore
        agent_instance.debug(f"ROUTE_DICT: Plan keys: {list(plan.keys())}")

        if plan_type == PlanType.CODE and content:
            agent_instance.debug("ROUTE_DICT: Routing to _execute_python")
            return self._execute_python(agent_instance, plan, problem, sandbox_context, problem_context)
        elif plan_type == PlanType.INPUT and content:
            agent_instance.debug("ROUTE_DICT: Routing to _input_from_user")
            return self._input_from_user(agent_instance, plan, problem, sandbox_context, problem_context)
        elif plan_type == PlanType.WORKFLOW:
            agent_instance.debug("ROUTE_DICT: Routing to workflow")
            if content:
                # TODO: try to turn content into a workflow instance
                return f"Workflow solution for '{problem}': {content}"
            else:
                return self._execute_workflow(agent_instance, plan, problem, sandbox_context, problem_context)
        elif plan_type in ["TYPE_DIRECT", "solution"]:
            agent_instance.debug("ROUTE_DICT: Routing to direct solution")
            if content and content not in ["Handle manually", "Manual handling"]:
                return content  # type: ignore
            else:
                return self._solve_manually(agent_instance, problem, sandbox_context, problem_context)
        else:
            agent_instance.debug("ROUTE_DICT: No match found, falling back to manual solution")
            return self._solve_manually(agent_instance, problem, sandbox_context, problem_context)

    # ============================================================================
    # UTILITIES
    # ============================================================================

    def _create_workflow_type(self, agent_instance: AgentInstance, problem: str) -> WorkflowType:
        """Create a workflow type based on problem keywords.

        Called by: _create_plan
        """
        agent_instance.debug(f"Creating workflow type for: '{problem}'")

        problem_lower = problem.lower()

        # Map keywords to workflow types
        workflow_configs = {
            ("analyze", "data", "sensor"): ("DataAnalysisWorkflow", "Workflow for analyzing sensor data"),
            ("health", "check", "maintenance"): ("HealthCheckWorkflow", "Workflow for checking equipment health"),
            ("pipeline", "process"): ("PipelineWorkflow", "Workflow for data processing pipeline"),
            ("status", "equipment", "line"): ("EquipmentStatusWorkflow", "Workflow for checking equipment status"),
        }

        # Find matching workflow type
        name = docstring = None
        for keywords, (workflow_name, workflow_docstring) in workflow_configs.items():
            if any(keyword in problem_lower for keyword in keywords):
                name, docstring = workflow_name, workflow_docstring
                agent_instance.debug(f"Detected {name} keywords")
                break
        else:
            name = "GenericWorkflow"
            docstring = "Generic workflow for problem solving"
            agent_instance.debug("No specific keywords detected, using generic workflow")

        # Create workflow type with standard fields
        fields = {"name": "str", "fsm": "str"}
        field_order = ["name", "fsm"]

        return WorkflowType(name=name, fields=fields, field_order=field_order, docstring=docstring)
