"""Runtime components for DXA agents.

This module provides the execution infrastructure for agents:

1. State Management:
   - Tracks agent state and history
   - Manages observations and messages
   - Maintains working memory

2. Progress Tracking:
   - Monitors execution progress
   - Provides status updates
   - Handles iteration control

3. Execution Flow:
   - Manages reasoning steps
   - Handles pre/post execution hooks
   - Controls execution lifecycle

Example:
    ```python
    state_manager = StateManager("researcher")
    runtime = AgentRuntime(state_manager)
    
    result = await runtime.execute(
        task={"objective": "Research quantum computing"},
        reasoning_step=reasoning.reason,
        pre_execute=setup,
        post_execute=cleanup
    )
    ```
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, AsyncIterator, Callable, Awaitable
from dxa.common.errors import DXAError

# Type aliases
ReasoningStep = Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]
ExecutionHook = Callable[[Dict[str, Any]], Awaitable[None]]
ContinuationCheck = Callable[[Dict[str, Any]], Awaitable[bool]]

@dataclass 
class AgentState:
    """Current state of an agent.
    
    Attributes:
        name: Agent identifier
        status: Current status
        timestamp: State update time
        metadata: Additional state information
    """
    name: str
    status: str
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Observation:
    """An observation made by the agent.
    
    Attributes:
        content: Observation content
        source: Origin of observation
        timestamp: When observed
        metadata: Additional context
    """
    content: Any
    source: str
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Message:
    """A message in the agent's communication.
    
    Attributes:
        content: Message content
        sender: Message origin
        receiver: Message destination
        timestamp: When sent
        metadata: Additional context
    """
    content: str
    sender: str
    receiver: str
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AgentProgress:
    """Progress updates during task execution.
    
    Attributes:
        type: "progress" or "result"
        message: Status message
        percent: Completion percentage
        result: Final result if complete
    """
    type: str  # "progress" or "result"
    message: str
    percent: Optional[float] = None
    result: Optional[Dict[str, Any]] = None

    @property
    def is_progress(self) -> bool:
        return self.type == "progress"

    @property
    def is_result(self) -> bool:
        return self.type == "result" 

class StateManager:
    """Manages agent state and execution context.
    
    Handles:
    - State transitions
    - Observation recording
    - Message tracking
    - Working memory
    """
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.state = AgentState(name=agent_name, status="initializing")
        self.observations: List[Observation] = []
        self.messages: List[Message] = []
        self.working_memory: Dict[str, Any] = {}

    def update_state(self, status: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        self.state = AgentState(name=self.agent_name, status=status, metadata=metadata or {})

    def add_observation(self, content: Any, source: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        self.observations.append(Observation(content=content, source=source, metadata=metadata or {}))

    def add_message(self, content: str, sender: str, receiver: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        self.messages.append(Message(content=content, sender=sender, receiver=receiver, metadata=metadata or {}))

    def get_recent_observations(self, n: int = 5) -> List[Observation]:
        return self.observations[-n:]

    def get_recent_messages(self, n: int = 5) -> List[Message]:
        return self.messages[-n:]

    def clear_history(self) -> None:
        self.observations.clear()
        self.messages.clear()
        self.working_memory.clear()

class AgentRuntime:
    """Manages the execution lifecycle of an agent.
    
    Handles:
    - Task execution flow
    - Progress monitoring
    - State management
    - Resource lifecycle
    
    Args:
        state_manager: Manages agent state
        max_iterations: Optional iteration limit
    """
    
    def __init__(self, state_manager: StateManager, max_iterations: Optional[int] = None):
        self.state_manager = state_manager
        self.max_iterations = max_iterations
        self.iteration_count = 0
        self._is_running = False

    async def execute_with_progress(
        self,
        task: Dict[str, Any],
        reasoning_step: ReasoningStep,
        pre_execute: Optional[ExecutionHook] = None,
        post_execute: Optional[ExecutionHook] = None,
        should_continue: Optional[ContinuationCheck] = None,
        context: Optional[Any] = None
    ) -> AsyncIterator[AgentProgress]:
        """Execute task with progress updates.
        
        Args:
            task: Task to execute
            reasoning_step: Core reasoning function
            pre_execute: Setup hook
            post_execute: Cleanup hook
            should_continue: Continuation check
            context: Execution context
            
        Yields:
            Progress updates and final result
        """
        try:
            yield AgentProgress(type="progress", message="Starting execution", percent=0)
            
            task_context = task.copy()
            self._is_running = True
            self.iteration_count = 0
            
            if pre_execute:
                await pre_execute(context or task_context)
                yield AgentProgress(type="progress", message="Setup complete", percent=10)
            
            while self._is_running:
                if self.max_iterations and self.iteration_count >= self.max_iterations:
                    self.state_manager.add_observation("Reached maximum iterations", "runtime")
                    break
                
                self.iteration_count += 1
                result = await reasoning_step(task_context)
                
                percent = min(90, (self.iteration_count / (self.max_iterations or 10)) * 80 + 10)
                yield AgentProgress(
                    type="progress",
                    message=f"Completed iteration {self.iteration_count}",
                    percent=percent,
                    result={"iteration_result": result}
                )
                
                task_context.update(result)
                
                if result.get("task_complete") or result.get("is_stuck"):
                    break
                    
                if should_continue and not await should_continue(result):
                    break
            
            if post_execute:
                result = await post_execute(result)
            
            yield AgentProgress(
                type="result",
                message="Execution complete",
                percent=100,
                result={
                    "success": True,
                    "iterations": self.iteration_count,
                    "results": result,
                    "state_history": {
                        "observations": self.state_manager.observations,
                        "messages": self.state_manager.messages
                    }
                }
            )
            
        except DXAError as e:
            self.state_manager.add_observation(
                f"Runtime error: {str(e)}",
                "runtime",
                {"error_type": e.__class__.__name__}
            )
            
            yield AgentProgress(
                type="result",
                message=f"Execution failed: {str(e)}",
                percent=100,
                result={
                    "success": False,
                    "error": str(e),
                    "iterations": self.iteration_count,
                    "state_history": {
                        "observations": self.state_manager.observations,
                        "messages": self.state_manager.messages
                    }
                }
            )

    async def execute(
        self,
        task: Dict[str, Any],
        reasoning_step: ReasoningStep,
        pre_execute: Optional[ExecutionHook] = None,
        post_execute: Optional[ExecutionHook] = None,
        should_continue: Optional[ContinuationCheck] = None,
        context: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Execute task and return result.
        
        Args:
            task: Task to execute
            reasoning_step: Core reasoning function
            pre_execute: Setup hook
            post_execute: Cleanup hook
            should_continue: Continuation check
            context: Execution context
            
        Returns:
            Execution result
        """
        async for progress in self.execute_with_progress(
            task=task,
            reasoning_step=reasoning_step,
            pre_execute=pre_execute,
            post_execute=post_execute,
            should_continue=should_continue,
            context=context
        ):
            if progress.is_result:
                return progress.result 

    async def cleanup(self) -> None:
        """Clean up runtime resources.
        
        Handles:
        - State manager cleanup
        - Iteration counter reset
        - Running state reset
        """
        # Reset runtime state
        self.iteration_count = 0
        self._is_running = False
        
        # Clean up state manager
        self.state_manager.clear_history()