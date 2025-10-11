"""
WorkflowSelectorResource - Intelligent workflow selection using LLM reasoning.

This resource selects the appropriate workflow for a given request
by analyzing user intent, request type, and target URL.
"""

import logging
from urllib.parse import urlparse

from adana.common.protocols import DictParams
from adana.common.protocols.war import tool_use
from adana.core.resource.base_resource import BaseResource


logger = logging.getLogger(__name__)


class WorkflowSelectorResource(BaseResource):
    """
    Resource for selecting appropriate workflow for web research requests.

    Uses LLM reasoning to intelligently classify
    requests and select the best workflow with appropriate parameters.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Configuration
        self.config = {
            "reasoning_cache_ttl": 3600,  # Cache for 1 hour
            "temperature": 0.1,  # Low temperature for deterministic classification
            "max_tokens": 500,
        }

    @tool_use
    def select_workflow(self, request: str, target_url: str | None = None) -> DictParams:
        """
        Select appropriate workflow and parameters for the request.

        Uses LLM reasoning to intelligently classify the request
        and select the best workflow.

        Args:
            request: User/agent request text
            target_url: Target URL if provided (optional)

        Returns:
            {
                "workflow": str,  # Workflow name
                "confidence": float (0.0-1.0),
                "reasoning": str,  # Explanation of selection
                "parameters": dict,  # Workflow-specific parameters
                "fallback_workflow": str | None  # Alternative if primary fails
            }
        """
        # Extract domain if URL provided
        domain = None
        if target_url:
            parsed = urlparse(target_url)
            domain = parsed.netloc

        # Use BaseWAR.reason() for intelligent selection
        result = self.reason(
            {
                "task": "Select appropriate web research workflow and configure parameters",
                "input": {
                    "request": request,
                    "target_url": target_url,
                    "has_url": bool(target_url),
                    "domain": domain,
                    "request_length": len(request),
                    "has_question_mark": "?" in request,
                },
                "output_schema": {
                    "workflow": "str (ONLY choose from: single_source_deep_dive|research_synthesis|structured_data_navigation)",
                    "confidence": "float (0.0-1.0)",
                    "reasoning": "str (why this workflow was chosen)",
                    "parameters": "dict (workflow-specific parameters: max_sources, require_recent, extract_code, rate_limit_sec, max_pages)",
                    "fallback_workflow": "str | null",
                },
                "context": {
                    "available_workflows": self._get_workflow_descriptions(),
                    "known_domains": {
                        "documentation": [
                            "docs.python.org",
                            "developer.mozilla.org",
                            "readthedocs.io",
                            "reactjs.org/docs",
                            "vuejs.org/guide",
                        ],
                        "data_portal": ["pypi.org", "github.com", "npmjs.com", "data.gov", "kaggle.com", "huggingface.co"],
                        "news": ["medium.com", "techcrunch.com", "bbc.co.uk", "nytimes.com", "reuters.com", "substack.com"],
                    },
                },
                "examples": [
                    {
                        "input": {"request": "What is asyncio?", "has_url": False, "domain": None},
                        "output": {
                            "workflow": "fact_finding",
                            "confidence": 0.95,
                            "reasoning": "Simple factual question, needs quick authoritative answer",
                            "parameters": {"max_sources": 2},
                            "fallback_workflow": "research_synthesis",
                        },
                    },
                    {
                        "input": {"request": "Top 10 PyPI packages", "has_url": False, "domain": None},
                        "output": {
                            "workflow": "structured_data_navigation",
                            "confidence": 0.98,
                            "reasoning": "Structured list extraction needed (top 10), requires table extraction",
                            "parameters": {"max_pages": 10, "extract_tables": True, "rate_limit_sec": 1.0},
                            "fallback_workflow": "research_synthesis",
                        },
                    },
                    {
                        "input": {"request": "Compare React vs Vue", "has_url": False, "domain": None},
                        "output": {
                            "workflow": "comparison",
                            "confidence": 0.97,
                            "reasoning": "Explicit comparison request (X vs Y pattern)",
                            "parameters": {"max_sources": 4, "structured_output": True},
                            "fallback_workflow": "research_synthesis",
                        },
                    },
                    {
                        "input": {"request": "Summarize this page", "has_url": True, "domain": "docs.python.org"},
                        "output": {
                            "workflow": "documentation_site",
                            "confidence": 0.93,
                            "reasoning": "Single URL provided, domain is documentation site",
                            "parameters": {"extract_code": True, "use_site_search": False},
                            "fallback_workflow": "single_source_deep_dive",
                        },
                    },
                ],
                "temperature": self.config["temperature"],
                "max_tokens": self.config["max_tokens"],
                "fallback": self._get_fallback_workflow(request, target_url),
            }
        )

        return result

    def classify_intent(self, request: str) -> DictParams:
        """
        Classify user intent (simpler version of select_workflow).

        Args:
            request: User/agent request text

        Returns:
            {
                "intent": str,  # Intent classification
                "confidence": float (0.0-1.0),
                "reasoning": str
            }
        """
        result = self.reason(
            {
                "task": "Classify user intent for web research request",
                "input": {"request": request, "request_length": len(request), "has_question_mark": "?" in request},
                "output_schema": {
                    "intent": "str (fact_finding|comparison|trend_analysis|how_to|structured_data|research)",
                    "confidence": "float (0.0-1.0)",
                    "reasoning": "str (explanation of classification)",
                },
                "temperature": 0.0,  # Very deterministic for simple classification
                "max_tokens": 200,
                "fallback": {"intent": "research", "confidence": 0.0, "reasoning": "LLM unavailable, defaulting to general research"},
            }
        )

        return result

    def _get_fallback_workflow(self, request: str, target_url: str | None) -> DictParams:
        """
        Get fallback workflow when LLM is unavailable.

        Uses simple heuristics:
        - If URL provided -> single_source_deep_dive
        - If no URL but has query -> research_synthesis
        - Otherwise -> research_synthesis (safe default)
        """
        # Has URL -> single source analysis
        if target_url:
            return {
                "workflow": "single_source_deep_dive",
                "confidence": 0.0,
                "reasoning": "LLM unavailable, using URL-based heuristic",
                "parameters": {},
                "fallback_workflow": None,
            }

        # No URL -> research/search
        return {
            "workflow": "research_synthesis",
            "confidence": 0.0,
            "reasoning": "LLM unavailable, using query-based heuristic",
            "parameters": {"max_sources": 3},
            "fallback_workflow": None,
        }

    def _get_workflow_descriptions(self) -> dict[str, str]:
        """Get descriptions of all available workflows."""
        return {
            # IMPLEMENTED Workflows (3 core workflows)
            "single_source_deep_dive": "Thoroughly analyze one specific document. Use when URL is provided. Deep content extraction, quality assessment, key points extraction.",
            "research_synthesis": "Understanding topics across 3-5 sources. Use for general queries without URL. Multi-source fetching and intelligent synthesis.",
            "structured_data_navigation": "Extract tables, lists, statistics from multiple pages. Use for 'top N', 'list of', numerical data requests. Handles pagination.",
            # NOT YET IMPLEMENTED (future enhancements)
            # "documentation_site": "Python docs, MDN, official docs (coming soon)",
            # "data_portal": "GitHub, PyPI, npm (coming soon)",
            # "news_site": "News articles, blogs (coming soon)",
            # "fact_finding": "Quick factual answers (coming soon)",
            # "comparison": "Compare X vs Y (coming soon)",
            # "trend_analysis": "Latest developments (coming soon)",
            # "how_to": "Step-by-step tutorials (coming soon)"
        }
