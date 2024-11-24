"""OODA (Observe, Orient, Decide, Act) loop reasoning pattern."""

from typing import Dict, Any
from dxa.core.reasoning.base import BaseReasoning
from dxa.core.state import StateManager

class OODAPhase:
    """OODA loop phases."""
    OBSERVE = "observe"
    ORIENT = "orient"
    DECIDE = "decide"
    ACT = "act"

class OODALoopReasoning(BaseReasoning):
    """OODA loop reasoning implementation."""
    
    def __init__(self):
        """Initialize OODA loop reasoning."""
        super().__init__()
        self.state_manager = StateManager()
        self.current_phase = OODAPhase.OBSERVE

    async def initialize(self) -> None:
        """Initialize the reasoning pattern."""
        self.state_manager = StateManager()
        self.current_phase = OODAPhase.OBSERVE
        self.logger.info("OODA loop reasoning initialized")

    async def cleanup(self) -> None:
        """Clean up resources."""
        self.state_manager.clear_history()
        self.logger.info("OODA loop reasoning cleaned up")

    def get_reasoning_prompt(self, context: Dict[str, Any], query: str) -> str:
        """Get the prompt template for the current OODA phase."""
        prompts = {
            OODAPhase.OBSERVE: self._get_observe_prompt,
            OODAPhase.ORIENT: self._get_orient_prompt,
            OODAPhase.DECIDE: self._get_decide_prompt,
            OODAPhase.ACT: self._get_act_prompt
        }
        return prompts[self.current_phase](context, query)

    async def reason(
        self,
        context: Dict[str, Any],
        query: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute OODA loop reasoning process."""
        # Record the start of reasoning
        self.state_manager.add_observation(
            content=f"Starting {self.current_phase} phase",
            source="ooda_reasoning",
            metadata={"phase": self.current_phase}
        )
        
        # Get phase-specific prompt
        prompt = self.get_reasoning_prompt(context, query)
        
        # Format proper LLM request
        llm_request = {
            "prompt": prompt,
            "temperature": kwargs.get('temperature', 0.7),
            "max_tokens": kwargs.get('max_tokens', None),
            "system_prompt": kwargs.get('system_prompt', None)
        }
        
        try:
            # Get response from LLM
            llm_response = await self._query_llm(llm_request)
            response = llm_response["content"]  # Extract content from response
            
            # Record the response
            self.state_manager.add_observation(
                content=response,
                source="ooda_reasoning",
                metadata={
                    "phase": self.current_phase,
                    "type": "llm_response"
                }
            )
            
            # Process response based on phase
            result = self._process_phase_response(response)
            
            # Advance to next phase
            self._advance_phase()
            
            return result
            
        except Exception as e:
            self.logger.error(
                "Error in %s phase: %s",
                self.current_phase,
                str(e)
            )
            self.state_manager.add_observation(
                content=str(e),
                source="ooda_reasoning",
                metadata={
                    "phase": self.current_phase,
                    "type": "error"
                }
            )
            raise

    def _advance_phase(self):
        """Advance to the next phase in the OODA loop."""
        phases = [OODAPhase.OBSERVE, OODAPhase.ORIENT, OODAPhase.DECIDE, OODAPhase.ACT]
        current_index = phases.index(self.current_phase)
        next_index = (current_index + 1) % len(phases)
        self.current_phase = phases[next_index]

    def _get_observe_prompt(self, context: Dict[str, Any], query: str) -> str:
        """Get prompt for observation phase."""
        return f"""OBSERVE phase:
        Query: {query}
        Context: {self._format_context(context)}
        
        What are the key observations about this situation?
        Consider:
        1. What information do we have?
        2. What information might we need?
        3. What patterns or anomalies do we notice?"""

    def _get_orient_prompt(self, context: Dict[str, Any], query: str) -> str:
        """Get prompt for orientation phase."""
        return f"""ORIENT phase:
        Query: {query}
        Context: {self._format_context(context)}
        
        How should we interpret this situation?
        Consider:
        1. What are the key patterns or insights?
        2. What are the potential implications?
        3. What assumptions are we making?"""

    def _get_decide_prompt(self, context: Dict[str, Any], query: str) -> str:
        """Get prompt for decision phase."""
        return f"""DECIDE phase:
        Query: {query}
        Context: {self._format_context(context)}
        
        What actions should we take?
        Consider:
        1. What are our options?
        2. What are the potential outcomes?
        3. What are the risks and trade-offs?"""

    def _get_act_prompt(self, context: Dict[str, Any], query: str) -> str:
        """Get prompt for action phase."""
        return f"""ACT phase:
        Query: {query}
        Context: {self._format_context(context)}
        
        How should we execute our chosen action?
        Consider:
        1. What specific steps should we take?
        2. How will we measure success?
        3. What adjustments might be needed?"""

    def _process_phase_response(self, response: str) -> Dict[str, Any]:
        """Process the response based on current phase."""
        return {
            "phase": self.current_phase,
            "response": response,
            "next_phase": self._get_next_phase()
        }

    def _get_next_phase(self) -> str:
        """Get the name of the next phase."""
        phases = [OODAPhase.OBSERVE, OODAPhase.ORIENT, OODAPhase.DECIDE, OODAPhase.ACT]
        current_index = phases.index(self.current_phase)
        next_index = (current_index + 1) % len(phases)
        return phases[next_index]

    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context for inclusion in prompts."""
        formatted = []
        for key, value in context.items():
            if isinstance(value, dict):
                formatted.append(f"{key}:")
                for k, v in value.items():
                    formatted.append(f"  {k}: {v}")
            elif isinstance(value, (list, tuple)):
                formatted.append(f"{key}:")
                for item in value:
                    formatted.append(f"  - {item}")
            else:
                formatted.append(f"{key}: {value}")
        return '\n'.join(formatted) 