"""
ExtractComponents - Parsing and extracting structured content.

Provides reusable extraction operations that can be composed into workflows.
"""

import logging

from adana.common.observable import observable
from adana.common.protocols import DictParams
from adana.common.protocols.war import tool_use
from adana.core.resource.base_resource import BaseResource
from adana.lib.agents.web_research.workflows.resources.components import _content_extractor


logger = logging.getLogger(__name__)


class ExtractResource(BaseResource):
    """Reusable extraction operations for workflow composition."""

    def __init__(self, **kwargs):
        """
        Initialize extract components.
        """
        super().__init__(**kwargs)
        self.content_extractor = _content_extractor

    def extract_main_content(self, html: str, base_url: str | None = None) -> DictParams:
        """
        Extract main article/content from HTML.

        Args:
            html: Raw HTML content
            base_url: Base URL for resolving relative links

        Returns:
            Extracted content with title, text, markdown, metadata
        """
        return self.content_extractor.extract_main_content(html, base_url)

    @tool_use
    def extract_metadata(self, html: str) -> DictParams:
        """
        Extract metadata from HTML (meta tags, Open Graph, etc.).

        Args:
            html: Raw HTML content

        Returns:
            Metadata including title, description, author, dates
        """
        return self.content_extractor.extract_metadata(html)

    def extract_tables(self, html: str) -> DictParams:
        """
        Extract all tables from HTML as structured data.

        Args:
            html: Raw HTML content

        Returns:
            Tables with headers, rows, captions
        """
        return self.content_extractor.extract_tables(html)

    def extract_links(self, html: str, base_url: str, filter_external: bool = False) -> DictParams:
        """
        Extract all links from HTML.

        Args:
            html: Raw HTML content
            base_url: Base URL for resolving relative links
            filter_external: If True, only return internal links

        Returns:
            Links with text, URLs, internal/external classification
        """
        return self.content_extractor.extract_links(html, base_url, filter_external)

    @tool_use
    def extract_code_blocks(self, html: str) -> DictParams:
        """
        Extract code blocks from HTML (pre, code tags).

        Args:
            html: Raw HTML content

        Returns:
            {
                "success": bool,
                "code_blocks": [
                    {
                        "language": str | None,
                        "code": str,
                        "index": int
                    }
                ],
                "total_blocks": int
            }
        """
        from bs4 import BeautifulSoup

        try:
            soup = BeautifulSoup(html, "lxml")
            code_blocks = []

            # Find code blocks (pre > code or standalone pre)
            for i, pre in enumerate(soup.find_all("pre")):
                code_tag = pre.find("code")

                if code_tag:
                    # Try to determine language from class
                    classes = code_tag.get("class")
                    language = None
                    if classes and isinstance(classes, list):
                        for cls in classes:
                            if cls.startswith("language-"):
                                language = cls.replace("language-", "")
                                break
                            elif cls.startswith("lang-"):
                                language = cls.replace("lang-", "")
                            break

                    code_text = code_tag.get_text()
                else:
                    # Standalone pre tag
                    code_text = pre.get_text()
                    language = None

                code_blocks.append({"language": language, "code": code_text, "index": i})

            return {"success": True, "code_blocks": code_blocks, "total_blocks": len(code_blocks), "error": None}

        except Exception as e:
            return {"success": False, "error": f"Code block extraction failed: {str(e)}"}

    @tool_use
    def extract_from_multiple(self, fetch_results: list[DictParams], base_urls: list[str] | None = None) -> list[DictParams]:
        """
        Extract content from multiple fetch results.

        Args:
            fetch_results: List of fetch results (from FetchComponents)
            base_urls: Optional list of base URLs (one per fetch result)

        Returns:
            List of extraction results
        """
        if base_urls is None:
            base_urls = [None] * len(fetch_results)  # type: ignore

        extraction_results = []

        for i, fetch_result in enumerate(fetch_results):
            if not fetch_result.get("success"):
                extraction_results.append(
                    {"success": False, "error": "Fetch failed, cannot extract", "original_error": fetch_result.get("error")}
                )
                continue

            html = fetch_result.get("content", "")
            base_url = base_urls[i] or fetch_result.get("url")  # type: ignore

            extraction = self.content_extractor.extract_main_content(html, base_url)

            # Add URL information to the extraction result
            if extraction.get("success"):
                extraction["url"] = fetch_result.get("url", base_url)  # Final URL after redirects
                extraction["status_code"] = fetch_result.get("status_code")
                extraction["fetch_time_ms"] = fetch_result.get("fetch_time_ms")

            extraction_results.append(extraction)

        return extraction_results

    @tool_use
    def extract_structured_data(self, html: str, base_url: str) -> DictParams:
        """
        Extract all structured data from HTML (tables, lists, metadata).

        Args:
            html: Raw HTML content
            base_url: Base URL for context

        Returns:
            {
                "success": bool,
                "metadata": dict,
                "tables": list,
                "lists": list,
                "code_blocks": list,
                "total_structured_elements": int
            }
        """
        from bs4 import BeautifulSoup

        try:
            # Extract metadata
            metadata_result = self.content_extractor.extract_metadata(html)
            metadata = metadata_result if metadata_result.get("success") else {}

            # Extract tables
            tables_result = self.content_extractor.extract_tables(html)
            tables = tables_result.get("tables", []) if tables_result.get("success") else []

            # Extract lists
            soup = BeautifulSoup(html, "lxml")
            lists = []

            for i, ul in enumerate(soup.find_all(["ul", "ol"])):
                list_items = [li.get_text(strip=True) for li in ul.find_all("li", recursive=False)]
                lists.append(
                    {
                        "type": ul.name,  # 'ul' or 'ol'
                        "items": list_items,
                        "index": i,
                    }
                )

            # Extract code blocks
            code_result = self.extract_code_blocks(html)
            code_blocks = code_result.get("code_blocks", []) if code_result.get("success") else []

            total_elements = len(tables) + len(lists) + len(code_blocks)

            return {
                "success": True,
                "metadata": metadata,
                "tables": tables,
                "lists": lists,
                "code_blocks": code_blocks,
                "total_structured_elements": total_elements,
                "error": None,
            }

        except Exception as e:
            return {"success": False, "error": f"Structured data extraction failed: {str(e)}"}

    @tool_use
    def extract_with_quality_check(self, html: str, base_url: str, purpose: str) -> DictParams:
        """
        Extract content and assess quality for purpose.

        Args:
            html: Raw HTML content
            base_url: Source URL
            purpose: What the content will be used for

        Returns:
            {
                "content": dict,  # Extracted content
                "quality": dict,  # Quality assessment
                "sufficient": bool  # Whether content is sufficient
            }
        """
        # Extract content
        content = self.content_extractor.extract_main_content(html, base_url)

        if not content.get("success"):
            return {"content": content, "quality": None, "sufficient": False, "error": "Content extraction failed"}

        # Assess quality
        quality = self.content_extractor.assess_content_quality(html, base_url, purpose)

        return {"content": content, "quality": quality, "sufficient": quality.get("is_sufficient", False), "error": None}

    @tool_use
    def extract_navigation_links(self, html: str, base_url: str, link_patterns: list[str] | None = None) -> DictParams:
        """
        Extract navigation links for multi-page workflows.

        Args:
            html: Raw HTML content
            base_url: Base URL for resolving relative links
            link_patterns: Patterns to match (e.g., ["next", "page", ">>"])

        Returns:
            {
                "success": bool,
                "navigation_links": list[dict],  # Links matching patterns
                "next_page": str | None,  # Most likely next page URL
                "total_navigation_links": int
            }
        """
        if link_patterns is None:
            link_patterns = ["next", "page", ">>", "→", "continue", "more", "view all", "show more", "load more", "pagination"]

        # Extract all links
        links_result = self.content_extractor.extract_links(html, base_url)

        if not links_result.get("success"):
            return {"success": False, "error": "Link extraction failed"}

        # Filter for navigation links
        navigation_links = []
        for link in links_result.get("links", []):
            link_text = link.get("text", "").lower()
            link_url = link.get("url", "")

            # Check if link matches navigation patterns
            if any(pattern.lower() in link_text or pattern.lower() in link_url for pattern in link_patterns):
                navigation_links.append(link)

        # Try to identify most likely next page
        next_page = None
        for link in navigation_links:
            text = link.get("text", "").lower()
            if "next" in text or ">>" in text or "→" in text:
                next_page = link.get("url")
                break

        return {
            "success": True,
            "navigation_links": navigation_links,
            "next_page": next_page,
            "total_navigation_links": len(navigation_links),
            "error": None,
        }

    def _has_structured_content(self, html: str) -> bool:
        """Quick check if page has structured content (tables, lists) without LLM calls."""
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html, "html.parser")
            return bool(soup.find_all(["table", "ul", "ol", "dl"]))
        except Exception:
            return False

    @tool_use
    @observable
    def navigate_and_extract_structured(
        self,
        start_url: str | None = None,
        query: str | None = None,
        max_pages: int = 10,
        extract_tables: bool = True,
        extract_lists: bool = True,
        rate_limit_sec: float = 1.0,
    ) -> DictParams:
        """
        Navigate multiple pages and extract structured data in one operation.

        This method handles large intermediate data (raw HTML) and pagination internally
        without exposing it to the caller. Only returns aggregated tables, lists, and statistics.

        Args:
            start_url: Starting URL (if known)
            query: Search query (used if no start_url provided)
            max_pages: Maximum pages to navigate
            extract_tables: Whether to extract tables
            extract_lists: Whether to extract lists
            rate_limit_sec: Rate limit between page fetches

        Returns:
            Dictionary with:
            - success: Whether operation succeeded
            - pages_processed: Number of pages processed
            - tables: List of all tables found (with source_url, page_number)
            - lists: List of all lists found (with source_url, page_number)
            - total_data_points: Total rows + list items
            - statistics: Detailed statistics
            - sources: List of page URLs processed
            - error: Error message if failed
        """
        import time

        # Import here to avoid circular dependency
        from adana.lib.agents.web_research.workflows.resources.fetch import FetchResource
        from adana.lib.agents.web_research.workflows.resources.search import SearchResource

        logger.info("Starting navigate_and_extract_structured")

        # Initialize variables for fallback strategy
        ranked_results = []

        # Step 1: Get starting URL (either from param or search with intelligent ranking)
        if not start_url:
            if not query:
                return {"success": False, "error": "Either start_url or query parameter is required"}

            logger.debug(f"Searching for: {query}")
            searcher = SearchResource()
            search_result = searcher.search_web(query, max_results=5)

            if not search_result.get("success") or not search_result.get("results"):
                return {"success": False, "error": "Search failed or no results found"}

            # Use intelligent ranking instead of arbitrary first result
            from adana.lib.agents.web_research.workflows.resources.components.web_fetcher import WebFetcher

            web_fetcher = WebFetcher()

            ranking_result = web_fetcher.rank_search_results(query=query, results=search_result["results"], criteria="relevance")

            if ranking_result.get("success"):
                ranked_results = ranking_result["ranked_results"]
                start_url = ranked_results[0]["url"]
                score = ranked_results[0].get("score", "N/A")
                logger.info(f"Using top-ranked result: {start_url} (score: {score})")
            else:
                # Fallback to first result if ranking fails
                start_url = search_result["results"][0]["url"]
                ranked_results = []
                logger.warning("Ranking failed, using first result")

        # Step 2: Navigate pages and extract data with fallback strategy
        fetcher = FetchResource()
        all_tables = []
        all_lists = []
        pages_processed = []
        current_url = start_url

        # Fallback strategy: track failed URLs and try alternatives
        failed_urls = set()
        max_attempts = min(3, len(ranked_results)) if ranked_results else 1

        for page_num in range(max_pages):
            logger.debug(f"Processing page {page_num + 1}/{max_pages}: {current_url}")

            # Check for duplicate URLs
            if current_url in pages_processed:
                logger.warning(f"URL {current_url} already processed, skipping")
                break

            # Fetch page
            fetch_result = fetcher.fetch_url(current_url or "")

            if not fetch_result.get("success"):
                error_msg = fetch_result.get("error", "Unknown error")
                logger.warning(f"Failed to fetch page {page_num + 1}: {error_msg}")

                # Check if it's a 403/429 error - stop immediately
                if "403" in error_msg or "429" in error_msg or "forbidden" in error_msg.lower():
                    logger.error("Server blocking requests (403/429), stopping extraction")
                    break

                # Try fallback URL if available (only for network/timeout errors)
                if ranked_results and len(failed_urls) < max_attempts - 1:
                    failed_urls.add(current_url)
                    for ranked_result in ranked_results:
                        alt_url = ranked_result["url"]
                        if alt_url not in failed_urls:
                            current_url = alt_url
                            logger.info(f"Trying alternative URL: {alt_url}")
                            continue  # Restart loop with new URL
                    else:
                        logger.error("All alternative URLs failed")
                        break
                else:
                    break

            html = fetch_result.get("content", "")
            pages_processed.append(current_url)

            # Quick pre-check for structured content (no LLM cost)
            if not self._has_structured_content(html):
                logger.warning(f"Page {current_url} has no structured content, skipping")
                continue

            # LLM-based content quality assessment
            content_assessment = self.content_extractor.assess_content_quality(
                html=html, url=current_url or "", purpose="structured data extraction"
            )

            if not content_assessment.get("is_sufficient", False):
                quality_score = content_assessment.get("quality_score", 0)
                logger.warning(f"Page {current_url} has low content quality (score: {quality_score:.2f}), skipping")
                continue

            # Extract structured data
            logger.debug("Extracting structured data from page...")
            structured_result = self.extract_structured_data(html, current_url or "")

            if structured_result.get("success"):
                # Collect tables
                page_tables = []
                if extract_tables:
                    page_tables = structured_result.get("tables", [])
                    for table in page_tables:
                        table["source_url"] = current_url
                        table["page_number"] = page_num + 1
                    all_tables.extend(page_tables)

                # Collect lists
                page_lists = []
                if extract_lists:
                    page_lists = structured_result.get("lists", [])
                    for lst in page_lists:
                        lst["source_url"] = current_url
                        lst["page_number"] = page_num + 1
                    all_lists.extend(page_lists)

                logger.info(
                    f"Page {page_num + 1}: Found {len(page_tables) if extract_tables else 0} tables, {len(page_lists) if extract_lists else 0} lists"
                )

            # Check if we've collected enough data
            total_elements = len(all_tables) + len(all_lists)
            if total_elements >= 50:  # Arbitrary threshold
                logger.info(f"Collected {total_elements} elements, stopping navigation")
                break

            # Find next page
            logger.debug("Looking for next page link...")
            nav_result = self.extract_navigation_links(html, current_url or "")

            next_page = nav_result.get("next_page")

            if not next_page:
                logger.info("No next page found, stopping navigation")
                break

            if next_page in pages_processed:
                logger.warning("Next page is duplicate, stopping navigation")
                break

            current_url = next_page

            # Rate limiting
            if page_num < max_pages - 1:  # Don't wait after last page
                time.sleep(rate_limit_sec)

        # Step 3: Calculate statistics
        total_rows = sum(len(t.get("rows", [])) for t in all_tables)
        total_list_items = sum(len(lst.get("items", [])) for lst in all_lists)
        total_data_points = total_rows + total_list_items

        logger.info(
            f"Collected: {len(all_tables)} tables ({total_rows} rows), {len(all_lists)} lists ({total_list_items} items) from {len(pages_processed)} pages"
        )

        return {
            "success": True,
            "pages_processed": len(pages_processed),
            "tables": all_tables,
            "lists": all_lists,
            "total_data_points": total_data_points,
            "statistics": {
                "total_tables": len(all_tables),
                "total_rows": total_rows,
                "total_lists": len(all_lists),
                "total_list_items": total_list_items,
            },
            "sources": pages_processed,
            "error": None,
        }
