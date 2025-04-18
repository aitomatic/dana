"""Execution System for OpenDXA.

This module implements the three-layer architecture for executing agent workflows:

1. Workflow Layer (WHY)
   - Defines what agents can do
   - Manages high-level workflow execution
   - Handles workflow strategies and optimization

2. Planning Layer (WHAT)
   - Converts workflows into concrete plans
   - Manages dependencies between steps
   - Handles data flow between nodes

3. Reasoning Layer (HOW)
   - Executes plans with specific reasoning strategies
   - Processes execution signals
   - Manages state and context

The execution system also includes a Pipeline layer that orchestrates the execution flow,
managing the interaction between different layers and components.

For detailed documentation, see:
- Execution Documentation: https://github.com/aitomatic/opendxa/blob/main/opendxa/execution/README.md

Example:
    >>> from opendxa.execution import Workflow, WorkflowExecutor
    >>> from opendxa.execution.workflow import ExecutionNode, NodeType
    >>> workflow = Workflow(objective="Analyze customer feedback")
    >>> workflow.add_node(ExecutionNode(
    ...     node_id="ANALYZE",
    ...     node_type=NodeType.TASK,
    ...     objective="Analyze feedback data"
    ... ))
    >>> executor = WorkflowExecutor()
    >>> result = await executor.execute(workflow)
"""

from opendxa.execution.pipeline import (
    Pipeline,
    PipelineFactory,
    PipelineExecutor,
    PipelineContext,
    PipelineNode,
    PipelineStrategy,
)
from opendxa.execution.workflow import (
    Workflow,
    WorkflowFactory,
    WorkflowExecutor,
    WorkflowStrategy,
    OptimalWorkflowExecutor,
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

__all__ = [
    'Pipeline',
    'PipelineFactory',
    'PipelineExecutor',
    'PipelineContext',
    'PipelineNode',
    'PipelineStrategy',
    'Workflow',
    'WorkflowFactory',
    'WorkflowExecutor',
    'OptimalWorkflowExecutor',
    'WorkflowStrategy',
    'Plan',
    'PlanFactory',
    'PlanStrategy',
    'PlanExecutor',
    'Reasoning',
    'ReasoningFactory',
    'ReasoningStrategy',
    'ReasoningExecutor',
]
