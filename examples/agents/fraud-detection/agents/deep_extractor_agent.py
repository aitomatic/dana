"""
DeepExtractorAgent - Extracts text from PDF and image files.

This agent is forced via system prompt to always call the DeepExtractionResource
for text extraction from documents.
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dana.core.agent.star_agent import STARAgent
from resources.deep_extraction_resource import DeepExtractionResource


class DeepExtractorAgent(STARAgent):
    """
    Agent specialized in extracting text from PDF and image files.

    This agent is configured to ALWAYS call the DeepExtractionResource
    for document text extraction. The system prompt enforces this behavior.
    """

    def __init__(self, agent_id: str | None = None, llm_provider: str = "anthropic", model: str = "claude-3-5-sonnet-20241022", **kwargs):
        """
        Initialize the DeepExtractorAgent.

        Args:
            agent_id: Unique identifier for this agent
            llm_provider: LLM provider (anthropic, openai, etc.)
            model: Model name
            **kwargs: Additional arguments passed to STARAgent
        """
        super().__init__(
            agent_type="deep-extractor", agent_id=agent_id or "deep-extractor-001", llm_provider=llm_provider, model=model, **kwargs
        )

        # Register the DeepExtractionResource with LLM provider and model
        self.with_resources(DeepExtractionResource(resource_id="deep-extraction", llm_provider=llm_provider, model=model))
