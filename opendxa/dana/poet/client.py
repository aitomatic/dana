"""POET Client - Unified local/remote API with .env configuration"""

import os
from typing import Any, Dict, Optional
from pathlib import Path

from opendxa.common.utils.logging import DXA_LOGGER
from opendxa.api.client import APIClient, APIConnectionError, APIServiceError
from .types import POETConfig, TranspiledFunction, POETResult, POETServiceError, POETTranspilationError


class POETClient:
    """POET client supporting both local and remote execution with unified API"""

    def __init__(self, config_path: Optional[str] = None):
        # Load configuration from .env file (generalized for all Aitomatic services)
        self._load_config(config_path)

        # Determine execution mode
        self.local_mode = self.service_uri == "local"

        DXA_LOGGER.info(f"POET Client initialized in {'local' if self.local_mode else 'remote'} mode")

        if self.local_mode:
            self._setup_local_mode()
        else:
            self._setup_remote_mode()

    def _load_config(self, config_path: Optional[str] = None):
        """Load configuration from .env file"""
        if config_path:
            # Load from specific file if provided
            from dotenv import load_dotenv

            load_dotenv(config_path)

        # Generalized configuration for all Aitomatic services
        self.service_uri = os.getenv("AITOMATIC_API_URL", "local")
        self.api_key = os.getenv("AITOMATIC_API_KEY")

        DXA_LOGGER.debug(f"Configuration loaded: service_uri={self.service_uri}, api_key={'***' if self.api_key else None}")

    def _setup_local_mode(self):
        """Setup for local transpilation mode"""
        try:
            from .transpiler import LocalPOETTranspiler

            self.transpiler = LocalPOETTranspiler()
            DXA_LOGGER.info("Local POET transpiler initialized")
        except ImportError as e:
            raise POETServiceError(f"Local transpiler not available: {e}")

    def _setup_remote_mode(self):
        """Setup for remote API mode"""
        if not self.service_uri or self.service_uri == "local":
            raise POETServiceError("AITOMATIC_API_URL must be set for remote mode")

        self.api_client = APIClient(base_uri=self.service_uri, api_key=self.api_key)

        # Verify connection with fail-fast behavior
        if not self.api_client.health_check():
            raise POETServiceError(f"POET service not available at {self.service_uri}. Check AITOMATIC_API_URL or use 'local' mode.")

        DXA_LOGGER.info(f"Connected to remote POET service at {self.service_uri}")

    def transpile_function(self, function_code: str, config: POETConfig, context: Optional[Dict[str, Any]] = None) -> TranspiledFunction:
        """Unified API - transpile function using local or remote execution with fail-fast behavior"""

        if self.local_mode:
            return self._transpile_local(function_code, config, context)
        else:
            return self._transpile_remote(function_code, config, context)

    def _transpile_local(self, function_code: str, config: POETConfig, context: Optional[Dict[str, Any]] = None) -> TranspiledFunction:
        """Local transpilation using embedded transpiler"""
        try:
            return self.transpiler.transpile_function(function_code, config, context)
        except Exception as e:
            DXA_LOGGER.error(f"Local transpilation failed: {e}")
            raise POETTranspilationError(f"Local transpilation failed: {e}")

    def _transpile_remote(self, function_code: str, config: POETConfig, context: Optional[Dict[str, Any]] = None) -> TranspiledFunction:
        """Remote transpilation via API service"""
        request_data = {"function_code": function_code, "language": "python", "config": config.dict()}

        if context:
            request_data["context"] = context

        try:
            # Use /poet prefix for POET-specific endpoints
            response_data = self.api_client.post("/poet/transpile", request_data)
            return TranspiledFunction.from_response(response_data)

        except (APIConnectionError, APIServiceError) as e:
            # Re-raise API errors as POET errors with context
            raise POETTranspilationError(f"Remote transpilation failed: {e}")

    def feedback(self, result: POETResult, feedback_payload: Any) -> None:
        """Submit feedback for POET function execution"""
        if not isinstance(result, POETResult):
            raise POETServiceError("result must be a POETResult instance")

        execution_id = result._poet["execution_id"]
        function_name = result._poet["function_name"]

        DXA_LOGGER.info(f"Processing feedback for {function_name} execution {execution_id}")

        if self.local_mode:
            self._feedback_local(result, feedback_payload)
        else:
            self._feedback_remote(result, feedback_payload)

    def _feedback_local(self, result: POETResult, feedback_payload: Any) -> None:
        """Process feedback locally"""
        try:
            # Import feedback system
            from .feedback import AlphaFeedbackSystem

            feedback_system = AlphaFeedbackSystem()
            feedback_system.feedback(result, feedback_payload)

        except Exception as e:
            DXA_LOGGER.error(f"Local feedback processing failed: {e}")
            raise POETServiceError(f"Local feedback processing failed: {e}")

    def _feedback_remote(self, result: POETResult, feedback_payload: Any) -> None:
        """Process feedback via remote API"""
        request_data = {
            "execution_id": result._poet["execution_id"],
            "function_name": result._poet["function_name"],
            "feedback_payload": feedback_payload,
        }

        try:
            self.api_client.post("/poet/feedback", request_data)
            DXA_LOGGER.info("Remote feedback submitted successfully")

        except (APIConnectionError, APIServiceError) as e:
            raise POETServiceError(f"Remote feedback submission failed: {e}")

    def get_function_status(self, function_name: str) -> Dict[str, Any]:
        """Get status information for a POET function"""
        if self.local_mode:
            # For local mode, check file system
            poet_dir = Path(".poet") / function_name
            if not poet_dir.exists():
                return {"status": "not_found", "function_name": function_name}

            current_link = poet_dir / "current"
            if current_link.exists() and current_link.is_symlink():
                current_version = current_link.readlink().name
                return {
                    "status": "available",
                    "function_name": function_name,
                    "current_version": current_version,
                    "local_path": str(poet_dir),
                }

            return {"status": "invalid", "function_name": function_name}
        else:
            # For remote mode, query service
            try:
                return self.api_client.get(f"/poet/functions/{function_name}")
            except (APIConnectionError, APIServiceError) as e:
                raise POETServiceError(f"Failed to get function status: {e}")

    def close(self):
        """Clean up resources"""
        if hasattr(self, "api_client"):
            self.api_client.close()


# Global client instance for convenience
_default_client: Optional[POETClient] = None


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
