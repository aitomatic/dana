"""
Agent Solving Implementation

This module contains the implementation methods for agent solving
functionality, including plan routing and problem analysis.
"""

from typing import Any, Union

import yaml

from dana.builtin_types.workflow_system import WorkflowInstance, WorkflowType
from dana.core.lang.sandbox_context import SandboxContext

from .agent_enums import PlanType, parse_plan_type

# Type aliases for better readability
PlanDict = dict[str, str]
ProblemContext = dict[str, Any] | None


class AgentSolvingMixin:
    """Mixin class providing solving implementation methods."""

    # ============================================================================
    # CORE SOLVING METHODS (Most Significant)
    # ============================================================================

    def _create_plan(
        self, task: str, context: ProblemContext = None, sandbox_context: SandboxContext | None = None
    ) -> Union[PlanDict, str, WorkflowInstance]:
        """Analyze problem and determine the best plan using agent reasoning.

        Called by: default_plan_method (via agent_methods.py)
        """

        self.debug(f"PLAN: Analyzing problem: '{task}'")

        # Analysis prompt that asks LLM to provide actual solutions
        analysis_prompt = f"""```yaml
content: |
  You are an AI agent specialized in problem analysis and solution planning.
  Analyze the given problem and determine the best plan.

task:
  problem: "{task}"
  context: {context}

requirements:
  - Choose the best plan from: DIRECT_SOLUTION, PYTHON_CODE, WORKFLOW, DELEGATE, ESCALATE
  - Provide the actual solution, code, or action
  - Return response in YAML format

plan_types:
  DIRECT_SOLUTION: For simple problems (arithmetic, facts, calculations) - provide direct answer
  PYTHON_CODE: For problems needing code generation - provide complete, executable Python code
  WORKFLOW: For complex processes requiring multiple steps - provide workflow definition
  DELEGATE: For problems needing specialized agents - specify which agent should handle this
  ESCALATE: For problems too complex for current capabilities - explain why human intervention needed

response_format:
  plan: PLAN_TYPE
  confidence: 0.95
  reasoning: Why this plan is best for this problem
  solution: The actual solution, code, or action
  details:
    complexity: SIMPLE|MODERATE|COMPLEX|CRITICAL
    estimated_duration: immediate|minutes|hours|days
    required_resources: [list, of, resources]
    risks: Any potential risks or limitations

configuration:
  format: yaml
  temperature: 0.7
  max_tokens: 1000
```"""

        analysis = self.reason(analysis_prompt, {"problem": task, "context": context}, sandbox_context, is_sync=True)
        self.debug(f"PLAN: Analysis result: {analysis}")

        plan = self._parse_analysis(analysis, task, context, sandbox_context)
        self.debug(f"PLAN: Determined plan: {type(plan).__name__}")

        return plan

    def _solve_problem(self, sandbox_context: SandboxContext, problem: str, context: ProblemContext = None) -> str:
        """Execute problem solving using plan routing pattern: plan -> execute.

        Called by: default_solve_method (via agent_methods.py)
        """

        self.debug(f"SOLVE: Starting plan routing for: '{problem}'")

        # Step 1: Plan - determine the best plan
        plan = self.plan(problem, context, sandbox_context, is_sync=True)
        self.debug(f"PLAN: Got plan: {type(plan).__name__}")

        # Step 2: Execute - run the determined plan
        result = self._execute_plan(plan, problem, context, sandbox_context)
        self.debug("SOLVE: Plan execution completed")
        return result

    def _execute_plan(
        self,
        plan: Union[PlanDict, str, WorkflowInstance, None],
        problem: str,
        context: ProblemContext = None,
        sandbox_context: SandboxContext | None = None,
    ) -> str:
        """Execute different types of plans based on plan type.

        Called by: _solve_problem
        """

        # Handle None plan
        if plan is None:
            self.debug("EXECUTE_PLAN: No plan returned, using direct solution")
            return self._solve_direct(problem, context, sandbox_context)

        # Handle string plans
        if isinstance(plan, str):
            # Check if it's a delegation or escalation string
            if plan.startswith("agent:") or plan == PlanType.ESCALATE.value:
                return self._route_string(plan, problem, context)
            else:
                # This is a direct solution from the LLM
                self.debug("EXECUTE_PLAN: Using direct solution from LLM")
                return plan

        # Handle workflow plans
        if hasattr(plan, "execute") and callable(plan.execute):
            self.debug("EXECUTE_PLAN: Executing workflow")
            return self._execute_workflow(plan, problem, context, sandbox_context)

        # Handle dict plans
        if isinstance(plan, dict):
            return self._route_dict(plan, problem, context, sandbox_context)

        # Handle other types as direct plans
        self.debug("EXECUTE_PLAN: Treating as direct solution")
        return self._solve_direct(problem, context, sandbox_context)

    # ============================================================================
    # ANALYSIS & PLAN CREATION
    # ============================================================================

    def _parse_analysis(
        self, analysis: str, problem: str, context: ProblemContext = None, sandbox_context: SandboxContext | None = None
    ) -> Union[PlanDict, str, WorkflowInstance]:
        """Convert analysis result into an appropriate plan object.

        Called by: _create_plan
        """

        self.debug("ANALYSIS: Converting analysis to plan")

        # Extract and parse YAML content
        try:
            yaml_content = self._extract_yaml_content(str(analysis))
            parsed_analysis = yaml.safe_load(yaml_content)
            plan_str = parsed_analysis.get("plan", "")
            self.debug(f"ANALYSIS: Parsed YAML response: {parsed_analysis}")
        except Exception as e:
            self.debug(f"ANALYSIS: YAML parsing failed, using fallback: {e}")
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

        self.info(f"ANALYSIS: Parsed plan type: {plan_type}")
        self.info(f"ANALYSIS: Confidence: {confidence}")
        self.info(f"ANALYSIS: Reasoning: {reasoning[:100]}...")
        self.info(f"ANALYSIS: Complexity: {details.get('complexity', 'UNKNOWN')}")
        self.info(f"ANALYSIS: Estimated duration: {details.get('estimated_duration', 'UNKNOWN')}")
        self.info(f"ANALYSIS: Extracted solution: {solution[:100]}...")

        # Route to appropriate plan handler based on type
        # TODO: This is where we need to add the plan type to the plan
        return self._complete_plan(plan_type, solution, problem)

    def _complete_plan(self, plan_type: PlanType, solution: str, problem: str) -> Union[PlanDict, str, WorkflowInstance]:
        """Create appropriate plan object based on plan type.

        Called by: _parse_analysis
        """

        self.debug(f"ANALYSIS: Creating {plan_type.value} plan")

        if plan_type == PlanType.DIRECT_SOLUTION:
            # LLM already provided the solution, use it directly
            if solution and solution.strip():
                return solution  # Return the solution directly

        elif plan_type == PlanType.PYTHON_CODE:
            # LLM already provided the code, use it directly
            if solution and solution.strip():
                # Clean up the solution by removing code block markers
                cleaned_solution = self._clean_code_block(solution)
                return {"type": PlanType.PYTHON_CODE.value, "content": cleaned_solution}

        elif plan_type == PlanType.WORKFLOW:
            if solution:
                return {"type": PlanType.WORKFLOW.value, "content": solution}
            else:
                workflow_type = self._create_workflow_type(problem)
                return WorkflowInstance(workflow_type, {})

        elif plan_type == PlanType.DELEGATE:
            return solution if solution else "agent:specialist"

        elif plan_type == PlanType.ESCALATE:
            return solution if solution else plan_type.value

        # Fail-over to direct solution
        self.debug("ANALYSIS: Default to direct solution")
        if solution and solution.strip():
            return solution  # Use LLM's solution directly
        else:
            return {"type": PlanType.DIRECT_SOLUTION.value, "content": "Default handling"}

    # ============================================================================
    # PLAN EXECUTION - SPECIFIC HANDLERS
    # ============================================================================

    def _solve_direct(self, problem: str, context: ProblemContext = None, sandbox_context: SandboxContext | None = None) -> str:
        """Fallback handler for direct problem solving using agent reasoning.

        Called by: _execute_plan, _route_string, _route_dict
        """
        self.debug(f"Using direct reasoning for: '{problem}'")

        # Safely serialize context for YAML
        context_str = "{}"
        if context is not None:
            try:
                # Convert context to a serializable format
                if hasattr(context, "__dict__"):
                    context_str = str(context.__dict__)
                else:
                    context_str = str(context)
            except Exception:
                context_str = "{}"

        # Create YAML-formatted prompt for direct solving
        direct_prompt = f"""```yaml
content: |
  You are an AI agent solving problems directly.
  Provide a clear, actionable solution to the given problem.

task:
  problem: "{problem}"
  context: {context_str}

configuration:
  format: yaml
  temperature: 0.7
  max_tokens: 800
```"""

        solution = self.reason(direct_prompt, context, sandbox_context, is_sync=True)
        return f"Direct solution: {solution}"

    def _execute_python(
        self, plan: PlanDict, problem: str, context: ProblemContext = None, sandbox_context: SandboxContext | None = None
    ) -> str:
        """Handle python code execution plan.

        Called by: _execute_plan
        """
        self.debug(f"PYTHON_CODE: Executing Python code for: '{problem}'")

        python_code = plan.get("content", "")
        if not python_code:
            return f"No code provided for '{problem}'"

        try:
            # Use the coding resource to execute Python code
            from dana.common.sys_resource.coding.coding_resource import CodingResource

            # Create a coding resource instance
            coding_resource = CodingResource()

            # Execute the Python code
            result = coding_resource._execute_python_code(python_code, timeout=30)

            return result

        except Exception as e:
            self.debug(f"PYTHON_CODE: Execution failed: {e}")
            return f"Python code execution failed for '{problem}': {str(e)}\n\nCode was:\n{python_code}"

    def _execute_workflow(
        self,
        workflow: Union[WorkflowInstance, PlanDict],
        problem: str,
        context: ProblemContext = None,
        sandbox_context: SandboxContext | None = None,
    ) -> str:
        """Handle workflow execution plan.

        Called by: _execute_plan, _route_dict
        """
        self.debug(f"WORKFLOW: Executing workflow for: '{problem}'")

        try:
            # Prepare workflow data
            workflow_data = {"problem": problem, "context": context or {}, "agent": self}

            # Execute the workflow
            if hasattr(workflow, "execute") and callable(workflow.execute):
                result = workflow.execute(workflow_data)
                return f"Workflow execution completed for '{problem}': {result}"
            else:
                return f"Workflow plan for '{problem}' (workflow object: {type(workflow).__name__})"

        except Exception as e:
            return f"Workflow execution failed for '{problem}': {str(e)}"

    def _delegate_to_agent(self, agent_id: str, problem: str, context: ProblemContext = None) -> str:
        """Handle agent delegation plan.

        Called by: _route_string
        """
        self.debug(f"DELEGATE: Delegating to agent: {agent_id}")

        # Extract agent name from "agent:name" format
        agent_name = agent_id.replace("agent:", "")
        return f"Delegated problem '{problem}' to agent: {agent_name}"

    def _escalate_to_human(self, problem: str, context: ProblemContext = None) -> str:
        """Handle escalation to human plan.

        Called by: _route_string
        """
        self.debug(f"ESCALATE: Escalating to human: '{problem}'")

        return f"Problem '{problem}' escalated to human for manual intervention"

    # ============================================================================
    # PLAN EXECUTION - HELPERS
    # ============================================================================

    def _route_string(self, plan: str, problem: str, context: ProblemContext) -> str:
        """Route string-based plans (escalate, delegate, or direct).

        Called by: _execute_plan
        """
        if plan == PlanType.ESCALATE.value:
            return self._escalate_to_human(problem, context)
        elif plan.startswith("agent:"):
            return self._delegate_to_agent(plan, problem, context)
        else:
            return self._solve_direct(problem, context, None)

    def _route_dict(self, plan: PlanDict, problem: str, context: ProblemContext, sandbox_context: SandboxContext | None = None) -> str:
        """Route dictionary-based plans.

        Called by: _execute_plan
        """
        plan_type = plan.get("type", "unknown").lower()  # Normalize to lowercase
        content = plan.get("content", "")

        from dana.builtin_types.agent.agent_enums import PlanType

        if plan_type == PlanType.PYTHON_CODE.value.lower() and content:
            return self._execute_python(plan, problem, context, sandbox_context)
        elif plan_type == PlanType.WORKFLOW.value.lower():
            if content:
                return f"Workflow solution for '{problem}': {content}"
            else:
                return self._execute_workflow(plan, problem, context, sandbox_context)
        elif plan_type in ["direct_solution", "solution"]:
            if content and content not in ["Handle directly", "Default handling"]:
                return content
            else:
                return self._solve_direct(problem, context, sandbox_context)
        else:
            return self._solve_direct(problem, context, sandbox_context)

    # ============================================================================
    # UTILITIES
    # ============================================================================

    def _create_workflow_type(self, problem: str) -> WorkflowType:
        """Create a workflow type based on problem keywords.

        Called by: _create_plan
        """
        self.debug(f"Creating workflow type for: '{problem}'")

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
                self.debug(f"Detected {name} keywords")
                break
        else:
            name = "GenericWorkflow"
            docstring = "Generic workflow for problem solving"
            self.debug("No specific keywords detected, using generic workflow")

        # Create workflow type with standard fields
        fields = {"name": "str", "fsm": "str"}
        field_order = ["name", "fsm"]

        return WorkflowType(name=name, fields=fields, field_order=field_order, docstring=docstring)

    def _extract_yaml_content(self, text: str) -> str:
        """Extract YAML content from text, handling code block wrappers.

        Called by: _parse_analysis
        """
        if "```yaml" in text:
            # Split on ```yaml and get everything after it
            parts = text.split("```yaml", 1)
            if len(parts) > 1:
                content = parts[1]
                # Find the last ``` to get the complete YAML block
                if "```" in content:
                    # Split on all ``` and take everything except the last part
                    yaml_parts = content.split("```")
                    if len(yaml_parts) > 1:
                        # Join all parts except the last (empty) one
                        return "```".join(yaml_parts[:-1]).strip()
                return content.strip()
        elif "```" in text:
            # Split on ``` and get everything after it
            parts = text.split("```", 1)
            if len(parts) > 1:
                content = parts[1]
                # Find the last ``` to get the complete block
                if "```" in content:
                    block_parts = content.split("```")
                    if len(block_parts) > 1:
                        # Join all parts except the last (empty) one
                        return "```".join(block_parts[:-1]).strip()
                return content.strip()
        return text.strip()

    def _clean_code_block(self, code: str) -> str:
        """Remove code block markers from code string.

        Called by: _complete_plan
        """
        # Remove ```python, ```py, ```, etc. from the beginning
        lines = code.strip().split("\n")
        if lines and lines[0].startswith("```"):
            lines = lines[1:]

        # Remove trailing ``` if present
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        return "\n".join(lines).strip()
