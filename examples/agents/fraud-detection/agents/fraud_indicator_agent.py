"""
FraudIndicatorAgent - Detects fraud patterns from normalized JSON data.

This agent is forced via system prompt to always call the FraudDetectionResource
for fraud pattern analysis.
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dana.core.agent.star_agent import STARAgent
from resources.fraud_detection_resource import FraudDetectionResource


class FraudIndicatorAgent(STARAgent):
    """
    Agent specialized in detecting fraud patterns from normalized data.

    This agent is configured to ALWAYS call the FraudDetectionResource
    for fraud analysis. The system prompt enforces this behavior.
    """

    def __init__(self, agent_id: str | None = None, llm_provider: str = "anthropic", model: str = "claude-3-5-sonnet-20241022", **kwargs):
        """
        Initialize the FraudIndicatorAgent.

        Args:
            agent_id: Unique identifier for this agent
            llm_provider: LLM provider (anthropic, openai, etc.)
            model: Model name
            **kwargs: Additional arguments passed to STARAgent
        """
        super().__init__(
            agent_type="fraud-indicator",
            agent_id=agent_id or "fraud-indicator-001",
            llm_provider=llm_provider,
            model=model,
            **kwargs,
        )

        # Register the FraudDetectionResource
        self.with_resources(FraudDetectionResource(resource_id="fraud-detection"))
