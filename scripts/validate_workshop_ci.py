#!/usr/bin/env python3
"""
Local validation script for workshop integration tests CI.

This script simulates the GitHub Actions workflow locally to help
developers validate their changes before pushing to a PR.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description, cwd=None):
    """Run a command and report results."""
    print(f"\n🔄 {description}")
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)
        print(f"✅ {description} - PASSED")
        if result.stdout.strip():
            print(f"Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED")
        print(f"Exit code: {e.returncode}")
        if e.stdout:
            print(f"STDOUT:\n{e.stdout}")
        if e.stderr:
            print(f"STDERR:\n{e.stderr}")
        return False
    except FileNotFoundError:
        print(f"❌ {description} - COMMAND NOT FOUND")
        print(f"Could not find command: {cmd[0]}")
        return False


def check_environment():
    """Check that the environment is set up correctly."""
    print("🔍 Checking environment setup...")
    
    # Check if we're in the project root
    if not Path("pyproject.toml").exists():
        print("❌ Must be run from project root (pyproject.toml not found)")
        return False
    
    # Check if virtual environment exists
    if not Path(".venv").exists():
        print("❌ Virtual environment not found. Please run 'make install' first.")
        return False
    
    # Check if workshop test files exist
    test_files = [
        "tests/integration/test_workshop_examples.py",
        "tests/integration/run_workshop_tests.py"
    ]
    
    missing_files = [f for f in test_files if not Path(f).exists()]
    if missing_files:
        print(f"❌ Missing test files: {missing_files}")
        return False
    
    print("✅ Environment setup looks good")
    return True


def main():
    """Main validation workflow."""
    print("🧪 Dana Workshop Integration Tests - Local Validation")
    print("=" * 60)
    
    if not check_environment():
        sys.exit(1)
    
    # Activate virtual environment
    venv_python = Path(".venv/bin/python").absolute()
    if not venv_python.exists():
        print("❌ Python executable not found in virtual environment")
        sys.exit(1)
    
    # Test commands to run (similar to GitHub Actions)
    test_commands = [
        {
            "cmd": [str(venv_python), "tests/integration/run_workshop_tests.py", "--file-validation", "-v"],
            "description": "File Validation Tests",
            "required": True
        },
        {
            "cmd": [str(venv_python), "tests/integration/run_workshop_tests.py", "--parametrized", "-v"],
            "description": "Parametrized Integration Tests",
            "required": True
        },
        {
            "cmd": [str(venv_python), "tests/integration/run_workshop_tests.py", "-k", "workshop_file_existence", "-v"],
            "description": "Workshop File Existence Check",
            "required": True
        },
        {
            "cmd": [str(venv_python), "tests/integration/run_workshop_tests.py", "-k", "builtin_reasoning or order_intelligence", "-v"],
            "description": "Basic Workshop Functionality",
            "required": True
        },
    ]
    
    # Optional MCP test
    mcp_test = {
        "cmd": [str(venv_python), "tests/integration/run_workshop_tests.py", "--with-mcp", "-k", "mcp_resource or reasoning_agent", "-v"],
        "description": "MCP Integration Tests (Optional)",
        "required": False
    }
    
    results = []
    
    # Run required tests
    for test in test_commands:
        success = run_command(test["cmd"], test["description"])
        results.append((test["description"], success, test["required"]))
    
    # Ask about MCP tests
    print("\n❓ Would you like to run MCP integration tests?")
    print("   This requires internet connection and may take longer.")
    response = input("   Run MCP tests? (y/N): ").lower().strip()
    
    if response in ['y', 'yes']:
        success = run_command(mcp_test["cmd"], mcp_test["description"])
        results.append((mcp_test["description"], success, False))
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 40)
    
    required_failures = 0
    optional_failures = 0
    
    for description, success, required in results:
        status = "✅ PASS" if success else "❌ FAIL"
        req_text = "(Required)" if required else "(Optional)"
        print(f"{status} {description} {req_text}")
        
        if not success:
            if required:
                required_failures += 1
            else:
                optional_failures += 1
    
    # Final verdict
    print("\n🎯 Final Result")
    if required_failures == 0:
        print("✅ All required tests passed! Your changes are ready for PR.")
        if optional_failures > 0:
            print(f"⚠️  {optional_failures} optional test(s) failed, but this won't block your PR.")
        sys.exit(0)
    else:
        print(f"❌ {required_failures} required test(s) failed. Please fix before creating PR.")
        print("\n💡 Tips for fixing issues:")
        print("   - Check Dana syntax in workshop .na files")
        print("   - Ensure virtual environment is properly set up")
        print("   - Run individual tests to debug specific failures")
        sys.exit(1)


if __name__ == "__main__":
    main() 