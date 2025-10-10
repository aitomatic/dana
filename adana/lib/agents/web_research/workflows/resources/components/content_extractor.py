"""
ContentExtractorResource - HTML parsing and content extraction operations.

This resource handles all content processing including:
- Extracting main content (removing boilerplate)
- Parsing metadata
- Extracting links and tables
- Converting HTML to markdown
- Assessing content quality using LLM reasoning
"""

import logging
import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
import html2text
from readability import Document

from adana.common.llm import LLM
from adana.common.protocols import DictParams
from adana.core.resource.base_resource import BaseResource


logger = logging.getLogger(__name__)


class ContentExtractor(BaseResource):
    """
    Component for parsing HTML and extracting structured content.

    Uses readability algorithm for main content extraction and
    LLM reasoning for quality assessment.
    """

    def __init__(self, llm_client: LLM | None = None, **kwargs):
        kwargs["llm_client"] = llm_client
        super().__init__(**kwargs)

        # Configuration
        self.config = {
            "min_text_length": 25,
            "max_text_length": 100_000,  # 100KB for LLM processing
            "readability_retry_length": 250,
        }

        # HTML to Markdown converter
        self.html_converter = html2text.HTML2Text()
        self.html_converter.body_width = 0  # No wrapping
        self.html_converter.emphasis_mark = "*"
        self.html_converter.strong_mark = "**"

    def extract_main_content(self, html: str, base_url: str | None = None) -> DictParams:
        """
        Extract main article/content from HTML, removing boilerplate.

        Uses readability algorithm to identify main content area,
        removing navigation, ads, sidebars, footers, etc.

        Args:
            html: Raw HTML content
            base_url: Base URL for resolving relative links

        Returns:
            {
                "success": bool,
                "title": str,
                "author": str | None,
                "content_text": str,  # Plain text
                "content_html": str,  # Cleaned HTML
                "content_markdown": str,  # Markdown format
                "excerpt": str,  # First 200 chars
                "word_count": int,
                "reading_time_minutes": int,
                "language": str | None,
                "published_date": str | None,
                "error": str | None
            }
        """
        try:
            # Use readability to extract main content
            doc = Document(html)

            title = doc.title()
            content_html = doc.summary()

            # Parse cleaned HTML
            soup = BeautifulSoup(content_html, "lxml")
            content_text = soup.get_text(separator=" ", strip=True)

            # Truncate if too long
            if len(content_text) > self.config["max_text_length"]:
                content_text = content_text[: self.config["max_text_length"]] + "...[truncated]"
                logger.warning(f"Content truncated to {self.config['max_text_length']} chars")

            # Convert to markdown
            content_markdown = self.html_converter.handle(content_html)

            # Calculate reading time (average 200 words per minute)
            word_count = len(content_text.split())
            reading_time = max(1, word_count // 200)

            # Extract excerpt (first 200 chars)
            excerpt = content_text[:200] + "..." if len(content_text) > 200 else content_text

            # Try to extract metadata
            metadata = self.extract_metadata(html)

            return {
                "success": True,
                "title": title,
                "author": metadata.get("author"),
                "content_text": content_text,
                "content_html": content_html,
                "content_markdown": content_markdown,
                "excerpt": excerpt,
                "word_count": word_count,
                "reading_time_minutes": reading_time,
                "language": metadata.get("language"),
                "published_date": metadata.get("published_date"),
                "error": None,
            }

        except Exception as e:
            return {"success": False, "error": f"Content extraction failed: {str(e)}"}

    def extract_links(self, html: str, base_url: str, filter_external: bool = False) -> DictParams:
        """
        Extract all links from HTML.

        Args:
            html: Raw HTML content
            base_url: Base URL for resolving relative links
            filter_external: If True, only return internal links

        Returns:
            {
                "success": bool,
                "base_url": str,
                "links": [
                    {
                        "text": str,  # Link text
                        "url": str,   # Absolute URL
                        "is_external": bool,
                        "element": str  # 'a', 'link', etc.
                    }
                ],
                "total_links": int,
                "internal_links": int,
                "external_links": int,
                "error": str | None
            }
        """
        try:
            soup = BeautifulSoup(html, "lxml")
            base_domain = urlparse(base_url).netloc

            links = []
            for tag in soup.find_all(["a", "link"]):
                href = tag.get("href")
                if not href or not isinstance(href, str) or href.startswith(("#", "javascript:", "mailto:")):
                    continue

                # Resolve relative URLs
                absolute_url = urljoin(base_url, href)
                url_domain = urlparse(absolute_url).netloc

                is_external = url_domain != base_domain

                # Skip external if filtering
                if filter_external and is_external:
                    continue

                links.append(
                    {
                        "text": tag.get_text(strip=True) if tag.name == "a" else "",
                        "url": absolute_url,
                        "is_external": is_external,
                        "element": tag.name,
                    }
                )

            internal_count = sum(1 for link in links if not link["is_external"])
            external_count = len(links) - internal_count

            return {
                "success": True,
                "base_url": base_url,
                "links": links,
                "total_links": len(links),
                "internal_links": internal_count,
                "external_links": external_count,
                "error": None,
            }

        except Exception as e:
            return {"success": False, "error": f"Link extraction failed: {str(e)}"}

    def extract_metadata(self, html: str) -> DictParams:
        """
        Extract metadata from HTML (meta tags, Open Graph, etc.).

        Args:
            html: Raw HTML content

        Returns:
            {
                "success": bool,
                "title": str | None,
                "description": str | None,
                "keywords": list[str],
                "author": str | None,
                "canonical_url": str | None,
                "published_date": str | None,
                "language": str | None,
                "open_graph": dict,
                "twitter_card": dict,
                "error": str | None
            }
        """
        try:
            soup = BeautifulSoup(html, "lxml")

            # Basic metadata
            title = soup.find("title")
            title_text = title.get_text(strip=True) if title else None

            description = soup.find("meta", attrs={"name": "description"})
            description_text = description.get("content") if description else None

            keywords = soup.find("meta", attrs={"name": "keywords"})
            keywords_list = []
            if keywords:
                content = keywords.get("content", "")
                if content:
                    keywords_list = [k.strip() for k in content.split(",")]

            author = soup.find("meta", attrs={"name": "author"})
            author_text = author.get("content") if author else None

            canonical = soup.find("link", attrs={"rel": "canonical"})
            canonical_url = canonical.get("href") if canonical else None

            # Language
            html_tag = soup.find("html")
            language = html_tag.get("lang") if html_tag else None

            # Open Graph metadata
            og_tags = {}
            for tag in soup.find_all("meta", attrs={"property": re.compile("^og:")}):
                property_name = tag.get("property")
                content = tag.get("content")
                if property_name and content:
                    og_tags[property_name] = content

            # Twitter Card metadata
            twitter_tags = {}
            for tag in soup.find_all("meta", attrs={"name": re.compile("^twitter:")}):
                name = tag.get("name")
                content = tag.get("content")
                if name and content:
                    twitter_tags[name] = content

            # Try to extract published date
            published_date = None
            date_meta = (
                soup.find("meta", attrs={"property": "article:published_time"})
                or soup.find("meta", attrs={"name": "publish_date"})
                or soup.find("time", attrs={"datetime": True})
            )

            if date_meta:
                published_date = date_meta.get("content") or date_meta.get("datetime")

            return {
                "success": True,
                "title": title_text,
                "description": description_text,
                "keywords": keywords_list,
                "author": author_text,
                "canonical_url": canonical_url,
                "published_date": published_date,
                "language": language,
                "open_graph": og_tags,
                "twitter_card": twitter_tags,
                "error": None,
            }

        except Exception as e:
            return {"success": False, "error": f"Metadata extraction failed: {str(e)}"}

    def html_to_markdown(
        self, html: str, base_url: str | None = None, include_images: bool = True, include_links: bool = True
    ) -> DictParams:
        """
        Convert HTML to clean Markdown format.

        Args:
            html: Raw HTML content
            base_url: Base URL for resolving relative URLs
            include_images: Include image references
            include_links: Include links

        Returns:
            {
                "success": bool,
                "markdown": str,
                "images": list[str],  # Image URLs found
                "links": list[str],   # Links found
                "error": str | None
            }
        """
        try:
            # Configure converter
            converter = html2text.HTML2Text()
            converter.body_width = 0
            converter.ignore_images = not include_images
            converter.ignore_links = not include_links

            if base_url:
                converter.baseurl = base_url

            markdown = converter.handle(html)

            # Extract images and links
            soup = BeautifulSoup(html, "lxml")

            images = []
            if include_images:
                for img in soup.find_all("img"):
                    src = img.get("src")
                    if src and isinstance(src, str):
                        images.append(urljoin(base_url, src) if base_url else src)

            links = []
            if include_links:
                for a in soup.find_all("a"):
                    href = a.get("href")
                    if href and isinstance(href, str):
                        links.append(urljoin(base_url, href) if base_url else href)

            return {"success": True, "markdown": markdown, "images": images, "links": links, "error": None}

        except Exception as e:
            return {"success": False, "error": f"HTML to markdown conversion failed: {str(e)}"}

    def extract_tables(self, html: str) -> DictParams:
        """
        Extract all tables from HTML as structured data.

        Args:
            html: Raw HTML content

        Returns:
            {
                "success": bool,
                "tables": [
                    {
                        "headers": list[str],
                        "rows": list[list[str]],
                        "caption": str | None,
                        "index": int  # Position in document
                    }
                ],
                "total_tables": int,
                "error": str | None
            }
        """
        try:
            soup = BeautifulSoup(html, "lxml")
            tables = []

            for i, table in enumerate(soup.find_all("table")):
                # Extract caption
                caption = table.find("caption")
                caption_text = caption.get_text(strip=True) if caption else None

                # Extract headers
                headers = []
                header_row = table.find("thead")
                if header_row:
                    for th in header_row.find_all(["th", "td"]):
                        headers.append(th.get_text(strip=True))
                else:
                    # Try first row as headers
                    first_row = table.find("tr")
                    if first_row:
                        for th in first_row.find_all(["th", "td"]):
                            headers.append(th.get_text(strip=True))

                # Extract rows
                rows = []
                tbody = table.find("tbody") or table
                for tr in tbody.find_all("tr"):
                    # Skip if this is the header row we already processed
                    if tr.find("th") and not rows:
                        continue

                    row = []
                    for td in tr.find_all(["td", "th"]):
                        row.append(td.get_text(strip=True))

                    if row:  # Only add non-empty rows
                        rows.append(row)

                tables.append({"headers": headers, "rows": rows, "caption": caption_text, "index": i})

            return {"success": True, "tables": tables, "total_tables": len(tables), "error": None}

        except Exception as e:
            return {"success": False, "error": f"Table extraction failed: {str(e)}"}

    def assess_content_quality(self, html: str, url: str, purpose: str) -> DictParams:
        """
        Use LLM reasoning to assess if extracted content is sufficient for purpose.

        Args:
            html: Raw HTML content
            url: Source URL
            purpose: What the content will be used for

        Returns:
            {
                "is_sufficient": bool,
                "quality_score": float (0.0-1.0),
                "content_type": str,
                "missing_elements": list[str],
                "recommendations": list[str],
                "confidence": float (0.0-1.0)
            }
        """
        # Extract basic metrics first
        content = self.extract_main_content(html)
        metadata = self.extract_metadata(html)

        if not content.get("success"):
            return {
                "is_sufficient": False,
                "quality_score": 0.0,
                "content_type": "unknown",
                "missing_elements": ["Failed to extract content"],
                "recommendations": ["Try a different source"],
                "confidence": 1.0,
            }

        # Use BaseWAR.reason() for quality assessment
        assessment = self.reason(
            {
                "task": "Assess content quality and sufficiency for intended purpose",
                "input": {
                    "url": url,
                    "purpose": purpose,
                    "content_length": len(content.get("content_text", "")),
                    "word_count": content.get("word_count", 0),
                    "has_metadata": bool(metadata.get("title")),
                    "has_author": bool(metadata.get("author")),
                    "has_date": bool(metadata.get("published_date")),
                    "has_headings": bool(re.search(r"<h[1-6]", html)),
                    "has_code": bool(re.search(r"<code|<pre", html)),
                    "has_tables": bool(re.search(r"<table", html)),
                    "content_preview": content.get("content_text", "")[:500],
                    "title": metadata.get("title", ""),
                },
                "output_schema": {
                    "is_sufficient": "bool (is content adequate for purpose)",
                    "quality_score": "float (0.0-1.0, overall quality)",
                    "content_type": "str (article|documentation|tutorial|forum|news|data_table|other)",
                    "missing_elements": "list[str] (what's needed but absent)",
                    "recommendations": "list[str] (suggestions for improvement)",
                    "confidence": "float (0.0-1.0)",
                },
                "context": {
                    "purpose_requirements": {
                        "tutorial": ["step_by_step_instructions", "code_examples", "explanations"],
                        "research": ["multiple_perspectives", "citations", "recent_date"],
                        "fact_finding": ["authoritative_source", "concise_answer"],
                        "structured_data": ["tables", "lists", "statistics"],
                    },
                    "quality_indicators": {
                        "high": ["long_content", "code_examples", "headings", "metadata"],
                        "low": ["very_short", "no_structure", "ads_heavy"],
                    },
                },
                "temperature": 0.2,
                "max_tokens": 1000,
                "fallback": {
                    "is_sufficient": True,  # Assume sufficient if LLM unavailable
                    "quality_score": 0.7,
                    "content_type": "article",
                    "missing_elements": [],
                    "recommendations": [],
                    "confidence": 0.0,
                },
            }
        )

        return assessment
