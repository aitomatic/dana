"""
WorkflowStepAgent - Provides intelligence for specific steps within workflows.

This agent is designed to be lazy-instantiated by workflows to handle
intelligence tasks at specific workflow decision points without polluting
the calling agent's conversation timeline.

Usage:
    from dana.lib.agents.workflow_step_agent import WorkflowStepAgent

    # Within a workflow
    step_agent = WorkflowStepAgent(agent_id="pareto-step-agent")
    result = step_agent.query("Classify these patterns: ...")
"""

from dana.core.agent.star_agent import STARAgent


class WorkflowStepAgent(STARAgent):
    """
    Reusable agent for providing intelligence at workflow decision points.

    Each workflow can instantiate its own WorkflowStepAgent, keeping
    intelligence context separate from the calling agent.

    The agent's system prompt is loaded from WorkflowStepAgent.xml.
    """

    def __init__(self, agent_id: str | None = None, **kwargs):
        """
        Initialize WorkflowStepAgent.

        Args:
            agent_id: Optional agent identifier
            **kwargs: Additional arguments passed to STARAgent
        """
        # Initialize STARAgent with workflow_step type (loads WorkflowStepAgent.xml)
        super().__init__(
            agent_type="workflow_step",
            agent_id=agent_id or "workflow_step",
            **kwargs
        )
