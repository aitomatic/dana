#!/usr/bin/env python3
"""
Smart HVAC Demo Launcher

Simple script to launch the HVAC demo with proper Python path setup.
"""

import os
import subprocess
import sys
from pathlib import Path


def setup_python_path():
    """Add the dana project to Python path."""
    # Get the path to the dana.poet project (parent of demos)
    current_dir = Path(__file__).parent.absolute()
    dana_path = current_dir.parent.parent

    # Add to Python path
    if str(dana_path) not in sys.path:
        sys.path.insert(0, str(dana_path))

    # Also set environment variable for subprocess
    env_path = os.environ.get("PYTHONPATH", "")
    if str(dana_path) not in env_path:
        os.environ["PYTHONPATH"] = f"{dana_path}:{env_path}"

    print(f"✅ Added to Python path: {dana_path}")


def check_dependencies():
    """Check if required dependencies are available."""
    required_modules = ["fastapi", "uvicorn", "websockets", "pydantic", "numpy"]

    missing = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module} is available")
        except ImportError:
            missing.append(module)
            print(f"❌ {module} is missing")

    if missing:
        print("\n🔧 Install missing dependencies:")
        print(f"pip install {' '.join(missing)}")
        return False

    return True


def check_poet_availability():
    """Check if POET framework is available."""
    try:
        # Just import the module to check availability
        import dana.frameworks.poet

        print("✅ POET framework is available")
        return True
    except ImportError as e:
        print(f"❌ POET framework not available: {e}")
        print("\n🔧 Make sure you're running from the dana.poet project directory")
        return False


def main():
    """Launch the HVAC demo."""
    print("🏠 Smart HVAC Demo Launcher")
    print("=" * 50)

    # Setup Python path
    setup_python_path()

    # Check dependencies
    print("\n📦 Checking Dependencies...")
    if not check_dependencies():
        print("\n❌ Please install missing dependencies and try again")
        return 1

    # Check POET availability
    print("\n🤖 Checking POET Framework...")
    if not check_poet_availability():
        print("\n❌ POET framework not available")
        return 1

    print("\n🚀 Starting Smart HVAC Demo...")
    print("🌐 Demo will be available at: http://localhost:8000")
    print("💡 Use Ctrl+C to stop the demo\n")

    # Change to demo directory
    demo_dir = Path(__file__).parent
    os.chdir(demo_dir)

    # Launch the FastAPI server
    try:
        subprocess.run([sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"])
    except KeyboardInterrupt:
        print("\n\n👋 Demo stopped. Thanks for trying POET!")
        return 0
    except Exception as e:
        print(f"\n❌ Error running demo: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
