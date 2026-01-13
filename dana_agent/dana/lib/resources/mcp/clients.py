"""
MCP Client Resources - Pre-configured MCP client resources for specific services.

This module provides ready-to-use MCP client resources for various services,
each configured with the appropriate parameters for that service.
"""

import logging
from typing import Any

from .mcp_client import MCPClientResource


logger = logging.getLogger(__name__)


class BrightQueryResource(MCPClientResource):
    """
    <PUBLIC_DESCRIPTION>
    BrightData MCP client resource for web scraping and data extraction.

    This resource provides a pre-configured interface to BrightData's MCP service
    for web scraping, data extraction, and search operations. It uses BrightData's
    local MCP server by default (requires npx and @brightdata/mcp package) and provides
    convenient methods for common BrightData operations.

    USE CASES:
    - Web scraping and data extraction
    - Search operations across web sources
    - Content analysis and processing
    - Data collection from various web sources
    - Automated web data gathering

    FEATURES:
    - Pre-configured for BrightData MCP service
    - Uses local server by default (requires npx and @brightdata/mcp package)
    - Fallback to hosted server if needed (experimental)
    - Convenient methods for common operations
    - Built-in error handling and logging
    - Context manager support for cleanup

    EXAMPLE USAGE:
    ```python
    # Initialize with your API token (uses local server by default)
    brightdata = BrightQueryResource(api_token="your-token")

    # Search the web
    results = brightdata.search(query="artificial intelligence", limit=10)

    # Scrape a website
    content = brightdata.scrape(url="https://example.com")

    # Extract specific data
    data = brightdata.extract(url="https://example.com", selector="h1")

    # Use hosted server if needed (experimental)
    brightdata_hosted = BrightQueryResource(api_token="your-token", use_hosted=True)
    ```
    </PUBLIC_DESCRIPTION>
    """

    def __init__(
        self,
        api_token: str,
        resource_id: str | None = None,
        timeout: float = 30.0,
        use_hosted: bool = False,
        **kwargs,
    ):
        """
        Initialize the BrightQueryResource.

        Args:
            api_token: BrightData API token
            resource_id: Unique identifier for this resource
            timeout: Request timeout in seconds
            use_hosted: Whether to use hosted server (False) or local server (True)
            **kwargs: Additional arguments passed to parent classes
        """
        if use_hosted:
            # Use BrightData's hosted MCP server (experimental)
            server_config = {"url": "https://mcp.brightdata.com/mcp", "uri_params": {"token": api_token}}
            server_type = "http"
        else:
            # Use local MCP server (recommended - requires npx)
            server_config = {"command": "npx", "args": ["@brightdata/mcp"], "env": {"API_TOKEN": api_token}}
            server_type = "local"

        super().__init__(
            server_type=server_type, server_config=server_config, resource_id=resource_id or "brightdata-query", timeout=timeout, **kwargs
        )

        self.api_token = api_token
        logger.info(f"Initialized BrightQueryResource with token: {api_token[:8]}...")

    @property
    def public_description(self) -> str:
        """Get the public description of this resource."""
        return """
        BrightData MCP client for web scraping and data extraction.

        Provides methods for:
        - search: Search the web for information
        - scrape: Extract content from web pages
        - extract: Extract specific data using selectors
        - crawl: Crawl multiple URLs
        - analyze: Analyze web content

        Requires BrightData API token for authentication.
        """

    def update_api_token(self, new_token: str) -> None:
        """
        Update the API token and restart the MCP server if needed.

        Args:
            new_token: New BrightData API token
        """
        self.api_token = new_token

        if self.server_type == "http":
            # Update URI parameters for hosted server
            self.server_config["uri_params"]["token"] = new_token
            self._build_full_url()
        elif self.server_type == "local":
            # Update environment variables and restart local server
            self.server_config["env"]["API_TOKEN"] = new_token
            self.restart_local_server()

        logger.info(f"Updated API token: {new_token[:8]}...")

    def get_available_methods(self) -> dict[str, Any]:
        """
        Get information about available methods from the BrightData MCP server.

        Returns:
            Dictionary containing available methods and their descriptions
        """
        try:
            # Try to get available methods from the MCP server
            result = self.query(method_name="list_methods")
            return result
        except Exception as e:
            logger.warning(f"Could not get available methods: {e}")
            return {
                "error": f"Could not retrieve methods: {e}",
                "common_methods": [
                    "search - Search the web for information",
                    "scrape - Extract content from web pages",
                    "extract - Extract specific data using selectors",
                    "crawl - Crawl multiple URLs",
                    "analyze - Analyze web content",
                ],
            }

    def search(self, query: str, limit: int = 10, source: str = "web", **kwargs) -> dict[str, Any]:
        """
        Search the web for information.

        Args:
            query: Search query
            limit: Maximum number of results
            source: Data source (web, social, etc.)
            **kwargs: Additional search parameters

        Returns:
            Search results from BrightData
        """
        params = {"query": query, "limit": limit, "source": source, **kwargs}
        return self._make_mcp_call("search", params)

    def scrape(self, url: str, extract: str = "text", **kwargs) -> dict[str, Any]:
        """
        Scrape content from a web page.

        Args:
            url: URL to scrape
            extract: Type of content to extract (text, html, json, etc.)
            **kwargs: Additional scraping parameters

        Returns:
            Scraped content from the URL
        """
        params = {"url": url, "extract": extract, **kwargs}
        return self._make_mcp_call("scrape", params)

    def extract(self, url: str, selector: str, **kwargs) -> dict[str, Any]:
        """
        Extract specific data from a web page using CSS selectors.

        Args:
            url: URL to extract data from
            selector: CSS selector for the data to extract
            **kwargs: Additional extraction parameters

        Returns:
            Extracted data matching the selector
        """
        params = {"url": url, "selector": selector, **kwargs}
        return self._make_mcp_call("extract", params)

    def crawl(self, urls: list[str], depth: int = 1, **kwargs) -> dict[str, Any]:
        """
        Crawl multiple URLs.

        Args:
            urls: List of URLs to crawl
            depth: Crawling depth
            **kwargs: Additional crawling parameters

        Returns:
            Crawled data from all URLs
        """
        params = {"urls": urls, "depth": depth, **kwargs}
        return self._make_mcp_call("crawl", params)

    def analyze(self, content: str, analysis_type: str = "sentiment", **kwargs) -> dict[str, Any]:
        """
        Analyze web content.

        Args:
            content: Content to analyze
            analysis_type: Type of analysis (sentiment, keywords, etc.)
            **kwargs: Additional analysis parameters

        Returns:
            Analysis results
        """
        params = {"content": content, "analysis_type": analysis_type, **kwargs}
        return self._make_mcp_call("analyze", params)


