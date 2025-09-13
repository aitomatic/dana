"""
Browser Resource

This module provides BrowserResourceType and BrowserResourceInstance for browsing URLs
using curl and returning their contents. This implements the standard .query(arg) method
where arg is the URL to browse.
"""

import subprocess
import json
import time
from typing import Any
from urllib.parse import urlparse

from dana.core.resource.resource_type import ResourceType
from dana.core.resource.resource_instance import ResourceInstance
from dana.common.utils.misc import Misc


class BrowserResourceType(ResourceType):
    """
    Resource type definition for browser resources.

    This class defines the structure and instantiation logic for browser resources
    that can browse URLs using curl and return their contents.
    """

    def __init__(self):
        """Initialize the browser resource type definition."""
        super().__init__(
            name="BrowserResource",
            fields={
                "name": "str",
                "user_agent": "str",
                "timeout": "int",
                "follow_redirects": "bool",
                "max_redirects": "int",
                "verify_ssl": "bool",
                "state": "str",
                "id": "str",
                "description": "str",
            },
            field_order=["name", "user_agent", "timeout", "follow_redirects", "max_redirects", "verify_ssl", "state", "id", "description"],
            field_defaults={
                "name": "browser",
                "user_agent": "Dana-Browser/1.0",
                "timeout": 30,
                "follow_redirects": True,
                "max_redirects": 5,
                "verify_ssl": True,
                "state": "READY",
                "id": Misc.generate_uuid(8),
                "description": "Browser resource for fetching web content using curl",
            },
            docstring="Browser resource that can fetch content from URLs using curl",
        )

    def create_instance(self, values: dict[str, Any] | None = None) -> "BrowserResourceInstance":
        """Create a new browser resource instance.

        Args:
            values: Optional field values to override defaults

        Returns:
            New BrowserResourceInstance
        """
        return BrowserResourceInstance(self, values or {})

    @classmethod
    def create_default_instance(cls) -> "BrowserResourceInstance":
        """Create a default browser resource instance.

        Returns:
            Default BrowserResourceInstance
        """
        return cls().create_instance()


