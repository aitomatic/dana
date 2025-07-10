"""Dana API Server CLI entry point."""

import argparse
import sys

from .server import create_app


def main() -> None:
    """Main entry point for Dana API Server CLI."""
    parser = argparse.ArgumentParser(description="Dana API Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to (default: 8080)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload on code changes")
    parser.add_argument("--log-level", default="info", choices=["debug", "info", "warning", "error"], help="Log level (default: info)")

    args = parser.parse_args()

    # Import uvicorn here to avoid circular imports
    try:
        import uvicorn
    except ImportError:
        print("❌ uvicorn not installed. Install with: uv add uvicorn")
        sys.exit(1)

    # Create the FastAPI app
    app = create_app()

    # Start the server
    print(f"🌐 Starting Dana API server on http://{args.host}:{args.port}")
    print(f"📊 Health check: http://{args.host}:{args.port}/health")
    print(f"🔗 Root endpoint: http://{args.host}:{args.port}/")

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level,
    )


if __name__ == "__main__":
    main()
