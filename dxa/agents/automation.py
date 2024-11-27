"""Automation agent implementation."""

from typing import Dict, Any, Optional
from dxa.agents.autonomous import AutonomousAgent
from dxa.core.reasoning.ooda import OODAReasoning

class AutomationAgent(AutonomousAgent):
    """Agent for automating tasks and workflows."""
    
    def __init__(
        self,
        name: str,
        llm_config: Dict[str, Any],
        workflow: Dict[str, Any],
        description: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """Initialize automation agent."""
        reasoning = OODAReasoning()  # Create reasoning instance first
        
        super().__init__(
            name=name,
            llm_config=llm_config,
            reasoning=reasoning,
            description=description
        )
        
        self.workflow = workflow
        self.max_retries = max_retries
        self.retry_delay = retry_delay 