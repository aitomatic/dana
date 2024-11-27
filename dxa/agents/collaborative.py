"""Collaborative agent implementation."""

from typing import Dict, Any, Optional
from dxa.agents.autonomous import AutonomousAgent
from dxa.core.reasoning.base_reasoning import BaseReasoning
from dxa.core.resources.agents import AgentResource
from dxa.common.errors import ReasoningError, ConfigurationError, AgentError

class CollaborativeAgent(AutonomousAgent):
    """Base class for agents that work with other agents."""
    
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
        
        Args:
            consultations: Dictionary mapping agent IDs to consultation requests
            
        Returns:
            Dictionary containing consultation results
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
        
        Args:
            task: The task/query to process
            
        Returns:
            Dict containing results of agent's operation
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
            
        except (ReasoningError, ConfigurationError, AgentError) as e:  # More specific exceptions
            self.logger.error("Collaborative agent error: %s", str(e))
            return {
                "success": False,
                "error": str(e)
            }