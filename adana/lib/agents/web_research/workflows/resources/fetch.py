"""
FetchComponents - Retrieving content from web sources.

Provides reusable fetch operations that can be composed into workflows.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

from adana.common.protocols import DictParams
from adana.common.protocols.war import tool_use
from adana.core.resource.base_resource import BaseResource
from adana.core.workflow.workflow_executor import observable

from .components import _web_fetcher


logger = logging.getLogger(__name__)


class FetchResource(BaseResource):
    """Reusable fetch operations for workflow composition."""

    def __init__(self, **kwargs):
        """
        Initialize fetch components.
        """
        super().__init__(**kwargs)
        self.web_fetcher = _web_fetcher

    @tool_use
    def fetch_url(self, url: str, timeout: int | None = None, max_size: int | None = None) -> DictParams:
        """
        Fetch content from a single URL.

        Args:
            url: URL to fetch
            timeout: Request timeout in seconds
            max_size: Maximum response size in bytes

        Returns:
            Fetch result with content and metadata
        """
        return self.web_fetcher.fetch_url(url, timeout=timeout, max_size=max_size)

    @observable
    @tool_use
    def fetch_multiple_urls(
        self, urls: list[str], timeout: int | None = None, max_size: int | None = None, max_workers: int = 3
    ) -> list[DictParams]:
        """
        Fetch content from multiple URLs in parallel.

        Args:
            urls: List of URLs to fetch
            timeout: Request timeout in seconds per URL
            max_size: Maximum response size in bytes per URL
            max_workers: Maximum parallel fetches (respects rate limits)

        Returns:
            List of fetch results in same order as input URLs
        """
        results: list[DictParams | None] = [None] * len(urls)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all fetch tasks
            future_to_index = {
                executor.submit(self.web_fetcher.fetch_url, url, timeout=timeout, max_size=max_size): i for i, url in enumerate(urls)
            }

            # Collect results as they complete
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    results[index] = future.result()
                except Exception as e:
                    logger.error(f"Failed to fetch URL at index {index}: {e}")
                    results[index] = {"success": False, "error": f"Fetch exception: {str(e)}"}

        return results  # type: ignore

    def fetch_with_progress(self, urls: list[str], timeout: int | None = None, max_size: int | None = None) -> DictParams:
        """
        Fetch multiple URLs with progress tracking.

        Args:
            urls: List of URLs to fetch
            timeout: Request timeout in seconds
            max_size: Maximum response size in bytes

        Returns:
            {
                "total": int,
                "successful": int,
                "failed": int,
                "results": list[DictParams],
                "progress": list[dict]  # Progress updates
            }
        """
        results = []
        progress = []

        for i, url in enumerate(urls):
            result = self.web_fetcher.fetch_url(url, timeout=timeout, max_size=max_size)
            results.append(result)

            progress_update = {
                "index": i,
                "url": url,
                "completed": i + 1,
                "total": len(urls),
                "success": result.get("success", False),
                "progress_percent": ((i + 1) / len(urls)) * 100,
            }
            progress.append(progress_update)

            logger.info(f"Fetch progress: {i + 1}/{len(urls)} ({progress_update['progress_percent']:.1f}%)")

        successful = sum(1 for r in results if r.get("success", False))
        failed = len(results) - successful

        return {"total": len(urls), "successful": successful, "failed": failed, "results": results, "progress": progress}

    def validate_url(self, url: str) -> DictParams:
        """
        Validate URL accessibility without fetching full content.

        Args:
            url: URL to validate

        Returns:
            Validation result with accessibility information
        """
        return self.web_fetcher.validate_url(url)

    def validate_multiple_urls(self, urls: list[str], max_workers: int = 5) -> list[DictParams]:
        """
        Validate multiple URLs in parallel.

        Args:
            urls: List of URLs to validate
            max_workers: Maximum parallel validations

        Returns:
            List of validation results
        """
        results: list[DictParams | None] = [None] * len(urls)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_index = {executor.submit(self.web_fetcher.validate_url, url): i for i, url in enumerate(urls)}

            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    results[index] = future.result()
                except Exception as e:
                    results[index] = {"valid": False, "accessible": False, "error": str(e)}

        return results  # type: ignore

    def try_api_endpoint(self, base_url: str, endpoint_paths: list[str]) -> DictParams:
        """
        Try multiple API endpoint paths to find working one.

        Useful for data portals (GitHub, PyPI, etc.) where API access
        is preferred over HTML scraping.

        Args:
            base_url: Base URL (e.g., "https://api.github.com")
            endpoint_paths: List of endpoint paths to try

        Returns:
            {
                "success": bool,
                "working_endpoint": str | None,
                "content": str | None,
                "status_code": int | None,
                "attempted": list[str]  # All attempted URLs
            }
        """
        attempted = []

        for path in endpoint_paths:
            url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
            attempted.append(url)

            logger.debug(f"Trying API endpoint: {url}")

            result = self.web_fetcher.fetch_url(url)

            if result.get("success") and 200 <= result.get("status_code", 0) < 300:
                return {
                    "success": True,
                    "working_endpoint": url,
                    "content": result.get("content"),
                    "status_code": result.get("status_code"),
                    "content_type": result.get("content_type"),
                    "attempted": attempted,
                }

        # No working endpoint found
        return {
            "success": False,
            "working_endpoint": None,
            "content": None,
            "status_code": None,
            "attempted": attempted,
            "error": "No working API endpoint found",
        }

    def fetch_with_fallback(self, primary_url: str, fallback_urls: list[str], timeout: int | None = None) -> DictParams:
        """
        Fetch URL with fallback options if primary fails.

        Args:
            primary_url: Primary URL to try first
            fallback_urls: List of fallback URLs to try if primary fails
            timeout: Request timeout in seconds

        Returns:
            Fetch result from first successful URL
        """
        # Try primary first
        result = self.web_fetcher.fetch_url(primary_url, timeout=timeout)

        if result.get("success"):
            return {**result, "source": "primary", "url_used": primary_url, "fallback_attempted": False}

        # Try fallbacks
        for i, fallback_url in enumerate(fallback_urls):
            logger.info(f"Primary failed, trying fallback {i + 1}/{len(fallback_urls)}")

            result = self.web_fetcher.fetch_url(fallback_url, timeout=timeout)

            if result.get("success"):
                return {**result, "source": "fallback", "url_used": fallback_url, "fallback_attempted": True, "fallback_index": i}

        # All failed
        return {
            "success": False,
            "error": f"Primary and all {len(fallback_urls)} fallback URLs failed",
            "primary_url": primary_url,
            "fallback_urls": fallback_urls,
        }

    def fetch_with_retry(self, url: str, max_retries: int = 3, timeout: int | None = None) -> DictParams:
        """
        Fetch URL with custom retry logic (beyond built-in retries).

        Args:
            url: URL to fetch
            max_retries: Maximum retry attempts
            timeout: Request timeout in seconds

        Returns:
            Fetch result after retries
        """
        last_error = None

        for attempt in range(max_retries):
            logger.debug(f"Fetch attempt {attempt + 1}/{max_retries} for {url}")

            result = self.web_fetcher.fetch_url(url, timeout=timeout)

            if result.get("success"):
                return {**result, "retry_attempt": attempt + 1, "retries_needed": attempt}

            last_error = result.get("error", "Unknown error")

            # Don't retry on certain errors (404, 403, etc.)
            status_code = result.get("status_code")
            if status_code in [404, 403, 401, 410]:
                logger.info(f"Not retrying due to status code {status_code}")
                break

        # All retries exhausted
        return {"success": False, "error": f"Failed after {max_retries} attempts: {last_error}", "retries_exhausted": True, "url": url}

    @observable
    @tool_use
    def fetch_and_extract(self, urls: list[str], max_workers: int = 3, deduplicate: bool = True) -> list[DictParams]:
        """
        Fetch multiple URLs, extract content, and optionally deduplicate - all in one operation.

        This method handles large intermediate data (raw HTML) internally without exposing it
        to the caller. Only returns the deduplicated extracted content, keeping memory usage
        minimal and avoiding LLM context overflow.

        Args:
            urls: List of URLs to fetch and extract
            max_workers: Number of parallel workers for fetching (default: 3)
            deduplicate: Whether to deduplicate extracted content (default: True)

        Returns:
            List of deduplicated extracted content dictionaries with:
            - success: Whether extraction succeeded
            - url: Source URL (final URL after redirects)
            - status_code: HTTP status code from fetch
            - fetch_time_ms: Time taken to fetch the URL
            - title: Page title
            - content_text: Extracted text content
            - content_markdown: Extracted markdown content
            - word_count: Number of words in content
            - metadata: Extraction metadata
        """
        # Import here to avoid circular dependency
        from adana.lib.agents.web_research.workflows.resources.extract import ExtractResource
        from adana.lib.agents.web_research.workflows.resources.process import ProcessResource

        logger.info(f"Starting fetch_and_extract for {len(urls)} URLs")

        # Step 1: Fetch URLs in parallel
        fetch_results = self.fetch_multiple_urls(urls, max_workers=max_workers)
        successful_fetches = [r for r in fetch_results if r.get("success")]
        logger.info(f"Successfully fetched {len(successful_fetches)}/{len(urls)} URLs")

        if not successful_fetches:
            logger.warning("No URLs were successfully fetched")
            return []

        # Step 2: Extract content from fetched pages
        extractor = ExtractResource()
        extraction_results = extractor.extract_from_multiple(successful_fetches)
        successful_extractions = [e for e in extraction_results if e.get("success")]
        logger.info(f"Successfully extracted {len(successful_extractions)}/{len(successful_fetches)} pages")

        if not successful_extractions:
            logger.warning("No content was successfully extracted")
            return []

        # Step 3: Deduplicate if requested
        if deduplicate:
            processor = ProcessResource()
            unique_content = processor.deduplicate_content(successful_extractions)
            logger.info(f"Deduplicated {len(successful_extractions)} -> {len(unique_content)} extractions")
            return unique_content

        return successful_extractions

    @tool_use
    def fetch_and_extract_single(
        self, url: str, purpose: str = "general analysis", extract_code: bool = False, max_key_points: int = 5
    ) -> DictParams:
        """
        Fetch single URL and extract all relevant content in one operation.

        This method handles large intermediate data (raw HTML) internally without exposing it
        to the caller. Only returns extracted content, metadata, code blocks, key points,
        and quality assessment.

        Args:
            url: URL to fetch and analyze
            purpose: Analysis purpose for quality assessment
            extract_code: Whether to extract code blocks
            max_key_points: Maximum number of key points to extract

        Returns:
            Dictionary with:
            - success: Whether operation succeeded
            - url: Final URL (after redirects)
            - title: Page title
            - content_text: Extracted text content
            - content_markdown: Extracted markdown content
            - word_count: Number of words
            - metadata: Page metadata (author, date, etc.)
            - quality: Quality assessment
            - key_points: List of key points
            - summary: Brief summary
            - code_blocks: List of code blocks (if extract_code=True)
            - error: Error message if failed
        """
        # Import here to avoid circular dependency
        from adana.lib.agents.web_research.workflows.resources.extract import ExtractResource
        from adana.lib.agents.web_research.workflows.resources.process import ProcessResource

        logger.info(f"Starting fetch_and_extract_single for: {url}")

        # Step 1: Fetch URL
        fetch_result = self.fetch_url(url)

        if not fetch_result.get("success"):
            logger.error(f"Failed to fetch URL: {fetch_result.get('error')}")
            return {"success": False, "error": f"Failed to fetch URL: {fetch_result.get('error')}", "url": url}

        html = fetch_result.get("content", "")
        final_url = fetch_result.get("url", url)  # After redirects

        # Step 2: Extract content with quality check
        extractor = ExtractResource()
        extraction_result = extractor.extract_with_quality_check(html, final_url, purpose)

        if not extraction_result.get("content", {}).get("success"):
            logger.error("Content extraction failed")
            return {"success": False, "error": "Content extraction failed", "url": final_url}

        content = extraction_result.get("content", {})
        quality = extraction_result.get("quality", {})

        # Step 3: Extract metadata
        metadata_result = extractor.extract_metadata(html)
        metadata = metadata_result if metadata_result.get("success") else {}

        # Step 4: Extract code blocks if requested
        code_blocks = []
        if extract_code:
            logger.debug("Extracting code blocks...")
            code_result = extractor.extract_code_blocks(html)
            if code_result.get("success"):
                code_blocks = code_result.get("code_blocks", [])

        # Step 5: Extract key points from content
        processor = ProcessResource()
        content_text = content.get("content_text", "")
        key_points_result = processor.extract_key_points(content_text, max_points=max_key_points)

        key_points = key_points_result.get("key_points", [])
        summary = key_points_result.get("summary", "")

        logger.info(f"Successfully extracted content from {final_url}")

        return {
            "success": True,
            "url": final_url,
            "title": content.get("title", "Untitled"),
            "content_text": content_text,
            "content_markdown": content.get("content_markdown", ""),
            "word_count": content.get("word_count", 0),
            "reading_time_minutes": content.get("reading_time_minutes", 0),
            "metadata": metadata,
            "quality": quality,
            "sufficient": extraction_result.get("sufficient", False),
            "key_points": key_points,
            "summary": summary,
            "code_blocks": code_blocks,
            "error": None,
        }
