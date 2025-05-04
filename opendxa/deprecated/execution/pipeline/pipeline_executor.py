"""Pipeline executor implementation."""

from time import perf_counter
from typing import Optional, cast
from opendxa.base.execution import BaseExecutor
from opendxa.base.execution.runtime_context import RuntimeContext
from opendxa.base.execution.execution_types import (
    ExecutionNode,
    ExecutionSignal,
    ExecutionStatus
)
from opendxa.execution.pipeline.pipeline import PipelineNode, Pipeline
from opendxa.execution.pipeline.pipeline_context import PipelineContext
from opendxa.execution.pipeline.pipeline_factory import PipelineFactory

class PipelineExecutor(BaseExecutor[PipelineNode, Pipeline]):
    """Executes pipeline steps in sequence."""

    # Class attributes for layer configuration
    graph_class = Pipeline
    _factory_class = PipelineFactory
    _depth = 0
    
    def __init__(
        self,
        factory: Optional[PipelineFactory] = None,
    ):
        """Initialize pipeline executor.
        
        Args:
            factory: Optional factory for creating graphs
        """
        super().__init__(factory=factory)

    async def execute_node_core(
        self,
        node: ExecutionNode,
        context: RuntimeContext
    ) -> ExecutionSignal:
        """Execute the core logic of a pipeline node.
        
        Args:
            node: The node to execute
            context: The execution context
            
        Returns:
            Execution signal indicating success or failure
        """
        if not isinstance(node, PipelineNode):
            raise TypeError(f"Expected PipelineNode, got {type(node)}")
        node = cast(PipelineNode, node)

        if not isinstance(context, PipelineContext):
            raise TypeError(f"Expected PipelineContext, got {type(context)}")
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
            return self._create_result_signal(node.node_id, result)

        except Exception as e:  # pylint: disable=broad-except
            self.error("Node %s failed: %s", node.node_id, str(e))
            return self._create_error_signal(node.node_id, str(e))

    def _create_result_signal(self, node_id: str, result: dict) -> ExecutionSignal:
        """Create a result signal for the node execution.
        
        Args:
            node_id: ID of the node that produced the result
            result: Result data from the node execution
            
        Returns:
            Execution signal with the result data
        """
        return ExecutionSignal(
            status=ExecutionStatus.COMPLETED,
            content={
                "node": node_id,
                "result": result
            }
        )
        
    def _create_error_signal(self, node_id: str, error: str) -> ExecutionSignal:
        """Create an error signal for the node execution.
        
        Args:
            node_id: ID of the node that failed
            error: Error message
            
        Returns:
            Execution signal with the error
        """
        return ExecutionSignal(
            status=ExecutionStatus.FAILED,
            node_id=node_id,
            message=error
        )
