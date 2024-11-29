"""WebSocket-based agent implementation.

This module provides an agent implementation that communicates through WebSocket
connections. It enables real-time bidirectional communication and maintains
connection state.

Example:
    ```python
    from dxa.agents.websocket import WebSocketAgent
    from dxa.core.reasoning import ChainOfThoughtReasoning
    
    agent = WebSocketAgent(
        name="remote_solver",
        config={
            "model": "gpt-4",
            "api_key": "your-key"
        },
        reasoning=ChainOfThoughtReasoning(),
        websocket_url="wss://your-server.com/agent"
    )
    
    result = await agent.run({
        "task": "solve_problem",
        "data": {"problem": "..."}
    })
    ```
"""

import json
from typing import Dict, Any, Optional, Union
from dxa.agent.base_agent import BaseAgent
from dxa.core.io.websocket import WebSocketIO
from dxa.common.errors import WebSocketError, DXAConnectionError
from dxa.core.reasoning import BaseReasoning, ChainOfThoughtReasoning

JsonMessage = Union[str, Dict[str, Any]]

class WebSocketAgent(BaseAgent):
    """Agent that interacts through WebSocket I/O.
    
    This agent type extends BaseAgent with WebSocket communication capabilities.
    It maintains a persistent connection and handles network-related errors.
    
    Attributes:
        All attributes inherited from BaseAgent
        io: WebSocket I/O handler
        
    Args:
        name: Agent identifier
        config: Configuration dictionary
        websocket_url: URL for WebSocket connection
        reasoning: Optional reasoning system (defaults to ChainOfThoughtReasoning)
        reconnect_attempts: Maximum reconnection attempts (default: 3)
        reconnect_delay: Delay between reconnection attempts in seconds (default: 1.0)
        max_iterations: Optional maximum iterations
    """
    
    def __init__(
        self,
        name: str,
        config: Dict[str, Any],
        websocket_url: str,
        reasoning: Optional[BaseReasoning] = None,
        reconnect_attempts: int = 3,
        reconnect_delay: float = 1.0,
        max_iterations: Optional[int] = None
    ):
        """Initialize WebSocket agent."""
        super().__init__(
            name=name,
            config=config,
            reasoning=reasoning or ChainOfThoughtReasoning(),
            mode="websocket",
            max_iterations=max_iterations
        )
        
        self.io = WebSocketIO(
            url=websocket_url,
            max_retries=reconnect_attempts,
            retry_delay=reconnect_delay
        )

    async def _send_message(self, message: JsonMessage) -> None:
        """Send a message through WebSocket.
        
        Args:
            message: Message to send (string or JSON-serializable dict)
            
        Raises:
            WebSocketError: If message sending fails
        """
        try:
            if isinstance(message, dict):
                message = json.dumps(message)
            await self.io.send_message(message)
        except (WebSocketError, TypeError) as e:
            raise WebSocketError(f"Failed to send message: {str(e)}") from e

    async def _pre_execute(self, context: Dict[str, Any]) -> None:
        """Establish WebSocket connection.
        
        Args:
            context: Initial execution context
            
        Raises:
            DXAConnectionError: If connection cannot be established
        """
        try:
            await self.io.initialize()
            
            # Send initial connection message
            await self._send_message({
                "type": "agent_connected",
                "agent_name": self.name,
                "mode": self.mode
            })
            
            # Get initial input if needed
            if 'initial_input' not in context:
                response = await self.io.get_input("Ready for input")
                try:
                    # Try to parse as JSON first
                    context['initial_input'] = json.loads(response)
                except json.JSONDecodeError:
                    # Fall back to string if not valid JSON
                    context['initial_input'] = response
                
        except WebSocketError as e:
            raise DXAConnectionError(f"Failed to establish WebSocket connection: {str(e)}") from e

    async def _post_execute(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Clean up WebSocket connection.
        
        Args:
            result: Results from final reasoning iteration
            
        Returns:
            Processed results with connection metadata
        """
        try:
            # Send completion message
            await self._send_message({
                "type": "execution_complete",
                "success": True,
                "results": result
            })
            
            # Clean up connection
            await self.io.cleanup()
            
        except WebSocketError as e:
            self.logger.log_error(
                error_type="websocket_cleanup_error",
                message=f"Error during WebSocket cleanup: {str(e)}"
            )
            
        result.update({
            "agent_type": "websocket",
            "execution_mode": self.mode
        })
        return result

    async def _should_continue(self, result: Dict[str, Any]) -> bool:
        """Check connection and task status.
        
        Args:
            result: Results from last reasoning iteration
            
        Returns:
            False if task is complete or connection is lost, True otherwise
        """
        # Check completion conditions
        if result.get("task_complete") or result.get("is_stuck"):
            return False
            
        # Try to send a ping to check connection
        try:
            await self._send_message({"type": "ping"})
            return True
        except WebSocketError:
            return False

    async def _reasoning_step(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute one reasoning iteration with WebSocket communication.
        
        Args:
            context: Current execution context
            
        Returns:
            Dict containing reasoning results and communication status
            
        Raises:
            DXAConnectionError: If WebSocket communication fails
        """
        try:
            # Send context update
            await self._send_message({
                "type": "iteration_start",
                "iteration": self.runtime.iteration_count,
                "context": context
            })
            
            # Run reasoning
            result = await self.reasoning.reason(context)
            
            # Send results
            await self._send_message({
                "type": "iteration_complete",
                "iteration": self.runtime.iteration_count,
                "results": result
            })
            
            return result
            
        except WebSocketError as e:
            raise DXAConnectionError(f"WebSocket communication failed: {str(e)}") from e
