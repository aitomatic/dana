"""Progress reporting for DXA agents.

This module provides the AgentProgress class for reporting task progress and results
during agent execution. It enables agents to provide real-time feedback about their
operations.

Example:
    ```python
    async for progress in agent.run_with_progress(task):
        if progress.is_progress:
            print(f"Progress: {progress.percent}% - {progress.message}")
        elif progress.is_result:
            if progress.result["success"]:
                print("Task completed successfully")
            else:
                print(f"Task failed: {progress.result['error']}")
    ```
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class AgentProgress:
    """Represents agent progress updates during task execution.
    
    This class provides a standardized way for agents to report their progress
    and results during task execution. It can represent both intermediate progress
    updates and final results.
    
    Attributes:
        type: Update type ("progress" or "result")
        message: Human-readable progress message
        percent: Optional completion percentage (0-100)
        result: Optional result dictionary for final updates
        
    Example:
        ```python
        # Progress update
        progress = AgentProgress(
            type="progress",
            message="Processing data",
            percent=45
        )
        
        # Result update
        result = AgentProgress(
            type="result",
            message="Task completed",
            percent=100,
            result={"success": True, "output": "..."}
        )
        ```
    """
    type: str  # "progress" or "result"
    message: str
    percent: Optional[float] = None
    result: Optional[Dict[str, Any]] = None

    @property
    def is_progress(self) -> bool:
        """Check if this is a progress update.
        
        Returns:
            True if this is a progress update, False if it's a result
        """
        return self.type == "progress"

    @property
    def is_result(self) -> bool:
        """Check if this is a final result.
        
        Returns:
            True if this is a result update, False if it's a progress update
        """
        return self.type == "result" 