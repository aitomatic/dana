"""Dana API Server - Manages API server lifecycle and routes"""

import os
import socket
import subprocess
import sys
import time
from contextlib import asynccontextmanager
from typing import Any, cast

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from dana.api.client import APIClient
from dana.api.core.bc_engine import broadcast_engine
from dana.api.background.task_manager import get_task_manager, shutdown_task_manager
from dana.common.config import ConfigLoader
from dana.common.mixins.loggable import Loggable
from alembic.config import Config
from alembic import command
from pathlib import Path
from ..core.database import Base, engine, SQLALCHEMY_DATABASE_URL


def run_migrations():
    package_dir = Path(__file__).parent.parent
    script_location = package_dir / "alembic"
    alembic_cfg = Config()
    alembic_cfg.set_main_option("sqlalchemy.url", SQLALCHEMY_DATABASE_URL)
    alembic_cfg.set_main_option("script_location", str(script_location))
    command.upgrade(alembic_cfg, "head")


# --- WebSocket manager for knowledge status updates ---
class KnowledgeStatusWebSocketManager:
    def __init__(self):
        self.clients = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.clients.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.clients.discard(websocket)

    async def broadcast(self, msg):
        to_remove = set()
        for ws in self.clients:
            try:
                await ws.send_json(msg)
            except Exception:
                to_remove.add(ws)
        for ws in to_remove:
            self.clients.discard(ws)


ws_manager = KnowledgeStatusWebSocketManager()

# WebSocket endpoint
from fastapi import APIRouter

ws_router = APIRouter()


