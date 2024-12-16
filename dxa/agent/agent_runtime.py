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
    
    context = ReasoningContext(
        objective="Research quantum computing",
        resources={},
        workspace={},
        history=[]
    )
    
    result = await runtime.execute(
        task={"objective": "Research quantum computing"},
        reasoning_step=reasoning.reason_about,
        pre_execute=setup,
        post_execute=cleanup,
        context=context
    )
    ```
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, AsyncIterator, Callable, Awaitable
from dxa.common.errors import DXAError
from dxa.core.reasoning import ReasoningContext, ReasoningResult, ReasoningTask

# Type aliases
DoReasoning = Callable[[ReasoningTask, ReasoningContext], Awaitable[ReasoningResult]]
"""Core reasoning function that processes a task."""

PreReasoning = Callable[[ReasoningContext], Awaitable[None]]
"""Setup hook called before reasoning starts."""

PostReasoning = Callable[[ReasoningContext, ReasoningResult], Awaitable[ReasoningResult]]
"""Cleanup/post-processing hook called after reasoning completes."""

ContinueReasoning = Callable[[ReasoningContext, ReasoningResult], Awaitable[bool]]
"""Function that decides whether to continue execution.

Args:
    context: Current reasoning context
    result: Latest reasoning result
Returns:
    True if execution should continue
"""

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

    def update_metadata(self, metadata: Dict[str, Any]) -> None:
        """Update state metadata."""
        self.metadata.update(metadata)

    def reset(self) -> None:
        """Reset state to initial values."""
        self.status = "initializing"
        self.metadata.clear()

    @property
    def is_initialized(self) -> bool:
        """Check if state is initialized."""
        return self.status != "initializing"

    @property
    def age(self) -> float:
        """Get age of state in seconds."""
        return datetime.now().timestamp() - self.timestamp

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value by key."""
        return self.metadata.get(key, default)

    def clear_metadata(self) -> None:
        """Clear all metadata."""
        self.metadata.clear()

    def validate_status(self, allowed_statuses: List[str]) -> bool:
        """Check if current status is in allowed list."""
        return self.status in allowed_statuses

    def validate_metadata(self, required_keys: List[str]) -> bool:
        """Check if all required metadata keys exist."""
        return all(key in self.metadata for key in required_keys)

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

    def add_metadata(self, metadata: Dict[str, Any]) -> None:
        """Add additional metadata to observation."""
        self.metadata.update(metadata)

    @property
    def age(self) -> float:
        """Get age of observation in seconds."""
        return datetime.now().timestamp() - self.timestamp

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

    def add_metadata(self, metadata: Dict[str, Any]) -> None:
        """Add additional metadata to message."""
        self.metadata.update(metadata)

    @property
    def age(self) -> float:
        """Get age of message in seconds."""
        return datetime.now().timestamp() - self.timestamp

@dataclass
class AgentProgress:
    """Progress updates during task execution.
    
    Attributes:
        type: "progress" or "result"
        message: Status message
        percent: Completion percentage
        result: Final result if complete
    
    Properties:
        is_progress: True if this is a progress update
        is_result: True if this is the final result
    """
    type: str  # "progress" or "result"
    message: str
    percent: Optional[float] = None
    result: Optional[Dict[str, Any]] = None

    @property
    def is_progress(self) -> bool:
        """Check if this is a progress update."""
        return self.type == "progress"

    @property
    def is_result(self) -> bool:
        """Check if this is the final result."""
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
        """Update agent state with new status and metadata."""
        self.state = AgentState(name=self.agent_name, status=status, metadata=metadata or {})

    def add_observation(self, content: Any, source: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Record a new observation."""
        self.observations.append(Observation(content=content, source=source, metadata=metadata or {}))

    def add_message(self, content: str, sender: str, receiver: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add a message to the communication history."""
        self.messages.append(Message(content=content, sender=sender, receiver=receiver, metadata=metadata or {}))

    def get_recent_observations(self, n: int = 5) -> List[Observation]:
        """Get the n most recent observations."""
        return self.observations[-n:]

    def get_recent_messages(self, n: int = 5) -> List[Message]:
        """Get the n most recent messages."""
        return self.messages[-n:]

    def clear_history(self) -> None:
        """Clear all history and reset state."""
        self.observations.clear()
        self.messages.clear()
        self.working_memory.clear()

    @property
    def current_state(self) -> AgentState:
        """Get current agent state."""
        return self.state

    @property
    def memory(self) -> Dict[str, Any]:
        """Get working memory."""
        return self.working_memory

    def set_memory(self, key: str, value: Any) -> None:
        """Set value in working memory."""
        self.working_memory[key] = value

    def get_memory(self, key: str, default: Any = None) -> Any:
        """Get value from working memory."""
        return self.working_memory.get(key, default)

    def validate_memory(self, required_keys: List[str]) -> bool:
        """Check if all required memory keys exist."""
        return all(key in self.working_memory for key in required_keys)

    def validate_state(self, allowed_statuses: List[str]) -> bool:
        """Check if current state is valid."""
        return self.state.validate_status(allowed_statuses)

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
        task: ReasoningTask,
        reasoning_step: DoReasoning,
        context: ReasoningContext,
        pre_execute: Optional[PreReasoning] = None,
        post_execute: Optional[PostReasoning] = None,
        should_continue: Optional[ContinueReasoning] = None,
    ) -> AsyncIterator[AgentProgress]:
        """Execute task with progress updates.
        
        Args:
            task: Task to execute
            reasoning_step: Core reasoning function (DoReasoning)
            context: ReasoningContext for execution
            pre_execute: Setup hook (PreReasoning)
            post_execute: Cleanup hook (PostReasoning)
            should_continue: Continuation check (ContinueReasoning)
            
        Yields:
            Progress updates and final result
        """
        try:
            yield AgentProgress(type="progress", message="Starting execution", percent=0)
            
            self._is_running = True
            self.iteration_count = 0
            
            if pre_execute:
                await pre_execute(context)
                yield AgentProgress(type="progress", message="Setup complete", percent=10)
            
            while self._is_running:
                if self.max_iterations and self.iteration_count >= self.max_iterations:
                    self.state_manager.add_observation("Reached maximum iterations", "runtime")
                    break
                
                self.iteration_count += 1
                result = await reasoning_step(task, context)
                
                percent = min(90, (self.iteration_count / (self.max_iterations or 10)) * 80 + 10)
                yield AgentProgress(
                    type="progress",
                    message=f"Completed iteration {self.iteration_count}",
                    percent=percent,
                    result={"iteration_result": result}
                )
                
                if not result.success or result.needs_objective_refinement:
                    break
                    
                if should_continue and not await should_continue(context, result):
                    break
            
            if post_execute:
                result = await post_execute(context, result)
            
            yield AgentProgress(
                type="result",
                message="Execution complete",
                percent=100,
                result={
                    "success": result.success,
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
        task: ReasoningTask,
        reasoning_step: DoReasoning,
        context: ReasoningContext,
        pre_execute: Optional[PreReasoning] = None,
        post_execute: Optional[PostReasoning] = None,
        should_continue: Optional[ContinueReasoning] = None,
    ) -> ReasoningResult:
        """Execute task and return final result only.
        
        This is a convenience wrapper around execute_with_progress() that
        returns only the final result without progress updates.
        """
        async for progress in self.execute_with_progress(
            task=task,
            reasoning_step=reasoning_step,
            context=context,
            pre_execute=pre_execute,
            post_execute=post_execute,
            should_continue=should_continue
        ):
            if progress.is_result:
                return progress.result["results"]

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

    @property
    def is_running(self) -> bool:
        """Check if runtime is currently executing."""
        return self._is_running

    @property
    def current_iteration(self) -> int:
        """Get current iteration count."""
        return self.iteration_count