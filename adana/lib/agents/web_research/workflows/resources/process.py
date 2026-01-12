"""
ProcessComponents - Transforming and analyzing extracted content.

Provides reusable processing operations that can be composed into workflows.
"""

import logging

from adana.common.protocols import DictParams
from adana.common.protocols.war import tool_use
from adana.core.resource.base_resource import BaseResource
from adana.lib.agents.web_research.workflows.resources.components import _content_extractor


logger = logging.getLogger(__name__)


class ProcessResource(BaseResource):
    """Reusable processing operations for workflow composition."""

    def __init__(self, **kwargs):
        """
        Initialize process components.
        """
        super().__init__(**kwargs)
        self.content_extractor = _content_extractor

    def assess_content_quality(self, html: str, url: str, purpose: str) -> DictParams:
        """
        Assess content quality using LLM reasoning.

        Args:
            html: Raw HTML content
            url: Source URL
            purpose: What the content will be used for

        Returns:
            Quality assessment with sufficiency, score, recommendations
        """
        return self.content_extractor.assess_content_quality(html, url, purpose)

    def filter_by_quality(self, extractions: list[DictParams], urls: list[str], purpose: str, min_quality: float = 0.6) -> list[DictParams]:
        """
        Filter extracted content by quality threshold.

        Args:
            extractions: List of extraction results
            urls: Corresponding URLs
            purpose: What content will be used for
            min_quality: Minimum quality score (0.0-1.0)

        Returns:
            Filtered list of high-quality extractions
        """
        high_quality = []

        for extraction, _ in zip(extractions, urls, strict=False):
            if not extraction.get("success"):
                continue

            # Get quality assessment (would need HTML, simplified here)
            # In real workflow, this would be called with full HTML
            content_text = extraction.get("content_text", "")
            word_count = extraction.get("word_count", 0)

            # Simple quality heuristics (would use LLM in full implementation)
            if word_count >= 100 and len(content_text) >= 500:
                high_quality.append(extraction)

        return high_quality

    @tool_use
    def extract_key_points(self, content_text: str, max_points: int = 5) -> DictParams:
        """
        Extract key points from content using LLM reasoning.

        Args:
            content_text: Text content to analyze
            max_points: Maximum number of key points

        Returns:
            {
                "key_points": list[str],
                "summary": str,
                "total_points": int
            }
        """
        # Use BaseWAR.reason() for intelligent extraction
        result = self.reason(
            {
                "task": "Extract key points and create summary from content",
                "input": {
                    "content": content_text[:5000],  # First 5000 chars
                    "content_length": len(content_text),
                    "max_points": max_points,
                },
                "output_schema": {
                    "key_points": f"list[str] (up to {max_points} key points)",
                    "summary": "str (2-3 sentence summary)",
                    "total_points": "int",
                },
                "context": {
                    "instructions": [
                        "Extract the most important points",
                        "Be concise and specific",
                        "Focus on factual information",
                        "Order by importance",
                    ]
                },
                "temperature": 0.3,
                "max_tokens": 1000,
                "fallback": {"key_points": [content_text[:200] + "..."], "summary": content_text[:300] + "...", "total_points": 1},
            }
        )

        return result

    def extract_steps(self, content_text: str) -> DictParams:
        """
        Extract step-by-step instructions from how-to content.

        Args:
            content_text: Text content containing instructions

        Returns:
            {
                "steps": list[dict],  # Each with 'number', 'instruction', 'details'
                "total_steps": int,
                "has_code": bool
            }
        """
        # Use BaseWAR.reason() for intelligent extraction
        result = self.reason(
            {
                "task": "Extract step-by-step instructions from tutorial/how-to content",
                "input": {"content": content_text[:5000], "content_length": len(content_text)},
                "output_schema": {
                    "steps": "list[dict] (each with 'number', 'instruction', 'details' keys)",
                    "total_steps": "int",
                    "has_code": "bool (whether steps include code examples)",
                },
                "context": {
                    "instructions": [
                        "Identify numbered or sequential steps",
                        "Each step should have clear instruction",
                        "Include relevant details for each step",
                        "Maintain original order",
                    ]
                },
                "examples": [
                    {
                        "input": {"content": "First, install the package. Then import it..."},
                        "output": {
                            "steps": [
                                {"number": 1, "instruction": "Install the package", "details": ""},
                                {"number": 2, "instruction": "Import it", "details": ""},
                            ],
                            "total_steps": 2,
                            "has_code": False,
                        },
                    }
                ],
                "temperature": 0.2,
                "max_tokens": 2000,
                "fallback": {
                    "steps": [{"number": 1, "instruction": "See original content", "details": ""}],
                    "total_steps": 1,
                    "has_code": False,
                },
            }
        )

        return result

    def structure_as_table(self, items: list[str | dict], columns: list[str] | None = None) -> DictParams:
        """
        Structure list of items as table for better presentation.

        Args:
            items: List of items to structure
            columns: Column names (if items are dicts)

        Returns:
            {
                "headers": list[str],
                "rows": list[list[str]],
                "total_rows": int
            }
        """
        if not items:
            return {"headers": [], "rows": [], "total_rows": 0}

        # If items are strings, create simple single-column table
        if isinstance(items[0], str):
            return {"headers": ["Item"], "rows": [[item] for item in items], "total_rows": len(items)}

        # If items are dicts, extract columns
        if isinstance(items[0], dict):
            if columns is None:
                columns = list(items[0].keys())

            rows = []
            for item in items:
                row = [str(item.get(col, "")) for col in columns]
                rows.append(row)

            return {"headers": columns, "rows": rows, "total_rows": len(rows)}

        # Fallback
        return {"headers": ["Value"], "rows": [[str(item)] for item in items], "total_rows": len(items)}

    @tool_use
    def deduplicate_content(self, extractions: list[DictParams], similarity_threshold: float = 0.8) -> list[DictParams]:
        """
        Remove duplicate or highly similar content.

        Args:
            extractions: List of extraction results
            similarity_threshold: Similarity threshold (0.0-1.0)

        Returns:
            Deduplicated list of extractions with preserved URL information
        """
        if not extractions:
            return []

        # Simple deduplication based on title and content length
        # (More sophisticated approach would use embeddings)
        unique = []
        seen_titles = set()

        for extraction in extractions:
            if not extraction.get("success"):
                continue

            title = extraction.get("title", "").lower().strip()
            word_count = extraction.get("word_count", 0)

            # Create fingerprint
            fingerprint = f"{title}_{word_count}"

            if fingerprint not in seen_titles:
                seen_titles.add(fingerprint)
                # Ensure URL information is preserved
                if "url" not in extraction:
                    extraction["url"] = "unknown"
                unique.append(extraction)
            else:
                # For duplicates, we could optionally merge URL information
                # but for now, just skip the duplicate
                logger.debug(f"Skipping duplicate content: {title}")

        logger.info(f"Deduplicated {len(extractions)} -> {len(unique)} extractions")
        return unique

    def merge_content(self, extractions: list[DictParams], merge_strategy: str = "concatenate") -> DictParams:
        """
        Merge multiple extractions into single content block.

        Args:
            extractions: List of extraction results
            merge_strategy: How to merge ("concatenate", "interleave", "weighted")

        Returns:
            {
                "merged_text": str,
                "merged_markdown": str,
                "sources": list[str],  # Source titles
                "total_word_count": int
            }
        """
        merged_text_parts = []
        merged_markdown_parts = []
        sources = []
        total_words = 0

        for extraction in extractions:
            if not extraction.get("success"):
                continue

            content_text = extraction.get("content_text", "")
            content_markdown = extraction.get("content_markdown", "")
            title = extraction.get("title", "Untitled")

            sources.append(title)
            total_words += extraction.get("word_count", 0)

            if merge_strategy == "concatenate":
                merged_text_parts.append(content_text)
                merged_markdown_parts.append(f"## {title}\n\n{content_markdown}")

        merged_text = "\n\n".join(merged_text_parts)
        merged_markdown = "\n\n---\n\n".join(merged_markdown_parts)

        return {
            "merged_text": merged_text,
            "merged_markdown": merged_markdown,
            "sources": sources,
            "total_word_count": total_words,
            "total_sources": len(sources),
        }

    def analyze_content_type(self, extraction: DictParams) -> DictParams:
        """
        Analyze content type and characteristics using LLM.

        Args:
            extraction: Extraction result to analyze

        Returns:
            {
                "content_type": str,  # article, tutorial, documentation, etc.
                "has_code": bool,
                "has_tables": bool,
                "is_technical": bool,
                "reading_level": str  # beginner, intermediate, advanced
            }
        """
        if not extraction.get("success"):
            return {"content_type": "unknown", "has_code": False, "has_tables": False, "is_technical": False, "reading_level": "unknown"}

        content_text = extraction.get("content_text", "")
        content_html = extraction.get("content_html", "")

        # Simple heuristics (could use LLM for better analysis)
        has_code = "<code" in content_html or "<pre" in content_html
        has_tables = "<table" in content_html

        # Use LLM for deeper analysis
        result = self.reason(
            {
                "task": "Analyze content type and characteristics",
                "input": {
                    "content_preview": content_text[:1000],
                    "word_count": extraction.get("word_count", 0),
                    "has_code": has_code,
                    "has_tables": has_tables,
                    "title": extraction.get("title", ""),
                },
                "output_schema": {
                    "content_type": "str (article|tutorial|documentation|news|blog|forum|data|other)",
                    "is_technical": "bool",
                    "reading_level": "str (beginner|intermediate|advanced)",
                    "primary_topic": "str",
                },
                "temperature": 0.2,
                "max_tokens": 300,
                "fallback": {
                    "content_type": "article",
                    "is_technical": has_code,
                    "reading_level": "intermediate",
                    "primary_topic": "general",
                },
            }
        )

        return {**result, "has_code": has_code, "has_tables": has_tables}
