"""POET Client - Remote API client for POET service"""

import os

from dana.api.client import APIClient
from dana.frameworks.poet.types import POETConfig


class POETClient:
    """POET client for remote API service"""

    def __init__(self, base_url: str | None = None):
        # Default to local service if URL not provided
        self.api = APIClient(base_url or os.getenv("POET_API_URL", "http://localhost:12345"))

    def transpile(self, code: str, config: POETConfig) -> dict:
        """Transpile function using remote POET service"""
        response = self.api.post(
            "/poet/transpile",
            {"code": code, "config": config.dict()},
        )
        return response


# Global client instance for convenience
_default_client: POETClient | None = None


def get_default_client() -> POETClient:
    """Get or create the default POET client instance"""
    global _default_client
    if _default_client is None:
        _default_client = POETClient()
    return _default_client


def set_default_client(client: POETClient):
    """Set the default POET client instance"""
    global _default_client
    _default_client = client
