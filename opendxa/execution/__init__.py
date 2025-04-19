"""Execution System for OpenDXA.

This module implements the two-layer architecture for executing agent workflows:

1. Planning Layer (WHAT)
   - Converts tasks into concrete plans
   - Manages dependencies between steps
   - Handles data flow between nodes

2. Reasoning Layer (HOW)
   - Executes plans with specific reasoning strategies
   - Processes execution signals
   - Manages state and context

The execution system also includes a Pipeline layer that orchestrates the execution flow,
managing the interaction between different layers and components.

For detailed documentation, see:
- Execution Documentation: https://github.com/aitomatic/opendxa/blob/main/opendxa/execution/README.md

Example:
    >>> from opendxa.execution import Plan, PlanExecutor
    >>> from opendxa.execution.planning import ExecutionNode, NodeType
    >>> plan = Plan(objective="Analyze customer feedback")
    >>> plan.add_node(ExecutionNode(
    ...     node_id="ANALYZE",
    ...     node_type=NodeType.TASK,
    ...     objective="Analyze feedback data"
    ... ))
    >>> executor = PlanExecutor()
    >>> result = await executor.execute(plan)
"""

from opendxa.execution.pipeline import (
    Pipeline,
    PipelineFactory,
    PipelineExecutor,
    PipelineContext,
    PipelineNode,
    PipelineStrategy,
)
from opendxa.execution.planning import (
    Plan,
    PlanFactory,
    PlanExecutor,
    PlanStrategy,
)
from opendxa.execution.reasoning import (
    Reasoning,
    ReasoningFactory,
    ReasoningExecutor,
    ReasoningStrategy,
)
from opendxa.execution.agent_runtime import AgentRuntime
from opendxa.execution.agent_state import AgentState

__all__ = [
    'Pipeline',
    'PipelineFactory',
    'PipelineExecutor',
    'PipelineContext',
    'PipelineNode',
    'PipelineStrategy',
    'Plan',
    'PlanFactory',
    'PlanStrategy',
    'PlanExecutor',
    'Reasoning',
    'ReasoningFactory',
    'ReasoningStrategy',
    'ReasoningExecutor',
    'AgentRuntime',
    'AgentState',
]
