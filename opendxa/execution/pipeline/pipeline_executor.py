"""Pipeline executor implementation."""

from time import perf_counter
from typing import Optional, List, cast
from ..base_executor import BaseExecutor
from ...execution import (
    ExecutionNode,
    ExecutionSignal, ExecutionContext,
    ExecutionSignalType
)
from .pipeline import PipelineNode, Pipeline
from .pipeline_context import PipelineContext
from .pipeline_strategy import PipelineStrategy
from .pipeline_factory import PipelineFactory

class PipelineExecutor(BaseExecutor[PipelineStrategy, Pipeline, PipelineFactory]):
    """Executes pipeline steps in sequence."""

    # Class attributes for layer configuration
    _strategy_type = PipelineStrategy
    _default_strategy = PipelineStrategy.DEFAULT
    graph_class = Pipeline
    _factory_class = PipelineFactory
    _depth = 0
    
    def __init__(
        self,
        strategy: Optional[PipelineStrategy] = None
    ):
        """Initialize pipeline executor.
        
        Args:
            strategy: Pipeline execution strategy
        """
        super().__init__(strategy=strategy)

    async def execute(
        self,
        graph: 'Pipeline',
        context: 'PipelineContext'
    ) -> List[ExecutionSignal]:
        """Execute the entire pipeline.
        
        Args:
            pipeline: The pipeline to execute
            context: The execution context
            
        Returns:
            List of execution signals from the terminal node
        """
        pipeline = cast(Pipeline, graph)
        self.info("Executing pipeline '%s'", pipeline.name)
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
            signals = await self.execute_node(next_node, context)
            current_node_id = next_node.node_id
            
        duration = perf_counter() - start_time
        self.info("Pipeline '%s' execution completed in %.4fs", pipeline.name, duration)
        return signals

    async def execute_node(
        self,
        node: ExecutionNode,
        context: ExecutionContext
    ) -> List[ExecutionSignal]:
        """Execute a pipeline step."""
        if not isinstance(node, PipelineNode):
            raise TypeError(f"Expected PipelineNode, got {type(node)}")

        node = cast(PipelineNode, node)
        context = cast(PipelineContext, context)
        self.info("Executing pipeline node %s of type %s", node.node_id, node.node_type)
        try:
            data = {}  # Initialize with empty dict as default

            # Get data from buffer if enabled
            if node.buffer_config["enabled"]:
                buffer_data = await context.receive_data(node.node_id)
                if buffer_data:
                    data = buffer_data  # Use buffer data if available and buffer enabled

            # Execute the step
            start_time = perf_counter()
            
            result = await node.execute(data)
            
            duration = perf_counter() - start_time
            data_keys = list(result.keys())
            
            if self.logger.log_data:
                self.debug(
                    "Node %s completed in %.4fs with data keys: %s. Result data: %s",
                    node.node_id, duration, data_keys, result
                )
            else:
                result_sample = str(result)[:100]
                self.debug(
                    "Node %s completed in %.4fs with data keys: %s. Result sample: %s",
                    node.node_id, duration, data_keys, result_sample
                )

            # Create and return result signal
            return [self._create_result_signal(node.node_id, result)]

        except Exception as e:  # pylint: disable=broad-except
            self.error("Node %s failed: %s", node.node_id, str(e))
            return [self._create_error_signal(node.node_id, str(e))]
            
    def _create_result_signal(self, node_id: str, result: dict) -> ExecutionSignal:
        """Create a result signal for the node execution.
        
        Args:
            node_id: ID of the node that produced the result
            result: Result data from the node execution
            
        Returns:
            Execution signal with the result data
        """
        return ExecutionSignal(
            type=ExecutionSignalType.DATA_RESULT,
            content={
                "node": node_id,
                "result": result
            }
        )
