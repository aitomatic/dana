"""
CoordinatorAgent - Orchestrates the fraud detection pipeline.

This agent is forced via system prompt to always call the FraudDetectionWorkflow
for orchestrating the sequential execution of the 3 specialist agents.
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dana.core.agent.star_agent import STARAgent
from workflows.fraud_detection_workflow import FraudDetectionWorkflow
from agents.deep_extractor_agent import DeepExtractorAgent
from agents.field_normalizer_agent import FieldNormalizerAgent
from agents.fraud_indicator_agent import FraudIndicatorAgent


class CoordinatorAgent(STARAgent):
    """
    Agent that orchestrates the fraud detection pipeline.

    This agent is configured to ALWAYS call the FraudDetectionWorkflow
    for coordinating the sequential execution of:
    1. DeepExtractor: PDF/Image → Text
    2. FieldNormalizer: Text → JSON
    3. FraudIndicator: JSON → Fraud Result

    The system prompt enforces this behavior.
    """

    def __init__(self, agent_id: str | None = None, llm_provider: str = "anthropic", model: str = "claude-3-5-sonnet-20241022", **kwargs):
        """
        Initialize the CoordinatorAgent.

        Args:
            agent_id: Unique identifier for this agent
            llm_provider: LLM provider (anthropic, openai, etc.)
            model: Model name
            **kwargs: Additional arguments passed to STARAgent
        """
        super().__init__(
            agent_type="fraud-coordinator", agent_id=agent_id or "fraud-coordinator-001", llm_provider=llm_provider, model=model, **kwargs
        )

        # Initialize the specialist agents
        self.deep_extractor = DeepExtractorAgent(agent_id="deep-extractor-001", llm_provider=llm_provider, model=model)

        self.field_normalizer = FieldNormalizerAgent(agent_id="field-normalizer-001", llm_provider=llm_provider, model=model)

        self.fraud_indicator = FraudIndicatorAgent(agent_id="fraud-indicator-001", llm_provider=llm_provider, model=model)

        # Initialize the workflow with agent references
        self.fraud_detection_workflow = FraudDetectionWorkflow(
            workflow_id="fraud-detection-pipeline",
            deep_extractor_agent=self.deep_extractor,
            field_normalizer_agent=self.field_normalizer,
            fraud_indicator_agent=self.fraud_indicator,
        )

        # Register the workflow
        self.with_workflows(self.fraud_detection_workflow)


if __name__ == "__main__":
    coordinator = CoordinatorAgent()
    coordinator.converse()
    print(coordinator.system_prompt)
