"""POET Client - Remote API client for POET service"""

import os
from typing import Any

from opendxa.api.client import APIClient, APIConnectionError, APIServiceError
from opendxa.common.utils.logging import DXA_LOGGER

from .types import POETConfig, POETResult, POETServiceError, POETTranspilationError, TranspiledFunction


class POETClient:
    """POET client for remote API service"""

    def __init__(self, config_path: str | None = None):
        # Load configuration from .env file
        self._load_config(config_path)

        # Setup API client
        self._setup_api_client()

    def _load_config(self, config_path: str | None = None):
        """Load configuration from .env file"""
        if config_path:
            # Load from specific file if provided
            from dotenv import load_dotenv

            load_dotenv(config_path)

        # Get service configuration
        service_uri = os.getenv("AITOMATIC_API_URL")
        if not service_uri:
            raise POETServiceError("AITOMATIC_API_URL must be set")
        self.service_uri = service_uri

        self.api_key = os.getenv("AITOMATIC_API_KEY")

        DXA_LOGGER.debug(f"Configuration loaded: service_uri={self.service_uri}, api_key={'***' if self.api_key else None}")

    def _setup_api_client(self):
        """Setup API client and verify connection"""
        self.api_client = APIClient(base_uri=self.service_uri, api_key=self.api_key)

        # Verify connection with fail-fast behavior
        if not self.api_client.health_check():
            raise POETServiceError(f"POET service not available at {self.service_uri}")

        DXA_LOGGER.info(f"Connected to POET service at {self.service_uri}")

    def transpile_function(self, function_code: str, config: POETConfig, context: dict[str, Any] | None = None) -> TranspiledFunction:
        """Transpile function using remote POET service"""
        request_data = {"function_code": function_code, "language": "python", "config": config.dict()}  # Default to Python for now

        if context:
            request_data["context"] = context

        try:
            # Use /poet prefix for POET-specific endpoints
            response_data = self.api_client.post("/poet/transpile", request_data)
            return TranspiledFunction.from_response(response_data)

        except (APIConnectionError, APIServiceError) as e:
            raise POETTranspilationError(f"Remote transpilation failed: {e}")

    def feedback(self, result: POETResult, feedback_payload: Any) -> None:
        """Submit feedback for POET function execution"""
        if not isinstance(result, POETResult):
            raise POETServiceError("result must be a POETResult instance")

        execution_id = result._poet["execution_id"]
        function_name = result._poet["function_name"]

        DXA_LOGGER.info(f"Processing feedback for {function_name} execution {execution_id}")

        request_data = {
            "execution_id": execution_id,
            "function_name": function_name,
            "feedback_payload": feedback_payload,
        }

        try:
            self.api_client.post("/poet/feedback", request_data)
            DXA_LOGGER.info("Feedback submitted successfully")

        except (APIConnectionError, APIServiceError) as e:
            raise POETServiceError(f"Feedback submission failed: {e}")

    def get_function_status(self, function_name: str) -> dict[str, Any]:
        """Get status information for a POET function"""
        try:
            return self.api_client.get(f"/poet/functions/{function_name}")
        except (APIConnectionError, APIServiceError) as e:
            raise POETServiceError(f"Failed to get function status: {e}")

    def close(self):
        """Clean up resources"""
        if hasattr(self, "api_client"):
            self.api_client.close()


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
