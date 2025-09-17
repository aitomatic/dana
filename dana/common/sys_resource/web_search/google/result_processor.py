"""Search result processing, scoring, and filtering."""

import logging
from urllib.parse import urlparse

from .search_engine import GoogleResult
from .config import GoogleSearchConfig

logger = logging.getLogger(__name__)


class ResultProcessor:
    """Processes and scores Google search results for relevance."""

    def __init__(self, config: GoogleSearchConfig):
        """
        Initialize result processor.

        Args:
            config: Google search configuration
        """
        self.config = config

    def process_and_score_results(self, results: list[GoogleResult], query: str) -> list[GoogleResult]:
        """
        Process, score, and filter search results for relevance.

        Args:
            results: Raw Google search results
            query: Original search query for context

        Returns:
            Filtered and sorted list of GoogleResult objects
        """
        if not results:
            return []

        logger.info(f"🎯 Processing {len(results)} search results")

        # Score and filter results
        scored_results = []
        for result in results:
            # Skip results from unwanted domains
            if self._should_skip_url(result.url):
                logger.debug(f"⏭️ Skipping URL from filtered domain: {result.display_link}")
                continue

            # Calculate relevance score
            score = self._calculate_relevance_score(result, query)
            scored_results.append((result, score))

        # Sort by relevance score (highest first)
        scored_results.sort(key=lambda x: x[1], reverse=True)

        # Extract results and log scoring
        processed_results = [result for result, score in scored_results]

        if processed_results:
            logger.info(f"✅ Processed results - kept {len(processed_results)}/{len(results)} after filtering")
            for i, (result, score) in enumerate(scored_results[:3]):  # Log top 3
                logger.debug(f"  {i + 1}. {result.display_link} (score: {score})")
        else:
            logger.warning("⚠️ No results passed filtering criteria")

        return processed_results

    def _should_skip_url(self, url: str) -> bool:
        """
        Check if URL should be skipped based on domain filtering.

        Args:
            url: URL to check

        Returns:
            True if URL should be skipped
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Check against skip domains
            for skip_domain in self.config.skip_domains:
                if skip_domain.lower() in domain:
                    return True

            return False

        except Exception:
            # If URL parsing fails, don't skip (better to include than exclude)
            return False

    def _calculate_relevance_score(self, result: GoogleResult, query: str) -> int:
        """
        Calculate relevance score for a search result.

        Args:
            result: Google search result
            query: Original search query

        Returns:
            Relevance score (higher is better)
        """
        score = 0
        url_lower = result.url.lower()
        title_lower = result.title.lower()
        snippet_lower = result.snippet.lower()
        display_link_lower = result.display_link.lower()

        # High-priority content types and file formats
        if self._is_technical_document(url_lower):
            score += 5
            logger.debug(f"  +5 technical document: {result.display_link}")

        # Technical documentation indicators
        tech_keywords = [
            "datasheet",
            "manual",
            "specification",
            "spec",
            "techsheet",
            "documentation",
        ]
        if any(keyword in url_lower or keyword in title_lower for keyword in tech_keywords):
            score += 5
            logger.debug(f"  +5 technical keywords: {result.display_link}")

        # Manufacturer and distributor domains
        if self._is_distributor_site(display_link_lower):
            score += 5
            logger.debug(f"  +5 distributor site: {result.display_link}")
        elif self._is_manufacturer_site(display_link_lower):
            score += 5
            logger.debug(f"  +5 manufacturer site: {result.display_link}")

        # Technical content in URLs and paths
        tech_url_keywords = [
            "support",
            "docs",
            "technical",
            "documentation",
            "resources",
            "products",
        ]
        if any(keyword in url_lower for keyword in tech_url_keywords):
            score += 2
            logger.debug(f"  +2 technical URL path: {result.display_link}")

        # Product information indicators
        product_keywords = [
            "specifications",
            "features",
            "technical data",
            "product details",
            "overview",
        ]
        if any(keyword in title_lower or keyword in snippet_lower for keyword in product_keywords):
            score += 2
            logger.debug(f"  +2 product information: {result.display_link}")

        # Specific product search terms in content
        if self._contains_query_terms(result, query):
            score += 1
            logger.debug(f"  +1 query terms match: {result.display_link}")

        # Bonus for structured data indicators
        structured_indicators = ["table", "database", "catalog", "directory"]
        if any(indicator in title_lower or indicator in snippet_lower for indicator in structured_indicators):
            score += 1
            logger.debug(f"  +1 structured data: {result.display_link}")

        return score

    def _is_technical_document(self, url: str) -> bool:
        """Check if URL points to a technical document."""
        doc_extensions = [".pdf", ".doc", ".docx", ".xls", ".xlsx"]
        return any(ext in url for ext in doc_extensions)

    def _is_distributor_site(self, domain: str) -> bool:
        """Check if domain is a known electronics distributor."""
        distributors = [
            "digikey",
            "mouser",
            "newark",
            "arrow",
            "avnet",
            "farnell",
            "element14",
            "rs-online",
            "allied",
            "digi-key",
            "future",
            "ttilectronics",
            "onlinecomponents",
            "findchips",
        ]
        return any(distributor in domain for distributor in distributors)

    def _is_manufacturer_site(self, domain: str) -> bool:
        """Check if domain appears to be a manufacturer website."""
        # Common manufacturer domain patterns
        manufacturer_indicators = [
            # Major semiconductor companies
            "ti.com",
            "intel.com",
            "amd.com",
            "nvidia.com",
            "qualcomm.com",
            "analog.com",
            "maxim",
            "linear.com",
            "cypress.com",
            "microsemi.com",
            "microchip.com",
            "freescale.com",
            "nxp.com",
            "st.com",
            "infineon.com",
            "renesas.com",
            "rohm.com",
            "toshiba.com",
            "fujitsu.com",
            # Other electronics manufacturers
            "samsung.com",
            "lg.com",
            "sony.com",
            "panasonic.com",
            "philips.com",
            "bosch.com",
            "siemens.com",
            "schneider",
            "abb.com",
            "rockwell",
        ]
        return any(mfg in domain for mfg in manufacturer_indicators)

    def _contains_query_terms(self, result: GoogleResult, query: str) -> bool:
        """Check if result contains important terms from the query."""
        # Extract meaningful terms from query (skip common words)
        query_lower = query.lower()
        skip_words = {"the", "and", "or", "in", "on", "at", "to", "for", "of", "with", "by"}

        # Simple term extraction (can be enhanced with NLP)
        query_terms = [
            term.strip('",()[]') for term in query_lower.split() if len(term.strip('",()[]')) > 2 and term.lower() not in skip_words
        ]

        if not query_terms:
            return False

        # Check if significant terms appear in title or snippet
        content = f"{result.title} {result.snippet}".lower()
        matches = sum(1 for term in query_terms if term in content)

        # Return True if at least 30% of terms match
        return matches >= len(query_terms) * 0.3

    def limit_results(self, results: list[GoogleResult], max_results: int = None) -> list[GoogleResult]:
        """
        Limit results to maximum number.

        Args:
            results: Processed search results
            max_results: Maximum number of results (defaults to config.max_results)

        Returns:
            Limited list of results
        """
        if max_results is None:
            max_results = self.config.max_results

        if len(results) <= max_results:
            return results

        limited_results = results[:max_results]
        logger.info(f"📏 Limited results from {len(results)} to {max_results}")

        return limited_results
