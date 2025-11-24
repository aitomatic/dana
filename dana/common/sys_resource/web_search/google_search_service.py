"""Google Custom Search + Web Scraping Service implementation."""

import asyncio
import json

from .core.interfaces import SearchService
from .core.models import SearchRequest, SearchResults, SearchSource
from .google import (
    GoogleSearchConfig,
    GoogleSearchEngine,
    WebContentExtractor,
    ResultProcessor,
    load_google_config,
    GoogleSearchError,
)
from .google.content_extractor import ContentResult
from .google.reference_extractor import ReferenceExtractor

from loguru import logger

# Minimum content length threshold for quality results
MIN_CONTENT_LENGTH = 100  # chars


class GoogleSearchService(SearchService):
    """
    Google Custom Search + Web Scraping implementation.

    Combines Google Custom Search API with BeautifulSoup-based content extraction
    to provide comprehensive search results with actual page content.
    """

    def __init__(self, config: GoogleSearchConfig | None = None, enable_summarization: bool = True):
        """
        Initialize Google search service.

        Args:
            config: Google search configuration (loads from environment if None)
            enable_summarization: Whether to enable content summarization
        """
        self.config = config or load_google_config()

        # Initialize components
        self.search_engine = GoogleSearchEngine(self.config)
        self.result_processor = ResultProcessor(self.config)
        self.reference_extractor = ReferenceExtractor(self.config)

        # Initialize content processor if enabled
        self.content_processor = None
        if enable_summarization:
            try:
                import os
                from .utils.content_processor import ContentProcessor

                if os.getenv("OPENAI_API_KEY"):
                    self.content_processor = ContentProcessor()
                    logger.info("✅ Content processing enabled")
                else:
                    logger.warning("OPENAI_API_KEY not found, content processing disabled")
            except Exception as e:
                logger.warning(f"Failed to initialize content processor: {e}")

        # Validate configuration
        if not self.search_engine.is_available():
            raise GoogleSearchError("Google Search service not available - check API key and CSE ID configuration")

        logger.info("✅ GoogleSearchService initialized successfully")

    async def _optimize_query(self, request: SearchRequest) -> str:
        """
        Optimize query based on search depth.

        Args:
            request: SearchRequest with query and search depth

        Returns:
            Optimized query string
        """
        optimized_query = self.search_engine.optimize_query(request.query, request.search_depth)

        if request.domain:
            optimized_query = f"{optimized_query} \nFocus on Domain (but not limited to): {request.domain}"
        if request.target_sites:
            sites_str = "\n".join([f"- {site}" for site in request.target_sites])
            optimized_query = f"{optimized_query} \nFocus on Sites (but not limited to): {sites_str}"

        if optimized_query != request.query:
            logger.info(f"🔧 Query optimized for {request.search_depth} search")
            logger.info(f"🔧 Optimized query: {optimized_query}")

        return optimized_query

    async def _execute_google_search(self, optimized_query: str) -> tuple[list, list]:
        """
        Execute Google Custom Search and process results.

        Args:
            optimized_query: The optimized search query

        Returns:
            List of processed and scored results

        Raises:
            GoogleSearchError: If search fails or returns no results
        """
        logger.info(f"🔍 Executing Google Custom Search: {optimized_query}")
        google_results = await self.search_engine.search(optimized_query, max_results=self.config.max_results)
        # logger.info(f"🔍 Google Search Results: {google_results}")

        if not google_results:
            raise GoogleSearchError("No results from Google Custom Search")

        # Process and score results
        processed_results = self.result_processor.process_and_score_results(google_results, optimized_query)

        if not processed_results:
            raise GoogleSearchError("No results passed filtering criteria")

        # Log the found links
        logger.info(f"📋 Found {len(processed_results)} links after filtering:")
        for i, result in enumerate(processed_results, 1):
            logger.info(f"  {i}. {result.url} - {result.title[:60]}...")

        return processed_results, google_results

    async def _extract_content_from_urls(self, processed_results: list, request: SearchRequest) -> tuple:
        """
        Extract content from URLs and collect reference links.

        Args:
            processed_results: List of processed Google search results
            request: SearchRequest with query and options

        Returns:
            Tuple of (search_sources, reference_links, urls_attempted, extraction_success)
        """
        search_sources = []
        reference_links = []
        urls_attempted = 0
        extraction_success = 0

        if not self.config.enable_content_extraction:
            # Content extraction disabled - use Google snippets
            logger.info("📝 Content extraction disabled, using Google snippets")
            for result in processed_results:
                search_source = SearchSource(url=result.url, content=result.snippet, full_content="")
                search_sources.append(search_source)
            return search_sources, reference_links, 0, 0

        # Extract URLs for content extraction
        urls = [result.url for result in processed_results]

        # Extract content concurrently with processing
        async with WebContentExtractor(self.config, self.content_processor) as extractor:
            if self.content_processor:
                # Use query-focused extraction when content processor is available
                # Use semaphore to limit concurrency
                semaphore = asyncio.Semaphore(self.config.max_concurrent_extractions)

                async def extract_with_semaphore(url):
                    async with semaphore:
                        return await extractor.extract_content_with_query_focus(url, request.query)

                logger.debug(
                    f"Processing {len(urls)} URLs concurrently with query focus (max {self.config.max_concurrent_extractions} at a time)"
                )
                tasks = [extract_with_semaphore(url) for url in urls]
                content_results_raw = await asyncio.gather(*tasks, return_exceptions=True)

                # Handle exceptions from gather
                content_results = []
                for i, result in enumerate(content_results_raw):
                    if isinstance(result, Exception):
                        logger.error(f"❌ Content extraction failed for {urls[i]}: {result}")
                        content_results.append(
                            ContentResult(url=urls[i], content="", full_content="", success=False, error_message=str(result))
                        )
                    else:
                        content_results.append(result)
            else:
                content_results = await extractor.extract_multiple_urls(urls)

            # For standard/extensive searches, also extract reference links
            if request.search_depth in ["standard", "extensive"]:
                logger.info(f"🔗 Extracting reference links for {request.search_depth} search")

                for _, content_result in enumerate(content_results):
                    if content_result.success and content_result.content:
                        # Get HTML+text for reference extraction
                        html_result = await extractor.extract_content_with_html(content_result.url)
                        if html_result.success and html_result.html:
                            ref_result = self.reference_extractor.extract_reference_links(
                                html_result.html,
                                content_result.url,
                                request.query,
                                request.search_depth,
                            )
                            if ref_result.success and ref_result.reference_links:
                                reference_links.extend([ref_link.url for ref_link in ref_result.reference_links])
                                logger.info(f"🔗 Found {len(ref_result.reference_links)} reference links from {content_result.url}")

            # Convert to SearchSource objects - only keep quality results
            urls_attempted = len(content_results)
            quality_results = 0

            for i, content_result in enumerate(content_results):
                google_result = processed_results[i] if i < len(processed_results) else None

                # Log content parsing result for each URL
                status = "✅ SUCCESS" if content_result.success and content_result.content.strip() else "❌ FAILED"
                content_length = len(content_result.content) if content_result.content else 0
                logger.info(f"📄 Content parsing {i + 1}. {content_result.url} - {status} ({content_length} chars)")

                # Determine content to use (extracted content or Google snippet fallback)
                if content_result.success and content_result.content.strip():
                    content = content_result.content
                    extraction_success += 1
                elif google_result and google_result.snippet.strip():
                    content = google_result.snippet
                    logger.debug(f"Using Google snippet fallback for {content_result.url}")
                else:
                    # No usable content - skip this result entirely
                    logger.warning(f"⏭️  Skipping {content_result.url} - no usable content")
                    continue

                # Quality check: skip if content is too short
                if len(content.strip()) < MIN_CONTENT_LENGTH:
                    logger.warning(f"⏭️  Skipping {content_result.url} - content too short ({len(content)} chars, min {MIN_CONTENT_LENGTH})")
                    continue

                # This is a quality result - add it
                full_content = content_result.full_content if request.with_full_content else ""
                search_source = SearchSource(url=content_result.url, content=content, full_content=full_content)
                search_sources.append(search_source)
                quality_results += 1

            # Log extraction statistics
            logger.info(
                f"📊 Content extraction stats: {quality_results} quality results from {urls_attempted} URLs attempted ({extraction_success} successful extractions)"
            )

        return search_sources, reference_links, urls_attempted, extraction_success

    async def _process_reference_links(self, reference_links: list, request: SearchRequest) -> list:
        """
        Process reference links for standard/extensive searches.

        Args:
            reference_links: List of reference link URLs
            request: SearchRequest with query and options

        Returns:
            List of SearchSource objects from reference links
        """
        ref_sources = []

        if not reference_links or request.search_depth not in ["standard", "extensive"]:
            return ref_sources

        logger.info(f"📚 Processing {len(reference_links)} reference links")

        # Remove duplicates and limit based on search depth
        unique_ref_links = list(dict.fromkeys(reference_links))  # Preserve order
        max_refs = 3 if request.search_depth == "standard" else 7
        limited_ref_links = unique_ref_links[:max_refs]

        if not limited_ref_links:
            return ref_sources

        # Extract content from reference links with query focus (concurrent processing)
        async with WebContentExtractor(self.config, self.content_processor) as ref_extractor:
            if self.content_processor:
                # Process all reference links concurrently with query focus
                logger.debug(f"Processing {len(limited_ref_links)} reference links concurrently with query focus")
                ref_tasks = [ref_extractor.extract_content_with_query_focus(ref_url, request.query) for ref_url in limited_ref_links]
                ref_content_results_raw = await asyncio.gather(*ref_tasks, return_exceptions=True)

                # Handle exceptions from gather
                ref_content_results = []
                for i, result in enumerate(ref_content_results_raw):
                    if isinstance(result, Exception):
                        logger.error(f"❌ Reference link extraction failed for {limited_ref_links[i]}: {result}")
                        ref_content_results.append(
                            ContentResult(url=limited_ref_links[i], content="", full_content="", success=False, error_message=str(result))
                        )
                    else:
                        ref_content_results.append(result)
            else:
                # Without content processor, use the standard concurrent extraction
                ref_content_results = await ref_extractor.extract_multiple_urls(limited_ref_links)

            # Add successful reference extractions to results (with quality check)
            for ref_result in ref_content_results:
                if ref_result.success and ref_result.content.strip():
                    # Quality check for reference content too
                    if len(ref_result.content.strip()) >= MIN_CONTENT_LENGTH:
                        ref_source = SearchSource(
                            url=ref_result.url,
                            content=ref_result.content,
                            full_content=ref_result.full_content if request.with_full_content else "",
                        )
                        ref_sources.append(ref_source)
                        logger.info(f"📚 Added reference content from: {ref_result.url} ({len(ref_result.content)} chars)")
                    else:
                        logger.warning(f"⏭️  Skipping reference link {ref_result.url} - content too short ({len(ref_result.content)} chars)")

        return ref_sources

    def _build_search_results(
        self,
        request: SearchRequest,
        optimized_query: str,
        google_results: list,
        processed_results: list,
        search_sources: list,
        reference_links: list,
        urls_attempted: int,
        extraction_success: int,
    ) -> SearchResults:
        """
        Build final SearchResults object with metadata.

        Args:
            request: Original SearchRequest
            optimized_query: The optimized query used
            google_results: Raw Google search results
            processed_results: Filtered and processed results
            search_sources: Final list of SearchSource objects
            reference_links: List of reference links found
            urls_attempted: Number of URLs attempted for extraction
            extraction_success: Number of successful extractions

        Returns:
            SearchResults object
        """
        # Create response with metadata
        raw_data = json.dumps(
            {
                "query": request.query,
                "optimized_query": optimized_query,
                "total_google_results": len(google_results),
                "filtered_results": len(processed_results),
                "quality_results": len(search_sources),
                "urls_attempted": len(processed_results) if self.config.enable_content_extraction else 0,
                "extraction_success_rate": f"{extraction_success}/{urls_attempted}" if self.config.enable_content_extraction else "N/A",
                "quality_pass_rate": f"{len(search_sources)}/{urls_attempted}" if self.config.enable_content_extraction else "N/A",
                "min_content_length": MIN_CONTENT_LENGTH,
                "content_extraction_enabled": self.config.enable_content_extraction,
                "search_depth": request.search_depth,
                "reference_links_found": len(reference_links) if reference_links else 0,
                "reference_links_processed": len([s for s in search_sources if s.url in reference_links]) if reference_links else 0,
            },
            indent=2,
        )

        # Check if we have any quality results after filtering
        if not search_sources:
            logger.warning("⚠️  No quality results found after filtering (all results failed quality check)")
            return SearchResults(
                success=False,
                sources=[],
                error_message="No quality results found - all results were too short or extraction failed",
                raw_data=raw_data,
            )

        logger.info(f"✅ Search completed - {len(search_sources)} quality results (from {len(google_results)} API results)")
        return SearchResults(success=True, sources=search_sources, raw_data=raw_data)

    async def search(self, request: SearchRequest) -> SearchResults:
        """
        Execute search using Google Custom Search + content extraction.

        Args:
            request: SearchRequest with query, depth, and options

        Returns:
            SearchResults with URLs and extracted content
        """
        logger.info(f"🚀 Starting Google search: {request.query[:100]}{'...' if len(request.query) > 100 else ''}")

        try:
            # Step 1: Optimize query based on search depth
            optimized_query = await self._optimize_query(request)

            # Step 2: Execute Google Custom Search and process results
            processed_results, google_results = await self._execute_google_search(optimized_query)

            # Step 3: Extract content from URLs (if enabled)
            search_sources, reference_links, urls_attempted, extraction_success = await self._extract_content_from_urls(
                processed_results, request
            )

            # Step 4: Process reference links for standard/extensive searches
            ref_sources = await self._process_reference_links(reference_links, request)
            search_sources.extend(ref_sources)

            # Step 5: Build and return final results
            return self._build_search_results(
                request,
                optimized_query,
                google_results,
                processed_results,
                search_sources,
                reference_links,
                urls_attempted,
                extraction_success,
            )

        except GoogleSearchError as e:
            logger.error(f"❌ Google search service error: {e}")
            return SearchResults(success=False, sources=[], error_message=f"Google search failed: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Unexpected error in Google search: {e}")
            return SearchResults(success=False, sources=[], error_message=f"Unexpected error: {str(e)}")

    def is_available(self) -> bool:
        """
        Check if Google search service is available.

        Returns:
            True if service is properly configured and available
        """
        return self.search_engine.is_available()

    def get_config(self) -> GoogleSearchConfig:
        """
        Get current configuration.

        Returns:
            Current GoogleSearchConfig
        """
        return self.config

    def __str__(self) -> str:
        """String representation of the service."""
        return f"GoogleSearchService(max_results={self.config.max_results}, content_extraction={self.config.enable_content_extraction})"


