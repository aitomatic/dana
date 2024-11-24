"""Base agent implementation."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging
from dxa.core.reasoning.base import BaseReasoning
from dxa.core.resources.llm import LLMResource
from dxa.core.expertise import ExpertResource

class BaseAgent(ABC):
    """Base class for all agents."""
    
    def __init__(
        self,
        name: str,
        reasoning: BaseReasoning,
        internal_llm_config: Dict[str, Any],
        expert_resources: Optional[List[ExpertResource]] = None,
        system_prompt: Optional[str] = None,
        description: Optional[str] = None
    ):
        """Initialize base agent."""
        self.name = name
        self.description = description or f"Agent: {name}"
        self.logger = logging.getLogger(f"Agent:{name}")
        
        # Set up internal LLM
        self._internal_llm = LLMResource(
            name=f"{name}_internal_llm",
            llm_config=internal_llm_config,
            system_prompt=self._build_system_prompt(system_prompt, expert_resources)
        )
        
        # Set up reasoning with internal LLM
        self.reasoning = reasoning
        self.reasoning.set_llm_fn(self._internal_llm.query)
        
        # Track available expertise
        self.expert_resources = expert_resources or []
        self.expertise_by_domain = {
            er.expertise.name: er for er in self.expert_resources
        }
        
        # Initialize state
        self._is_running = False

    def _build_system_prompt(
        self,
        base_prompt: Optional[str],
        expert_resources: Optional[List[ExpertResource]]
    ) -> str:
        """Build system prompt including expertise information."""
        prompt_parts = [base_prompt or "You are a helpful agent."]
        
        if expert_resources:
            prompt_parts.append("\nYou have access to the following domain experts:")
            for er in expert_resources:
                prompt_parts.extend([
                    f"\n{er.expertise.name} Expert:",
                    f"- Description: {er.expertise.description}",
                    f"- Capabilities: {', '.join(er.expertise.capabilities)}",
                    f"- When to use: When you see terms like: {', '.join(er.expertise.keywords)}",
                    f"- Required input: {', '.join(er.expertise.requirements)}"
                ])
        
        return "\n".join(prompt_parts)

    async def initialize(self) -> None:
        """Initialize agent resources."""
        # Initialize internal LLM first
        await self._internal_llm.initialize()
        
        # Initialize all expert resources
        for expert in self.expert_resources:
            await expert.resource.initialize()
            
        self._is_running = True
        self.logger.info(
            "Agent initialized with experts: %s",
            [er.expertise.name for er in self.expert_resources]
        )

    async def cleanup(self) -> None:
        """Clean up agent resources."""
        # Clean up all expert resources
        for expert in self.expert_resources:
            await expert.resource.cleanup()
            
        # Clean up internal LLM
        await self._internal_llm.cleanup()
        
        self._is_running = False
        self.logger.info("Agent cleaned up")

    @abstractmethod
    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run the agent's main loop."""
        pass

    async def use_expert(
        self,
        domain: str,
        request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use a specific domain expert.
        
        Args:
            domain: Name of the domain expertise needed
            request: Request to send to the expert
            
        Returns:
            Expert response
            
        Raises:
            ValueError: If expert doesn't exist or can't handle request
        """
        if domain not in self.expertise_by_domain:
            raise ValueError(f"No expert found for domain: {domain}")
            
        expert = self.expertise_by_domain[domain]
        if not expert.resource.can_handle(request):
            raise ValueError(
                f"Expert for {domain} cannot handle request: {request}"
            )
            
        return await expert.resource.query(request)

    def _parse_expertise_check(self, response: str) -> Dict[str, Any]:
        """Parse expertise check response."""
        result = {}
        
        for line in response.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                
                if key == 'expertise_needed':
                    result['domain'] = value
                elif key == 'confidence':
                    try:
                        result['confidence'] = float(value)
                    except ValueError:
                        result['confidence'] = 0.0
                elif key == 'reason':
                    result['reason'] = value
                    
        return result

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup() 