"""OODA loop reasoning implementation."""

from typing import Dict, List, Any
from ..execution.execution_types import ExecutionSignal, ExecutionContext, ExecutionSignalType
from ..execution.execution_graph import ExecutionNode, ExecutionNodeType
from .reasoning_pattern import ReasoningPattern

class OODAReasoning(ReasoningPattern):
    """Observe-Orient-Decide-Act loop pattern."""
    
    def _setup_graph(self) -> None:
        """Setup OODA loop graph structure."""
        # Create nodes
        start = self.add_node("start", ExecutionNodeType.START, "Begin OODA loop")
        observe = self.add_node("observe", ExecutionNodeType.TASK, "Gather data")
        orient = self.add_node("orient", ExecutionNodeType.TASK, "Analyze context")
        decide = self.add_node("decide", ExecutionNodeType.TASK, "Make decision")
        act = self.add_node("act", ExecutionNodeType.TASK, "Execute action")
        check = self.add_node("check", ExecutionNodeType.CONDITION, "Check continuation")
        end = self.add_node("end", ExecutionNodeType.END, "End OODA loop")

        # Create loop structure
        self.add_transition("start", "observe")
        self.add_transition("observe", "orient")
        self.add_transition("orient", "decide")
        self.add_transition("decide", "act")
        self.add_transition("act", "check")
        self.add_transition("check", "observe", condition="continue")
        self.add_transition("check", "end", condition="complete")

    async def _execute_node(self, node: ExecutionNode, context: ExecutionContext) -> List[ExecutionSignal]:
        """Execute a node in the OODA loop."""
        if node.type == ExecutionNodeType.TASK:
            if node.node_id == "observe":
                data = await context.sensors.gather()
                return [self._create_signal(ExecutionSignalType.OBSERVATION, data)]
                
            elif node.node_id == "orient":
                analysis = await context.llm.analyze(context.step["observation"])
                return [self._create_signal(ExecutionSignalType.ANALYSIS, analysis)]
                
            elif node.node_id == "decide":
                decision = {"action": context.step["analysis"].get("recommended_action")}
                return [self._create_signal(ExecutionSignalType.DECISION, decision)]
                
            elif node.node_id == "act":
                result = await self._take_action(context.step["decision"])
                return [self._create_signal(ExecutionSignalType.ACTION, result)]
                
        elif node.type == ExecutionNodeType.CONDITION:
            if node.node_id == "check":
                should_continue = context.step["action"].get("status") == "continue"
                if should_continue:
                    self.cursor().set_next(self.nodes["observe"])
                else:
                    self.cursor().set_next(self.nodes["end"])
                return []
                
        return []

    async def _take_action(self, decision: Dict) -> Dict:
        """Execute decided action."""
        return {"status": "completed", "result": decision.get("action")} 