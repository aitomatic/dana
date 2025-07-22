#!/usr/bin/env python3
"""
Test runner for Dana workshop integration tests.

This script provides an easy way to run all workshop integration tests
with proper environment setup and reporting.
"""

import os
import subprocess
import sys
import time
from pathlib import Path


def setup_test_environment():
    """Set up the test environment."""
    # Ensure we're in a virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Warning: Not running in a virtual environment")
        print("   Consider activating the virtual environment with: source .venv/bin/activate")
    
    # Set up mock environment variables for testing
    test_env = os.environ.copy()
    test_env.update({
        "OPENAI_API_KEY": "test-openai-key",
        "ANTHROPIC_API_KEY": "test-anthropic-key",
        "GROQ_API_KEY": "test-groq-key", 
        "DEEPSEEK_API_KEY": "test-deepseek-key",
        "DANA_MOCK_LLM": "true",
    })
    
    return test_env


def install_mcp_server():
    """Install the MCP weather server."""
    print("📦 Installing MCP Weather Server...")
    
    try:
        # Try different pip installation methods
        install_commands = [
            # First try with pip directly
            ["pip", "install", "https://GitHub.com/AI-App/IsDaniel.MCP-Weather-Server/archive/dev.zip", "--upgrade"],
            # Then try with python -m pip
            ["python", "-m", "pip", "install", "https://GitHub.com/AI-App/IsDaniel.MCP-Weather-Server/archive/dev.zip", "--upgrade"],
            # Then try with uv
            ["uv", "pip", "install", "https://GitHub.com/AI-App/IsDaniel.MCP-Weather-Server/archive/dev.zip", "--upgrade"]
        ]
        
        for cmd in install_commands:
            try:
                print(f"🔄 Trying: {' '.join(cmd)}")
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                print("✅ MCP Weather Server installed successfully")
                return True
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                print(f"⚠️  Command failed: {e}")
                continue
        
        print("❌ All installation methods failed")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error during installation: {e}")
        return False


def check_mcp_server_running():
    """Check if MCP server is already running on port 8000."""
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', 8000))
        sock.close()
        return result == 0
    except Exception:
        return False


