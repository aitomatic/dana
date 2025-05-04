"""Pipeline context for OpenDXA."""

from typing import Dict, Any, Optional
import asyncio
from datetime import datetime
from opendxa.base.execution import RuntimeContext
from opendxa.common.mixins.loggable import Loggable

class PipelineContext(RuntimeContext, Loggable):
    """Context for pipeline execution."""

    def __init__(self,
                 agent_state: Optional[Dict[str, Any]] = None,
                 world_state: Optional[Dict[str, Any]] = None,
                 execution_state: Optional[Dict[str, Any]] = None,
                 state_handlers: Optional[Dict[str, Dict[str, Any]]] = None):
        """Initialize pipeline context.
        
        Args:
            agent_state: Optional agent state
            world_state: Optional world state
            execution_state: Optional execution state
            state_handlers: Optional state handlers
        """
        super().__init__(
            agent_state=agent_state or {},
            world_state=world_state or {},
            execution_state=execution_state or {},
            state_handlers=state_handlers or {}
        )
        Loggable.__init__(self)
        self.buffers: Dict[str, asyncio.Queue] = {}
        self.buffer_metrics: Dict[str, Dict[str, Any]] = {}
        self.buffer_data: Dict[str, Any] = {}

    async def setup_buffer(self, node_id: str, size: int = 1000) -> None:
        """Setup buffer for node."""
        self.buffers[node_id] = asyncio.Queue(maxsize=size)
        self.buffer_metrics[node_id] = {
            "created": datetime.now(),
            "messages_processed": 0,
            "last_activity": datetime.now()
        }

    async def send_data(self, node_id: str, data: Any) -> None:
        """Send data to node buffer."""
        if node_id in self.buffers:
            buffer = self.buffers[node_id]
            if buffer.full():
                self.warning("Buffer %s full", node_id, size=buffer.qsize())
            await buffer.put(data)
            self.buffer_metrics[node_id]["messages_processed"] += 1
            self.buffer_metrics[node_id]["last_activity"] = datetime.now()

    async def receive_data(self, node_id: str) -> Optional[Any]:
        """Receive data from node buffer."""
        if node_id in self.buffers:
            try:
                data = await asyncio.wait_for(self.buffers[node_id].get(), timeout=0.1)
                self.buffer_metrics[node_id]["last_activity"] = datetime.now()
                return data
            except asyncio.TimeoutError:
                return None
        return None

    async def cleanup_buffers(self) -> None:
        """Cleanup all buffers."""
        self.debug("Cleaning up pipeline buffers (count: %d)", len(self.buffers))
        for buffer in self.buffers.values():
            while not buffer.empty():
                try:
                    buffer.get_nowait()
                except asyncio.QueueEmpty:
                    break 