"""
Core interfaces defining how Planning and Reasoning interact
with objectives, plans, steps, and signals.
"""
from abc import ABC
from typing import List, Optional, Tuple

from ..types import Objective, Signal, Context
from .plan import Plan
from ..execution_graph import ExecutionNode
class BasePlanner(ABC):
    """
    Basic planner that maps workflow nodes directly to plan steps.
    
    Planning is responsible for:
    1. Creating plans from objectives
    2. Updating plans based on signals
    3. Evolving objectives when needed
    """
    
    def __init__(self, context: Context):
        """Initialize the planner with a context.
        Context has everything: Workflow, Plan, Reasoning, current state of Agent, World, Execution, etc."""
        self.context = context
        self._current_node_id: Optional[str] = None

    async def create_plan(self, objective: Objective) -> Plan:
        """
        Create a simple one-step plan from current workflow node.
        
        Args:
            objective: The objective to create a plan for
            
        Returns:
            Plan: Single-step plan mapping current workflow node
        """
        if not self.context.current_workflow:
            raise ValueError("No workflow set - cannot create plan")

        # Get current or initial workflow node
        if not self._current_node_id:
            current_node = self.context.current_workflow.get_start_node()
        else:
            current_node = self.context.current_workflow.get_node_by_id(self._current_node_id)
            
        if not current_node:
            raise ValueError("No current workflow node found")

        # Create plan with single step matching workflow node
        plan = Plan(objective)
        plan_node = ExecutionNode(
            node_id=current_node.node_id,
            description=current_node.description or "",
        )
        plan.add_node(plan_node)
        
        self._current_node_id = current_node.node_id
        return plan

    def process_signals(
        self,
        plan: Plan,
        signals: List[Signal]
    ) -> Tuple[Optional[Plan], List[Signal]]:
        """
        Process signals and advance to next workflow node if step complete.
        
        Args:
            plan: Current plan being executed
            signals: List of signals to process
            
        Returns:
            Tuple containing:
            - Optional[Plan]: New single-step plan if current step complete
            - List[Signal]: Signals to propagate
        """
        # Update world state from discoveries
        for signal in signals:
            if signal.type == SignalType.DISCOVERY:
                self.update_world_state(signal.content)

        # Check for step completion
        if any(s.type == SignalType.STEP_COMPLETE for s in signals):
            if not self.workflow:
                return None, signals
                
            # Get next workflow node
            next_node = self.workflow.get_next_node(self._current_node_id)
            if next_node:
                # Create new single-step plan
                new_plan = Plan(plan.objective)
                new_plan.add_step(
                    step_id=next_node.id,
                    description=next_node.description,
                    status=PlanStepStatus.PENDING,
                    context={"workflow_node_id": next_node.id}
                )
                self._current_node_id = next_node.id
                return new_plan, []

        return None, signals
