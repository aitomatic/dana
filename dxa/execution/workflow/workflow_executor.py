"""Workflow executor implementation."""

from enum import Enum
from typing import List, cast, Optional, TYPE_CHECKING
from uuid import uuid4
from ..execution_context import ExecutionContext
from ..execution_types import ExecutionNode, ExecutionSignal, Objective
from ..execution_graph import ExecutionGraph
from ..executor import Executor
from .workflow import Workflow
from .workflow_factory import WorkflowFactory
from ...common.graph import NodeType
from ...common.utils.text_processor import TextProcessor
if TYPE_CHECKING:
    from ..planning.plan_executor import PlanExecutor
from ...common.graph import Edge
from ..planning.plan import Plan

class WorkflowStrategy(Enum):
    """Workflow execution strategies."""
    DEFAULT = "DEFAULT"      # same as WORKFLOW_IS_PLAN
    WORKFLOW_IS_PLAN = "WORKFLOW_IS_PLAN"
    SEQUENTIAL = "SEQUENTIAL"
    PARALLEL = "PARALLEL"
    CONDITIONAL = "CONDITIONAL"

class WorkflowExecutor(Executor):
    """Executes workflow graphs."""

    def __init__(self, plan_executor: 'PlanExecutor', strategy: WorkflowStrategy = WorkflowStrategy.DEFAULT):
        super().__init__(depth=1)
        self.plan_executor = plan_executor
        self._strategy = strategy
        self.layer = "workflow"
        self._configure_logger()
        self.parse_by_key = TextProcessor().parse_by_key

    @property
    def strategy(self) -> WorkflowStrategy:
        """Get workflow strategy."""
        if self._strategy == WorkflowStrategy.DEFAULT:
            self._strategy = WorkflowStrategy.WORKFLOW_IS_PLAN
        return self._strategy

    @strategy.setter
    def strategy(self, strategy: WorkflowStrategy):
        """Set workflow strategy."""
        if strategy == WorkflowStrategy.DEFAULT:
            strategy = WorkflowStrategy.WORKFLOW_IS_PLAN
        self._strategy = strategy

    async def execute_workflow(self, workflow: Workflow, context: ExecutionContext) -> List[ExecutionSignal]:
        """Execute given workflow graph."""
        context.current_workflow = workflow
        self.graph = cast(ExecutionGraph, workflow)
        return await self.execute(upper_graph=cast(ExecutionGraph, None), context=context, upper_signals=None)

    def _parse_plan(self, plan):
        steps = []
        step_count = 1
        while True:
            step_key = f"step_{step_count}"
            expected_key = f"expected_output_step_{step_count}"
            
            step_prompt = self.parse_by_key(plan, step_key)
            expected_output = self.parse_by_key(plan, expected_key)
            
            # Break the loop if no more steps are found
            if step_prompt == "Unknown" or expected_output == "Unknown":
                break
            
            steps.append({"step": step_prompt, "expected_output": expected_output, "id": str(uuid4())})
            step_count += 1
        return steps

    def _construct_plan_graph_from_nodes(self, nodes, plan, objective):
        plan_graph = Plan(objective=objective)
        plan_graph.add_node(ExecutionNode(node_id="START", node_type=NodeType.START, description="Start"))
        for node in nodes:
            plan_graph.add_node(node)
        plan_graph.add_node(ExecutionNode(node_id="END", node_type=NodeType.END, description="End"))
        plan_graph.add_edge(Edge(source="START", target=nodes[0].node_id))
        for i in range(len(plan) - 1):
            plan_graph.add_edge(Edge(source=nodes[i].node_id, target=nodes[i+1].node_id))
        plan_graph.add_edge(Edge(source=nodes[-1].node_id, target="END"))
        return plan_graph
    
    def _construct_plan_graph(self, plan, objective):
        steps = plan
        nodes = []
        validation_nodes = []
        for i, step in enumerate(steps):
            nodes.append(ExecutionNode(node_id=f"step_{i+1}", node_type=NodeType.TASK, description=step['step']))
            validation_nodes.append(ExecutionNode(node_id=f"step_{i+1}", node_type=NodeType.TASK, description=step['expected_output']))
        
        plan_graph = self._construct_plan_graph_from_nodes(nodes, plan, objective)
        validation_plan_graph = self._construct_plan_graph_from_nodes(validation_nodes, plan, objective)
        
        return plan_graph, validation_plan_graph
    
    async def execute(self,
                      upper_graph: ExecutionGraph,
                      context: ExecutionContext,
                      upper_signals: Optional[List[ExecutionSignal]] = None) -> List[ExecutionSignal]:
        """Execute workflow graph. Upper signals are not used in the workflow layer."""
        context.current_plan = self.graph
        context.current_reasoning = self.graph
        # PLEASE CHECK THIS
        if self.strategy == WorkflowStrategy.WORKFLOW_IS_PLAN:
            # Go directly to plan execution, via the START node
            assert self.graph is not None
            return await self.plan_executor.execute(self.graph, context, None)
        
        
        if self.strategy == WorkflowStrategy.PROSEA:
            execution_signals = []
            analyze_response = None
            plan = []
            for node_id in self.graph.nodes.keys():
                node = self.graph.nodes[node_id]
                print("Executing node:", node.node_id)
                if node.node_type == NodeType.TASK:
                    if node.node_id == "ANALYZE":
                        response = await self.plan_executor.execute_node(node=node, context=context, prev_signals=execution_signals, upper_signals=None, lower_signals=None)
                        analyze_response = response[0].content['result']['content']
                        response[0].content['result']['content'] = f"{node.node_id}: \nStep Output: " + response[0].content['result']['content']
                        execution_signals.extend(response)
                    elif node.node_id == "PLANNING":
                        while len(plan) == 0:
                            node.description = node.description.replace("<problem_analysis>", analyze_response)
                            response = await self.plan_executor.execute_node(node=node, context=context, prev_signals=execution_signals, upper_signals=None, lower_signals=None)
                            plan = self._parse_plan(response[0].content['result']['content'])
                            print(plan)
                        execution_signals.extend(response)
                        plan_graph, validation_plan_graph = self._construct_plan_graph(plan, objective=context.current_workflow.objective)
                        step_id = 1
                        for plan_node_id in plan_graph.nodes.keys():
                            plan_node = plan_graph.nodes[plan_node_id]
                            validation_plan_node = validation_plan_graph.nodes[plan_node_id]
                            if plan_node.node_type == NodeType.TASK:
                                print(f"\033[92mStep {step_id}:\033[0m", plan_node.description)
                                step_id += 1
                                response = await self.plan_executor.execute_node(plan_node, context, validation_node=validation_plan_node, 
                                                                                 original_problem=context.current_plan.objective.original, 
                                                                                 agent_role=context.current_workflow.metadata["role"],
                                                                                 prev_signals=execution_signals, upper_signals=None, lower_signals=None)
                                print("Workflow executor", response)
                                response[0].content['result']['content'] = f"{plan_node.node_id}: {plan_node.description} \nStep Output: " \
                                                                            + response[0].content['result']['content']
                                execution_signals.extend(response)
                    elif node.node_id == "FINALIZE_ANSWER":
                        response = await self.plan_executor.execute_node(node=node, context=context, prev_signals=execution_signals, upper_signals=None, lower_signals=None)
                        execution_signals.extend(response)
    
            return execution_signals
        

        return await super().execute(upper_graph=upper_graph, context=context, upper_signals=None)

    async def execute_node(self, node: ExecutionNode,
                           context: ExecutionContext,
                           prev_signals: Optional[List[ExecutionSignal]] = None,
                           upper_signals: Optional[List[ExecutionSignal]] = None,
                           lower_signals: Optional[List[ExecutionSignal]] = None) -> List[ExecutionSignal]:
        """Execute node based on its type and strategy.
        Upper signals are not used in the workflow layer."""

        # Safety: make sure our graph is set
        if self.graph is None and context.current_workflow:
            self.graph = context.current_workflow

        if context.current_workflow is None and self.graph:
            context.current_workflow = cast(Workflow, self.graph)

        if node.node_type in [NodeType.START, NodeType.END]:
            return []  # Start and end nodes just initialize/terminate flow

        if node.node_type == NodeType.TASK:
            assert self.graph is not None
            # Pass current cursor position
            return await self.plan_executor.execute(
                upper_graph=self.graph,
                context=context,
                upper_signals=prev_signals  # Pass my prev_signals down to plan executor
            )

        self.logger.debug(
            "Processing workflow node",
            node_id=node.node_id,
            node_type=node.node_type
        )

        return []

    def _create_graph(self, upper_graph: ExecutionGraph, objective: Optional[Objective] = None,
                       context: Optional[ExecutionContext] = None) -> ExecutionGraph:
        """Create workflow graph from objective. At the Worflow layer, there is no upper graph."""
        workflow = WorkflowFactory.create_minimal_workflow(objective)
        assert context is not None
        context.current_workflow = workflow
        return cast(ExecutionGraph, workflow)
