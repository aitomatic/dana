"""Source ranking resource for evaluating and ranking information sources by quality."""

import time
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

from dana.common.observable import observable
from dana.common.protocols import DictParams
from dana.common.protocols.war import tool_use
from dana.core.resource.base_resource import BaseResource


class SourceRankingResource(BaseResource):
    """
    <PUBLIC_DESCRIPTION>
    Domain-agnostic resource for evaluating and ranking information sources by quality.

    Provides methods for:
    - **rank_by_quality**: Multi-factor scoring (relevance, authority, recency)
    - **assess_authority**: Domain reputation and credibility assessment
    - **check_recency**: Information freshness evaluation

    USE CASES:
    - Multi-source research and information gathering
    - Content curation and aggregation
    - Source validation and verification
    - Academic and professional research

    FEATURES:
    - Configurable scoring weights
    - Domain authority database
    - Recency scoring with decay curves
    - Graceful degradation on missing data
    </PUBLIC_DESCRIPTION>
    """

    # Domain authority scores (0-1)
    DOMAIN_AUTHORITY = {
        # Academic
        "arxiv.org": 0.95,
        "scholar.google.com": 0.95,
        "ieee.org": 0.95,
        "acm.org": 0.95,
        "nature.com": 0.98,
        "science.org": 0.98,
        ".edu": 0.90,

        # Technical documentation
        "github.com": 0.85,
        "stackoverflow.com": 0.80,
        "developer.mozilla.org": 0.90,
        "docs.python.org": 0.95,

        # News and media
        "nytimes.com": 0.85,
        "reuters.com": 0.88,
        "bloomberg.com": 0.87,
        "techcrunch.com": 0.75,
        "arstechnica.com": 0.80,

        # Tech blogs
        "medium.com": 0.60,
        "dev.to": 0.60,
        "blog": 0.55,  # Generic blog subdomain
    }

    def __init__(self, resource_id: str | None = None, **kwargs):
        super().__init__(resource_id=resource_id or "source-ranking", **kwargs)

    @tool_use
    @observable
    def rank_by_quality(
        self,
        sources: list[dict[str, Any]],
        query: str,
        criteria: dict[str, float] | None = None,
        **kwargs
    ) -> DictParams:
        """
        Rank sources by quality using multi-factor scoring.

        Args:
            sources: List of source dicts with keys: url, title, content, date
            query: The search query for relevance scoring
            criteria: Optional scoring weights {relevance, authority, recency}
                     Defaults to {0.4, 0.3, 0.3}

        Returns:
            {
                "success": True,
                "ranked_sources": [...],  # Sorted by score (highest first)
                "scoring_criteria": {...},
                "metadata": {...}
            }
        """
        try:
            start_time = time.time()

            # Default criteria weights
            if criteria is None:
                criteria = {
                    "relevance": 0.4,
                    "authority": 0.3,
                    "recency": 0.3
                }

            ranked = []
            for source in sources:
                # Calculate individual scores
                relevance = self._calculate_relevance(source, query)
                authority_result = self.assess_authority(
                    url=source.get("url", ""),
                    domain=source.get("domain", "")
                )
                authority = authority_result.get("authority_score", 0.5)

                recency_result = self.check_recency(
                    date=source.get("date", ""),
                    content=source.get("content", "")
                )
                recency = recency_result.get("recency_score", 0.5)

                # Calculate weighted score
                overall_score = (
                    relevance * criteria["relevance"] +
                    authority * criteria["authority"] +
                    recency * criteria["recency"]
                )

                ranked.append({
                    **source,
                    "scores": {
                        "overall": round(overall_score, 3),
                        "relevance": round(relevance, 3),
                        "authority": round(authority, 3),
                        "recency": round(recency, 3)
                    }
                })

            # Sort by overall score (descending)
            ranked.sort(key=lambda x: x["scores"]["overall"], reverse=True)

            processing_time = time.time() - start_time

            return {
                "success": True,
                "ranked_sources": ranked,
                "total_sources": len(ranked),
                "scoring_criteria": criteria,
                "metadata": {
                    "processing_time": round(processing_time, 3),
                    "timestamp": time.time()
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "ranked_sources": sources,  # Return unranked as fallback
                "total_sources": len(sources)
            }

    @tool_use
    @observable
    def assess_authority(
        self,
        url: str,
        domain: str | None = None,
        **kwargs
    ) -> DictParams:
        """
        Assess source authority and credibility.

        Args:
            url: Source URL
            domain: Optional pre-parsed domain

        Returns:
            {
                "success": True,
                "authority_score": float,  # 0-1
                "authority_level": str,    # high/medium/low
                "reasoning": str,
                "domain": str
            }
        """
        try:
            # Parse domain if not provided
            if not domain:
                parsed = urlparse(url)
                domain = parsed.netloc.lower()

            # Check exact domain matches
            authority_score = None
            for known_domain, score in self.DOMAIN_AUTHORITY.items():
                if known_domain in domain:
                    authority_score = score
                    break

            # Default score for unknown domains
            if authority_score is None:
                # Apply heuristics
                if ".gov" in domain:
                    authority_score = 0.90
                elif ".edu" in domain:
                    authority_score = 0.85
                elif ".org" in domain:
                    authority_score = 0.70
                else:
                    authority_score = 0.50  # Neutral for unknown

            # Determine authority level
            if authority_score >= 0.85:
                authority_level = "high"
                reasoning = f"Highly authoritative source ({domain})"
            elif authority_score >= 0.65:
                authority_level = "medium"
                reasoning = f"Moderately authoritative source ({domain})"
            else:
                authority_level = "low"
                reasoning = f"Lower authority or unknown source ({domain})"

            return {
                "success": True,
                "authority_score": authority_score,
                "authority_level": authority_level,
                "reasoning": reasoning,
                "domain": domain,
                "timestamp": time.time()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "authority_score": 0.5,  # Fallback neutral score
                "authority_level": "unknown",
                "reasoning": f"Error assessing authority: {str(e)}",
                "domain": domain or "unknown"
            }

    @tool_use
    @observable
    def check_recency(
        self,
        date: str,
        content: str | None = None,
        **kwargs
    ) -> DictParams:
        """
        Assess information freshness based on date.

        Args:
            date: Publication date (ISO format or natural language)
            content: Optional content to extract date from if date is empty

        Returns:
            {
                "success": True,
                "recency_score": float,  # 0-1
                "recency_level": str,    # very_recent/recent/dated/old
                "days_old": int,
                "reasoning": str
            }
        """
        try:
            # Parse date
            if not date and content:
                # Try to extract date from content (simplified)
                date = self._extract_date_from_content(content)

            if not date:
                # No date available
                return {
                    "success": True,
                    "recency_score": 0.5,  # Neutral
                    "recency_level": "unknown",
                    "days_old": None,
                    "reasoning": "No publication date available"
                }

            # Parse date string to datetime
            try:
                if "T" in date:  # ISO format
                    pub_date = datetime.fromisoformat(date.replace("Z", "+00:00"))
                else:  # Try common formats
                    from dateutil import parser
                    pub_date = parser.parse(date)
            except Exception:
                # Date parsing failed
                return {
                    "success": True,
                    "recency_score": 0.5,
                    "recency_level": "unknown",
                    "days_old": None,
                    "reasoning": f"Could not parse date: {date}"
                }

            # Calculate days old
            now = datetime.now(pub_date.tzinfo) if pub_date.tzinfo else datetime.now()
            days_old = (now - pub_date).days

            # Score based on age (exponential decay)
            # Very recent (0-30 days): 0.9-1.0
            # Recent (30-180 days): 0.7-0.9
            # Dated (180-365 days): 0.5-0.7
            # Old (>365 days): 0.3-0.5
            if days_old < 0:
                days_old = 0  # Future date, treat as today

            if days_old <= 30:
                recency_score = 1.0 - (days_old / 300)  # Slow decay
                recency_level = "very_recent"
                reasoning = f"Very recent ({days_old} days old)"
            elif days_old <= 180:
                recency_score = 0.9 - ((days_old - 30) / 750)
                recency_level = "recent"
                reasoning = f"Recent ({days_old} days old)"
            elif days_old <= 365:
                recency_score = 0.7 - ((days_old - 180) / 925)
                recency_level = "dated"
                reasoning = f"Somewhat dated ({days_old} days old)"
            else:
                recency_score = max(0.3, 0.5 - ((days_old - 365) / 3650))
                recency_level = "old"
                reasoning = f"Old information ({days_old} days old)"

            return {
                "success": True,
                "recency_score": round(recency_score, 3),
                "recency_level": recency_level,
                "days_old": days_old,
                "date": date,
                "reasoning": reasoning,
                "timestamp": time.time()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "recency_score": 0.5,  # Fallback neutral
                "recency_level": "unknown",
                "days_old": None,
                "reasoning": f"Error assessing recency: {str(e)}"
            }

    def _calculate_relevance(self, source: dict, query: str) -> float:
        """
        Calculate relevance score using simple keyword matching.

        More sophisticated implementations could use:
        - TF-IDF
        - Semantic similarity (embeddings)
        - LLM-based relevance scoring
        """
        try:
            # Normalize query and content
            query_lower = query.lower()
            title = source.get("title", "").lower()
            content = source.get("content", "").lower()
            snippet = source.get("snippet", "").lower()

            # Extract query keywords
            query_words = set(query_lower.split())

            # Count keyword matches
            title_matches = sum(1 for word in query_words if word in title)
            content_matches = sum(1 for word in query_words if word in content or word in snippet)

            # Calculate score (weighted by position)
            title_score = min(1.0, title_matches / max(1, len(query_words)))
            content_score = min(1.0, content_matches / max(1, len(query_words)))

            # Weighted combination (title more important)
            relevance = (title_score * 0.6) + (content_score * 0.4)

            return max(0.1, relevance)  # Minimum 0.1 to avoid zero scores

        except Exception:
            return 0.5  # Fallback neutral score

    def _extract_date_from_content(self, content: str) -> str | None:
        """
        Extract date from content using simple pattern matching.

        More sophisticated implementations could use:
        - Regex patterns for various date formats
        - NLP-based date extraction
        - LLM-based date identification
        """
        # Simplified: return None and rely on explicit date field
        # A real implementation would use regex or dateutil
        return None
