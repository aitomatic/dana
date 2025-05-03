"""Plan executor implementation."""

from typing import Optional, TYPE_CHECKING, Union
from opendxa.base.execution import RuntimeContext
from opendxa.base.execution.execution_types import (
    ExecutionNode,
    ExecutionSignal,
    ExecutionStatus,
)
from opendxa.base.execution.base_executor import BaseExecutor
from opendxa.base.resource import LLMResource
from opendxa.execution.planning.plan import Plan
from opendxa.execution.planning.plan_factory import PlanFactory
from opendxa.execution.planning.plan_strategy import PlanStrategy
from opendxa.common.mixins.loggable import Loggable

# Avoid circular import for type hinting
if TYPE_CHECKING:
    from opendxa.execution.reasoning.reasoner import Reasoner 

class Planner(BaseExecutor[Plan], Loggable):
    """Executor for the planning layer of OpenDXA.
    
    Responsible for managing the execution of a Plan graph, which represents
    a sequence of steps to achieve a higher-level objective. The Planner typically
    delegates the execution of each step (node) in its Plan graph to a 
    `lower_executor` (which could be another Planner or a Reasoner).

    Initialization (`__init__`):
        - strategy (PlanStrategy): Defines potential strategies for plan creation 
          or execution (currently less utilized in the core delegation logic).
        - lower_executor (Union[Planner, Reasoner]): The executor instance responsible 
          for handling the execution of each node within this Planner's graph.
        - llm (LLMResource): Optional language model. Not used in the default 
          delegation logic but could be used by strategies for plan generation.
        - factory (PlanFactory): Used by BaseExecutor for creating Plan graphs.

    Execution (`execute_node_core`):
        Receives:
        - node (ExecutionNode): The specific node within this Planner's Plan graph 
          (e.g., a single step like "Find flights"). `node.objective` defines 
          the goal for this specific step.
        - context (RuntimeContext): Passed down (mutably) through the execution chain. 
          Used for accessing shared state via StateManager (`context.get`/`set`).
        Core Logic:
        - Calls `lower_executor.create_graph_from_upper_node` to generate the 
          sub-graph needed to execute the current `node`.
        - Calls `lower_executor.execute(sub_graph, context, upper_executor=self)` to 
          run the sub-graph, passing itself as the `upper_executor` parameter.
        - Updates its own `node.status` based on the result signal.

    Hierarchy Context:
        - Acts as a node in the execution hierarchy.
        - Provides context to the `lower_executor` by passing `self` as the 
          `upper_executor` parameter in the delegated `execute` call.
        - `self.graph.objective`: Represents the overall goal of the Plan being executed.
        - `node.objective`: Represents the specific goal of the current step being delegated, 
          which forms the basis for the lower executor's graph objective.
    """
    
    _factory_class = PlanFactory
    
    def __init__(
        self,
        strategy: PlanStrategy,
        lower_executor: Union['Planner', 'Reasoner'],
        llm: Optional[LLMResource] = None,
        factory: Optional[PlanFactory] = None
    ):
        """Initialize the planner.
        
        Args:
            strategy: The planning strategy
            lower_executor: The executor for the lower layer (Planner or Reasoner)
            llm: Optional LLM resource
            factory: Optional factory for creating graphs
        """
        super().__init__(factory=factory)
        self._strategy = strategy
        self.lower_executor: Union['Planner', 'Reasoner'] = lower_executor

    async def execute_node_core(
        self,
        node: ExecutionNode,
        context: RuntimeContext
    ) -> ExecutionSignal:
        """Execute the core planning node logic by delegating to a lower executor.
        WARNING: Passes the original mutable context down.
        """
        self.info(f"Planner delegating node {node.id} to lower executor.")

        if not self.lower_executor:
            self.error("Planner requires a lower_executor to be configured.")
            return ExecutionSignal(
                status=ExecutionStatus.FAILED,
                content="Planner requires a lower_executor."
            )

        # Ensure the lower executor can create a graph from the node objective
        # This assumes create_graph_from_upper_node sets the new graph's objective from node.objective
        # We also now use self.graph, which is set by BaseExecutor.execute
        lower_graph = self.lower_executor.create_graph_from_upper_node(node, self.graph)

        if not lower_graph:
            self.error(f"Lower executor failed to create a graph for node {node.id}.")
            node.status = ExecutionStatus.FAILED
            return ExecutionSignal(
                status=ExecutionStatus.FAILED,
                content="Failed to create lower graph"
            )

        # Execute the lower graph, passing self as the upper_executor parameter
        self.info(f"Executing lower graph {lower_graph.name or lower_graph.id} for node {node.id}")
        try:
            final_signal = await self.lower_executor.execute(
                graph=lower_graph, 
                context=context, 
                upper_executor=self # Pass self directly
            )
        except Exception as lower_exec_error:
             self.error(f"Error during lower_executor execution for node {node.id}: {lower_exec_error}", exc_info=True)
             final_signal = ExecutionSignal(status=ExecutionStatus.FAILED, content=f"Lower execution failed: {lower_exec_error}")

        self.info(f"Lower graph execution for node {node.id} finished with status: {final_signal.status}")
        
        # Update the current planner node's status based on the final signal
        if final_signal.status == ExecutionStatus.FAILED:
            node.status = ExecutionStatus.FAILED
        elif final_signal.status == ExecutionStatus.COMPLETED:
            node.status = ExecutionStatus.COMPLETED
        
        self.info(f"Planner completed delegation for node {node.id} with status: {node.status}")

        return final_signal

    def create_graph_from_upper_node(
        self,
        node: ExecutionNode,
        upper_graph: Optional[Plan] = None
    ) -> Optional[Plan]:
        """Planner typically doesn't create plans from upper nodes."""
        self.warning("create_graph_from_upper_node called on Planner, which is unusual.")
        return None
    