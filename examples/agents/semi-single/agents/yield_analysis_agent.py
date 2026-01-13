"""YieldAnalysisAgent - Interactive semiconductor yield analysis agent."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dana.core.agent.star_agent import STARAgent
from dana.lib.resources.conversation import ConversationResource

# Import workflows
from workflows.yield_pareto_workflow import YieldParetoWorkflow
from workflows.failure_correlation_workflow import FailureCorrelationWorkflow
from workflows.roi_prioritization_workflow import ROIPrioritizationWorkflow

# Import resources for ULTIMATE pattern
from resources.wafer_map_resource import WaferMapResource
from resources.statistical_analysis_resource import StatisticalAnalysisResource
from resources.historical_pattern_resource import HistoricalPatternResource
from resources.test_data_resource import TestDataResource


class YieldAnalysisAgent(STARAgent):
    """
    Interactive semiconductor yield analysis agent.

    Capabilities:
    - Analyze wafer test failures
    - Perform Pareto analysis to identify top failure bins
    - Correlate failures with process changes
    - Prioritize fixes based on ROI
    - Provide conversational guidance for yield improvement
    """

    def __init__(
        self, agent_id: str = "yield-analyst", llm_provider: str = "anthropic", model: str = "claude-3-5-sonnet-20241022", **kwargs
    ):
        """
        Initialize YieldAnalysisAgent.

        Args:
            agent_id: Unique identifier for this agent
            llm_provider: LLM provider (anthropic, openai, etc.)
            model: Model name to use
        """
        super().__init__(agent_type="yield_analysis", agent_id=agent_id, llm_provider=llm_provider, model=model, **kwargs)

        # Add LLM resource
        self.with_resources(ConversationResource(resource_id=f"{agent_id}-llm", llm_provider=llm_provider, model=model))

        # Add domain-specific resources (ULTIMATE pattern)
        self.with_resources(
            TestDataResource(resource_id="test-data"),
            WaferMapResource(resource_id="wafer-map"),
            StatisticalAnalysisResource(resource_id="stats"),
            HistoricalPatternResource(resource_id="historical-patterns"),
        )

        # Add analysis workflows
        self.with_workflows(
            YieldParetoWorkflow(workflow_id="pareto-analysis", llm_provider=llm_provider, model=model),
            FailureCorrelationWorkflow(workflow_id="correlation-analysis", llm_provider=llm_provider, model=model),
            ROIPrioritizationWorkflow(workflow_id="roi-prioritization", llm_provider=llm_provider, model=model),
        )

    @property
    def public_description(self) -> str:
        """Public description of the agent."""
        return """YieldAnalysisAgent: Expert semiconductor yield analyst with capabilities for:
- Pareto analysis of wafer test failures
- Root cause correlation analysis
- ROI-based prioritization of fixes
- Spatial defect pattern analysis
- Statistical significance testing
- Historical pattern matching"""
