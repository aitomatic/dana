"""Base class for graph execution."""

from abc import ABC, abstractmethod
from typing import Optional, List, cast, TYPE_CHECKING, Any
from .execution_types import (
    ExecutionNode,
    ExecutionSignal,
    Objective,
    ExecutionSignalType,
    ExecutionNodeStatus,
    ExecutionError,
)
from .execution_graph import ExecutionGraph
from ...common.graph import NodeType
if TYPE_CHECKING:
    from .execution_context import ExecutionContext

class Executor(ABC):
    """Base class for executing any graph-based process."""
    
    def __init__(self):
        self._graph = None

    @property
    def graph(self) -> Optional[ExecutionGraph]:
        """Get the graph."""
        return self._graph
    
    @graph.setter
    def graph(self, graph: ExecutionGraph) -> None:
        """Set the graph."""
        self._graph = graph

    async def execute(self, 
                      upper_graph: ExecutionGraph, 
                      context: 'ExecutionContext', 
                      upper_signals: Optional[List[ExecutionSignal]] = None) -> List[ExecutionSignal]:
        """Execute the graph using cursor traversal."""
        if not self._graph:
            self._graph = self._create_graph(upper_graph, upper_graph.objective, context)
        
        cursor = self._graph.start_cursor()
        all_signals = []
        prev_signals = []
        lower_signals = []

        while (current := cursor.next()) is not None:
            try:
                assert self.graph is not None
                self.graph.update_node_status(current.node_id, ExecutionNodeStatus.IN_PROGRESS)
                node = cast(ExecutionNode, current)
                
                # Execute node and get its result signals
                new_signals = await self.execute_node(node, context, prev_signals, upper_signals, lower_signals)
                
                # Propagate signals between layers
                signals = []
                if prev_signals and self._should_propagate_horizontal(prev_signals[0]):
                    signals = prev_signals

                signals.extend(new_signals)  # Add node's result signals first

                # Update signals for next iteration
                prev_signals = signals
                all_signals.extend(signals)
                
                # Process signals (update node status, store results, etc)
                self._process_node_signals(current.node_id, signals)
                
            except Exception as e:  # pylint: disable=broad-exception-caught
                self._handle_node_error(current.node_id, str(e))
                all_signals.append(self._create_error_signal(current.node_id, str(e)))
                break

        # Handle signal propagation up and down layers
        if upper_signals:
            signals.extend(s for s in upper_signals if self._should_propagate_down(s))
        if lower_signals:
            signals.extend(s for s in lower_signals if self._should_propagate_up(s))
        
        return all_signals

    # pylint: disable=unused-argument
    def _should_propagate_down(self, signal: ExecutionSignal) -> bool:
        """Pipelines are flat, so no downward propagation."""
        # Add logic here to filter downward signals
        return True

    def _should_propagate_up(self, signal: ExecutionSignal) -> bool:
        """Pipelines are flat, so no upward propagation."""
        # Add logic here to filter upward signals
        return True

    def _should_propagate_horizontal(self, signal: ExecutionSignal) -> bool:
        """Pipelines should always propagate horizontally."""
        # Add logic here to filter horizontal signals
        return True

    @abstractmethod
    async def execute_node(self,
                           node: ExecutionNode, 
                           context: 'ExecutionContext', 
                           prev_signals: Optional[List[ExecutionSignal]] = None,
                           upper_signals: Optional[List[ExecutionSignal]] = None,
                           lower_signals: Optional[List[ExecutionSignal]] = None) -> List[ExecutionSignal]:
        """Execute a single node. To be implemented by subclasses."""
        pass

    def _process_node_signals(self, node_id: str, signals: List[ExecutionSignal]) -> None:
        """Process signals from node execution."""
        if not self.graph:
            raise ExecutionError("No graph to process signals")
        
        for signal in signals:
            if signal.type == ExecutionSignalType.DATA_RESULT:
                # Store result in node
                if self.graph and (node := self.graph.nodes.get(signal.content["node"])):
                    node.result = signal.content["result"]
                self.graph.update_node_status(node_id, ExecutionNodeStatus.COMPLETED)
            elif signal.type == ExecutionSignalType.CONTROL_ERROR:
                self.graph.update_node_status(node_id, ExecutionNodeStatus.FAILED)

    def _handle_node_error(self, node_id: str, error: str) -> None:
        """Handle node execution error."""
        print(f"Error handling node {node_id}: {error}")
        if self.graph:
            self.graph.update_node_status(node_id, ExecutionNodeStatus.FAILED)

    def _create_error_signal(self, node_id: str, error: str) -> ExecutionSignal:
        """Create error signal."""
        return ExecutionSignal(
            type=ExecutionSignalType.CONTROL_ERROR,
            content={"node": node_id, "error": error}
        )

    @abstractmethod
    def _create_graph(self, 
                      upper_graph: ExecutionGraph, 
                      objective: Optional[Objective] = None, 
                      context: Optional['ExecutionContext'] = None) -> ExecutionGraph:
        """Create this layer's graph from the upper layer's graph.
        To be implemented by subclasses."""
        pass

    def _create_sequence_graph(self, nodes: List[ExecutionNode]) -> ExecutionGraph:
        """Create graph from list of nodes."""
        graph = ExecutionGraph()
        prev_node = None
        for node in nodes:
            graph.add_node(node)
            if prev_node:
                graph.add_transition(prev_node.node_id, node.node_id)
            prev_node = node
        return graph
    
    def _create_execution_graph(self, nodes: List[ExecutionNode]) -> ExecutionGraph:
        """Create graph from list of nodes with START and END nodes."""
        assert len(nodes) > 0
        nodes.insert(0, ExecutionNode(node_id="START", node_type=NodeType.START, description="Start"))
        nodes.append(ExecutionNode(node_id="END", node_type=NodeType.END, description="End"))
        return self._create_sequence_graph(nodes)
    
    def create_result_signal(self, node_id: str, result: Any) -> ExecutionSignal:
        """Create a result signal for a node."""
        return ExecutionSignal(
            type=ExecutionSignalType.DATA_RESULT,
            content={
                "node": node_id,
                "result": result
            }
        )

    def create_error_signal(self, node_id: str, error: str) -> ExecutionSignal:
        """Create an error signal for a node."""
        return ExecutionSignal(
            type=ExecutionSignalType.CONTROL_ERROR,
            content={
                "node": node_id,
                "error": error
            }
        )
    
