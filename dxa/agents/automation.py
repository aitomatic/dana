"""Automation agent implementation.

This module provides an agent implementation specialized for workflow automation.
It extends the autonomous agent with workflow tracking and validation capabilities.

Example:
    ```python
    from dxa.agents.automation import AutomationAgent
    
    # Define workflow steps
    workflow = {
        "name": "data_processing",
        "steps": [
            {
                "name": "collect",
                "validation": lambda r: len(r.get("data", [])) > 0
            },
            {
                "name": "process",
                "validation": lambda r: "processed_data" in r
            }
        ]
    }
    
    agent = AutomationAgent(
        name="data_processor",
        llm_config={"model": "gpt-4"},
        workflow=workflow,
        max_retries=3
    )
    
    result = await agent.run({
        "input_source": "data.csv",
        "output_format": "json"
    })
    ```
"""

from typing import Dict, Any, Optional
from dxa.agents.autonomous import AutonomousAgent
from dxa.core.reasoning.ooda import OODAReasoning

class AutomationAgent(AutonomousAgent):
    """Agent for automating tasks and workflows.
    
    This agent type extends AutonomousAgent with workflow management capabilities.
    It tracks workflow progress, validates step completion, and handles retries
    for failed steps.
    
    Attributes:
        workflow: Workflow definition dictionary
        max_retries: Maximum retry attempts per step
        retry_delay: Delay between retry attempts
        
    Args:
        name: Agent identifier
        llm_config: LLM configuration dictionary
        workflow: Workflow definition
        description: Optional agent description
        max_retries: Maximum retries per step (default: 3)
        retry_delay: Seconds between retries (default: 1.0)
        
    Example:
        ```python
        agent = AutomationAgent(
            name="web_scraper",
            llm_config={"model": "gpt-4"},
            workflow={
                "name": "scraping",
                "steps": [
                    {"name": "fetch", "validation": lambda r: r["status"] == 200},
                    {"name": "extract", "validation": lambda r: len(r["data"]) > 0}
                ]
            },
            max_retries=3
        )
        ```
    """
    
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