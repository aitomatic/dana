"""OpenDXA Server - Generic API server infrastructure"""

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from opendxa.common.mixins.loggable import Loggable


class OpenDXAServer(Loggable):
    """Generic OpenDXA API server supporting multiple services"""

    def __init__(self, host: str = "localhost", port: int = 8080, title: str = "OpenDXA API Server"):
        super().__init__()  # Initialize Loggable mixin
        self.host = host
        self.port = port
        self.title = title

        # Create FastAPI app with lifespan management
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            self.info(f"Starting {self.title} on {self.host}:{self.port}")
            yield
            self.info(f"Shutting down {self.title}")

        self.app = FastAPI(title=self.title, description="Generic API server for OpenDXA services", version="1.0.0", lifespan=lifespan)

        # Add CORS middleware for local development
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        self._setup_health_routes()
        self._setup_service_routes()

    def _setup_health_routes(self):
        """Setup basic health check endpoints"""

        @self.app.get("/health")
        async def health_check():
            """Basic health check endpoint"""
            return {"status": "healthy", "service": "opendxa-api"}

        @self.app.get("/")
        async def root():
            """Root endpoint with service information"""
            return {"service": self.title, "version": "1.0.0", "status": "running", "endpoints": {"health": "/health", "poet": "/poet/*"}}

    def _setup_service_routes(self):
        """Setup routes for specific OpenDXA services"""
        try:
            # Try to import and register POET routes
            from opendxa.api.poet_routes import router as poet_router

            self.app.include_router(poet_router, prefix="/poet", tags=["POET"])
            self.info("POET routes registered successfully")
        except ImportError as e:
            self.warning(f"POET routes not available: {e}")

        # Future services can be added here:
        # try:
        #     from opendxa.magic_functions.routes import router as magic_router
        #     self.app.include_router(magic_router, prefix="/magic", tags=["MagicFunctions"])
        # except ImportError:
        #     self.warning("MagicFunctions routes not available")

    def start(self, reload: bool = False, log_level: str = "info", workers: int | None = None):
        """Start the server with uvicorn"""
        try:
            self.info(f"Starting OpenDXA server on http://{self.host}:{self.port}")
            uvicorn.run(
                self.app,
                host=self.host,
                port=self.port,
                reload=reload,
                log_level=log_level,
                workers=workers,
                access_log=False,  # Reduce noise for local development
            )
        except Exception as e:
            self.error(f"Failed to start server: {e}")
            raise

    def run_dev(self):
        """Start development server with reload enabled"""
        self.start(reload=True, log_level="debug")


def create_server(host: str = "localhost", port: int = 8080) -> OpenDXAServer:
    """Factory function to create OpenDXA server instance"""
    return OpenDXAServer(host=host, port=port)


# Standalone FastAPI app instance for direct uvicorn usage
app = create_server().app


# CLI entry point for starting the server
def main():
    """Main entry point for CLI usage"""
    import argparse

    parser = argparse.ArgumentParser(description="OpenDXA API Server")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--workers", type=int, help="Number of worker processes")

    args = parser.parse_args()

    server = OpenDXAServer(host=args.host, port=args.port)
    server.start(reload=args.reload, workers=args.workers)


if __name__ == "__main__":
    main()
