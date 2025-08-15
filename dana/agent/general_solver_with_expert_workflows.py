"""
General Problem Solver with Expert Workflows

This module implements the core problem-solving algorithm that intelligently routes
problems to specialized workflows and interprets results. Based on the design in
.docs/design/Agent-Problem-Solving.md
"""

from typing import Any
from types import ModuleType
from dataclasses import dataclass
import logging

from dana.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource
from dana.util.llm import from_prompts_to_request, from_response_to_content

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Prompt Templates ---

WORKFLOW_SELECTION_PROMPT_TEMPLATE = """
Given the following problem:

PROBLEM:
```
{problem}
```

And the following named expert workflows:

NAMED EXPERT WORKFLOWS:
```
{expert_workflow_names}
```

Return the name of the expert workflow that is most relevant to the problem; OR
if none of such named expert workflows is deemed relevant to the problem, return the string NONE.

!!! RETURN EITHER NONE OR ONLY THE NAME OF THE WORKFLOW AS A PURE STRING, NO OTHER TEXT, NO SURROUNDING QUOTES !!!
"""

SOLUTION_SYNTHESIS_PROMPT_TEMPLATE = """
Given the following problem:

PROBLEM:
```
{problem}
```

And the following result(s) from an expert workflow:

EXPERT WORKFLOW RESULT:
```
{workflow_result}
```

Return your best conclusion about / solution to the posed problem.
"""

SOLUTION_FORMAT_TEMPLATE = """
Problem: {problem}

Solution (using {workflow_name}):
{result}

This solution was generated using the {workflow_name} workflow with a confidence score of {score:.3f}.
"""

FALLBACK_SOLUTION_TEMPLATE = """
Problem: {problem}

No suitable expert workflows found for this problem. Available resources: {available_resources}

Consider:
1. Adding more specialized workflows for this domain
2. Providing different resources that match existing workflow requirements
3. Breaking down the problem into smaller, more specific sub-problems
"""

ERROR_SOLUTION_TEMPLATE = """
Problem: {problem}

Error during execution of {workflow_name}: {error_message}

This may be due to:
1. Missing or incompatible resources
2. Workflow implementation issues
3. Data format problems

Please check the resource requirements and try again.
"""


@dataclass
class WorkflowInfo:
    """Information about a workflow for matching and execution."""
    name: str
    description: str
    input_signature: dict[str, type]
    output_signature: dict[str, type]
    workflow_function: callable


@dataclass
class ResourceMatch:
    """Information about how well resources match workflow requirements."""
    workflow: WorkflowInfo
    score: float
    matched_resources: dict[str, Any]
    missing_resources: list[str]
    error_message: str | None = None


