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
from dana.common.config import ConfigLoader
from dana.common.mixins.loggable import Loggable

from ..core.database import Base, engine


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
    from ..core.migrations import run_migrations

    # Create base tables first
    Base.metadata.create_all(bind=engine)

    # Run any pending migrations
    run_migrations()

    yield

    # Shutdown (if needed in the future)
    pass


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
    from ..routers.agent_test import router as agent_test_router
    from ..routers.agents import router as agents_router

    # Legacy routers (for endpoints not yet migrated)
    from ..routers.api import router as api_router
    from ..routers.chat import router as new_chat_router
    from ..routers.conversations import router as new_conversations_router
    from ..routers.documents import router as new_documents_router
    from ..routers.domain_knowledge import router as domain_knowledge_router
    from ..routers.extract_documents import router as extract_documents_router
    from ..routers.main import router as main_router
    from ..routers.poet import router as poet_router
    from ..routers.smart_chat import router as smart_chat_router
    from ..routers.topics import router as new_topics_router

    app.include_router(main_router)

    # Use new consolidated routers
    app.include_router(agents_router, prefix="/api")
    app.include_router(new_chat_router, prefix="/api")
    app.include_router(new_conversations_router, prefix="/api")
    app.include_router(new_documents_router, prefix="/api")
    app.include_router(new_topics_router, prefix="/api")
    app.include_router(poet_router, prefix="/api")
    app.include_router(domain_knowledge_router, prefix="/api")
    if os.getenv("USE_SMART_CHAT_V2", "true").lower() == "true":
        from ..routers.smart_chat_v2 import router as smart_chat_v2_router

        app.include_router(smart_chat_v2_router, prefix="/api")
        print("\033[92mInitializing smart chat v2 router\033[0m")
    else:
        app.include_router(smart_chat_router, prefix="/api")
        print("\033[96mInitializing smart chat router\033[0m")
    app.include_router(extract_documents_router, prefix="/api")
    app.include_router(ws_router)

    # Keep legacy api router for endpoints not yet migrated:
    # - /run-na-file - Run Dana files
    # - /write-files - Write multi-file projects to disk
    # - /write-files-temp - Write multi-file projects to temp directory
    # - /validate-multi-file - Validate multi-file project structure
    # - /open-agent-folder - Open agent folder in file explorer
    # - /task-status/{task_id} - Get background task status
    # - /deep-train - Perform deep training on agents
    app.include_router(api_router, prefix="/api/legacy")
    app.include_router(agent_test_router, prefix="/api")

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
        # Serve index.html for all other routes
        from fastapi.responses import FileResponse, JSONResponse

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
