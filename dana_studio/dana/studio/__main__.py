#!/usr/bin/env python3
"""
Dana Command Line Interface - Main Entry Point

ARCHITECTURE ROLE:
    This is the PRIMARY ENTRY POINT for all Dana operations, analogous to the 'python' command.
    It acts as a ROUTER that decides whether to:
    - Execute a .na file directly (file mode)
    - Launch the Terminal User Interface (TUI mode)

USAGE PATTERNS:
    dana                 # Start TUI → delegates to tui_app.py
    dana script.na       # Execute file → uses DanaSandbox directly
    dana --help         # Show help and usage information

DESIGN DECISIONS:
    - Single entry point for all Dana operations (consistency)
    - File execution bypasses TUI overhead (performance)
    - TUI delegation to specialized interactive application (separation of concerns)
    - Console script integration via pyproject.toml (standard Python packaging)

INTEGRATION:
    - Console script: 'dana' command → this file's main() function
    - File execution: Uses DanaSandbox.quick_run() for direct .na file processing
    - TUI mode: Imports and delegates to tui_app.main() for interactive experience

This script serves as the main entry point for the Dana language, similar to the python command.
It either starts the TUI when no arguments are provided, or executes a .na file when given.

Usage:
  dana                         Start the Dana Terminal User Interface
  dana [file.na]               Execute a Dana file
  dana deploy [file.na]        Deploy a .na file as an agent endpoint
      [--protocol mcp|a2a|restful]  Protocol to use (default: restful)
      [--host HOST]            Host to bind the server (default: 0.0.0.0)
      [--port PORT]            Port to bind the server (default: 8000)
  dana studio                  Start the Dana Agent Studio
      [--host HOST]            Host to bind the server (default: 127.0.0.1)
      [--port PORT]            Port to bind the server (default: 8080)
      [--reload]               Enable auto-reload for development
      [--log-level LEVEL]      Log level (default: info)
  dana repl                    Start the Dana Interactive REPL
  dana tui                     Start the Dana Terminal User Interface
  dana -h, --help              Show help message
  dana --version               Show version information
  dana --debug                 Enable debug logging
  dana --no-color              Disable colored output
  dana --force-color           Force colored output

Examples:
  dana script.na               Execute a Dana script
  dana deploy agent.na         Deploy an agent
  dana deploy agent.na --protocol mcp --port 9000
  dana studio --port 9000      Start studio on port 9000
  dana repl                    Start interactive REPL
"""

import argparse
import os
import sys
from pathlib import Path

import uvicorn

# Set up compatibility layer for new dana structure
# Resolve the real path to avoid symlink issues
real_file = os.path.realpath(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(real_file))))
sys.path.insert(0, project_root)

# Compatibility layer removed - direct Dana imports only

from dana.lang.common.terminal_utils import ColorScheme, supports_color

# Initialize color scheme
colors = ColorScheme(supports_color())


def show_help():
    """Display help information."""
    print(f"{colors.header('Dana Studio - A Web-based IDE for Domain-Aware Neurosymbolic Agents')}")
    print(f"{colors.bold('Commands:')}")
    print(f"  {colors.accent('dana-studio')}            Start the Dana Studio")
    print(f"    {colors.accent('--host HOST')}          Host to bind the server (default: 127.0.0.1)")
    print(f"    {colors.accent('--port PORT')}          Port to bind the server (default: 8080)")
    print(f"    {colors.accent('--reload')}             Enable auto-reload for development")
    print("")
    print(f"{colors.bold('Requirements:')}")
    print(f"  {colors.accent('🔑 API Keys:')} At least one LLM provider API key required")
    print("")


