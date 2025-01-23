"""Pipeline executor implementation."""

from typing import Dict, Any, Optional, List
from ...execution import (
    Executor, ExecutionNode, ExecutionGraph,
    ExecutionSignal, ExecutionContext
)
from .pipeline import PipelineNode

class PipelineExecutor(Executor):
    """Executes pipeline steps in sequence."""

    async def execute_node(
        self,
        node: ExecutionNode,
        context: ExecutionContext,
        prev_signals: List[ExecutionSignal],
        upper_signals: Optional[List[ExecutionSignal]] = None
    ) -> List[ExecutionSignal]:
        """Execute a pipeline step."""
        if not isinstance(node, PipelineNode):
            raise TypeError(f"Expected PipelineNode, got {type(node)}")
        try:
            data = context.buffer_data.get(node.node_id, {})
            result = await node.execute(data)
            return [self.create_result_signal(node.node_id, result)]
        except Exception as e:  # pylint: disable=broad-except
            return [self.create_error_signal(node.node_id, str(e))]

    def _create_graph(
        self,
        upper_graph: ExecutionGraph,
        objective: Optional[Any] = None,
        context: Optional[ExecutionContext] = None
    ) -> ExecutionGraph:
        """Create execution graph - for pipeline this is already built."""
        return upper_graph 