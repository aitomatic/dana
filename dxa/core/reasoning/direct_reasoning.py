"""Direct reasoning implementation."""

from typing import List, Any
from ..execution.execution_types import ExecutionSignal, ExecutionContext, ExecutionSignalType
from ..execution.execution_node import ExecutionNode, ExecutionNodeType
from .base_reasoning_pattern import BaseReasoningPattern

class DirectReasoning(BaseReasoningPattern):
    """Simple LLM query and response pattern."""
    
    async def execute_node(self, node: ExecutionNode, context: ExecutionContext) -> List[ExecutionSignal]:
        """Execute a node in the reasoning pattern."""
        try:
            if node.type == ExecutionNodeType.TASK:
                response = await context.llm.query(context.step["prompt"])
                return [self._create_signal(ExecutionSignalType.RESULT, response)]
            return []
            
        except Exception as e:
            return [self._create_signal(ExecutionSignalType.ERROR, str(e))] 