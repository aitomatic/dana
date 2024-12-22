"""Direct reasoning implementation - simplest reasoning pattern."""

from typing import Dict, Any, List
from ..types import Signal, SignalType, Step
from .base_reasoner import BaseReasoner
from ..resource.llm_resource import LLMResource

class DirectReasoner(BaseReasoner):
    """Simplest reasoning pattern - just queries LLM."""
    
    async def reason_about(
        self,
        step: Step,
        context: Dict[str, Any],
        agent_llm: LLMResource,
        resources: Dict[str, Any]
    ) -> List[Signal]:
        """Execute step by querying LLM."""
        try:
            response = await agent_llm.query({"prompt": step.description})
            step.result = {"answer": response["content"]}
            return [Signal(type=SignalType.STEP_COMPLETE, content=step.result)]
        except Exception as e:
            return [Signal(
                type=SignalType.STEP_FAILED,
                content={"error": str(e)}
            )]

    def validate(self, step: Step, result: Dict[str, Any]) -> bool:
        """Simple validation - just checks for answer."""
        return "answer" in result