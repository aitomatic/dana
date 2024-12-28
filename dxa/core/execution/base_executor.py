"""Base class for components that manage execution graphs."""

from abc import ABC, abstractmethod
from typing import Optional, List
from .execution_types import (
    ExecutionNode,
    ExecutionSignal,
    ExecutionContext,
    ExecutionSignalType,
    Objective,
    ExecutionNodeStatus,
    ExecutionError
)
from .execution_graph import ExecutionGraph

class BaseExecutor(ABC):
    """Base class for execution control."""
    
    def __init__(self):
        self.graph: Optional[ExecutionGraph] = None
        self._current_node_id: Optional[str] = None

    async def execute(self, context: ExecutionContext) -> List[ExecutionSignal]:
        """Main execution loop."""
        if not self.graph:
            raise ExecutionError("No graph initialized")
            
        signals = []
        current = self.graph.get_start_node()
        if not current:
            raise ExecutionError("Graph has no start node")
        
        while current and not self.graph.is_complete():
            # Update status to in progress
            self.graph.update_node_status(current.node_id, ExecutionNodeStatus.IN_PROGRESS)
            
            try:
                # Execute current node
                node_signals = await self.execute_node(current, context)
                signals.extend(node_signals)
                
                # Process signals and get next node
                self.process_signals(node_signals)
                current = self._get_next_node(current.node_id, context)
            # pylint: disable=broad-exception-caught
            except Exception as e:
                self.graph.update_node_status(current.node_id, ExecutionNodeStatus.FAILED)
                signals.append(ExecutionSignal(
                    ExecutionSignalType.STEP_FAILED,
                    {"node": current.node_id, "error": str(e)}
                ))
                break
            
        return signals

    @abstractmethod
    async def execute_node(self, node: ExecutionNode, context: ExecutionContext) -> List[ExecutionSignal]:
        """Execute a single node."""
        pass

    @abstractmethod 
    async def initialize(self, objective: Objective) -> None:
        """Initialize execution graph."""
        pass 

    def process_signals(self, signals: List[ExecutionSignal]) -> None:
        """Process execution signals."""
        if not self.graph:
            return
        for signal in signals:
            if signal.type == ExecutionSignalType.STEP_COMPLETE:
                node_id = signal.content.get("node")
                if node_id:
                    node = self.graph.get_step(node_id)
                    if node and node.status == ExecutionNodeStatus.IN_PROGRESS:
                        self.graph.update_node_status(node_id, ExecutionNodeStatus.COMPLETED)
            elif signal.type == ExecutionSignalType.STEP_FAILED:
                node_id = signal.content.get("node")
                if node_id:
                    self.graph.update_node_status(node_id, ExecutionNodeStatus.FAILED)

    def _get_next_node(self, current_id: str, context: ExecutionContext) -> Optional[ExecutionNode]:
        """Get next executable node."""
        if not self.graph:
            return None
        valid_nodes = self.graph.get_valid_transitions(current_id, context)
        # Filter out nodes that are already completed or failed
        valid_nodes = [
            n for n in valid_nodes if n.status not in (ExecutionNodeStatus.COMPLETED, ExecutionNodeStatus.FAILED)
        ]
        return valid_nodes[0] if valid_nodes else None 