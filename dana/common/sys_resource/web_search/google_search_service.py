"""Google Custom Search + Web Scraping Service implementation."""

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
from .google.reference_extractor import ReferenceExtractor

from loguru import logger


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
            optimized_query = self.search_engine.optimize_query(request.query, request.search_depth)

            if optimized_query != request.query:
                logger.info(f"🔧 Query optimized for {request.search_depth} search")

            # Step 2: Execute Google Custom Search
            logger.info(f"🔍 Executing Google Custom Search: {optimized_query}")
            google_results = await self.search_engine.search(optimized_query, max_results=self.config.max_results)
            logger.info(f"🔍 Google Search Results: {google_results}")

            if not google_results:
                logger.warning("❌ No results from Google Custom Search")
                return SearchResults(success=False, sources=[], error_message="No search results found")

            # Step 3: Process and score results
            processed_results = self.result_processor.process_and_score_results(google_results, request.query)

            if not processed_results:
                logger.warning("❌ No results passed filtering criteria")
                return SearchResults(
                    success=False,
                    sources=[],
                    error_message="No relevant results found after filtering",
                )

            # Log the 8 found links
            logger.info(f"📋 Found {len(processed_results)} links after filtering:")
            for i, result in enumerate(processed_results, 1):
                logger.info(f"  {i}. {result.url} - {result.title[:60]}...")

            # Step 4: Extract content from URLs (if enabled)
            search_sources = []
            reference_links = []  # Track reference links for extensive searches

            if self.config.enable_content_extraction:
                # Extract URLs for content extraction
                urls = [result.url for result in processed_results]

                # Extract content concurrently with processing
                async with WebContentExtractor(self.config, self.content_processor) as extractor:
                    if self.content_processor:
                        # Use query-focused extraction when content processor is available
                        content_results = []
                        for url in urls:
                            result = await extractor.extract_content_with_query_focus(url, request.query)
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

                # Convert to SearchSource objects
                for i, content_result in enumerate(content_results):
                    google_result = processed_results[i] if i < len(processed_results) else None

                    # Log content parsing result for each URL
                    status = "✅ SUCCESS" if content_result.success and content_result.content.strip() else "❌ FAILED"
                    content_length = len(content_result.content) if content_result.content else 0
                    logger.info(f"📄 Content parsing {i + 1}. {content_result.url} - {status} ({content_length} chars)")

                    # Use extracted content or fallback to snippet
                    content = (
                        content_result.content
                        if content_result.success and content_result.content.strip()
                        else (google_result.snippet if google_result else "Content extraction failed")
                    )

                    # Ensure content is not empty (SearchSource validation requirement)
                    if not content.strip():
                        content = "No content available"

                    full_content = content_result.full_content if request.with_full_content else ""

                    search_source = SearchSource(url=content_result.url, content=content, full_content=full_content)
                    search_sources.append(search_source)
            else:
                # Content extraction disabled - use Google snippets
                logger.info("📝 Content extraction disabled, using Google snippets")
                for result in processed_results:
                    search_source = SearchSource(url=result.url, content=result.snippet, full_content="")
                    search_sources.append(search_source)

            # Step 5: Process reference links for standard/extensive searches
            if reference_links and request.search_depth in ["standard", "extensive"]:
                logger.info(f"📚 Processing {len(reference_links)} reference links")

                # Remove duplicates and limit based on search depth
                unique_ref_links = list(dict.fromkeys(reference_links))  # Preserve order
                max_refs = 3 if request.search_depth == "standard" else 7
                limited_ref_links = unique_ref_links[:max_refs]

                if limited_ref_links:
                    # Extract content from reference links with query focus
                    async with WebContentExtractor(self.config, self.content_processor) as ref_extractor:
                        if self.content_processor:
                            ref_content_results = []
                            for ref_url in limited_ref_links:
                                ref_result = await ref_extractor.extract_content_with_query_focus(ref_url, request.query)
                                ref_content_results.append(ref_result)
                        else:
                            ref_content_results = await ref_extractor.extract_multiple_urls(limited_ref_links)

                        # Add successful reference extractions to results
                        for ref_result in ref_content_results:
                            if ref_result.success and ref_result.content.strip():
                                ref_source = SearchSource(
                                    url=ref_result.url,
                                    content=ref_result.content,
                                    full_content=ref_result.full_content if request.with_full_content else "",
                                )
                                search_sources.append(ref_source)
                                logger.info(f"📚 Added reference content from: {ref_result.url}")

            # Step 6: Create response with metadata
            raw_data = json.dumps(
                {
                    "query": request.query,
                    "optimized_query": optimized_query,
                    "total_google_results": len(google_results),
                    "filtered_results": len(processed_results),
                    "content_extraction_enabled": self.config.enable_content_extraction,
                    "search_depth": request.search_depth,
                    "reference_links_found": len(reference_links) if reference_links else 0,
                    "reference_links_processed": len([s for s in search_sources if s.url in reference_links]) if reference_links else 0,
                },
                indent=2,
            )

            logger.info(f"✅ Search completed - {len(search_sources)} results with content")

            return SearchResults(success=True, sources=search_sources, raw_data=raw_data)

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
            **{k: v for k, v in kwargs.items() if hasattr(GoogleSearchConfig, k)},
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
