"""Plan executor implementation."""

from typing import List, Optional
from opendxa.base.execution.base_executor import BaseExecutor, ExecutionError
from opendxa.base.execution.execution_context import ExecutionContext
from opendxa.base.execution.execution_types import ExecutionNode, ExecutionSignal
from opendxa.base.resource import LLMResource
from opendxa.execution.planning.plan import Plan
from opendxa.execution.planning.plan_factory import PlanFactory
from opendxa.execution.planning.plan_strategy import PlanStrategy
from opendxa.execution.reasoning import Reasoner, ReasoningStrategy

class Planner(BaseExecutor[PlanStrategy, Plan, PlanFactory]):
    """Executor for the planning layer."""
    
    # Required class attributes
    _strategy_type = PlanStrategy
    _default_strategy = PlanStrategy.DEFAULT
    graph_class = Plan
    _factory_class = PlanFactory
    _depth = 1

    def __init__(self, 
                 strategy: Optional[PlanStrategy] = None, 
                 lower_executor: Optional[BaseExecutor] = None,
                 planning_llm: Optional[LLMResource] = None):
        """Initialize planner.
        
        Args:
            strategy: Planning strategy
            lower_executor: Executor for the lower (reasoning) layer
            planning_llm: LLM resource for planning tasks
        """
        if lower_executor is None:
            lower_executor = Reasoner(ReasoningStrategy.DEFAULT)
        super().__init__(strategy=strategy, lower_executor=lower_executor)
        self._planning_llm = planning_llm
        if self._planning_llm is None:
            self.warning("Planner initialized without an LLM resource.")
    
    async def _execute_node_core(self, node: ExecutionNode, context: ExecutionContext) -> List[ExecutionSignal]:
        """Execute a planning node by delegating to the lower executor (Reasoner).
        
        If the strategy requires direct LLM interaction at the planning level 
        (e.g., for plan refinement or high-level decision making), that logic
        would be added here, potentially using self._planning_llm.
        
        Currently, it primarily orchestrates the lower layer.
        """
        if self.lower_executor is None:
            raise ExecutionError("Planner requires a lower executor (Reasoner) to function.")
            
        if not self.graph:
            # This should ideally not happen if execute is called correctly
            raise ExecutionError("Planner has no current graph (Plan) to execute.")

        # --- Check if Planning LLM is needed for this strategy/node --- 
        # Example: If strategy involves plan refinement using an LLM
        # if self.strategy == PlanStrategy.REFINE_WITH_LLM:
        #     if not self._planning_llm:
        #         raise ExecutionError("Planning strategy requires a planning_llm, but none was provided.")
        #     # Build prompt for plan refinement
        #     refinement_prompt = self._build_plan_refinement_prompt(node, context)
        #     # Call planning LLM
        #     refined_plan_data = await self._planning_llm.acall(refinement_prompt)
        #     # Update node or context based on refinement
        #     self._apply_plan_refinement(node, context, refined_plan_data)
        #     # Potentially return signals indicating refinement
        #     # return [ExecutionSignal(...)] 
        
        # --- Standard delegation to lower executor --- 
        self.info(f"Planner delegating node {node.node_id} to lower executor.")
        
        # Create the graph for the lower layer (Reasoning Graph)
        # The lower executor is responsible for creating its specific graph type
        lower_graph = self.lower_executor.create_graph_from_upper_node(node, self.graph)
        
        if not lower_graph:
            self.error(f"Lower executor failed to create a graph for node {node.node_id}.")
            # Return an error signal or raise?
            raise ExecutionError(f"Lower executor could not create graph for node {node.node_id}")
        
        # Execute the lower graph using the lower executor
        return await self.lower_executor.execute(lower_graph, context)

    def create_graph_from_upper_node(
        self,
        node: ExecutionNode,
        upper_graph: Optional['Plan'] = None  # Type hint specific to Planner
    ) -> Optional[Plan]:
        """Planner typically doesn't create plans from upper nodes (it's the top layer executor)."""
        # This method might be used if Planner was nested under another layer,
        # but as the top domain executor, it usually receives a complete Plan.
        self.warning("create_graph_from_upper_node called on Planner, which is unusual.")
        # Depending on context, maybe return a sub-plan or raise an error.
        return None 
    