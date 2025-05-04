"""Step execution result representation."""

from typing import Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field

class StepStatus(Enum):
    """Status of a step execution."""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    IN_PROGRESS = "IN_PROGRESS"

class StepResult(BaseModel):
    """Represents the result of executing a step.
    
    Attributes:
        step_id: ID of the step that was executed
        status: Execution status of the step
        output: Output from the step execution
        metrics: Optional metrics about the execution
        environment_updates: Optional updates to the environment state
    """
    step_id: str = Field(description="ID of the step that was executed")
    status: StepStatus = Field(description="Execution status of the step")
    output: Dict[str, Any] = Field(description="Output from the step execution")
    metrics: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional metrics about the execution")
    environment_updates: Optional[Dict[str, Any]] = Field(default=None, description="Optional updates to the environment state")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StepResult':
        """Create a StepResult from a dictionary.
        
        Args:
            data: Dictionary containing step result data
            
        Returns:
            StepResult instance
            
        Raises:
            ValueError: If required fields are missing or invalid
        """
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")
            
        required_fields = ['step_id', 'status', 'output']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
                
        try:
            status = StepStatus(data['status'])
        except ValueError:
            raise ValueError(f"Invalid status value: {data['status']}")
            
        return cls(
            step_id=data['step_id'],
            status=status,
            output=data['output'],
            metrics=data.get('metrics', {}),
            environment_updates=data.get('environment_updates')
        ) 