"""
SynthesizeComponents - Combining and analyzing information from multiple sources.

Provides reusable synthesis operations that can be composed into workflows.
"""

import logging

from adana.common.protocols import DictParams
from adana.common.protocols.war import tool_use
from adana.core.resource.base_resource import BaseResource


logger = logging.getLogger(__name__)


class SynthesizeResource(BaseResource):
    """Reusable synthesis operations for workflow composition."""

    def __init__(self, **kwargs):
        """Initialize synthesis components."""
        super().__init__(**kwargs)

    @tool_use
    def synthesize_by_themes(self, extractions: list[DictParams], topic: str) -> DictParams:
        """
        Synthesize content by identifying and organizing around themes.

        Args:
            extractions: List of extraction results from multiple sources
            topic: Overall topic being researched

        Returns:
            {
                "themes": list[dict],  # Each with 'name', 'description', 'sources'
                "synthesis": str,  # Overall synthesis text
                "confidence": float,
                "total_sources": int,
                "source_urls": list[str]  # URLs of all sources used
            }
        """
        # Prepare content for analysis
        contents = []
        sources = []
        source_urls = []

        for extraction in extractions:
            if extraction.get("success"):
                content_text = extraction.get("content_text", "")
                title = extraction.get("title", "Untitled")
                url = extraction.get("url", "")

                contents.append(
                    {
                        "title": title,
                        "excerpt": content_text[:1000],  # First 1000 chars
                        "word_count": extraction.get("word_count", 0),
                        "url": url,  # Include URL for source attribution
                    }
                )
                sources.append(title)
                source_urls.append(url)

        # Use BaseWAR.reason() for intelligent synthesis
        result = self.reason(
            {
                "task": "Identify themes and synthesize information across multiple sources",
                "input": {"topic": topic, "num_sources": len(contents), "contents": contents},
                "output_schema": {
                    "themes": "list[dict] (each with 'name', 'description', 'supporting_sources' keys)",
                    "synthesis": "str (3-5 paragraph synthesis organized by themes)",
                    "confidence": "float (0.0-1.0, how consistent sources are)",
                    "total_sources": "int",
                },
                "context": {
                    "instructions": [
                        "Identify 3-5 major themes across sources",
                        "Note which sources support each theme",
                        "Synthesize information, noting agreements and disagreements",
                        "Organize synthesis by themes, not by source",
                        "Be objective and balanced",
                    ]
                },
                "temperature": 0.3,
                "max_tokens": 3000,
                "fallback": {
                    "themes": [{"name": "General", "description": topic, "supporting_sources": sources}],
                    "synthesis": f"Information gathered from {len(sources)} sources about {topic}.",
                    "confidence": 0.5,
                    "total_sources": len(sources),
                    "source_urls": source_urls,
                },
            }
        )

        return result

    def synthesize_by_comparison(self, item1: str, item2: str, extractions: list[DictParams]) -> DictParams:
        """
        Synthesize comparison information between two items.

        Args:
            item1: First item being compared
            item2: Second item being compared
            extractions: List of extraction results from comparison sources

        Returns:
            {
                "comparison_table": dict,  # Structured comparison
                "synthesis": str,  # Comparison synthesis
                "winner": str | None,  # If clear winner emerges
                "confidence": float
            }
        """
        # Prepare content
        contents = []

        for extraction in extractions:
            if extraction.get("success"):
                contents.append({"title": extraction.get("title", ""), "excerpt": extraction.get("content_text", "")[:1500]})

        # Use BaseWAR.reason() for intelligent comparison
        result = self.reason(
            {
                "task": f"Compare {item1} vs {item2} based on multiple sources",
                "input": {"item1": item1, "item2": item2, "num_sources": len(contents), "contents": contents},
                "output_schema": {
                    "comparison_table": {
                        "categories": "list[str] (comparison dimensions)",
                        f"{item1}": "list[str] (characteristics for each category)",
                        f"{item2}": "list[str] (characteristics for each category)",
                    },
                    "synthesis": "str (2-3 paragraph comparison synthesis)",
                    "winner": f"str | null ({item1}|{item2}|tie, if clear winner)",
                    "confidence": "float (0.0-1.0)",
                    "key_differences": "list[str] (3-5 key differences)",
                },
                "context": {
                    "instructions": [
                        "Identify key comparison dimensions",
                        "Be objective and balanced",
                        "Note strengths and weaknesses of each",
                        "Only declare winner if sources clearly agree",
                        "Focus on factual differences",
                    ]
                },
                "temperature": 0.2,
                "max_tokens": 2500,
                "fallback": {
                    "comparison_table": {"categories": ["General"], item1: ["See sources"], item2: ["See sources"]},
                    "synthesis": f"Comparison of {item1} and {item2} based on {len(contents)} sources.",
                    "winner": None,
                    "confidence": 0.5,
                    "key_differences": [],
                },
            }
        )

        return result

    @tool_use
    def synthesize_by_timeline(self, extractions: list[DictParams], topic: str) -> DictParams:
        """
        Synthesize information by temporal progression (trends over time).

        Args:
            extractions: List of extraction results with temporal information
            topic: Topic being analyzed

        Returns:
            {
                "timeline": list[dict],  # Events/trends over time
                "trend_direction": str,  # increasing, decreasing, stable, cyclical
                "synthesis": str,
                "confidence": float
            }
        """
        # Prepare temporal content
        contents = []

        for extraction in extractions:
            if extraction.get("success"):
                contents.append(
                    {
                        "title": extraction.get("title", ""),
                        "excerpt": extraction.get("content_text", "")[:1000],
                        "published_date": extraction.get("published_date"),
                        "word_count": extraction.get("word_count", 0),
                    }
                )

        # Use BaseWAR.reason() for temporal synthesis
        result = self.reason(
            {
                "task": "Analyze trends and temporal progression across sources",
                "input": {"topic": topic, "num_sources": len(contents), "contents": contents},
                "output_schema": {
                    "timeline": "list[dict] (each with 'period', 'description', 'sources' keys)",
                    "trend_direction": "str (increasing|decreasing|stable|cyclical|mixed)",
                    "synthesis": "str (2-3 paragraph temporal analysis)",
                    "confidence": "float (0.0-1.0)",
                    "key_developments": "list[str] (major developments over time)",
                },
                "context": {
                    "instructions": [
                        "Identify temporal patterns and trends",
                        "Note how topic evolved over time",
                        "Identify key inflection points",
                        "Analyze direction of change",
                        "Be specific about timeframes",
                    ]
                },
                "temperature": 0.3,
                "max_tokens": 2500,
                "fallback": {
                    "timeline": [{"period": "Recent", "description": topic, "sources": []}],
                    "trend_direction": "stable",
                    "synthesis": f"Temporal analysis of {topic} based on {len(contents)} sources.",
                    "confidence": 0.5,
                    "key_developments": [],
                },
            }
        )

        return result

    def extract_fact(self, extractions: list[DictParams], query: str) -> DictParams:
        """
        Extract specific factual answer from multiple sources.

        Args:
            extractions: List of extraction results
            query: Specific factual question

        Returns:
            {
                "answer": str,  # The factual answer
                "sources": list[str],  # Sources that support answer
                "confidence": float,
                "contradictions": list[str]  # Any contradicting information
            }
        """
        # Prepare content
        contents = []
        source_titles = []

        for extraction in extractions:
            if extraction.get("success"):
                contents.append({"title": extraction.get("title", ""), "excerpt": extraction.get("content_text", "")[:1500]})
                source_titles.append(extraction.get("title", ""))

        # Use BaseWAR.reason() for fact extraction
        result = self.reason(
            {
                "task": "Extract specific factual answer from multiple sources",
                "input": {"query": query, "num_sources": len(contents), "contents": contents},
                "output_schema": {
                    "answer": "str (concise factual answer)",
                    "sources": "list[str] (titles of sources supporting answer)",
                    "confidence": "float (0.0-1.0)",
                    "contradictions": "list[str] (any contradicting information found)",
                    "details": "str (additional context or details)",
                },
                "context": {
                    "instructions": [
                        "Provide concise, factual answer",
                        "List sources that support the answer",
                        "Note any contradictions between sources",
                        "If sources disagree, present most authoritative view",
                        "Be specific with numbers, dates, etc.",
                    ]
                },
                "temperature": 0.1,  # Very deterministic for facts
                "max_tokens": 1000,
                "fallback": {
                    "answer": "Unable to determine from sources",
                    "sources": [],
                    "confidence": 0.0,
                    "contradictions": [],
                    "details": "",
                },
            }
        )

        return result

    def aggregate_statistics(self, extractions: list[DictParams], metric_name: str) -> DictParams:
        """
        Aggregate statistical information from multiple sources.

        Args:
            extractions: List of extraction results with tables/data
            metric_name: Name of metric to aggregate

        Returns:
            {
                "values": list[float],  # All values found
                "mean": float,
                "median": float,
                "range": tuple[float, float],
                "sources": list[str],
                "confidence": float
            }
        """
        # Extract values from tables in extractions
        # This is a simplified version; real implementation would parse tables
        values = []
        sources = []

        # Use BaseWAR.reason() to help extract numerical values
        for extraction in extractions:
            if not extraction.get("success"):
                continue

            content_text = extraction.get("content_text", "")
            title = extraction.get("title", "")

            # Use LLM to extract values
            extract_result = self.reason(
                {
                    "task": f"Extract numerical values for {metric_name}",
                    "input": {"metric_name": metric_name, "content": content_text[:1000]},
                    "output_schema": {"values": "list[float] (numerical values found)", "found": "bool (whether metric was found)"},
                    "temperature": 0.1,
                    "max_tokens": 300,
                    "fallback": {"values": [], "found": False},
                }
            )

            if extract_result.get("found"):
                extracted_values = extract_result.get("values", [])
                values.extend(extracted_values)
                sources.extend([title] * len(extracted_values))

        # Calculate statistics
        if values:
            import statistics

            return {
                "values": values,
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                "range": (min(values), max(values)),
                "sources": sources,
                "total_values": len(values),
                "confidence": min(1.0, len(values) / 5.0),  # More sources = higher confidence
            }
        else:
            return {
                "values": [],
                "mean": None,
                "median": None,
                "range": None,
                "sources": [],
                "total_values": 0,
                "confidence": 0.0,
                "error": f"No values found for {metric_name}",
            }

    @tool_use
    def create_executive_summary(self, extractions: list[DictParams], topic: str, max_words: int = 200) -> DictParams:
        """
        Create executive summary from multiple sources.

        Args:
            extractions: List of extraction results
            topic: Topic being summarized
            max_words: Maximum words in summary

        Returns:
            {
                "summary": str,
                "key_findings": list[str],
                "sources_used": int,
                "confidence": float
            }
        """
        # Prepare content
        contents = []

        for extraction in extractions:
            if extraction.get("success"):
                contents.append({"title": extraction.get("title", ""), "excerpt": extraction.get("excerpt", "")})

        # Use BaseWAR.reason() for summary creation
        result = self.reason(
            {
                "task": "Create executive summary from multiple sources",
                "input": {"topic": topic, "max_words": max_words, "num_sources": len(contents), "contents": contents},
                "output_schema": {
                    "summary": f"str (executive summary, max {max_words} words)",
                    "key_findings": "list[str] (3-5 key findings)",
                    "sources_used": "int",
                    "confidence": "float (0.0-1.0)",
                },
                "context": {
                    "instructions": [
                        "Create concise executive summary",
                        "Focus on most important insights",
                        "Be objective and factual",
                        "Highlight key findings separately",
                        f"Keep summary under {max_words} words",
                    ]
                },
                "temperature": 0.3,
                "max_tokens": 1500,
                "fallback": {
                    "summary": f"Summary of {topic} based on {len(contents)} sources.",
                    "key_findings": [],
                    "sources_used": len(contents),
                    "confidence": 0.5,
                },
            }
        )

        return result