class GeneralProblemSolver:
    """
    General problem solver that routes problems to appropriate expert workflows.

    This implements the Resource-Aware Expertise Matching algorithm from the design document.
    """

    def __init__(self):
        self.workflows: list[WorkflowInfo] = []
        self.llm_resource = None  # Will be initialized when needed

    def register_workflow(self, workflow: WorkflowInfo) -> None:
        """Register a workflow for problem-solving."""
        self.workflows.append(workflow)
        logger.info(f"Registered workflow: {workflow.name} ({workflow.expertise_domain})")

    def discover_workflows_from_modules(self, expertise_modules: list[ModuleType]) -> None:
        """Discover and register workflows from expertise modules."""
        for module in expertise_modules:
            if hasattr(module, '__all__'):
                workflow_names = module.__all__
                for workflow_name in workflow_names:
                    if hasattr(module, workflow_name):
                        workflow_function = getattr(module, workflow_name)

                        # Create workflow info (with placeholder metadata for now)
                        workflow_info = WorkflowInfo(
                            name=workflow_name,
                            description=f"Workflow from {module.__name__}",
                            input_signature={},  # TODO: Extract from function signature
                            output_signature={},  # TODO: Extract from function signature
                            workflow_function=workflow_function
                        )

                        self.register_workflow(workflow_info)
                        logger.info(f"Discovered workflow: {workflow_name}")

    def solve(self, problem: str, expertise_modules: list[ModuleType] = None, resources: dict[str, Any] = None) -> str:
        """
        Solve a problem using available resources and expertise modules.

        Args:
            problem: Natural language description of the problem to solve
            expertise_modules: List of modules containing expert workflows
            resources: Dictionary mapping resource keys to resource objects

        Returns:
            Solution to the problem as a string
        """
        if expertise_modules is None:
            expertise_modules = []
        if resources is None:
            resources = {}

        logger.info(f"Solving problem: {problem}")
        logger.info(f"Expertise modules: {[m.__name__ for m in expertise_modules]}")
        logger.info(f"Available resources: {list(resources.keys())}")

        # Discover workflows from expertise modules
        self.discover_workflows_from_modules(expertise_modules)

        if not self.workflows:
            return self._generate_fallback_solution(problem, resources)

        # Use LLM-based workflow selection (from original default_solve_method)
        llm = LegacyLLMResource()

        # Build combined list of all importable workflows from all expertise modules
        expert_workflow_names: list[str] = []
        expert_workflow_name_to_module_map: dict[str, ModuleType] = {}

        for workflow in self.workflows:
            expert_workflow_names.append(workflow.name)
            # Find the module that contains this workflow
            for module in expertise_modules:
                if hasattr(module, workflow.name):
                    expert_workflow_name_to_module_map[workflow.name] = module
                    break

        closest_matched_expert_workflow_lookup_prompt: str = WORKFLOW_SELECTION_PROMPT_TEMPLATE.format(
            problem=problem,
            expert_workflow_names=expert_workflow_names
        )

        closest_matched_expert_workflow_name: str = ''
        while not ((closest_matched_expert_workflow_name in expert_workflow_name_to_module_map) or
                   (closest_matched_expert_workflow_name == 'NONE')):
            closest_matched_expert_workflow_name: str = (
                from_response_to_content(
                    llm.query_sync(
                        from_prompts_to_request(
                            closest_matched_expert_workflow_lookup_prompt)))
                    .strip('"').strip("'"))

        # Find the expertise module that contains the matched workflow
        if closest_matched_expert_workflow_name == 'NONE':
            solution: str = from_response_to_content(llm.query_sync(from_prompts_to_request(problem)))
        else:
            matched_expertise_module = expert_workflow_name_to_module_map[closest_matched_expert_workflow_name]
            matched_workflow = None

            # Find the workflow object
            for workflow in self.workflows:
                if workflow.name == closest_matched_expert_workflow_name:
                    matched_workflow = workflow
                    break

            logger.info(f'Executing `{matched_expertise_module.__name__}.{closest_matched_expert_workflow_name}` on `{resources}`...')

            # Execute the workflow function with the full resources dictionary
            workflow_result = matched_workflow.workflow_function(resources)

            solution: str = from_response_to_content(
                llm.query_sync(
                    from_prompts_to_request(
                        SOLUTION_SYNTHESIS_PROMPT_TEMPLATE.format(
                            problem=problem,
                            workflow_result=workflow_result
                        )
                    )
                )
            )

        return solution

    def _analyze_problem(self, problem: str) -> dict[str, Any]:
        """
        Phase 1: Problem Analysis

        Parse and understand the problem statement to identify key concepts,
        entities, and required operations.
        """
        # TODO: Use LLM to analyze problem and extract key concepts
        # For now, return a simple analysis
        return {
            "key_concepts": self._extract_key_concepts(problem),
            "entities": self._extract_entities(problem),
            "operations": self._extract_operations(problem),
            "constraints": self._extract_constraints(problem)
        }

    def _analyze_resources(self, resources: dict[str, Any]) -> dict[str, Any]:
        """
        Phase 2: Resource Inspection

        Examine available resources in the dictionary to understand what's available.
        """
        resource_analysis = {
            "available_keys": list(resources.keys()),
            "resource_types": {},
            "capabilities": {}
        }

        for key, value in resources.items():
            resource_analysis["resource_types"][key] = type(value).__name__
            resource_analysis["capabilities"][key] = self._infer_resource_capabilities(value)

        return resource_analysis

    def _match_workflows(self, problem_analysis: dict[str, Any],
                         resource_analysis: dict[str, Any]) -> list[ResourceMatch]:
        """
        Phase 3: Expertise Matching

        Match problem requirements against available workflows and score them
        based on relevance and resource compatibility.
        """
        matches = []

        for workflow in self.workflows:
            match = self._evaluate_workflow_match(workflow, problem_analysis, resource_analysis)
            if match.score > 0:  # Only include workflows with some relevance
                matches.append(match)

        # Sort by score (highest first)
        matches.sort(key=lambda x: x.score, reverse=True)
        return matches

    def _evaluate_workflow_match(self, workflow: WorkflowInfo,
                                 problem_analysis: dict[str, Any],
                                 resource_analysis: dict[str, Any]) -> ResourceMatch:
        """
        Evaluate how well a workflow matches the problem and available resources.
        """
        # Calculate conceptual match score
        conceptual_match = self._calculate_conceptual_match(workflow, problem_analysis)

        # Calculate resource compatibility score
        resource_compatibility, matched_resources, missing_resources = self._calculate_resource_compatibility(
            workflow, resource_analysis
        )

        # Calculate output relevance score
        output_relevance = self._calculate_output_relevance(workflow, problem_analysis)

        # Overall score (average of three components)
        overall_score = (conceptual_match + resource_compatibility + output_relevance) / 3

        return ResourceMatch(
            workflow=workflow,
            score=overall_score,
            matched_resources=matched_resources,
            missing_resources=missing_resources
        )

    def _calculate_conceptual_match(self, workflow: WorkflowInfo,
                                    problem_analysis: dict[str, Any]) -> float:
        """
        Calculate how well the workflow conceptually matches the problem.
        """
        # TODO: Use LLM to evaluate conceptual match
        # For now, use simple keyword matching
        problem_text = " ".join(problem_analysis.get("key_concepts", []))
        workflow_text = f"{workflow.name} {workflow.description} {workflow.expertise_domain}"

        # Simple overlap calculation
        problem_words = set(problem_text.lower().split())
        workflow_words = set(workflow_text.lower().split())

        if not problem_words:
            return 0.0

        overlap = len(problem_words.intersection(workflow_words))
        return min(overlap / len(problem_words), 1.0)

    def _calculate_resource_compatibility(self, workflow: WorkflowInfo,
                                          resource_analysis: dict[str, Any]) -> tuple[float, dict[str, Any], list[str]]:
        """
        Calculate how well available resources match workflow input requirements.
        """
        available_keys = set(resource_analysis["available_keys"])
        required_inputs = set(workflow.input_signature.keys())

        # Find matching resources
        matched_keys = available_keys.intersection(required_inputs)
        missing_keys = required_inputs - available_keys

        # Calculate compatibility score
        if not required_inputs:
            return 1.0, {}, []

        compatibility_score = len(matched_keys) / len(required_inputs)

        # Build matched resources dictionary
        matched_resources = {}
        for key in matched_keys:
            # TODO: Add type validation here
            matched_resources[key] = f"resource_{key}"  # Placeholder

        return compatibility_score, matched_resources, list(missing_keys)

    def _calculate_output_relevance(self, workflow: WorkflowInfo,
                                    problem_analysis: dict[str, Any]) -> float:
        """
        Calculate how relevant the workflow output is to the problem.
        """
        # TODO: Use LLM to evaluate output relevance
        # For now, return a default score
        return 0.7

    def _select_best_workflow(self, matches: list[ResourceMatch]) -> ResourceMatch:
        """
        Phase 4: Execution Planning

        Select the best-matching workflow for execution.
        """
        if not matches:
            raise ValueError("No suitable workflows found")

        # Select the highest-scoring workflow
        best_match = matches[0]

        # Log selection details
        logger.info(f"Selected workflow: {best_match.workflow.name} (score: {best_match.score:.3f})")
        logger.info(f"Matched resources: {list(best_match.matched_resources.keys())}")
        if best_match.missing_resources:
            logger.warning(f"Missing resources: {best_match.missing_resources}")

        return best_match

    def _execute_workflow(self, match: ResourceMatch, problem: str, resources: dict[str, Any]) -> Any:
        """
        Phase 5: Solution Execution

        Execute the selected workflow with the matched resources.
        """
        workflow = match.workflow

        logger.info(f"Executing workflow: {workflow.name}")
        logger.info(f"Available resources: {list(resources.keys())}")

        # Execute the workflow function with the full resources dictionary
        # The workflow function should handle extracting what it needs from resources
        result = workflow.workflow_function(resources)

        logger.info("Workflow execution completed")
        return result

    def _synthesize_solution(self, problem: str, result: Any, match: ResourceMatch) -> str:
        """
        Phase 6: Result Synthesis

        Synthesize a comprehensive solution from the workflow results.
        """
        # TODO: Use LLM to synthesize solution from workflow results
        # For now, return a simple formatted response

        workflow_name = match.workflow.name
        score = match.score

        solution = SOLUTION_FORMAT_TEMPLATE.format(
            problem=problem,
            workflow_name=workflow_name,
            result=result,
            score=score
        )

        return solution.strip()

    def _generate_fallback_solution(self, problem: str, resources: dict[str, Any]) -> str:
        """Generate a fallback solution when no suitable workflows are found."""
        return FALLBACK_SOLUTION_TEMPLATE.format(
            problem=problem,
            available_resources=list(resources.keys())
        )

    def _generate_error_solution(self, problem: str, error: Exception, match: ResourceMatch) -> str:
        """Generate a solution when workflow execution fails."""
        return ERROR_SOLUTION_TEMPLATE.format(
            problem=problem,
            workflow_name=match.workflow.name,
            error_message=str(error)
        )

    # Helper methods for problem analysis
    def _extract_key_concepts(self, problem: str) -> list[str]:
        """Extract key concepts from the problem statement."""
        # TODO: Use LLM for better concept extraction
        # For now, use simple word extraction
        words = problem.lower().split()
        # Filter out common words and keep meaningful terms
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        return [word for word in words if word not in stop_words and len(word) > 3]

    def _extract_entities(self, problem: str) -> list[str]:
        """Extract entities from the problem statement."""
        # TODO: Use LLM for entity extraction
        # For now, return empty list
        return []

    def _extract_operations(self, problem: str) -> list[str]:
        """Extract operations from the problem statement."""
        # TODO: Use LLM for operation extraction
        # For now, return empty list
        return []

    def _extract_constraints(self, problem: str) -> list[str]:
        """Extract constraints from the problem statement."""
        # TODO: Use LLM for constraint extraction
        # For now, return empty list
        return []

    def _infer_resource_capabilities(self, resource: Any) -> dict[str, Any]:
        """Infer capabilities of a resource object."""
        # TODO: Implement resource capability inference
        # For now, return basic type information
        return {
            "type": type(resource).__name__,
            "capabilities": ["unknown"]
        }


