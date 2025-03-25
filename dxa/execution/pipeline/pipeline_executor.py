"""Pipeline executor implementation."""

from time import perf_counter
from typing import Any, Optional, List, cast
from ...execution.executor import Executor
from ...execution import (
    ExecutionNode, ExecutionGraph,
    ExecutionSignal, ExecutionContext,
    ExecutionSignalType, Objective
)
from .pipeline import PipelineNode, Pipeline
from .pipeline_context import PipelineContext
from ...common import DXA_LOGGER

class PipelineExecutor(Executor):
    """Executes pipeline steps in sequence."""

    async def execute(self, pipeline: 'Pipeline', context: 'PipelineContext') -> List[ExecutionSignal]:
        """Execute the entire pipeline.
        
        Args:
            pipeline: The pipeline to execute
            context: The execution context
            
        Returns:
            List of execution signals from the terminal node
        """
        DXA_LOGGER.info("Executing pipeline '%s'", pipeline.name)
        start_time = perf_counter()
        
        # Get the start node and execute the pipeline
        start_node = pipeline.get_start_node()
        if not start_node:
            raise ValueError("Pipeline has no start node")
            
        # Execute the pipeline starting from the start node
        signals = await self.execute_node(start_node, context)
        
        # Process each node in sequence
        current_node_id = start_node.node_id
        while signals and pipeline.get_next_nodes(current_node_id):
            next_nodes = pipeline.get_next_nodes(current_node_id)
            if not next_nodes:
                break
                
            next_node = next_nodes[0]  # Pipeline is linear, so take first node
            signals = await self.execute_node(next_node, context, prev_signals=signals)
            current_node_id = next_node.node_id
            
        duration = perf_counter() - start_time
        DXA_LOGGER.info("Pipeline '%s' execution completed in %.4fs", pipeline.name, duration)
        return signals

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
        DXA_LOGGER.info("Executing pipeline node %s of type %s", node.node_id, node.node_type)
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
            start_time = perf_counter()
            
            result = await node.execute(data)
            
            duration = perf_counter() - start_time
            data_keys = list(result.keys())
            
            if DXA_LOGGER.log_data:
                DXA_LOGGER.debug(
                    "Node %s completed in %.4fs with data keys: %s. Result data: %s",
                    node.node_id, duration, data_keys, result
                )
            else:
                result_sample = str(result)[:100]
                DXA_LOGGER.debug(
                    "Node %s completed in %.4fs with data keys: %s. Result sample: %s",
                    node.node_id, duration, data_keys, result_sample
                )

            # Create and return result signal
            return [self.create_result_signal(node.node_id, result)]

        except Exception as e:  # pylint: disable=broad-except
            DXA_LOGGER.error("Node %s failed: %s", node.node_id, str(e))
            return [self._create_error_signal(node.node_id, str(e))]

    # pylint: disable=unused-argument
    def _should_propagate_down(self, signal: ExecutionSignal) -> bool:
        """Pipelines are flat, so no downward propagation."""
        # Add logic here to filter downward signals
        return False

    def _should_propagate_up(self, signal: ExecutionSignal) -> bool:
        """Pipelines are flat, so no upward propagation."""
        # Add logic here to filter upward signals
        return False

    def create_graph_from_upper_node(
        self,
        upper_node: Optional[ExecutionNode] = None,
        upper_graph: Optional[ExecutionGraph] = None,
        objective: Optional[Any] = None,
        context: Optional[ExecutionContext] = None
    ) -> ExecutionGraph:
        """Create execution graph - for pipeline this is already built."""
        # For pipelines, we typically use the provided graph directly
        # If we already have a graph, return it
        if self.graph is not None:
            return self.graph
            
        # If no graph is available, create a minimal one
        return ExecutionGraph(objective=objective or Objective("Pipeline execution")) 