class BrowserResourceInstance(ResourceInstance):
    """
    Resource instance that provides web browsing capabilities using curl.

    This class implements the standard .query(arg) method where arg is the URL
    to browse. It uses curl to fetch content and returns structured data.
    """

    def __init__(self, resource_type: "BrowserResourceType", values: dict[str, Any] | None = None):
        """
        Initialize BrowserResourceInstance.

        Args:
            resource_type: The BrowserResourceType that defines this instance
            values: Additional field values for the resource instance
        """
        # Set the kind attribute for resource identification
        self.kind = "browser"

        # Initialize with the provided resource type and values
        super().__init__(resource_type, values or {})

    def query(self, url: str) -> dict[str, Any]:  # type: ignore
        """
        Browse a URL and return its contents.

        This is the standard method that all resources should implement.

        Args:
            url: The URL to browse

        Returns:
            Dictionary containing the response data, status, and metadata

        Raises:
            ValueError: If URL is invalid or empty
            RuntimeError: If curl command fails
        """
        if not url or not url.strip():
            raise ValueError("URL cannot be empty")

        # Validate URL format
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError(f"Invalid URL format: {url}")

        # Ensure URL has a scheme
        if not parsed_url.scheme:
            url = f"https://{url}"

        try:
            # Build curl command
            curl_cmd = self._build_curl_command(url)

            # Execute curl command
            result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=self.timeout)

            # Process the response
            return self._process_curl_response(result, url)

        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Request timed out after {self.timeout} seconds")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"curl command failed: {e.stderr}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error during request: {str(e)}")

    def _build_curl_command(self, url: str) -> list[str]:
        """Build the curl command with appropriate options.

        Args:
            url: The URL to fetch

        Returns:
            List of command arguments for subprocess
        """
        cmd = ["curl", "-s", "-L"]  # Silent mode, follow redirects

        # Add user agent
        cmd.extend(["-A", self.user_agent])

        # Add timeout
        cmd.extend(["--max-time", str(self.timeout)])

        # Handle redirects
        if self.follow_redirects:
            cmd.extend(["--max-redirs", str(self.max_redirects)])
        else:
            cmd.append("--location-trusted")

        # Handle SSL verification
        if not self.verify_ssl:
            cmd.append("-k")

        # Add headers for better compatibility
        cmd.extend(
            [
                "-H",
                "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "-H",
                "Accept-Language: en-US,en;q=0.5",
                "-H",
                "Accept-Encoding: gzip, deflate",
                "-H",
                "Connection: keep-alive",
            ]
        )

        # Add the URL
        cmd.append(url)

        return cmd

    def _process_curl_response(self, result: subprocess.CompletedProcess, url: str) -> dict[str, Any]:  # type: ignore
        """Process the curl response and return structured data.

        Args:
            result: The completed subprocess result
            url: The original URL that was requested

        Returns:
            Dictionary containing response data and metadata
        """
        response_data = {
            "url": url,
            "status_code": result.returncode,
            "success": result.returncode == 0,
            "content": result.stdout,
            "error": result.stderr if result.stderr else None,
            "content_length": len(result.stdout),
            "metadata": {
                "user_agent": self.user_agent,
                "timeout": self.timeout,
                "follow_redirects": self.follow_redirects,
                "verify_ssl": self.verify_ssl,
            },
        }

        # Try to extract additional metadata from curl output
        if result.returncode == 0:
            response_data["content_type"] = self._detect_content_type(result.stdout)
            response_data["is_html"] = self._is_html_content(result.stdout)
            response_data["is_json"] = self._is_json_content(result.stdout)

            # If it's JSON, try to parse it
            if response_data["is_json"]:
                try:
                    response_data["parsed_json"] = json.loads(result.stdout)
                except json.JSONDecodeError:
                    response_data["json_parse_error"] = "Failed to parse JSON content"

        return response_data

    def _detect_content_type(self, content: str) -> str:
        """Detect the content type based on content analysis.

        Args:
            content: The response content

        Returns:
            Detected content type
        """
        content_lower = content.lower().strip()

        if content_lower.startswith("<!doctype html") or content_lower.startswith("<html"):
            return "text/html"
        elif content_lower.startswith("{") or content_lower.startswith("["):
            return "application/json"
        elif content_lower.startswith("<?xml"):
            return "application/xml"
        elif content_lower.startswith("<"):
            return "text/xml"
        else:
            return "text/plain"

    def _is_html_content(self, content: str) -> bool:
        """Check if content is HTML.

        Args:
            content: The response content

        Returns:
            True if content appears to be HTML
        """
        content_lower = content.lower().strip()
        return content_lower.startswith("<!doctype html") or content_lower.startswith("<html") or "<html" in content_lower

    def _is_json_content(self, content: str) -> bool:
        """Check if content is JSON.

        Args:
            content: The response content

        Returns:
            True if content appears to be JSON
        """
        content_stripped = content.strip()
        return (content_stripped.startswith("{") and content_stripped.endswith("}")) or (
            content_stripped.startswith("[") and content_stripped.endswith("]")
        )

    def get_status(self) -> str:
        """Get the current status of the browser resource.

        Returns:
            Current status string
        """
        return self.state

    def start(self) -> bool:
        """Start the browser resource (no-op for this resource)."""
        self.state = "ACTIVE"
        return True

    def stop(self) -> bool:
        """Stop the browser resource (no-op for this resource)."""
        self.state = "STOPPED"
        return True

    def shutdown(self) -> bool:
        """Shutdown the browser resource (no-op for this resource)."""
        self.state = "STOPPED"
        return True

    def restart(self) -> bool:
        """Restart the browser resource."""
        self.stop()
        self.start()
        return True

    def startup(self) -> bool:
        """Startup the browser resource (no-op for this resource)."""
        self.state = "ACTIVE"
        return True

    def health_check(self) -> dict[str, Any]:  # type: ignore
        """Perform a health check on the browser resource.

        Returns:
            Dictionary containing health check results
        """
        try:
            # Test with a simple URL
            test_url = "https://httpbin.org/get"
            result = self.query(test_url)

            return {
                "status": "healthy",
                "test_url": test_url,
                "test_successful": result["success"],
                "response_time": "unknown",  # Could be enhanced to measure actual time
                "last_check": time.time(),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": time.time(),
            }

    def get_capabilities(self) -> dict[str, Any]:  # type: ignore
        """Get the capabilities of this browser resource.

        Returns:
            Dictionary describing the resource capabilities
        """
        return {
            "can_browse": True,
            "supports_https": True,
            "supports_redirects": self.follow_redirects,
            "max_redirects": self.max_redirects,
            "timeout_seconds": self.timeout,
            "user_agent": self.user_agent,
            "ssl_verification": self.verify_ssl,
            "supported_methods": ["query"],
            "content_types": ["text/html", "application/json", "text/plain", "application/xml"],
        }


# Convenience function for creating a default browser resource
def create_browser_resource() -> BrowserResourceInstance:
    """Create a default browser resource instance.

    Returns:
        Default BrowserResourceInstance
    """
    return BrowserResourceType.create_default_instance()
