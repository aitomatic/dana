"""
FieldNormalizerAgent - Converts extracted text to structured JSON.

This agent is forced via system prompt to always call the NormalizationResource
for converting text to normalized JSON data.
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dana.core.agent.star_agent import STARAgent
from resources.normalization_resource import NormalizationResource


class FieldNormalizerAgent(STARAgent):
    """
    Agent specialized in normalizing extracted text to structured JSON.

    This agent is configured to ALWAYS call the NormalizationResource
    for text-to-JSON conversion. The system prompt enforces this behavior.
    """

    def __init__(self, agent_id: str | None = None, llm_provider: str = "anthropic", model: str = "claude-3-5-sonnet-20241022", **kwargs):
        """
        Initialize the FieldNormalizerAgent.

        Args:
            agent_id: Unique identifier for this agent
            llm_provider: LLM provider (anthropic, openai, etc.)
            model: Model name
            **kwargs: Additional arguments passed to STARAgent
        """
        super().__init__(
            agent_type="field-normalizer", agent_id=agent_id or "field-normalizer-001", llm_provider=llm_provider, model=model, **kwargs
        )

        # Register the NormalizationResource
        self.with_resources(NormalizationResource(resource_id="field-normalization"))
