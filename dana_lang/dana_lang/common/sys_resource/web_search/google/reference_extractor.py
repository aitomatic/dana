"""Reference link extraction and processing."""

import logging
import re
from typing import NamedTuple
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .config import GoogleSearchConfig

logger = logging.getLogger(__name__)


class ReferenceLink(NamedTuple):
    """A reference link with metadata."""

    url: str
    text: str
    relevance_score: int
    context: str = ""  # Surrounding text context


class ReferenceResult(NamedTuple):
    """Result of reference link extraction."""

    source_url: str
    reference_links: list[ReferenceLink]
    total_links_found: int
    relevant_links_found: int
    success: bool
    error_message: str = ""


class ReferenceExtractor:
    """Extracts relevant reference links from HTML content."""

    def __init__(self, config: GoogleSearchConfig):
        """
        Initialize reference extractor.

        Args:
            config: Google search configuration
        """
        self.config = config

    def extract_reference_links(self, html_content: str, base_url: str, query: str, search_depth: str = "basic") -> ReferenceResult:
        """
        Extract relevant reference links from HTML content.

        Args:
            html_content: Raw HTML content
            base_url: Base URL for resolving relative links
            query: Search query for relevance scoring
            search_depth: Search depth level (basic, standard, extensive)

        Returns:
            ReferenceResult with extracted links
        """
        # Skip reference extraction for basic search depth
        if search_depth == "basic":
            logger.info("📋 Skipping reference extraction for basic search depth")
            return ReferenceResult(
                source_url=base_url,
                reference_links=[],
                total_links_found=0,
                relevant_links_found=0,
                success=True,
            )

        logger.info(f"🔗 Extracting reference links from: {base_url} (depth: {search_depth})")

        try:
            # Parse HTML content
            soup = BeautifulSoup(html_content, "html.parser")

            # Extract all links
            all_links = self._extract_all_links(soup, base_url)
            total_links = len(all_links)

            if not all_links:
                logger.info("No links found in HTML content")
                return ReferenceResult(
                    source_url=base_url,
                    reference_links=[],
                    total_links_found=0,
                    relevant_links_found=0,
                    success=True,
                )

            # Filter and score for relevance
            relevant_links = self._filter_and_score_links(all_links, query, search_depth)

            # Limit results based on search depth
            max_links = self._get_max_links_for_depth(search_depth)
            limited_links = relevant_links[:max_links]

            logger.info(f"🔗 Found {len(limited_links)} relevant links from {total_links} total links")

            return ReferenceResult(
                source_url=base_url,
                reference_links=limited_links,
                total_links_found=total_links,
                relevant_links_found=len(relevant_links),
                success=True,
            )

        except Exception as e:
            logger.error(f"❌ Reference extraction failed for {base_url}: {e}")
            return ReferenceResult(
                source_url=base_url,
                reference_links=[],
                total_links_found=0,
                relevant_links_found=0,
                success=False,
                error_message=str(e),
            )

    def _extract_all_links(self, soup: BeautifulSoup, base_url: str) -> list[dict]:
        """Extract all links from HTML soup."""
        all_links = []

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()

            # Skip invalid or unwanted links
            if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
                continue

            # Convert relative URLs to absolute
            absolute_url = urljoin(base_url, href)

            # Skip self-references
            if absolute_url == base_url:
                continue

            # Get link text and surrounding context
            link_text = a_tag.get_text(strip=True)
            context = self._get_link_context(a_tag)

            all_links.append({"url": absolute_url, "text": link_text, "context": context, "element": a_tag})

        return all_links

    def _get_link_context(self, a_tag) -> str:
        """Get surrounding text context for a link."""
        try:
            # Get parent element text
            parent = a_tag.parent
            if parent:
                context = parent.get_text(strip=True)
                # Limit context length
                if len(context) > 200:
                    context = context[:200] + "..."
                return context
        except Exception:
            pass
        return ""

    def _filter_and_score_links(self, all_links: list[dict], query: str, search_depth: str) -> list[ReferenceLink]:
        """Filter links for relevance and score them."""
        scored_links = []
        query_lower = query.lower()
        query_terms = self._extract_query_terms(query_lower)

        for link_data in all_links:
            url = link_data["url"].lower()
            text = link_data["text"].lower()
            context = link_data["context"].lower()

            # Skip obviously irrelevant links
            if self._should_skip_link(url):
                continue

            # Score the link
            score = self._calculate_relevance_score(url, text, context, query_terms, search_depth)

            if score > 0:
                scored_links.append(
                    ReferenceLink(
                        url=link_data["url"],
                        text=link_data["text"],
                        context=link_data["context"],
                        relevance_score=score,
                    )
                )

        # Sort by relevance score (highest first)
        scored_links.sort(key=lambda x: x.relevance_score, reverse=True)
        return scored_links

    def _should_skip_link(self, url: str) -> bool:
        """Check if link should be skipped based on URL patterns."""
        skip_patterns = [
            "facebook.com",
            "twitter.com",
            "linkedin.com",
            "instagram.com",
            "youtube.com",
            "tiktok.com",
            "pinterest.com",
            "reddit.com",
            "terms-of-service",
            "privacy-policy",
            "cookie-policy",
            "contact-us",
            "about-us",
            "careers",
            "news",
            "blog",
            "login",
            "register",
            "signup",
            "cart",
            "checkout",
            "account",
            "search",
            "sitemap",
            "rss",
            "feed",
        ]

        return any(pattern in url for pattern in skip_patterns)

    def _extract_query_terms(self, query: str) -> list[str]:
        """Extract meaningful terms from search query."""
        # Remove common words and extract terms
        stop_words = {
            "the",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "about",
            "how",
            "what",
            "when",
            "where",
            "why",
            "which",
            "who",
            "is",
            "are",
            "was",
            "were",
        }

        terms = re.findall(r"\b\w{3,}\b", query.lower())
        return [term for term in terms if term not in stop_words]

    def _calculate_relevance_score(self, url: str, text: str, context: str, query_terms: list[str], search_depth: str) -> int:
        """Calculate relevance score for a link."""
        score = 0
        combined_text = f"{url} {text} {context}"

        # Query term matching (high priority)
        for term in query_terms:
            if term in combined_text:
                score += 10 * combined_text.count(term)

        # Technical document indicators (medium priority)
        tech_indicators = [
            "spec",
            "specification",
            "manual",
            "datasheet",
            "technical",
            "documentation",
            "doc",
            "pdf",
            "download",
            "guide",
            "instruction",
            "support",
            "reference",
            "api",
            "whitepaper",
        ]
        for indicator in tech_indicators:
            if indicator in combined_text:
                score += 5

        # Official/authoritative sources (high priority)
        authority_indicators = [
            ".gov",
            ".edu",
            ".org",
            "official",
            "documentation",
            "developer",
            "docs",
            "support",
            "help",
        ]
        for indicator in authority_indicators:
            if indicator in url:
                score += 8

        # File type bonuses
        if any(ext in url for ext in [".pdf", ".doc", ".docx", ".xls", ".xlsx"]):
            score += 7

        # Search depth multipliers
        if search_depth == "extensive":
            # Be more inclusive for extensive searches
            score = int(score * 1.2)
        elif search_depth == "standard":
            # Standard scoring
            pass

        # Minimum threshold
        return score if score >= 5 else 0

    def _get_max_links_for_depth(self, search_depth: str) -> int:
        """Get maximum number of reference links based on search depth."""
        if search_depth == "basic":
            return 0  # No reference links for basic
        elif search_depth == "standard":
            return 5  # Moderate number of references
        elif search_depth == "extensive":
            return 15  # More comprehensive references
        else:
            return 5  # Default to standard
