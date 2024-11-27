"""OODA (Observe, Orient, Decide, Act) loop reasoning pattern."""

from typing import Dict, Any
from dxa.core.reasoning.base_reasoning import BaseReasoning

class OODAPhase:
    """OODA loop phases."""
    OBSERVE = "observe"
    ORIENT = "orient"
    DECIDE = "decide"
    ACT = "act"

class OODAReasoning(BaseReasoning):
    """OODA loop reasoning implementation."""
    
    def __init__(self):
        """Initialize OODA reasoning."""
        super().__init__()
        self.current_phase = OODAPhase.OBSERVE

    async def initialize(self) -> None:
        """Initialize reasoning system."""
        if self.agent_llm:
            await self.agent_llm.initialize()
    
    async def cleanup(self) -> None:
        """Clean up reasoning system."""
        if self.agent_llm:
            await self.agent_llm.cleanup()
    
    async def reason(self, context: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Run reasoning cycle."""
        # Get prompts
        system_prompt = self.get_system_prompt(context, query)
        user_prompt = self.get_prompt(context, query)
        
        # Query LLM
        response = await self._query_agent_llm({
            "system_prompt": system_prompt,
            "prompt": user_prompt,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens
        })
        
        # Process response and advance phase
        result = self.reason_post_process(response["content"])
        self._advance_phase()
        return result
    
    def get_reasoning_system_prompt(self, context: Dict[str, Any], query: str) -> str:
        """Get system prompt for OODA reasoning."""
        return """You are executing one step in an OODA reasoning process.
        Always show your work step by step."""

    def get_reasoning_prompt(self, context: Dict[str, Any], query: str) -> str:
        """Get prompt for OODA reasoning."""
        prompts = {
            OODAPhase.OBSERVE: self._get_observe_prompt,
            OODAPhase.ORIENT: self._get_orient_prompt,
            OODAPhase.DECIDE: self._get_decide_prompt,
            OODAPhase.ACT: self._get_act_prompt
        }
        return prompts[self.current_phase](context, query)

    def reason_post_process(self, response: str) -> Dict[str, Any]:
        """Process the response based on current phase."""
        return {
            "phase": self.current_phase,
            "response": response,
            "next_phase": self._get_next_phase()
        }

    def _advance_phase(self) -> None:
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