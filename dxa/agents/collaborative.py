"""Collaborative agent implementation.

This module provides an agent implementation that can work with other agents
to accomplish tasks. It enables agent-to-agent communication, task delegation,
and result aggregation.

Example:
    ```python
    from dxa.agents.collaborative import CollaborativeAgent
    from dxa.core.reasoning import ChainOfThoughtReasoning
    
    # Create agent registry
    agent_registry = {
        "researcher": researcher_agent,
        "analyst": analyst_agent
    }
    
    coordinator = CollaborativeAgent(
        name="coordinator",
        llm_config={
            "model": "gpt-4",
            "api_key": "your-key"
        },
        reasoning=ChainOfThoughtReasoning(),
        agent_registry=agent_registry
    )
    
    result = await coordinator.run({
        "task": "analyze_market_trends",
        "required_analyses": ["historical", "current"]
    })
    ```
"""

from typing import Dict, Any, Optional
from dxa.agents.autonomous import AutonomousAgent
from dxa.core.reasoning.base_reasoning import BaseReasoning
from dxa.core.resources.agents import AgentResource
from dxa.common.errors import ReasoningError, ConfigurationError, AgentError

class CollaborativeAgent(AutonomousAgent):
    """Agent that collaborates with other agents to accomplish tasks.
    
    This agent type extends AutonomousAgent with capabilities for consulting
    and collaborating with other agents. It maintains a history of collaborations
    and can coordinate multi-agent tasks.
    
    Attributes:
        agent_resource: Resource for accessing other agents
        collaborations: History of agent collaborations
        
    Args:
        name: Agent identifier
        llm_config: LLM configuration dictionary
        reasoning: Reasoning system instance
        agent_registry: Dictionary mapping agent IDs to agent instances
        description: Optional agent description
        
    Example:
        ```python
        agent = CollaborativeAgent(
            name="research_coordinator",
            llm_config={"model": "gpt-4"},
            reasoning=ChainOfThoughtReasoning(),
            agent_registry={
                "data_analyst": analyst_agent,
                "researcher": researcher_agent
            }
        )
        ```
    """
    
    def __init__(
        self,
        name: str,
        llm_config: Dict[str, Any],
        reasoning: BaseReasoning,
        agent_registry: Dict[str, Any],
        description: Optional[str] = None
    ):
        """Initialize collaborative agent."""
        super().__init__(
            name=name,
            llm_config=llm_config,
            reasoning=reasoning,
            description=description,
            max_iterations=None
        )
        
        self.agent_resource = AgentResource(
            name=f"{name}_agents",
            agent_registry=agent_registry
        )
        self.collaborations: Dict[str, Any] = {}
        self._is_running = True

    async def _handle_consultations(
        self,
        consultations: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle consultations with other agents.
        
        Manages the process of consulting other agents and collecting their responses.
        
        Args:
            consultations: Dictionary mapping agent IDs to consultation requests
            
        Returns:
            Dictionary containing consultation results
            
        Example:
            ```python
            results = await agent._handle_consultations({
                "analyst": "Analyze this dataset",
                "researcher": "Find related papers"
            })
            ```
        """
        results = {}
        for agent_id, request in consultations.items():
            try:
                response = await self.agent_resource.query({
                    "agent_id": agent_id,
                    "query": request
                })
                
                if response["success"]:
                    results[agent_id] = response["response"]
                    self.collaborations[agent_id] = {
                        "request": request,
                        "response": response["response"]
                    }
                else:
                    self.logger.warning(
                        "Consultation with agent %s failed: %s",
                        agent_id,
                        response.get("error", "Unknown error")
                    )
                    
            except (ValueError, KeyError) as e:
                self.logger.error("Collaborative agent error: %s", str(e))
                
        return results

    async def run(self, task: str) -> Dict[str, Any]:
        """Run the collaborative agent's main loop.
        
        Coordinates task execution across multiple agents, managing consultations
        and aggregating results.
        
        Args:
            task: The task/query to process
            
        Returns:
            Dict containing:
                - success: Whether the task completed successfully
                - results: Results from reasoning system
                - collaborations: History of agent collaborations
                
        Raises:
            ReasoningError: If reasoning system fails
            ConfigurationError: If agent is misconfigured
            AgentError: If agent operations fail
            
        Example:
            ```python
            result = await agent.run({
                "task": "market_analysis",
                "scope": ["historical", "current"],
                "format": "report"
            })
            ```
        """
        context = {"task": task}
        try:
            while self._is_running:
                result = await self.reasoning.reason(
                    context,
                    task
                )
                
                if result.get("needs_consultation"):
                    consultation_results = await self._handle_consultations(
                        result["consultations"]
                    )
                    context.update({"consultation_results": consultation_results})
                
                if result.get("task_complete"):
                    self.logger.info("Collaborative task completed")
                    break
            
            return {
                "success": True,
                "results": result,
                "collaborations": self.collaborations
            }
            
        except (ReasoningError, ConfigurationError, AgentError) as e:
            self.logger.error("Collaborative agent error: %s", str(e))
            return {
                "success": False,
                "error": str(e)
            }