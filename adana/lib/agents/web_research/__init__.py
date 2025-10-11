"""
Web Research Agent - Specialized agent for web research and information synthesis.

This package provides a complete web research agent with:
- Three specialized resources (WebFetcher, ContentExtractor, WorkflowSelector)
- Ten situation-specific workflows (composition-based)
- LLM-augmented decision making via BaseWAR.reason()
"""

from adana.lib.agents.web_research.web_research_agent import WebResearchAgent


__all__ = ["WebResearchAgent"]