def start_mcp_server():
    """Start the MCP weather server in the background."""
    print("🚀 Starting MCP Weather Server...")
    
    # Check if server is already running
    if check_mcp_server_running():
        print("ℹ️  MCP server already running on port 8000")
        return "already_running"
    
    try:
        # Start MCP server directly with python module
        process = subprocess.Popen([
            "python", "-m", "mcp_weather_server", "--transport", "streamable-http"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Give it a moment to start
        time.sleep(3)
        
        # Check if process is still running and port is open
        if process.poll() is None and check_mcp_server_running():
            print("✅ MCP Weather Server started successfully")
            return process
        else:
            stdout, stderr = process.communicate()
            print("❌ MCP Weather Server failed to start")
            if "address already in use" in stderr:
                print("ℹ️  Port 8000 is already in use - server may already be running")
                if check_mcp_server_running():
                    return "already_running"
            print(f"STDERR: {stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Failed to start MCP Weather Server: {e}")
        return None


def stop_mcp_server(process):
    """Stop the MCP weather server."""
    if process == "already_running":
        print("ℹ️  MCP server was already running - leaving it running")
        return
    
    if process and process.poll() is None:
        print("⏹️  Stopping MCP Weather Server...")
        try:
            process.terminate()
            process.wait(timeout=5)
            print("✅ MCP Weather Server stopped")
        except subprocess.TimeoutExpired:
            print("⚠️  Force killing MCP Weather Server...")
            process.kill()
            process.wait()
        except Exception as e:
            print(f"⚠️  Error stopping MCP Weather Server: {e}")


def run_workshop_tests(verbose=False, specific_test=None, with_mcp=False):
    """
    Run the workshop integration tests.
    
    Args:
        verbose: Enable verbose output
        specific_test: Run a specific test (optional)
        with_mcp: Whether to start MCP server for tests
    """
    print("🧪 Running Dana Workshop Integration Tests")
    print("=" * 50)
    
    # Setup environment
    test_env = setup_test_environment()
    
    # Handle MCP server if requested
    mcp_process = None
    if with_mcp:
        print("\n🔧 Setting up MCP Weather Server...")
        
        # Install MCP server
        if not install_mcp_server():
            print("❌ Failed to install MCP server. Running tests without MCP integration.")
        else:
            # Start MCP server
            mcp_process = start_mcp_server()
            if mcp_process:
                # Update environment to disable mock mode for MCP tests
                test_env["DANA_MOCK_LLM"] = "false"
                print("🎯 MCP server ready - tests will run with real MCP integration")
            else:
                print("⚠️  MCP server failed to start. Running tests in mock mode.")
    
    # Get the directory of this script
    script_dir = Path(__file__).parent
    test_file = script_dir / "test_workshop_examples.py"
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        if mcp_process:
            stop_mcp_server(mcp_process)
        return False
    
    # Build pytest command
    cmd = ["python", "-m", "pytest", str(test_file)]
    
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    if specific_test:
        cmd.extend(["-k", specific_test])
    
    # Add output capture settings
    cmd.extend(["-s", "--tb=short"])
    
    print(f"📋 Running command: {' '.join(cmd)}")
    print()
    
    try:
        # Run the tests
        result = subprocess.run(cmd, env=test_env, cwd=script_dir.parent.parent)
        
        if result.returncode == 0:
            print("\n✅ All workshop tests completed successfully!")
            success = True
        else:
            print(f"\n❌ Some tests failed (exit code: {result.returncode})")
            success = False
            
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        success = False
    except Exception as e:
        print(f"\n💥 Error running tests: {e}")
        success = False
    finally:
        # Clean up MCP server
        if mcp_process:
            stop_mcp_server(mcp_process)
    
    return success


def run_file_validation_only():
    """Run only the file validation tests."""
    print("🔍 Running file validation for workshop Dana files")
    print("=" * 50)
    
    test_env = setup_test_environment()
    script_dir = Path(__file__).parent
    test_file = script_dir / "test_workshop_examples.py"
    
    cmd = [
        "python", "-m", "pytest", str(test_file),
        "-k", "file_discovery_and_basic_validation",
        "-v", "-s"
    ]
    
    try:
        result = subprocess.run(cmd, env=test_env, cwd=script_dir.parent.parent)
        return result.returncode == 0
    except Exception as e:
        print(f"💥 Error running file validation: {e}")
        return False


def run_parametrized_tests_only():
    """Run only the parametrized tests."""
    print("⚙️  Running parametrized workshop tests")
    print("=" * 50)
    
    test_env = setup_test_environment()
    script_dir = Path(__file__).parent
    test_file = script_dir / "test_workshop_examples.py"
    
    cmd = [
        "python", "-m", "pytest", str(test_file),
        "-k", "test_workshop_file_execution",
        "-v", "-s"
    ]
    
    try:
        result = subprocess.run(cmd, env=test_env, cwd=script_dir.parent.parent)
        return result.returncode == 0
    except Exception as e:
        print(f"💥 Error running parametrized tests: {e}")
        return False


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Run Dana workshop integration tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_workshop_tests.py                    # Run all tests
  python run_workshop_tests.py -v                 # Run with verbose output
  python run_workshop_tests.py -k builtin         # Run tests matching 'builtin'
  python run_workshop_tests.py --file-validation  # Run only file validation
  python run_workshop_tests.py --parametrized     # Run only parametrized tests
  python run_workshop_tests.py --with-mcp         # Run with MCP server
        """
    )
    
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Enable verbose output")
    parser.add_argument("-k", "--keyword", type=str,
                       help="Run tests matching the given keyword")
    parser.add_argument("--file-validation", action="store_true",
                       help="Run only file validation tests")
    parser.add_argument("--parametrized", action="store_true", 
                       help="Run only parametrized tests")
    parser.add_argument("--with-mcp", action="store_true",
                       help="Install and start MCP weather server for testing")
    
    args = parser.parse_args()
    
    if args.file_validation:
        success = run_file_validation_only()
    elif args.parametrized:
        success = run_parametrized_tests_only()
    else:
        success = run_workshop_tests(
            verbose=args.verbose,
            specific_test=args.keyword,
            with_mcp=args.with_mcp
        )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 