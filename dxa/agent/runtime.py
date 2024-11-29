"""Runtime management for DXA agents.

This module provides the AgentRuntime class which standardizes execution patterns
across different agent types. It handles:

1. Execution lifecycle management
2. Progress reporting
3. State tracking
4. Error handling
5. Iteration control

The runtime uses a hook-based system that allows agents to customize behavior at key points:
- pre_execute: Setup before main execution loop
- reasoning_step: Core iteration logic
- post_execute: Cleanup and result processing
- should_continue: Custom continuation logic

Example:
    ```python
    # Create runtime with state manager
    runtime = AgentRuntime(
        state_manager=StateManager("my_agent"),
        max_iterations=10
    )
    
    # Define hooks
    async def reasoning_step(context):
        return await perform_reasoning(context)
        
    async def should_continue(result):
        return not result.get("complete")
    
    # Execute with progress updates
    async for progress in runtime.execute_with_progress(
        task={"objective": "analyze_data"},
        reasoning_step=reasoning_step,
        should_continue=should_continue
    ):
        if progress.is_progress:
            print(f"Progress: {progress.percent}%")
        else:
            print(f"Final result: {progress.result}")
    ```

The runtime provides two main execution methods:
1. execute_with_progress: Yields AgentProgress updates during execution
2. execute: Returns only the final result (wrapper around execute_with_progress)
"""

from typing import Dict, Any, Optional, AsyncIterator, Callable, Awaitable
from dxa.agent.state import StateManager
from dxa.agent.progress import AgentProgress
from dxa.common.errors import DXAError

# Type aliases for clarity
ReasoningStep = Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]
ExecutionHook = Callable[[Dict[str, Any]], Awaitable[None]]
ContinuationCheck = Callable[[Dict[str, Any]], Awaitable[bool]]

class AgentRuntime:
    """Manages the execution lifecycle of an agent.
    
    This class standardizes how agents execute tasks by providing:
    - Progress tracking and reporting
    - State management
    - Error handling
    - Iteration control
    - Customization hooks
    
    The runtime uses a hook-based architecture where agents can inject custom
    behavior at key points in the execution lifecycle:
    
    Execution Flow:
    1. Initialize context from task
    2. Run pre_execute hook (if provided)
    3. Enter main execution loop:
        - Check iteration limits
        - Run reasoning_step
        - Update context with results
        - Check completion conditions
        - Run should_continue check
    4. Run post_execute hook (if provided)
    5. Return final results
    
    Attributes:
        state_manager: Manages agent state and history
        max_iterations: Maximum number of iterations (None for unlimited)
        iteration_count: Current iteration count
        _is_running: Internal execution state flag
    """
    
    def __init__(
        self,
        state_manager: StateManager,
        max_iterations: Optional[int] = None
    ):
        """Initialize the runtime.
        
        Args:
            state_manager: StateManager instance for tracking agent state
            max_iterations: Optional maximum number of iterations
        """
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
        should_continue: Optional[ContinuationCheck] = None
    ) -> AsyncIterator[AgentProgress]:
        """Execute with progress updates.
        
        This method runs the agent's execution loop while yielding progress
        updates. It handles the complete execution lifecycle including setup,
        iteration, and cleanup.
        
        Args:
            task: Task configuration and parameters
            reasoning_step: Core reasoning function for each iteration
            pre_execute: Optional hook run before main execution
            post_execute: Optional hook run after main execution
            should_continue: Optional custom continuation check
            
        Yields:
            AgentProgress objects containing:
                - Progress updates during execution
                - Final results or error information
                
        Progress Reporting:
            - 0%: Starting execution
            - 10%: After pre-execution
            - 10-90%: During main execution loop
            - 100%: Final result or error
            
        State Management:
            - Tracks iterations
            - Records observations
            - Maintains execution context
            
        Error Handling:
            - Catches and processes DXAErrors
            - Records errors in state
            - Reports errors through progress updates
        """
        try:
            # Initial progress
            yield AgentProgress(
                type="progress",
                message="Starting execution",
                percent=0
            )
            
            context = task.copy()
            self._is_running = True
            self.iteration_count = 0
            
            # Pre-execution hook
            if pre_execute:
                await pre_execute(context)
                yield AgentProgress(
                    type="progress",
                    message="Completed pre-execution setup",
                    percent=10
                )
            
            while self._is_running:
                # Check iteration limit
                if (self.max_iterations and self.iteration_count >= self.max_iterations):
                    self.state_manager.add_observation(
                        "Reached maximum iterations",
                        source="runtime"
                    )
                    break
                
                # Run iteration
                self.iteration_count += 1
                result = await reasoning_step(context)
                
                # Calculate progress percentage
                if self.max_iterations:
                    percent = min(90, (self.iteration_count / self.max_iterations) * 80 + 10)
                else:
                    percent = min(90, self.iteration_count * 10 + 10)
                
                yield AgentProgress(
                    type="progress",
                    message=f"Completed iteration {self.iteration_count}",
                    percent=percent,
                    result={"iteration_result": result}
                )
                
                # Update context
                context.update(result)
                
                # Check completion
                if result.get("task_complete") or result.get("is_stuck"):
                    break
                    
                # Custom continuation check
                if should_continue and not await should_continue(result):
                    break
            
            # Post-execution hook
            if post_execute:
                result = await post_execute(result)
            
            # Final result
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
                source="runtime",
                metadata={"error_type": e.__class__.__name__}
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
        should_continue: Optional[ContinuationCheck] = None
    ) -> Dict[str, Any]:
        """Execute without progress updates.
        
        This is a convenience wrapper around execute_with_progress that returns
        only the final result. It provides the same execution flow and error
        handling but without intermediate progress updates.
        
        Args:
            task: Task configuration and parameters
            reasoning_step: Core reasoning function for each iteration
            pre_execute: Optional hook run before main execution
            post_execute: Optional hook run after main execution
            should_continue: Optional custom continuation check
            
        Returns:
            Dict containing:
                success: Whether execution completed successfully
                iterations: Number of iterations performed
                results: Results from final reasoning cycle
                state_history: Record of observations and messages
                error: Error information if execution failed
                
        Example:
            ```python
            result = await runtime.execute(
                task={"objective": "analyze_data"},
                reasoning_step=my_reasoning_step
            )
            
            if result["success"]:
                print(f"Completed in {result['iterations']} iterations")
                print(f"Results: {result['results']}")
            else:
                print(f"Failed: {result['error']}")
            ```
            
        Note:
            This method is best used when you don't need progress updates.
            For progress tracking, use execute_with_progress instead.
        """
        async for progress in self.execute_with_progress(
            task=task,
            reasoning_step=reasoning_step,
            pre_execute=pre_execute,
            post_execute=post_execute,
            should_continue=should_continue
        ):
            if progress.is_result:
                return progress.result 