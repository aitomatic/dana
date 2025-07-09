#!/usr/bin/env python3
"""
Branch Validation Tool for OpenDXA → Dana Migration

This script validates that a branch works correctly after migration,
testing both old and new import paths to ensure compatibility.
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any


def run_command(cmd: list[str], cwd: str | None = None) -> tuple[int, str, str]:
    """Run a shell command and return exit code, stdout, stderr."""
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            cwd=cwd
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def get_current_branch() -> str:
    """Get the current git branch name."""
    code, stdout, stderr = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if code == 0:
        return stdout.strip()
    else:
        raise Exception(f"Failed to get current branch: {stderr}")


def test_import_compatibility() -> dict[str, Any]:
    """Test that both old and new import paths work."""
    
    print("🔍 Testing import compatibility...")
    
    # Test cases for common import paths
    import_tests = [
        # Core Dana Language
        ("dana.core.lang.dana_sandbox", "DanaSandbox"),
        ("dana.core.lang.parser.dana_parser", "DanaParser"),
        ("dana.core.lang.interpreter.dana_interpreter", "DanaInterpreter"),
        
        # Runtime and Module System
        ("dana.core.runtime.modules.core.registry", "ModuleRegistry"),
        ("dana.core.repl.dana", "main"),
        
        # Standard Library Functions
        ("dana.core.stdlib.function_registry", "FunctionRegistry"),
        ("dana.core.stdlib.core.log_function", "LogFunction"),
        
        # Common Utilities
        ("dana.common.utils.logging.dana_logger", "DANA_LOGGER"),
        ("dana.common.mixins.loggable", "Loggable"),
        ("dana.common.resource.llm_resource", "LLMResource"),
        
        # POET Framework
        ("dana.frameworks.poet", "poet"),
        ("dana.frameworks.poet.client", "POETClient"),
        ("dana.frameworks.poet.enhancer", "POETEnhancer"),
        
        # KNOWS Framework
        ("dana.frameworks.knows.core.base", "KnowledgeBase"),
        ("dana.frameworks.knows.extraction.meta.extractor", "MetaExtractor"),
        
        # Agent Framework
        ("dana.frameworks.agent.agent", "Agent"),
        ("dana.frameworks.agent.capability.domain_expertise", "DomainExpertise"),
        
        # Integrations
        ("dana.integrations.python", "Dana"),
        ("dana.integrations.rag", "RAGResource"),
        ("dana.integrations.mcp", "McpResource"),
        ("dana.integrations.llm", "LLMResource"),
    ]
    
    # Old import paths for compatibility testing
    old_import_tests = [
        ("opendxa.dana.sandbox.dana_sandbox", "DanaSandbox"),
        ("opendxa.dana.poet", "poet"),
        ("opendxa.knows.core.base", "KnowledgeBase"),
        ("opendxa.agent.agent", "Agent"),
        ("opendxa.common.utils.logging.dxa_logger", "DXA_LOGGER"),
        ("opendxa.integrations.python", "Dana"),
    ]
    
    results = {
        "new_imports_passed": 0,
        "new_imports_failed": 0,
        "old_imports_passed": 0,
        "old_imports_failed": 0,
        "failed_imports": []
    }
    
    # Test new import paths
    print("\n📦 Testing new import paths...")
    for module_path, item_name in import_tests:
        try:
            # Create temporary test script
            test_script = f"""
import sys
import os
sys.path.insert(0, os.getcwd())

# Set up compatibility layer
from dana.compat import setup_migration_compatibility
setup_migration_compatibility()

try:
    from {module_path} import {item_name}
    print(f"✅ {module_path}.{item_name}")
except ImportError as e:
    print(f"❌ {module_path}.{item_name}: {{e}}")
    sys.exit(1)
"""
            
            # Run test
            code, stdout, stderr = run_command([
                sys.executable, "-c", test_script
            ])
            
            if code == 0:
                results["new_imports_passed"] += 1
                print(f"  ✅ {module_path}.{item_name}")
            else:
                results["new_imports_failed"] += 1
                results["failed_imports"].append(f"NEW: {module_path}.{item_name}")
                print(f"  ❌ {module_path}.{item_name}")
                
        except Exception as e:
            results["new_imports_failed"] += 1
            results["failed_imports"].append(f"NEW: {module_path}.{item_name} - {e}")
            print(f"  ❌ {module_path}.{item_name}: {e}")
    
    # Test old import paths (compatibility)
    print("\n🔄 Testing old import paths (compatibility)...")
    for module_path, item_name in old_import_tests:
        try:
            # Create temporary test script
            test_script = f"""
import sys
import os
sys.path.insert(0, os.getcwd())

# Set up compatibility layer
from dana.compat import setup_migration_compatibility
setup_migration_compatibility()

try:
    from {module_path} import {item_name}
    print(f"✅ {module_path}.{item_name} (compatibility)")
except ImportError as e:
    print(f"❌ {module_path}.{item_name}: {{e}}")
    sys.exit(1)