@ws_router.websocket("/ws/knowledge-status")
async def knowledge_status_ws(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep alive
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events"""
    # Startup
    # from ..core.migrations import run_migrations

    try:
        # Run any pending migrations
        run_migrations()
    except Exception as e:
        print(f"Warning: Failed to run migrations: {e}. Creating base tables instead.")
        # Create base tables first
        Base.metadata.create_all(bind=engine)

    await broadcast_engine.connect()
    get_task_manager()  # INIT
    yield

    # Shutdown (if needed in the future)
    await broadcast_engine.disconnect()
    shutdown_task_manager()


def create_app():
    """Create FastAPI app with routers and static file serving"""
    app = FastAPI(title="Dana API Server", version="1.0.0", lifespan=lifespan)

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers under /api
    # New consolidated routers (preferred)
    from ..routers.v1 import router as v1_router
    from ..routers.main import router as main_router
    from ..routers.poet import router as poet_router
    from ..routers.v2 import router as v2_router

    app.include_router(main_router)

    # Use new consolidated routers
    app.include_router(poet_router, prefix="/api")
    app.include_router(ws_router)
    app.include_router(v2_router, prefix="/api/v2")
    app.include_router(v1_router, prefix="/api")

    # Serve static files (React build)
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # Catch-all route for SPA (serves index.html for all non-API, non-static routes)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # If the path starts with api or static, return 404 (should be handled by routers or static mount)
        if full_path.startswith("api") or full_path.startswith("static"):
            from fastapi.responses import JSONResponse

            return JSONResponse({"error": "Not found"}, status_code=404)

        from fastapi.responses import FileResponse, JSONResponse

        # Return image files directly
        if (
            full_path.endswith(".png")
            or full_path.endswith(".jpg")
            or full_path.endswith(".jpeg")
            or full_path.endswith(".gif")
            or full_path.endswith(".svg")
            or full_path.endswith(".ico")
        ):
            img_path = os.path.join(static_dir, full_path)
            if os.path.exists(img_path):
                return FileResponse(img_path)
            return JSONResponse({"error": f"Image {full_path} not found"}, status_code=404)

        # Serve index.html for all other routes

        index_path = os.path.join(static_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return JSONResponse({"error": "index.html not found"}, status_code=404)

    return app


# Default port for local API server
DEFAULT_LOCAL_PORT = 12345


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

        if self.local_mode:
            self._start_local_server()
        else:
            # Remote mode - just validate connection
            self._validate_remote_connection()

        # Check service health after starting
        if not self.check_health():
            raise RuntimeError("Service is not healthy")

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

        # Get service URI and determine port
        raw_uri = config_data.get("AITOMATIC_API_URL") or os.environ.get("AITOMATIC_API_URL")

        if not raw_uri:
            # Default to localhost with default port
            self.service_uri = f"localhost:{DEFAULT_LOCAL_PORT}"
        else:
            self.service_uri = raw_uri

        # Parse and normalize the URI
        self._normalize_service_uri()

        # Get API key
        self.api_key = config_data.get("AITOMATIC_API_KEY")
        if not self.api_key:
            if self.local_mode:
                # In local mode, use a default API key
                self.api_key = "local"
                os.environ["AITOMATIC_API_KEY"] = self.api_key
            else:
                raise ValueError("AITOMATIC_API_KEY environment variable must be set")

        self.info(f"Service config loaded: uri={self.service_uri}")

    def _normalize_service_uri(self) -> None:
        """Normalize service URI and determine port"""
        if not self.service_uri:
            self.service_uri = f"localhost:{DEFAULT_LOCAL_PORT}"
            return

        # Handle different URI formats
        if self.service_uri == "localhost":
            # localhost without port -> use default port DEFAULT_LOCAL_PORT
            self.service_uri = f"localhost:{DEFAULT_LOCAL_PORT}"
        elif self.service_uri.startswith("localhost:"):
            # localhost with port -> use as-is
            pass
        elif "localhost" in self.service_uri and ":" in self.service_uri:
            # http://localhost:port format -> extract localhost:port
            if "://" in self.service_uri:
                self.service_uri = self.service_uri.split("://")[1]
        elif not (":" in self.service_uri or self.service_uri.startswith("http")):
            # Just a hostname/IP without port -> assume remote with default port
            pass

        self.debug(f"Normalized service URI: {self.service_uri}")

    def _init_api_client(self) -> None:
        """Initialize API client with configuration."""
        from dana.api.client import APIClient

        if not self.service_uri:
            raise ValueError("Service URI must be set before initializing API client")
        self.api_client = APIClient(base_uri=cast(str, self.service_uri), api_key=self.api_key)

    def _start_local_server(self) -> None:
        """Start local API server or use existing one"""
        # Extract port from normalized URI (localhost:port)
        try:
            if self.service_uri and ":" in self.service_uri:
                port = int(self.service_uri.split(":")[-1])
            else:
                port = DEFAULT_LOCAL_PORT  # Default port
        except ValueError:
            port = DEFAULT_LOCAL_PORT  # Fallback to default

        # Convert to full HTTP URL
        full_uri = f"http://localhost:{port}"

        # Check if server is already running on this port
        if self._is_server_running(port):
            self.info(f"Found existing server on port {port}, using it")
            self.service_uri = full_uri
            os.environ["AITOMATIC_API_URL"] = full_uri
            self._init_api_client()
            return

        # No server running, start a new one
        self.info(f"Starting new API server on port {port}")

        try:
            # Use uvicorn to start the FastAPI server with integrated POET routes
            cmd = [
                sys.executable,
                "-m",
                "uvicorn",
                "dana.api.server.server:create_app",
                "--factory",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
                "--log-level",
                "warning",  # Reduce noise
            ]

            self.server_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            # Wait for server to be ready
            self._wait_for_server_ready(port)

            # Update service URI and environment to reflect reality
            self.service_uri = full_uri
            os.environ["AITOMATIC_API_URL"] = full_uri
            self._init_api_client()

        except Exception as e:
            self.error(f"Failed to start local API server: {e}")
            raise RuntimeError(f"Could not start local API server: {e}")

    def _is_server_running(self, port: int) -> bool:
        """Check if a server is already running on the specified port"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(("127.0.0.1", port))
                return result == 0
        except Exception:
            return False

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

        # Ensure full HTTP URL format for remote connections
        if not self.service_uri.startswith("http"):
            self.service_uri = f"https://{self.service_uri}"

        # Update environment to reflect the actual URL
        os.environ["AITOMATIC_API_URL"] = self.service_uri

        # Initialize API client for remote connection
        self._init_api_client()

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

            # Ensure API client is started before making requests
            if not self.api_client._started:
                self.api_client.startup()

            response = self.api_client.get("/health")
            return response.get("status") == "healthy"
        except Exception as e:
            self.error(f"Health check failed: {str(e)}")
            return False

    def get_service_uri(self) -> str:
        """Get service URI."""
        return cast(str, self.service_uri)

    def get_api_key(self) -> str:
        """Get API key."""
        return cast(str, self.api_key)
