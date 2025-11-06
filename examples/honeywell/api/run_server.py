#!/usr/bin/env python3
"""
Wrapper script to run server.py with proper environment setup.
This ensures the uv-managed virtual environment is used.
"""
import sys
import os
import subprocess

# Get the project root directory
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
server_path = os.path.join(script_dir, "server.py")

# Check if we're in a venv or if uv is available
if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
    # We're in a virtual environment, run directly
    print(f"Running server from virtual environment: {sys.prefix}")
    os.execv(sys.executable, [sys.executable, server_path] + sys.argv[1:])
else:
    # Not in venv, use uv run
    print("Not in virtual environment. Using 'uv run' to ensure dependencies are available...")
    print(f"Project root: {project_root}")
    os.chdir(project_root)
    try:
        subprocess.run(["uv", "run", "python3", server_path] + sys.argv[1:], check=True)
    except FileNotFoundError:
        print("ERROR: 'uv' command not found. Please install uv or activate the virtual environment.")
        print("\nTo activate the venv manually:")
        print(f"  source {project_root}/.venv/bin/activate")
        print(f"  python3 {server_path}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nServer stopped by user.")
        sys.exit(0)

