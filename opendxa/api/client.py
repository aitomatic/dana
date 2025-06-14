"""OpenDXA Client - Generic API client utilities"""

from typing import Dict, Any, Optional
import httpx
from opendxa.common.utils.logging import DXA_LOGGER


class APIClientError(Exception):
    """Base exception for API client errors"""

    pass


class APIConnectionError(APIClientError):
    """Raised when connection to API fails"""

    pass


class APIServiceError(APIClientError):
    """Raised when API returns an error response"""

    pass


class APIClient:
    """Generic API client for OpenDXA services with fail-fast behavior"""

    def __init__(self, base_uri: str, api_key: Optional[str] = None, timeout: float = 30.0):
        self.base_uri = base_uri.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

        # Setup headers
        headers = {"Content-Type": "application/json", "User-Agent": "OpenDXA-Client/1.0"}

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        # Create httpx client with configured timeout
        self.session = httpx.Client(base_url=self.base_uri, timeout=self.timeout, headers=headers)

        DXA_LOGGER.debug(f"APIClient initialized for {self.base_uri}")

    def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """POST request with standardized error handling and fail-fast behavior"""
        endpoint = endpoint.lstrip("/")
        url = f"/{endpoint}"

        try:
            DXA_LOGGER.debug(f"POST {self.base_uri}{url}")
            response = self.session.post(url, json=data)
            response.raise_for_status()

            result = response.json()
            DXA_LOGGER.debug(f"POST {url} succeeded")
            return result

        except httpx.RequestError as e:
            # Network/connection errors - fail fast
            error_msg = f"Connection failed to {self.base_uri}: {e}"
            DXA_LOGGER.error(error_msg)
            raise APIConnectionError(error_msg) from e

        except httpx.HTTPStatusError as e:
            # HTTP error responses - fail fast with details
            try:
                error_detail = e.response.json().get("detail", e.response.text)
            except Exception:
                error_detail = e.response.text

            error_msg = f"Service error ({e.response.status_code}): {error_detail}"
            DXA_LOGGER.error(f"POST {url} failed: {error_msg}")
            raise APIServiceError(error_msg) from e

        except Exception as e:
            # Unexpected errors - fail fast
            error_msg = f"Unexpected error during POST {url}: {e}"
            DXA_LOGGER.error(error_msg)
            raise APIClientError(error_msg) from e

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """GET request with standardized error handling"""
        endpoint = endpoint.lstrip("/")
        url = f"/{endpoint}"

        try:
            DXA_LOGGER.debug(f"GET {self.base_uri}{url}")
            response = self.session.get(url, params=params)
            response.raise_for_status()

            result = response.json()
            DXA_LOGGER.debug(f"GET {url} succeeded")
            return result

        except httpx.RequestError as e:
            error_msg = f"Connection failed to {self.base_uri}: {e}"
            DXA_LOGGER.error(error_msg)
            raise APIConnectionError(error_msg) from e

        except httpx.HTTPStatusError as e:
            try:
                error_detail = e.response.json().get("detail", e.response.text)
            except Exception:
                error_detail = e.response.text

            error_msg = f"Service error ({e.response.status_code}): {error_detail}"
            DXA_LOGGER.error(f"GET {url} failed: {error_msg}")
            raise APIServiceError(error_msg) from e

        except Exception as e:
            error_msg = f"Unexpected error during GET {url}: {e}"
            DXA_LOGGER.error(error_msg)
            raise APIClientError(error_msg) from e

    def health_check(self) -> bool:
        """Check if the API service is healthy"""
        try:
            result = self.get("/health")
            return result.get("status") == "healthy"
        except Exception as e:
            DXA_LOGGER.warning(f"Health check failed: {e}")
            return False

    def close(self):
        """Close the HTTP session"""
        if hasattr(self, "session"):
            self.session.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


def create_client(base_uri: str, api_key: Optional[str] = None) -> APIClient:
    """Factory function to create API client instance"""
    return APIClient(base_uri=base_uri, api_key=api_key)