"""
            
            # Run test
            code, stdout, stderr = run_command([
                sys.executable, "-c", test_script
            ])
            
            if code == 0:
                results["old_imports_passed"] += 1
                print(f"  ✅ {module_path}.{item_name} (compatibility)")
            else:
                results["old_imports_failed"] += 1
                results["failed_imports"].append(f"OLD: {module_path}.{item_name}")
                print(f"  ❌ {module_path}.{item_name} (compatibility)")
                
        except Exception as e:
            results["old_imports_failed"] += 1
            results["failed_imports"].append(f"OLD: {module_path}.{item_name} - {e}")
            print(f"  ❌ {module_path}.{item_name}: {e}")
    
    return results


def run_existing_tests() -> dict[str, Any]:
    """Run existing test suites to verify nothing is broken."""
    
    print("\n🧪 Running existing tests...")
    
    results = {
        "tests_run": False,
        "tests_passed": False,
        "test_output": ""
    }
    
    # Check if pytest is available and there are tests
    test_dirs = ["tests/", "test/"]
    test_dir = None
    
    for dir_name in test_dirs:
        if Path(dir_name).exists():
            test_dir = dir_name
            break
    
    if not test_dir:
        print("  ℹ️  No test directory found (tests/, test/)")
        return results
    
    # Run pytest
    print(f"  🏃 Running tests in {test_dir}...")
    code, stdout, stderr = run_command([
        "uv", "run", "pytest", test_dir, "-v", "--tb=short"
    ])
    
    results["tests_run"] = True
    results["test_output"] = stdout + stderr
    
    if code == 0:
        results["tests_passed"] = True
        print("  ✅ All tests passed!")
    else:
        results["tests_passed"] = False
        print("  ❌ Some tests failed")
        
        # Show last few lines of output
        lines = (stdout + stderr).split('\n')
        print("  Last few lines of test output:")
        for line in lines[-10:]:
            if line.strip():
                print(f"    {line}")
    
    return results


def check_syntax_errors() -> dict[str, Any]:
    """Check for syntax errors in Python files."""
    
    print("\n🔍 Checking for syntax errors...")
    
    results = {
        "files_checked": 0,
        "syntax_errors": 0,
        "error_files": []
    }
    
    # Find Python files
    python_files = []
    for file_path in Path(".").rglob("*.py"):
        if any(skip in str(file_path) for skip in [".git", "__pycache__", ".pytest_cache", "node_modules"]):
            continue
        python_files.append(file_path)
    
    print(f"  📝 Checking {len(python_files)} Python files...")
    
    for file_path in python_files:
        try:
            with open(file_path, encoding='utf-8') as f:
                content = f.read()
            
            # Try to compile the file
            compile(content, str(file_path), 'exec')
            results["files_checked"] += 1
            
        except SyntaxError as e:
            results["syntax_errors"] += 1
            results["error_files"].append(str(file_path))
            print(f"  ❌ Syntax error in {file_path}: {e}")
            
        except Exception as e:
            # Other errors (like encoding issues) are not necessarily syntax errors
            results["files_checked"] += 1
            print(f"  ⚠️  Warning in {file_path}: {e}")
    
    if results["syntax_errors"] == 0:
        print(f"  ✅ No syntax errors found in {results['files_checked']} files")
    else:
        print(f"  ❌ Found {results['syntax_errors']} syntax errors")
    
    return results


def validate_branch(branch_name: str) -> None:
    """Validate a branch after migration."""
    
    print(f"🔍 Validating branch: {branch_name}")
    print("=" * 60)
    
    # Check if we're on the right branch
    current_branch = get_current_branch()
    if current_branch != branch_name:
        print(f"❌ Currently on branch '{current_branch}', expected '{branch_name}'")
        print(f"Please run: git checkout {branch_name}")
        return
    
    # Run all validation tests
    import_results = test_import_compatibility()
    test_results = run_existing_tests()
    syntax_results = check_syntax_errors()
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    
    # Import compatibility
    print("📦 Import Compatibility:")
    print(f"  ✅ New imports: {import_results['new_imports_passed']}")
    print(f"  ❌ New imports: {import_results['new_imports_failed']}")
    print(f"  ✅ Old imports (compatibility): {import_results['old_imports_passed']}")
    print(f"  ❌ Old imports (compatibility): {import_results['old_imports_failed']}")
    
    # Test results
    print("\n🧪 Test Results:")
    if test_results["tests_run"]:
        print(f"  {'✅' if test_results['tests_passed'] else '❌'} Tests {'passed' if test_results['tests_passed'] else 'failed'}")
    else:
        print("  ℹ️  No tests found or run")
    
    # Syntax check
    print("\n🔍 Syntax Check:")
    print(f"  📝 Files checked: {syntax_results['files_checked']}")
    print(f"  {'✅' if syntax_results['syntax_errors'] == 0 else '❌'} Syntax errors: {syntax_results['syntax_errors']}")
    
    # Overall status
    all_passed = (
        import_results['new_imports_failed'] == 0 and
        import_results['old_imports_failed'] == 0 and
        (not test_results["tests_run"] or test_results["tests_passed"]) and
        syntax_results['syntax_errors'] == 0
    )
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 VALIDATION PASSED!")
        print("✅ Branch is ready for use")
    else:
        print("❌ VALIDATION FAILED!")
        print("🔧 Issues found that need attention:")
        
        if import_results['failed_imports']:
            print("\n📦 Failed imports:")
            for failed_import in import_results['failed_imports']:
                print(f"  - {failed_import}")
        
        if syntax_results['error_files']:
            print("\n🔍 Files with syntax errors:")
            for error_file in syntax_results['error_files']:
                print(f"  - {error_file}")
        
        if test_results["tests_run"] and not test_results["tests_passed"]:
            print("\n🧪 Test failures detected - check test output above")
    
    print("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate a branch after migration")
    parser.add_argument("--branch", "-b", help="Branch name to validate (defaults to current branch)")
    
    args = parser.parse_args()
    
    # Get branch name
    if args.branch:
        branch_name = args.branch
    else:
        try:
            branch_name = get_current_branch()
        except Exception as e:
            print(f"❌ Error getting current branch: {e}")
            sys.exit(1)
    
    # Validate we're in a git repository
    if not Path(".git").exists():
        print("❌ This script must be run from the root of a git repository")
        sys.exit(1)
    
    try:
        validate_branch(branch_name)
    except KeyboardInterrupt:
        print("\n🛑 Validation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()