"""Web content extraction using BeautifulSoup."""

import asyncio
import logging
import re
from typing import NamedTuple

import httpx
from bs4 import BeautifulSoup, Comment

from .config import GoogleSearchConfig
from .exceptions import ContentExtractionError
from .pdf_service import PDFService

logger = logging.getLogger(__name__)

# Default headers to mimic a real browser
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


class ContentResult(NamedTuple):
    """Result of content extraction."""

    url: str
    content: str
    full_content: str
    success: bool
    error_message: str = ""
    content_type: str = "html"  # "html" or "pdf"


class ContentWithHtml(NamedTuple):
    """Result of content extraction with both HTML and text."""

    url: str
    html: str
    text: str
    success: bool
    error_message: str = ""
    content_type: str = "html"


class WebContentExtractor:
    """Handles web content fetching and cleaning with BeautifulSoup."""

    def __init__(self, config: GoogleSearchConfig, content_processor=None):
        """
        Initialize web content extractor.

        Args:
            config: Google search configuration
            content_processor: Optional content processor for query-relevant extraction
        """
        self.config = config
        self._client: httpx.AsyncClient | None = None
        self.pdf_service = PDFService(timeout=config.content_timeout)
        self.content_processor = content_processor

    async def __aenter__(self):
        """Async context manager entry."""
        timeout = httpx.Timeout(timeout=self.config.content_timeout)
        self._client = httpx.AsyncClient(
            headers=DEFAULT_HEADERS,
            timeout=timeout,
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    async def extract_content(self, url: str) -> ContentResult:
        """
        Extract and clean content from a URL (supports both HTML and PDF).

        Args:
            url: URL to fetch content from

        Returns:
            ContentResult with extracted content
        """
        if not self._client:
            raise RuntimeError("WebContentExtractor must be used as async context manager")

        logger.info(f"🌐 Extracting content from: {url}")

        try:
            # Check if it's a PDF URL
            if url.lower().endswith(".pdf"):
                return await self._extract_pdf_content(url)
            else:
                return await self._extract_html_content(url)

        except Exception as e:
            logger.error(f"❌ Content extraction failed for {url}: {e}")
            return ContentResult(url=url, content="", full_content="", success=False, error_message=str(e))

    async def _extract_pdf_content(self, url: str) -> ContentResult:
        """Extract content from PDF URL."""
        logger.info(f"📄 Processing PDF: {url}")

        pdf_text = await self.pdf_service.extract_text_from_pdf_url(url)

        if not pdf_text:
            return ContentResult(
                url=url,
                content="",
                full_content="",
                success=False,
                error_message="Failed to extract PDF content",
                content_type="pdf",
            )

        # Truncate if too long
        content = pdf_text
        if len(content) > self.config.max_content_length:
            logger.info(f"📏 Truncating PDF content from {len(content)} to {self.config.max_content_length} characters")
            content = content[: self.config.max_content_length] + "... [truncated]"

        logger.info(f"✅ Extracted {len(content)} characters from PDF")

        return ContentResult(
            url=url,
            content=content,
            full_content=pdf_text if len(pdf_text) <= self.config.max_content_length else "",
            success=True,
            content_type="pdf",
        )

    async def _extract_html_content(self, url: str) -> ContentResult:
        """Extract content from HTML URL."""
        # Fetch HTML content
        html_content = await self._fetch_html(url)
        if not html_content:
            return ContentResult(
                url=url,
                content="",
                full_content="",
                success=False,
                error_message="Failed to fetch HTML content",
            )

        # Clean and extract text
        cleaned_content = self._clean_html_content(html_content)

        # Truncate if too long
        if len(cleaned_content) > self.config.max_content_length:
            logger.info(f"📏 Truncating content from {len(cleaned_content)} to {self.config.max_content_length} characters")
            cleaned_content = cleaned_content[: self.config.max_content_length] + "... [truncated]"

        logger.info(f"✅ Extracted {len(cleaned_content)} characters")

        return ContentResult(
            url=url,
            content=cleaned_content,
            full_content=html_content if self.config.max_content_length > len(html_content) else "",
            success=True,
        )

    async def _fetch_html(self, url: str) -> str:
        """
        Fetch HTML content from URL.

        Args:
            url: URL to fetch from

        Returns:
            Raw HTML content as string

        Raises:
            ContentExtractionError: If fetching fails
        """
        try:
            response = await self._client.get(url)
            response.raise_for_status()

            # Check if it's HTML content
            content_type = response.headers.get("content-type", "").lower()
            if "text/html" not in content_type:
                logger.warning(f"⚠️ Non-HTML content type: {content_type}")

            return response.text

        except httpx.HTTPStatusError as e:
            raise ContentExtractionError(f"HTTP {e.response.status_code}: {e.response.reason_phrase}")
        except httpx.TimeoutException:
            raise ContentExtractionError("Request timed out")
        except httpx.RequestError as e:
            raise ContentExtractionError(f"Request failed: {e}")

    def _clean_html_content(self, html_content: str) -> str:
        """
        Clean HTML content and extract readable text.

        Args:
            html_content: Raw HTML content

        Returns:
            Cleaned text content
        """
        if not html_content.strip():
            return ""

        logger.debug(f"🧹 Cleaning HTML content ({len(html_content)} characters)")

        try:
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html_content, "html.parser")

            # Remove unwanted elements
            self._remove_unwanted_elements(soup)

            # Extract text content
            text = soup.get_text(separator=" ", strip=True)

            # Clean up whitespace
            text = self._clean_text(text)

            logger.debug(f"✅ Cleaned to {len(text)} characters")
            return text

        except Exception as e:
            logger.error(f"❌ HTML cleaning failed: {e}")
            # Fallback: return raw text with basic cleaning
            return self._fallback_text_extraction(html_content)

    def _remove_unwanted_elements(self, soup: BeautifulSoup) -> None:
        """Remove unwanted HTML elements from soup."""

        # Remove script and style elements
        for element in soup(["script", "style"]):
            element.decompose()

        # Remove navigation, header, footer elements
        for element in soup(["nav", "header", "footer", "aside"]):
            element.decompose()

        # Remove comments
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        # Remove elements by class/id (common unwanted content)
        unwanted_selectors = [
            "[class*='nav']",
            "[class*='menu']",
            "[class*='sidebar']",
            "[class*='advertisement']",
            "[class*='ad-']",
            "[class*='cookie']",
            "[id*='nav']",
            "[id*='menu']",
            "[id*='sidebar']",
            "[id*='ad']",
        ]

        for selector in unwanted_selectors:
            for element in soup.select(selector):
                element.decompose()

    def _clean_text(self, text: str) -> str:
        """Clean extracted text content."""
        if not text:
            return ""

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove excessive punctuation
        text = re.sub(r"[^\w\s\.\,\!\?\:\;\-\(\)\[\]\/\%\$\@\#\&\*\+\=]", " ", text)

        # Clean up multiple spaces again after punctuation removal
        text = re.sub(r"\s+", " ", text)

        # Remove leading/trailing whitespace
        text = text.strip()

        return text

    def _fallback_text_extraction(self, html_content: str) -> str:
        """Fallback text extraction when BeautifulSoup fails."""
        # Simple regex-based tag removal
        text = re.sub(r"<script[^>]*>.*?</script>", "", html_content, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", "", text)

        # Clean up entities and whitespace
        text = re.sub(r"&[a-zA-Z0-9#]+;", " ", text)
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    async def extract_multiple_urls(self, urls: list[str]) -> list[ContentResult]:
        """
        Extract content from multiple URLs concurrently.

        Args:
            urls: List of URLs to extract content from

        Returns:
            List of ContentResult objects
        """
        if not urls:
            return []

        logger.info(f"🚀 Starting concurrent extraction from {len(urls)} URLs")

        # Limit concurrent extractions
        semaphore = asyncio.Semaphore(self.config.max_concurrent_extractions)

        async def extract_with_semaphore(url: str) -> ContentResult:
            async with semaphore:
                return await self.extract_content(url)

        # Create tasks for all URLs
        tasks = [extract_with_semaphore(url) for url in urls]

        # Execute all extractions
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle results and exceptions
        content_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"❌ Extraction failed for URL {i + 1}: {result}")
                content_results.append(
                    ContentResult(
                        url=urls[i] if i < len(urls) else "unknown",
                        content="",
                        full_content="",
                        success=False,
                        error_message=str(result),
                    )
                )
            else:
                content_results.append(result)

        successful = sum(1 for result in content_results if result.success)
        logger.info(f"📊 Content extraction completed: {successful}/{len(urls)} successful")

        return content_results

    async def extract_content_with_html(self, url: str) -> ContentWithHtml:
        """
        Extract both raw HTML and cleaned text from URL.

        Args:
            url: URL to fetch content from

        Returns:
            ContentWithHtml with both HTML and text content
        """
        if not self._client:
            raise RuntimeError("WebContentExtractor must be used as async context manager")

        logger.info(f"🌐 Extracting HTML+text from: {url}")

        try:
            # Check if it's a PDF URL - PDFs don't have HTML
            if url.lower().endswith(".pdf"):
                pdf_text = await self.pdf_service.extract_text_from_pdf_url(url)
                return ContentWithHtml(
                    url=url,
                    html="",  # PDFs don't have HTML
                    text=pdf_text,
                    success=bool(pdf_text),
                    error_message="" if pdf_text else "Failed to extract PDF content",
                    content_type="pdf",
                )

            # Fetch HTML content
            html_content = await self._fetch_html(url)
            if not html_content:
                return ContentWithHtml(
                    url=url,
                    html="",
                    text="",
                    success=False,
                    error_message="Failed to fetch HTML content",
                )

            # Clean and extract text
            cleaned_text = self._clean_html_content(html_content)

            logger.info(f"✅ Extracted HTML ({len(html_content)} chars) and text ({len(cleaned_text)} chars)")

            return ContentWithHtml(url=url, html=html_content, text=cleaned_text, success=True)

        except Exception as e:
            logger.error(f"❌ HTML+text extraction failed for {url}: {e}")
            return ContentWithHtml(url=url, html="", text="", success=False, error_message=str(e))

    async def extract_content_with_query_focus(self, url: str, query: str) -> ContentResult:
        """
        Extract content and apply query-focused summarization if needed.

        Args:
            url: URL to fetch content from
            query: Search query for relevance filtering

        Returns:
            ContentResult with query-focused content
        """
        # First extract content normally
        content_result = await self.extract_content(url)

        if not content_result.success or not self.content_processor:
            return content_result

        # Apply query-focused processing
        try:
            processed_content = await self.content_processor.process_content(content_result.content, query)

            # Return updated result
            return ContentResult(
                url=content_result.url,
                content=processed_content,
                full_content=content_result.full_content,
                success=True,
                content_type=content_result.content_type,
            )

        except Exception as e:
            logger.error(f"Query-focused processing failed for {url}: {e}")
            return content_result  # Return original on error
