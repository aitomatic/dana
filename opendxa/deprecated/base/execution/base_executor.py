"""Base executor for the OpenDXA framework."""

from typing import Optional, Type, TypeVar, Generic
from abc import ABC, abstractmethod
from opendxa.common.mixins.loggable import Loggable
from opendxa.base.execution.execution_types import (
    ExecutionSignal,
    ExecutionStatus,
    ExecutionNode
)
from opendxa.base.execution.execution_graph import ExecutionGraph
from opendxa.base.execution.execution_factory import ExecutionFactory
from opendxa.base.execution.runtime_context import RuntimeContext

# Generic type for graphs
GraphT = TypeVar('GraphT', bound=ExecutionGraph)

class BaseExecutor(Generic[GraphT], Loggable, ABC):
    """Abstract Base Class for all executors in the OpenDXA framework.

    Provides the core execution flow for traversing an ExecutionGraph and common 
    functionality needed by concrete executor implementations (like Planner, Reasoner,
    PipelineExecutor).

    Handles:
    - Graph traversal using a cursor.
    - Iterative node execution by calling `execute_node`.
    - Basic error handling during traversal and node execution.
    - Processing ExecutionSignals returned by nodes.
    - Temporary storage of the currently executing graph (`self.graph`).

    Initialization (`__init__`):
        - Requires subclasses to define a `_factory_class` (Type[ExecutionFactory]).
        - Instantiates and stores the appropriate factory in `self._factory`.

    Execution (`execute`):
        - Takes the `graph` to execute, the `context` (RuntimeContext), and an 
          optional `upper_executor` (Optional[BaseExecutor]).
        - **WARNING:** Passes the mutable `context` object down to `execute_node`.
        - Manages the lifecycle of `self.graph`.
        - Manages the lifecycle of `self.upper_executor` based on the passed parameter.
        - Iterates through graph nodes, calling `execute_node` for each.
        - Updates the status of the graph's nodes based on returned signals.
        - Returns a final ExecutionSignal indicating the overall status.

    Node Execution (`execute_node`, `execute_node_core`):
        - `execute_node` is a wrapper providing error handling.
        - `execute_node_core` is an **abstract method** that MUST be implemented 
          by subclasses. It contains the specific logic for processing a single 
          node of the type managed by that executor (e.g., delegation, LLM call).

    Hierarchy Context (`upper_executor`):
        - Contains an `upper_executor: Optional[BaseExecutor]` attribute.
        - This link is **managed by BaseExecutor.execute**. It is set temporarily 
          during execution based on the `upper_executor` parameter passed 
          directly to the `execute` method by the *calling* executor.
        - It is cleared automatically in the `finally` block of `execute`.
        - This mechanism allows lower executors (like Reasoner) to traverse up the 
          call chain (e.g., `self.upper_executor.upper_executor...`) to access 
          context (like graph objectives) from parent executions.

    Subclass Requirements:
        - Must define `_factory_class: Type[ExecutionFactory]` class attribute.
        - Must implement the `async def execute_node_core(...)` method.
    """
    
    # Required class attributes
    _factory_class: Type[ExecutionFactory]
    
    # Add attribute to hold the current graph
    graph: Optional[GraphT] = None 
    # Add link to the executor that called this one
    upper_executor: Optional['BaseExecutor'] = None 
    
    def __init__(
        self,
        factory: Optional[ExecutionFactory] = None,
    ):
        """Initialize the executor.
        
        Args:
            factory: Optional factory for creating graphs
        """
        super().__init__()
        self._factory = factory or self._factory_class()
    
    async def execute(
        self, 
        graph: GraphT, 
        context: RuntimeContext, 
        upper_executor: Optional['BaseExecutor'] = None
    ) -> ExecutionSignal:
        """Execute the graph.
        WARNING: Passes the mutable context object down.
        """
        self.logger.info(f"Starting execution for graph: {graph.name or graph.id}")
        self.graph = graph
        # Set upper executor directly from the parameter
        self.upper_executor = upper_executor 
        if self.upper_executor:
            # Assuming executors have id or identifiable representation
            self.logger.debug(
                f"Executor {getattr(self, 'id', id(self))} called by "
                f"{getattr(self.upper_executor, 'id', id(self.upper_executor))}"
            )

        cursor = graph.create_cursor(graph.start_node_id)
        final_signal = ExecutionSignal(status=ExecutionStatus.PENDING)
        
        try:
            # Traverse and execute nodes
            for node in cursor:
                try:
                    self.logger.debug(f"Executing node {node.id} with objective: {node.objective}")
                    
                    # Execute node and get signal - PASSING MUTABLE CONTEXT!
                    signal = await self.execute_node(node, context)
                    final_signal = signal
                    
                    # Update node status based on signal (same logic as before)
                    if signal.status in [ExecutionStatus.COMPLETED, ExecutionStatus.SKIPPED]:
                        node.status = signal.status 
                    elif signal.status == ExecutionStatus.FAILED:
                        node.status = ExecutionStatus.FAILED
                        self.logger.error(f"Node {node.id} failed. Signal: {signal.content or 'No details'}")
                        return signal 
                    elif signal.status == ExecutionStatus.RUNNING:
                        node.status = ExecutionStatus.RUNNING
                        pass  # Continue loop
                    else:
                        self.logger.warning(f"Unhandled signal status {signal.status} for node {node.id}")
                        return signal

                except Exception as e:
                    # Handle node execution errors (same logic as before)
                    self.logger.error(f"Exception executing node {node.id}: {str(e)}", exc_info=True)
                    node.status = ExecutionStatus.FAILED
                    final_signal = ExecutionSignal(
                        status=ExecutionStatus.FAILED,
                        node_id=node.id,
                        content=f"Exception: {str(e)}"
                    )
                    return final_signal
                    
            # Graph completion (same logic as before)
            if final_signal.status not in [ExecutionStatus.FAILED, ExecutionStatus.CANCELLED]:
                final_signal = ExecutionSignal(status=ExecutionStatus.COMPLETED)
            
            return final_signal
                    
        except Exception as e:
            # Handle graph traversal errors (same logic as before)
            self.logger.error(f"Error during graph traversal: {str(e)}", exc_info=True)
            return ExecutionSignal(
                status=ExecutionStatus.FAILED,
                content=f"Traversal Exception: {str(e)}"
            )
        finally:
            # Clean up graph and upper executor references
            self.graph = None
            upper_ref_cleared_id = getattr(self.upper_executor, 'id', id(self.upper_executor)) if self.upper_executor else 'None'
            self.upper_executor = None 
            log_msg = (
                 f"Finished execution for graph: {graph.name or graph.id}. "
                 f"Cleared upper_executor ref: {upper_ref_cleared_id}. "
                 f"Final Status: {final_signal.status}"
             )
            self.logger.info(log_msg)
    
    async def execute_node(self, node: ExecutionNode, context: RuntimeContext) -> ExecutionSignal:
        """Execute a single node.
        
        Args:
            node: Node to execute
            context: Runtime context
            
        Returns:
            Execution signal indicating success or failure
        """
        try:
            # Execute node core logic
            return await self.execute_node_core(node, context)
            
        except Exception as e:
            # Handle execution errors
            self.logger.error(f"Error in node {node.id} core logic: {str(e)}", exc_info=True)
            return ExecutionSignal(
                status=ExecutionStatus.FAILED,
                node_id=node.id,
                content=f"Core Logic Exception: {str(e)}"
            )
    
    @abstractmethod
    async def execute_node_core(self, node: ExecutionNode, context: RuntimeContext) -> ExecutionSignal:
        """Execute the core logic for a node.
        
        This method must be implemented by subclasses to provide
        the specific execution logic for their node types.
        
        Args:
            node: Node to execute
            context: Runtime context
            
        Returns:
            Execution signal indicating success or failure
        """
        pass
    
    def create_basic_graph(
        self,
        objective: Optional[str] = None,
        name: Optional[str] = None
    ) -> GraphT:
        """Create a basic graph with START -> task -> END nodes.
        
        Args:
            objective: Optional graph objective
            name: Optional graph name
            
        Returns:
            Created graph
        """
        return self._factory.create_basic_graph(objective, name)