def build_frontend():
    """Build the frontend by running npm install and npm run build.

    This function detects whether we're running from a pip installation
    (where frontend is pre-built) or a development installation (where
    we need to build it).
    """
    import subprocess

    try:
        # Check if we're running from a pip installation
        # Pip installations are located in site-packages, not in the current directory
        import dana.studio as dana_studio

        is_pip_installation = "site-packages" in dana_studio.__file__

        if is_pip_installation:
            # Running from pip installation - frontend is already built
            print(f"{colors.accent('✅ Using pre-built frontend from pip installation')}")
            return True

        # Development installation - need to build frontend
        # Get the project root directory (where we are now)
        dana_studio_dir = Path(__file__).parent.parent.parent
        frontend_dir = dana_studio_dir / "dana" / "studio" / "contrib" / "ui"
        print(f"Frontend directory: {frontend_dir}")
        # Check if frontend directory exists
        if not frontend_dir.exists():
            print(f"{colors.error(f'❌ Frontend directory not found: {frontend_dir}')}")
            return False

        # Change to frontend directory and run npm install
        print(f"📦 Installing dependencies in {frontend_dir}...")
        subprocess.run(["npm", "install"], cwd=str(frontend_dir), capture_output=True, text=True, check=True)
        print(f"{colors.accent('✅ Dependencies installed successfully')}")

        # Run npm run build
        print("🔨 Building frontend...")
        subprocess.run(["npm", "run", "build"], cwd=str(frontend_dir), capture_output=True, text=True, check=True)
        print(f"{colors.accent('✅ Frontend built successfully')}")

        return True

    except subprocess.CalledProcessError as e:
        print(f"{colors.error('❌ Frontend build failed:')}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"{colors.error('❌ npm command not found. Please ensure Node.js and npm are installed.')}")
        return False
    except Exception as e:
        print(f"{colors.error(f'❌ Unexpected error during frontend build: {str(e)}')}")
        return False


def handle_start_command(args):
    """Start the Dana API server using uvicorn."""
    try:
        # Build frontend before starting server
        if not args.skip_build:
            print("\n🔨 Building frontend...")
            frontend_build_success = build_frontend()
            if not frontend_build_success:
                print(f"{colors.error('❌ Frontend build failed. Server startup aborted.')}")
                return 1
        else:
            print(f"{colors.accent('✅ Skipping frontend build')}")

        # Start the server directly without configuration validation
        host = args.host or "127.0.0.1"
        port = args.port or 8080
        reload = args.reload
        log_level = args.log_level or "info"

        os.environ["STUDIO_RAG"] = "true"

        print(f"{colors.accent('✅ Enable STUDIO_RAG')}")

        print(f"\n🌐 Starting Dana API server on http://{host}:{port}")
        print(f"📊 Health check: http://{host}:{port}/health")
        print(f"🔗 Root endpoint: http://{host}:{port}/")

        uvicorn.run(
            "dana.studio.api.server.server:create_app",
            host=host,
            port=port,
            reload=reload,
            log_level=log_level,
            factory=True,
        )

    except Exception as e:
        print(f"{colors.error(f'❌ Server startup error: {str(e)}')}")
        return 1


def main():
    """Main entry point for the Dana CLI."""
    # if developer puts an .env file in the current working directory, load it
    # Note: Environment loading is now handled automatically by initlib startup

    args = None  # Initialize args to avoid unbound variable error
    try:
        parser = argparse.ArgumentParser(description="Dana Command Line Interface", add_help=False)
        parser.add_argument("--version", action="store_true", help="Show version information")

        # Studio subcommand for Dana Studio
        parser.add_argument(
            "--host",
            default="127.0.0.1",
            help="Host to bind the server (default: 127.0.0.1)",
        )
        parser.add_argument(
            "--port",
            type=int,
            default=8080,
            help="Port to bind the server (default: 8080)",
        )
        parser.add_argument("--skip-build", action="store_true", help="Skip building the frontend before starting the server")
        parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
        parser.add_argument("--log-level", default="info", help="Log level (default: info)")

        # Parse subcommand
        args = parser.parse_args()

        # Show version if requested
        if args.version:
            from dana import __version__

            print(f"Dana {__version__}")
            return 0

        return handle_start_command(args)

    except KeyboardInterrupt:
        print("\nDANA execution interrupted by user")
        return 0
    except Exception as e:
        print(f"\n{colors.error(f'Unexpected error: {str(e)}')}")
        if args and hasattr(args, "debug") and args.debug:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nDANA execution interrupted by user")
        sys.exit(0)
