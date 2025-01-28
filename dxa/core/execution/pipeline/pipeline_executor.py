"""Pipeline executor implementation."""

from typing import Any, Optional, List, cast
from ...execution import (
    Executor, ExecutionNode, ExecutionGraph,
    ExecutionSignal, ExecutionContext,
    ExecutionSignalType
)
from .pipeline import PipelineNode
from .pipeline_context import PipelineContext

class PipelineExecutor(Executor):
    """Executes pipeline steps in sequence."""

    async def execute_node(
        self,
        node: ExecutionNode,
        context: ExecutionContext,
        prev_signals: Optional[List[ExecutionSignal]] = None,
        upper_signals: Optional[List[ExecutionSignal]] = None,
        lower_signals: Optional[List[ExecutionSignal]] = None
    ) -> List[ExecutionSignal]:
        """Execute a pipeline step."""
        if not isinstance(node, PipelineNode):
            raise TypeError(f"Expected PipelineNode, got {type(node)}")

        node = cast(PipelineNode, node)
        context = cast(PipelineContext, context)
        try:
            data = {}  # Initialize with empty dict as default

            # 1. Check DATA_RESULT signals (primary)
            if prev_signals and prev_signals[-1].type == ExecutionSignalType.DATA_RESULT:
                data = prev_signals[-1].content.get("result", {})

            # 2. Fallback to Buffer Data (if signals not available and buffer enabled)
            if data is None and node.buffer_config["enabled"]:  # Check if data is still empty (no signal data)
                buffer_data = await context.receive_data(node.node_id)
                if buffer_data:
                    data = buffer_data  # Use buffer data if available and buffer enabled
                else:
                    data = {}  # if buffer enabled but no data, default to empty dict

            # 3. If neither signal nor buffer data, data remains empty dict (default)

            # Execute the step
            result = await node.execute(data)
            
            # Create and return result signal
            return [self.create_result_signal(node.node_id, result)]

        except Exception as e:  # pylint: disable=broad-except
            return [self.create_error_signal(node.node_id, str(e))]

    # pylint: disable=unused-argument
    def _should_propagate_down(self, signal: ExecutionSignal) -> bool:
        """Pipelines are flat, so no downward propagation."""
        # Add logic here to filter downward signals
        return False

    def _should_propagate_up(self, signal: ExecutionSignal) -> bool:
        """Pipelines are flat, so no upward propagation."""
        # Add logic here to filter upward signals
        return False

    def _create_graph(
        self,
        upper_graph: ExecutionGraph,
        objective: Optional[Any] = None,
        context: Optional[ExecutionContext] = None
    ) -> ExecutionGraph:
        """Create execution graph - for pipeline this is already built."""
        return upper_graph 