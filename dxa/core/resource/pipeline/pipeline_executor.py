"""Pipeline executor implementation.

This module provides the execution engine for pipeline resources, handling:
- Step execution and data flow
- Buffer management
- Resource lifecycle
- Error handling
"""

import asyncio
from typing import Dict, Any
from ..base_resource import BaseResource
from .pipeline_resource import PipelineResource
from .pipeline_types import PipelineStep, PipelineData

class PipelineExecutor:
    """Executes pipeline steps in sequence.
    
    Handles step execution, buffer management, and cleanup.
    """
    
    async def setup_buffers(self, pipeline: PipelineResource) -> None:
        """Setup pipeline step buffers."""
        for i, _ in enumerate(pipeline.nodes):
            buffer_name = f"{pipeline.name}_step_{i}"
            pipeline.context.buffers[buffer_name] = asyncio.Queue(
                maxsize=pipeline.buffer_size
            )

    async def execute_step(self, step: PipelineStep, data: PipelineData) -> PipelineData:
        """Execute single pipeline step."""
        if isinstance(step, BaseResource):
            if not step._is_available:
                await step.initialize()
            return await step.query(data)
        return await step(data)

    async def execute(self, pipeline: PipelineResource) -> PipelineData:
        """Execute full pipeline."""
        await self.setup_buffers(pipeline)
        data: PipelineData = {}
        
        try:
            for node in pipeline.nodes.values():
                step = node["step"]
                node_id = node["id"]
                
                # Process through buffers
                input_buffer = pipeline.context.buffers.get(node_id)
                if input_buffer:
                    await input_buffer.put(data)
                
                data = await self.execute_step(step, data)
                
                # Get next node's buffer
                next_nodes = pipeline.get_next_nodes(node_id)
                if next_nodes:
                    next_buffer = pipeline.context.buffers.get(next_nodes[0]["id"])
                    if next_buffer:
                        await next_buffer.put(data)
            
            return data
            
        finally:
            # Cleanup
            for node in pipeline.nodes.values():
                step = node["step"]
                if isinstance(step, BaseResource):
                    await step.cleanup()
            
            for buffer in pipeline.context.buffers.values():
                while not buffer.empty():
                    try:
                        buffer.get_nowait()
                    except asyncio.QueueEmpty:
                        break 