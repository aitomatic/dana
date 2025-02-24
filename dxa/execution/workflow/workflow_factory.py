"""Workflow factory for creating common workflow patterns."""

from pathlib import Path
from typing import List, Optional, Union, Dict
import yaml

from ..execution_graph import ExecutionGraph
from ..execution_types import Objective, ExecutionNode
from .workflow import Workflow
from ...common.graph import NodeType, Edge

class WorkflowFactory:
    """Factory for creating workflow patterns."""

    @classmethod
    def from_yaml(cls, yaml_data: Union[str, Dict, Path]) -> Workflow:
        """Create workflow from YAML data or file."""
        # Handle different input types
        if isinstance(yaml_data, (str, Path)):
            with open(yaml_data, encoding="utf-8") as f:
                data = yaml.safe_load(f)
        else:
            data = yaml_data

        # Create workflow
        workflow = Workflow(
            objective=Objective(data.get('description', '')),
            name=data.get('name', 'unnamed_workflow')
        )

        # Add nodes
        for node_data in data.get('nodes', []):
            node = ExecutionNode(
                node_id=node_data['id'],
                node_type=NodeType[node_data['type']],
                description=node_data.get('description', ''),
                metadata=node_data.get('metadata', {})
            )
            workflow.add_node(node)

        # Add edges
        for edge_data in data.get('edges', []):
            edge = Edge(
                source=edge_data['source'],
                target=edge_data['target'],
                metadata=edge_data.get('metadata', {})
            )
            workflow.add_edge(edge)

        return workflow

    @classmethod
    def create_sequential_workflow(cls, objective: Union[str, Objective], commands: List[str]) -> Workflow:
        """Create a sequential workflow from list of commands."""
        objective = Objective(objective) if isinstance(objective, str) else objective
        workflow = Workflow(objective)
        # pylint: disable=protected-access
        ExecutionGraph._add_start_end_nodes(graph=workflow)

        # Remove the edge from START to END
        workflow.remove_edge_between("START", "END")

        # Create task nodes for each command
        prev_id = "START"
        for i, command in enumerate(commands):
            node_id = f"TASK_{i}"
            workflow.add_node(ExecutionNode(
                node_id=node_id,
                node_type=NodeType.TASK,
                description=str(command)
            ))
            workflow.add_transition(prev_id, node_id)
            prev_id = node_id

        workflow.add_transition(prev_id, "END")
        return workflow

    @classmethod
    def create_minimal_workflow(cls, objective: Optional[Union[str, Objective]] = None) -> Workflow:
        """Create minimal workflow with START -> TASK -> END.
        The task node will have the objective as its description.
        """
        objective = Objective(objective) if isinstance(objective, str) else objective
        workflow = Workflow(objective)
        # pylint: disable=protected-access
        ExecutionGraph._add_start_end_nodes(graph=workflow)

        # Remove the edge from START to END
        workflow.remove_edge_between("START", "END")

        # Add task node
        workflow.add_node(ExecutionNode(
            node_id="PERFORM_TASK",
            node_type=NodeType.TASK,
            description=objective.original if objective else ""
        ))

        workflow.add_transition("START", "PERFORM_TASK")
        workflow.add_transition("PERFORM_TASK", "END")

        return workflow
    
    
    def _create_problem_analysis_prompt(cls, objective: Objective) -> str:
        problem_analysis_prompt = f"""
        \nAnalyze the question and interpret the problem.
        Problem: {objective.original}
        Tell me the problem statement.
        Now, please analyze the problem and interpret the question. Try to understand the problem and its context.
        Justify if there are any additional information can be inferred from the question.
        Let me know all the information you can get from the question.
        You can infer more information based on provided information in the question, but DO NOT hallucinate any information.
        No need to do any task, just analyze the problem and next step will be based on your analysis to construct the plan/solution.
        Please do reasoning to see if it's mandatory to get more extra information to solve the problem.
        If there are any well-known knowledge that would be helpful for the problem, please provide it.
        Do not assume the important information if you are not sure and do not assume customized information (for example, different company will have different level ladder).
        
        Based on the information from documents above, let me know if the problem can be solved by only looking at the documents.
        """      
        return problem_analysis_prompt
    
    def _create_planning_prompt(cls, objective: Objective) -> str:
        planning_prompt = f"""\n            
Remember, you have 2 tools to solve the problem:
1. Use a LLM as a tool to solve the problem.
2. Ask for more information from user if you need to interact with physical world.

Generate for me an excutable plan to fix the issue. 
All the steps for the plan must be solvable.
Then, let me know what do you expect to get for each step.

The step need to be for the problem identification and the solution in a logical order.
Criteria for the plan: After executing the plan, the solution must be achieved.
All the steps must be solvable with LLMs.

required problem: {objective.original}
problem analysis result: <problem_analysis>


Think straightforward and logically to generate the plan.
You should try your best to solve the problem with the information provided in the question and only ask for more information if without it, it's impossible to solve the problem.
For the simple problem, make simple plan and do not overkill the plan and overcomplicate the plan if not necessary.
try you best to find the solution with the information provided in the question.
Just do enough things to get the solution, do not do more than enough. Do not do the redundant step.
For the step required calculation, please do the calculation step by step and make sure that the calculation is correct. Say the accurate formula before doing the calculation.
Do not assume the important information if you are not sure and do not assume customized information (for example, different company will have different level ladder). 
Remember final output is a plan with steps with expected output for each step.


Answer must follow this format:
step_<i>: step <i> to solve current problem. The step should help me get closer to the solution. Give the necessary information from the question to solve the problem. Just do the thing that essential to solve the problem. Must be in one line, do not use "\n".

expected_output_step_<i>: What do you expect from the output for step <i>. This is just the criteria for the output to make sure that this step is success and can be used to get the accurate answer after gathering all step. Do not specify exact output answer unless you are extremely sure about it. If the step is request to gather information, it must have expected information to be completed. Must be in one line, do not use "\n".

If analysis show that the problem can be solved by only looking at the documents, then your plan must be only look at documents, the expected output is nothing special, any output should be accepted. The step should be only Get information XXXX from documents, expected output is nothing special, any output should be accepted. 
Do not forget to generate both step and expected output step.
Do not forget the key and do not change the key format. Do not highlight the key.
            """
        return planning_prompt
    
    def _create_finalize_answer_prompt(cls, objective: Objective) -> str:
        finalize_answer_prompt = f"""
        These are the reasoning steps and their outputs:
        <reasoning_result>
        
        Now, based on the reasoning steps and their outputs above, please give me the final answer for the original problem: {objective.original}
        """
        return finalize_answer_prompt
    
    @classmethod
    def create_prosea_workflow(cls, objective: Union[str, Objective]) -> Workflow:
        """Create a Prosea workflow for given parameters."""
        objective = Objective(objective) if isinstance(objective, str) else objective
        workflow = Workflow(objective)
        
        problem_analysis_prompt = cls._create_problem_analysis_prompt(cls, objective=objective)
        planning_prompt = cls._create_planning_prompt(cls, objective=objective)
        finalize_answer_prompt = cls._create_finalize_answer_prompt(cls, objective=objective)
        # Add standard monitoring nodes
        nodes = {
            "START": ExecutionNode(
                node_id="START",
                node_type=NodeType.START,
                description="Begin Prosea workflow"
            ),
            "ANALYZE": ExecutionNode(
                node_id="ANALYZE",
                node_type=NodeType.TASK,
                description=problem_analysis_prompt
            ),
            "PLANNING": ExecutionNode(
                node_id="PLANNING",
                node_type=NodeType.TASK,
                description=planning_prompt
            ),
            "FINALIZE_ANSWER": ExecutionNode(
                node_id="FINALIZE_ANSWER",
                node_type=NodeType.TASK,
                description=finalize_answer_prompt
            ),
            "END": ExecutionNode(
                node_id="END",
                node_type=NodeType.END,
                description="End Prosea workflow"
            )
        }

        # Add all nodes
        for node in nodes.values():
            workflow.add_node(node)
        
        # Add edges
        edges = [
            Edge("START", "ANALYZE"),
            Edge("ANALYZE", "PLANNING"),
            Edge("PLANNING", "FINALIZE_ANSWER"),
            Edge("FINALIZE_ANSWER", "END")
        ]
        
        for edge in edges:
            workflow.add_edge(edge)

        return workflow

        
    @classmethod
    def create_monitoring_workflow(cls,
                                   parameters: List[str],
                                   name: str = "monitoring",
                                   description: str = "") -> Workflow:
        """Create a monitoring workflow for given parameters."""
        workflow = Workflow(
            objective=Objective(description or f"Monitor {', '.join(parameters)}"),
            name=name
        )

        # Add standard monitoring nodes
        nodes = {
            "START": ExecutionNode(
                node_id="START",
                node_type=NodeType.START,
                description="Begin monitoring"
            ),
            "MONITOR": ExecutionNode(
                node_id="MONITOR",
                node_type=NodeType.TASK,
                description="Monitor parameters",
                metadata={"parameters": parameters}
            ),
            "CHECK": ExecutionNode(
                node_id="CHECK",
                node_type=NodeType.CONDITION,
                description="Check parameter values"
            ),
            "DIAGNOSE": ExecutionNode(
                node_id="DIAGNOSE",
                node_type=NodeType.TASK,
                description="Diagnose issues"
            ),
            "END": ExecutionNode(
                node_id="END",
                node_type=NodeType.END,
                description="End monitoring cycle"
            )
        }

        # Add all nodes
        for node in nodes.values():
            workflow.add_node(node)

        # Add edges with conditions
        edges = [
            Edge("START", "MONITOR"),
            Edge("MONITOR", "CHECK"),
            Edge("CHECK", "MONITOR", {"condition": "parameters_normal"}),
            Edge("CHECK", "DIAGNOSE", {"condition": "parameters_abnormal"}),
            Edge("DIAGNOSE", "END")
        ]

        for edge in edges:
            workflow.add_edge(edge)

        return workflow