class GitHubMCPResource(MCPClientResource):
    """
    GitHub MCP client resource for GitHub operations.

    This resource provides a pre-configured interface to GitHub's MCP service
    for repository operations, issue management, and code analysis.
    """

    def __init__(
        self,
        github_token: str,
        resource_id: str | None = None,
        timeout: float = 30.0,
        **kwargs,
    ):
        """
        Initialize the GitHubMCPResource.

        Args:
            github_token: GitHub Personal Access Token
            resource_id: Unique identifier for this resource
            timeout: Request timeout in seconds
            **kwargs: Additional arguments passed to parent classes
        """
        # GitHub MCP server configuration (assuming HTTP-based)
        server_config = {
            "url": "https://api.github.com/mcp",
            "headers": {"Authorization": f"Bearer {github_token}", "Accept": "application/vnd.github.v3+json"},
        }

        super().__init__(
            server_type="http", server_config=server_config, resource_id=resource_id or "github-mcp", timeout=timeout, **kwargs
        )

        self.github_token = github_token
        logger.info(f"Initialized GitHubMCPResource with token: {github_token[:8]}...")

    def get_repository(self, owner: str, repo: str) -> dict[str, Any]:
        """Get repository information."""
        return self._make_mcp_call("get_repository", {"owner": owner, "repo": repo})

    def list_issues(self, owner: str, repo: str, state: str = "open") -> dict[str, Any]:
        """List repository issues."""
        return self._make_mcp_call("list_issues", {"owner": owner, "repo": repo, "state": state})

    def create_issue(self, owner: str, repo: str, title: str, body: str) -> dict[str, Any]:
        """Create a new issue."""
        return self._make_mcp_call("create_issue", {"owner": owner, "repo": repo, "title": title, "body": body})


class SlackMCPResource(MCPClientResource):
    """
    Slack MCP client resource for Slack operations.

    This resource provides a pre-configured interface to Slack's MCP service
    for messaging, channel management, and team collaboration.
    """

    def __init__(
        self,
        slack_token: str,
        resource_id: str | None = None,
        timeout: float = 30.0,
        **kwargs,
    ):
        """
        Initialize the SlackMCPResource.

        Args:
            slack_token: Slack Bot Token
            resource_id: Unique identifier for this resource
            timeout: Request timeout in seconds
            **kwargs: Additional arguments passed to parent classes
        """
        # Slack MCP server configuration (assuming HTTP-based)
        server_config = {
            "url": "https://slack.com/api/mcp",
            "headers": {"Authorization": f"Bearer {slack_token}", "Content-Type": "application/json"},
        }

        super().__init__(server_type="http", server_config=server_config, resource_id=resource_id or "slack-mcp", timeout=timeout, **kwargs)

        self.slack_token = slack_token
        logger.info(f"Initialized SlackMCPResource with token: {slack_token[:8]}...")

    def send_message(self, channel: str, text: str, **kwargs) -> dict[str, Any]:
        """Send a message to a Slack channel."""
        return self._make_mcp_call("send_message", {"channel": channel, "text": text, **kwargs})

    def list_channels(self) -> dict[str, Any]:
        """List available Slack channels."""
        return self._make_mcp_call("list_channels", {})

    def get_channel_info(self, channel: str) -> dict[str, Any]:
        """Get information about a specific channel."""
        return self._make_mcp_call("get_channel_info", {"channel": channel})
