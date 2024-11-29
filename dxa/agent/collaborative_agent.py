"""Collaborative agent implementation.

This module provides an agent implementation that can work with other agents
to accomplish tasks. It enables agent-to-agent communication, task delegation,
and result aggregation.

Example:
    ```python
    from dxa.agent import CollaborativeAgent
    
    # Create agent registry
    agent_registry = {
        "researcher": ResearchAgent(...),
        "analyst": AnalysisAgent(...),
        "writer": WritingAgent(...)
    }
    
    agent = CollaborativeAgent(
        name="coordinator",
        llm_config={"model": "gpt-4"},
        agent_registry=agent_registry
    )
    
    result = await agent.run({
        "objective": "research_and_report",
        "topic": "AI trends 2024"
    })
    ```
"""

from typing import Dict, Any, Optional
from dxa.agent.base_agent import BaseAgent
from dxa.core.reasoning.base_reasoning import BaseReasoning
from dxa.core.reasoning.cot import ChainOfThoughtReasoning
from dxa.core.resource.agents import AgentResource

class CollaborativeAgent(BaseAgent):
    """Agent that collaborates with other agents to accomplish tasks.
    
    This agent type extends BaseAgent with capabilities for consulting
    and collaborating with other agents. It maintains a history of collaborations
    and can coordinate multi-agent tasks.
    
    Attributes:
        All attributes inherited from BaseAgent
        agent_resource: Resource for accessing other agents
        collaborations: History of agent collaborations
        
    Args:
        name: Agent identifier
        llm_config: LLM configuration dictionary
        agent_registry: Dictionary mapping agent IDs to agent instances
        reasoning: Optional reasoning system (defaults to ChainOfThoughtReasoning)
        description: Optional agent description
        max_iterations: Optional maximum iterations
    """
    
    def __init__(
        self,
        name: str,
        llm_config: Dict[str, Any],
        agent_registry: Dict[str, Any],
        reasoning: Optional[BaseReasoning] = None,
        description: Optional[str] = None,
        max_iterations: Optional[int] = None
    ):
        """Initialize collaborative agent."""
        config = {
            "llm": llm_config,
            "description": description
        }
        
        super().__init__(
            name=name,
            config=config,
            reasoning=reasoning or ChainOfThoughtReasoning(),
            mode="collaborative",
            max_iterations=max_iterations
        )
        
        self.agent_resource = AgentResource(
            name=f"{name}_agents",
            agent_registry=agent_registry
        )
        self.collaborations: Dict[str, Any] = {}

    async def _pre_execute(self, context: Dict[str, Any]) -> None:
        """Prepare for collaborative execution.
        
        Args:
            context: Initial execution context
            
        Raises:
            ValueError: If required collaboration parameters are missing
        """
        # Check if we have any agents in the registry
        if not self.agent_resource.agent_registry:
            raise ValueError("No collaborative agents available")
            
        # Add collaboration info to context
        context.update({
            "available_agents": list(self.agent_resource.agent_registry.keys()),
            "collaboration_history": self.collaborations
        })

    async def _post_execute(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Process collaboration results.
        
        Args:
            result: Results from final reasoning iteration
            
        Returns:
            Processed results with collaboration metadata
        """
        result.update({
            "agent_type": "collaborative",
            "execution_mode": self.mode,
            "collaborations": self.collaborations
        })
        return result

    async def _should_continue(self, result: Dict[str, Any]) -> bool:
        """Check if collaboration should continue.
        
        Args:
            result: Results from last reasoning iteration
            
        Returns:
            True if more collaboration is needed, False otherwise
        """
        # Stop if task is complete or we're stuck
        if result.get("task_complete") or result.get("is_stuck"):
            return False
            
        # Continue if there are pending collaborations
        return bool(result.get("pending_collaborations"))

    async def _reasoning_step(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute one collaborative reasoning iteration.
        
        Args:
            context: Current execution context
            
        Returns:
            Dict containing reasoning results and collaboration status
        """
        # Run base reasoning
        result = await self.reasoning.reason(context)
        
        # Handle any agent collaborations
        if collaborations := result.get("collaborations", []):
            for collab in collaborations:
                agent_id = collab["agent"]
                task = collab["task"]
                
                # Get agent from registry
                agent = self.agent_resource.agent_registry.get(agent_id)
                
                if agent:
                    collab_result = await agent.run(task)
                    
                    # Record collaboration using runtime's iteration count
                    collab_key = f"{agent_id}_{self.runtime.iteration_count}"
                    self.collaborations[collab_key] = {
                        "agent": agent_id,
                        "task": task,
                        "result": collab_result
                    }
                    
                    # Update result with collaboration outcome
                    result["collaboration_results"] = result.get("collaboration_results", [])
                    result["collaboration_results"].append({
                        "agent": agent_id,
                        "result": collab_result
                    })
        
        return result