# Global solver instance
_solver = GeneralProblemSolver()


def solve(problem: str, expertise_modules: list[ModuleType] = None, resources: dict[str, Any] = None) -> str:
    """
    Main solve function that routes problems to appropriate expert workflows.

    Args:
        problem: Natural language description of the problem to solve
        expertise_modules: List of modules containing expert workflows
        resources: Dictionary mapping resource keys to resource objects

    Returns:
        Solution to the problem as a string
    """
    if expertise_modules is None:
        expertise_modules = []
    if resources is None:
        resources = {}

    return _solver.solve(problem, expertise_modules, resources)


def register_workflow(name: str, description: str, input_signature: dict[str, type],
                      output_signature: dict[str, type], workflow_function: callable,
                      expertise_domain: str = "general") -> None:
    """
    Register a workflow for problem-solving.

    Args:
        name: Name of the workflow
        description: Description of what the workflow does
        input_signature: Dictionary mapping input parameter names to their types
        output_signature: Dictionary mapping output parameter names to their types
        workflow_function: The actual workflow function to execute
        expertise_domain: Domain of expertise (e.g., "finance", "healthcare", "engineering")
    """
    workflow_info = WorkflowInfo(
        name=name,
        description=description,
        input_signature=input_signature,
        output_signature=output_signature,
        workflow_function=workflow_function,
        expertise_domain=expertise_domain
    )
    _solver.register_workflow(workflow_info)
