"""Base class for graph execution."""

from abc import ABC, abstractmethod
from typing import Optional, List, cast
from .execution_types import (
    ExecutionNode,
    ExecutionSignal,
    ExecutionContext,
    Objective,
    ExecutionSignalType,
    ExecutionNodeStatus,
    ExecutionError,
)
from .execution_graph import ExecutionGraph
from ...common.graph import NodeType

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

    async def execute(self, upper_graph: ExecutionGraph, context: ExecutionContext) -> List[ExecutionSignal]:
        """Execute the graph using cursor traversal.
        
        Args:
            upper_graph: The graph from the layer above (for context)
            context: Execution context
        """
        if not self._graph:
            # Create our graph based on the upper graph, if needed
            assert upper_graph is not None
            self._graph = self._create_graph(upper_graph, upper_graph.objective, context)
        
        # Use cursor on our own graph
        cursor = self._graph.start_cursor()

        signals = []
        while (current := cursor.next()) is not None:
            indent = ""
            if self.__class__.__name__ == "PlanExecutor":
                indent = "          "
            elif self.__class__.__name__ == "ReasoningExecutor":
                indent = "                 "
            print(f"{indent}Executing {self.__class__.__name__} node {current.node_id}")

            try:
                assert self.graph is not None
                self.graph.update_node_status(current.node_id, ExecutionNodeStatus.IN_PROGRESS)
                node = cast(ExecutionNode, current)
                node_signals = await self.execute_node(node, context)
                signals.extend(node_signals)
                self._process_node_signals(current.node_id, node_signals)
            # pylint: disable=broad-exception-caught
            except Exception as e:
                self._handle_node_error(current.node_id, str(e))
                signals.append(self._create_error_signal(current.node_id, str(e)))
                break
                
        return signals

    @abstractmethod
    async def execute_node(self, node: ExecutionNode, context: ExecutionContext) -> List[ExecutionSignal]:
        """Execute a single node. To be implemented by subclasses."""
        pass

    def _process_node_signals(self, node_id: str, signals: List[ExecutionSignal]) -> None:
        """Process signals from node execution."""
        if not self.graph:
            raise ExecutionError("No graph to process signals")
        
        for signal in signals:
            if signal.type == ExecutionSignalType.RESULT:
                self.graph.update_node_status(node_id, ExecutionNodeStatus.COMPLETED)
            elif signal.type == ExecutionSignalType.ERROR:
                self.graph.update_node_status(node_id, ExecutionNodeStatus.FAILED)

    def _handle_node_error(self, node_id: str, error: str) -> None:
        """Handle node execution error."""
        print(f"Error handling node {node_id}: {error}")
        if self.graph:
            self.graph.update_node_status(node_id, ExecutionNodeStatus.FAILED)

    def _create_error_signal(self, node_id: str, error: str) -> ExecutionSignal:
        """Create error signal."""
        return ExecutionSignal(
            type=ExecutionSignalType.ERROR,
            content={"node": node_id, "error": error}
        )

    @abstractmethod
    def _create_graph(self, 
                      upper_graph: ExecutionGraph, 
                      objective: Optional[Objective] = None, 
                      context: Optional[ExecutionContext] = None) -> ExecutionGraph:
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
    
