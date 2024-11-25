"""Collaborative agent implementation."""

from typing import Dict, Any, Optional
import asyncio
from dxa.agents.base_agent import BaseAgent
from dxa.core.reasoning.base_reasoning import BaseReasoning
from dxa.core.resources.agents import AgentResource

class CollaborativeAgent(BaseAgent):
    """Base class for agents that work with other agents."""
    
    def __init__(
        self,
        name: str,
        llm_config: Dict[str, Any],
        reasoning: BaseReasoning,
        agent_registry: Dict[str, BaseAgent],
        description: Optional[str] = None
    ):
        """Initialize collaborative agent.
        
        Args:
            name: Name of this agent
            llm_config: Configuration for the agent's LLM
            reasoning: Reasoning pattern to use
            agent_registry: Dictionary of available agents
            description: Optional description of this agent
        """
        super().__init__(
            name=name,
            llm_config=llm_config,
            reasoning=reasoning,
            description=description
        )
        
        # Set up agent resource
        self.agent_resource = AgentResource(
            name=f"{name}_agents",
            agent_registry=agent_registry
        )
        
        # Track collaborations
        self.collaborations: Dict[str, Dict[str, Any]] = {}

    async def initialize(self) -> None:
        """Initialize agent resources."""
        await super().initialize()
        await self.agent_resource.initialize()
        self.logger.info("Collaborative agent initialized")

    async def cleanup(self) -> None:
        """Clean up agent resources."""
        await self.agent_resource.cleanup()
        await super().cleanup()
        self.logger.info("Collaborative agent cleaned up")

    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run the collaborative agent's main loop.
        
        Args:
            context: Initial context for the agent
            
        Returns:
            Dict containing results of agent's operation
        """
        try:
            while self._is_running:
                # Run reasoning cycle
                result = await self.reasoning.reason(
                    context,
                    "Coordinate with other agents"
                )
                
                # Check if we need to consult other agents
                if result.get("needs_consultation"):
                    consultation_results = await self._handle_consultations(
                        result["consultations"],
                        context
                    )
                    context.update({"consultation_results": consultation_results})
                
                # Check if task is complete
                if result.get("task_complete"):
                    self.logger.info("Collaborative task completed")
                    break
            
            return {
                "success": True,
                "results": result,
                "collaborations": self.collaborations
            }
            
        except Exception as e:
            await self.handle_error(e)
            return {
                "success": False,
                "error": str(e)
            }

    async def _handle_consultations(
        self,
        consultations: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle consultations with other agents.
        
        Args:
            consultations: Dictionary of consultation requests
            context: Current context
            
        Returns:
            Dict containing consultation results
        """
        results = {}
        for agent_id, query in consultations.items():
            try:
                response = await self.agent_resource.query({
                    "agent_id": agent_id,
                    "query": query
                })
                
                if response["success"]:
                    results[agent_id] = response["response"]
                    # Track successful collaboration
                    self.collaborations[agent_id] = {
                        "timestamp": asyncio.get_event_loop().time(),
                        "query": query,
                        "response": response["response"]
                    }
                else:
                    self.logger.warning(
                        "Consultation with agent %s failed: %s",
                        agent_id,
                        response.get("error", "Unknown error")
                    )
                    
            except Exception as e:
                self.logger.error(
                    "Error consulting agent %s: %s",
                    agent_id,
                    str(e)
                )
                
        return results 