# Factory function for easy instantiation
def create_google_search_service(api_key: str | None = None, cse_id: str | None = None, **kwargs) -> GoogleSearchService:
    """
    Create GoogleSearchService with optional configuration override.

    Args:
        api_key: Google Custom Search API key (overrides environment)
        cse_id: Custom Search Engine ID (overrides environment)
        **kwargs: Additional configuration parameters

    Returns:
        Configured GoogleSearchService instance
    """
    if api_key or cse_id:
        # Create config with override values
        base_config = load_google_config()
        config = GoogleSearchConfig(
            api_key=api_key or base_config.api_key,
            cse_id=cse_id or base_config.cse_id,
            base_url=kwargs.get("base_url", base_config.base_url),
            **{k: v for k, v in kwargs.items() if k != "base_url" and hasattr(GoogleSearchConfig, k)},
        )
        return GoogleSearchService(config)
    else:
        # Use environment configuration
        return GoogleSearchService()


# Mock service for testing
class MockGoogleSearchService(SearchService):
    """Mock implementation for testing and development."""

    def __init__(self):
        """Initialize mock service."""
        logger.info("✅ MockGoogleSearchService initialized")

    async def search(self, request: SearchRequest) -> SearchResults:
        """Return mock search results."""
        logger.info(f"🔍 Mock Google search: {request.query}")

        # Create mock results based on query
        mock_sources = [
            SearchSource(
                url="https://example.com/product1",
                content=f"Mock content for query: {request.query}. This is simulated search result content with product specifications and technical details.",
                full_content="<html><body>Mock HTML content</body></html>" if request.with_full_content else "",
            ),
            SearchSource(
                url="https://manufacturer.com/datasheet",
                content="Technical datasheet with detailed specifications, dimensions, and performance characteristics.",
                full_content="",
            ),
            SearchSource(
                url="https://distributor.com/product-page",
                content="Product availability, pricing, and ordering information from authorized distributor.",
                full_content="",
            ),
        ]

        raw_data = json.dumps(
            {
                "query": request.query,
                "mock_service": True,
                "search_depth": request.search_depth,
                "mock_results_count": len(mock_sources),
            },
            indent=2,
        )

        return SearchResults(success=True, sources=mock_sources, raw_data=raw_data)
