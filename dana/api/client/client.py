"""Dana Client - Generic API client utilities"""

from typing import Any, cast

import httpx

from dana.common.mixins.loggable import Loggable


class APIClientError(Exception):
    """Base exception for API client errors"""

    pass


class APIConnectionError(APIClientError):
    """Raised when connection to API fails"""

    pass


class APIServiceError(APIClientError):
    """Raised when API returns an error response"""

    pass


class APIClient(Loggable):
    """Generic API client for Dana
    services with fail-fast behavior"""

    def __init__(self, base_uri: str, api_key: str | None = None, timeout: float = 30.0):
        super().__init__()  # Initialize Loggable mixin
        self.base_uri = base_uri.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.session: httpx.Client | None = None
        self._started = False

        self.debug(f"APIClient initialized for {self.base_uri}")

    def startup(self) -> None:
        """Initialize the HTTP session and validate connection"""
        if self._started:
            return

        # Setup headers
        headers = {"Content-Type": "application/json", "User-Agent": "Dana-Client/1.0"}

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        # Create httpx client with configured timeout
        self.session = httpx.Client(base_url=self.base_uri, timeout=self.timeout, headers=headers)

        # Validate connection with health check
        if not self.health_check():
            raise APIConnectionError(f"API service not available at {self.base_uri}")

        self._started = True
        self.info(f"APIClient connected to {self.base_uri}")

    def shutdown(self) -> None:
        """Close the HTTP session and cleanup"""
        if not self._started:
            return

        if self.session:
            self.session.close()
            self.session = None

        self._started = False
        self.info(f"APIClient disconnected from {self.base_uri}")

    def _ensure_started(self) -> None:
        """Ensure client is started before making requests"""
        if not self._started or self.session is None:
            raise RuntimeError("APIClient not started. Call startup() first.")

    def post(self, endpoint: str, data: dict[str, Any]) -> dict[str, Any]:
        """POST request with standardized error handling and fail-fast behavior"""
        self._ensure_started()
        endpoint = endpoint.lstrip("/")
        url = f"/{endpoint}"

        try:
            self.debug(f"POST {self.base_uri}{url}")
            response = cast(httpx.Response, self.session).post(url, json=data)
            response.raise_for_status()

            result = response.json()
            self.debug(f"POST {url} succeeded")
            return result

        except httpx.RequestError as e:
            # Network/connection errors - fail fast
            error_msg = f"Connection failed to {self.base_uri}: {e}"
            self.error(error_msg)
            raise APIConnectionError(error_msg) from e

        except httpx.HTTPStatusError as e:
            # HTTP error responses - fail fast with details
            try:
                error_detail = e.response.json().get("detail", e.response.text)
            except Exception:
                error_detail = e.response.text

            error_msg = f"Service error ({e.response.status_code}): {error_detail}"
            self.error(f"POST {url} failed: {error_msg}")
            raise APIServiceError(error_msg) from e

        except Exception as e:
            # Unexpected errors - fail fast
            error_msg = f"Unexpected error during POST {url}: {e}"
            self.error(error_msg)
            raise APIClientError(error_msg) from e

    def get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """GET request with standardized error handling"""
        self._ensure_started()
        endpoint = endpoint.lstrip("/")
        url = f"/{endpoint}"

        try:
            self.debug(f"GET {self.base_uri}{url}")
            response = cast(httpx.Response, self.session).get(url, params=params)
            response.raise_for_status()

            result = response.json()
            self.debug(f"GET {url} succeeded")
            return result

        except httpx.RequestError as e:
            error_msg = f"Connection failed to {self.base_uri}: {e}"
            self.error(error_msg)
            raise APIConnectionError(error_msg) from e

        except httpx.HTTPStatusError as e:
            try:
                error_detail = e.response.json().get("detail", e.response.text)
            except Exception:
                error_detail = e.response.text

            error_msg = f"Service error ({e.response.status_code}): {error_detail}"
            self.error(f"GET {url} failed: {error_msg}")
            raise APIServiceError(error_msg) from e

        except Exception as e:
            error_msg = f"Unexpected error during GET {url}: {e}"
            self.error(error_msg)
            raise APIClientError(error_msg) from e

    def health_check(self) -> bool:
        """Check if the API service is healthy"""
        try:
            # Always use direct session access to avoid _ensure_started() circular dependency
            if self.session is None:
                headers = {"Content-Type": "application/json", "User-Agent": "Dana-Client/1.0"}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"
                temp_session = httpx.Client(base_url=self.base_uri, timeout=self.timeout, headers=headers)
                try:
                    response = temp_session.get("/health")
                    result = response.json()
                    return result.get("status") == "healthy"
                finally:
                    temp_session.close()
            else:
                # Use session directly to avoid _ensure_started() circular dependency during startup
                response = self.session.get("/health")
                response.raise_for_status()
                result = response.json()
                return result.get("status") == "healthy"
        except Exception as e:
            self.warning(f"Health check failed: {e}")
            return False

    def close(self):
        """Close the HTTP session"""
        if hasattr(self, "session"):
            cast(httpx.Client, self.session).close()

    def __enter__(self):
        """Context manager entry"""
        self.startup()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.shutdown()


def create_client(base_uri: str, api_key: str | None = None) -> APIClient:
    """Factory function to create API client instance"""
    return APIClient(base_uri=base_uri, api_key=api_key)
