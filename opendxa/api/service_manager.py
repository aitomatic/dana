"""API Service Manager - Manages local API server lifecycle"""

import os
import socket
import subprocess
import time
from typing import Any, cast

from opendxa.common.config import ConfigLoader
from opendxa.common.mixins.loggable import Loggable
from opendxa.common.utils.logging import DXA_LOGGER

from .client import APIClient


class APIServiceManager(Loggable):
    """Manages API server lifecycle for DanaSandbox sessions"""

    def __init__(self):
        super().__init__()  # Initialize Loggable mixin
        self.service_uri: str | None = None
        self.api_key: str | None = None
        self.server_process: subprocess.Popen | None = None
        self._started = False
        self.api_client = None
        self._load_config()

    def startup(self) -> None:
        """Start API service based on environment configuration"""
        if self._started:
            return

        # Check service health
        if not self.check_health():
            raise RuntimeError("Service is not healthy")

        if self.local_mode:
            self._start_local_server()
        else:
            # Remote mode - just validate connection
            self._validate_remote_connection()

        self._started = True
        self.info(f"API Service Manager started - {self.service_uri}")

    def shutdown(self) -> None:
        """Stop API service and cleanup"""
        if not self._started:
            return

        if self.server_process:
            self.info("Stopping local API server")
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.warning("Local server didn't stop gracefully, killing")
                self.server_process.kill()
            self.server_process = None

        self._started = False
        self.info("API Service Manager shut down")

    def get_client(self) -> APIClient:
        """Get API client connected to the managed service"""
        if not self._started:
            raise RuntimeError("Service manager not started. Call startup() first.")

        return APIClient(base_uri=cast(str, self.service_uri), api_key=self.api_key)

    @property
    def local_mode(self) -> bool:
        """Check if running in local mode"""
        if not self.service_uri:
            return False
        return self.service_uri == "local" or "localhost" in self.service_uri

    def _load_config(self) -> None:
        """Load configuration from environment"""
        config = ConfigLoader()
        config_data: dict[str, Any] = config.get_default_config() or {}

        # Get service URI
        self.service_uri = config_data.get("AITOMATIC_API_URL")
        if not self.service_uri:
            # Launch embedded server at random port
            port = self._find_free_port()
            self.service_uri = f"http://localhost:{port}"
            os.environ["AITOMATIC_API_URL"] = self.service_uri

        # Get API key
        self.api_key = config_data.get("AITOMATIC_API_KEY")
        if not self.api_key:
            if self.local_mode:
                # In local mode, use a default API key
                self.api_key = "local"
                os.environ["AITOMATIC_API_KEY"] = self.api_key
            else:
                raise ValueError("AITOMATIC_API_KEY environment variable must be set")

        # Initialize API client
        self._init_api_client()

        DXA_LOGGER.info(f"Service config loaded: uri={self.service_uri}")

    def _init_api_client(self) -> None:
        """Initialize API client with configuration."""
        from opendxa.api.client import APIClient

        if not self.service_uri:
            raise ValueError("Service URI must be set before initializing API client")
        self.api_client = APIClient(base_uri=cast(str, self.service_uri), api_key=self.api_key)

    def _start_local_server(self) -> None:
        """Start local API server on available port"""
        # Determine port
        if self.service_uri and ":" in self.service_uri:
            # Extract port from localhost:port
            try:
                port = int(self.service_uri.split(":")[-1])
            except ValueError:
                port = self._find_free_port()
        else:
            port = self._find_free_port()

        # Update service URI to actual port
        self.service_uri = f"http://localhost:{port}"

        # Start server process
        try:
            # Use uvicorn to start the FastAPI server
            cmd = [
                "uvicorn",
                "opendxa.api.server:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
                "--log-level",
                "warning",  # Reduce noise
            ]

            self.info(f"Starting local API server on port {port}")
            self.server_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            # Wait for server to be ready
            self._wait_for_server_ready(port)

        except Exception as e:
            self.error(f"Failed to start local API server: {e}")
            raise RuntimeError(f"Could not start local API server: {e}")

    def _find_free_port(self) -> int:
        """Find an available port for the local server"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]

    def _wait_for_server_ready(self, port: int, timeout: int = 30) -> None:
        """Wait for server to be ready to accept connections"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1)
                    result = s.connect_ex(("127.0.0.1", port))
                    if result == 0:
                        self.info(f"Local API server ready on port {port}")
                        return
            except Exception:
                pass

            time.sleep(0.5)

        raise RuntimeError(f"Local API server did not start within {timeout} seconds")

    def _validate_remote_connection(self) -> None:
        """Validate that remote service is accessible"""
        if not self.service_uri:
            raise RuntimeError("AITOMATIC_API_URL must be set for remote mode")

        # Basic validation - actual connection test will be done by APIClient
        self.info(f"Using remote API service: {self.service_uri}")

    def __enter__(self) -> "APIServiceManager":
        self.startup()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.shutdown()

    def check_health(self) -> bool:
        """Check if service is healthy."""
        if not self.api_client:
            self._init_api_client()

        try:
            if not self.api_client:
                return False
            response = self.api_client.get("/health")
            return response.get("status") == "healthy"
        except Exception as e:
            DXA_LOGGER.error(f"Health check failed: {str(e)}")
            return False

    def get_service_uri(self) -> str:
        """Get service URI."""
        return cast(str, self.service_uri)

    def get_api_key(self) -> str:
        """Get API key."""
        return cast(str, self.api_key)
