#!/usr/bin/env python3
"""
Local parallel testing script that mirrors the CI/CD workflow groupings.

This script runs the same test groups as the GitHub Actions parallel workflow,
allowing developers to test locally with the same organization.
"""

import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Test groups matching the CI workflow
TEST_GROUPS = {
    "dana-core": {
        "description": "Dana Language Core - Parser, AST, interpreter, sandbox",
        "paths": ["tests/dana/sandbox/", "tests/dana/ipv/"],
        "extra_cmd": ["tests/dana/sandbox/interpreter/test_struct_*"],
    },
    "dana-integration": {
        "description": "Dana Integration - REPL, transcoder, module system, .na files",
        "paths": ["tests/dana/repl/", "tests/dana/integration/", "tests/dana/module/", "tests/dana/na/", "tests/dana/ux/"],
    },
    "common-utilities": {
        "description": "Common Utilities - Graph, I/O, mixins, resources, logging",
        "paths": ["tests/common/"],
    },
    "agent-framework": {
        "description": "Agent Framework - Capabilities and resources",
        "paths": ["tests/agent/"],
    },
    "execution-engine": {
        "description": "Execution Engine - Pipeline and reasoning",
        "paths": ["tests/execution/"],
    },
    "miscellaneous": {
        "description": "Miscellaneous - Catch-all for unmatched tests",
        "paths": ["tests/"],
        "ignore_paths": ["tests/dana/", "tests/common/", "tests/agent/", "tests/execution/"],
    },
}


def run_test_group(group_name: str, group_config: dict) -> tuple[str, bool, str, float]:
    """Run a single test group and return results."""
    print(f"\n🚀 Starting {group_name}: {group_config['description']}")

    start_time = time.time()

    # Build the pytest command
    cmd = ["uv", "run", "pytest"]

    # Add paths
    if "ignore_paths" in group_config:
        # For miscellaneous group, add ignore patterns
        cmd.extend(group_config["paths"])
        for ignore_path in group_config["ignore_paths"]:
            cmd.extend(["--ignore", ignore_path])
    else:
        cmd.extend(group_config["paths"])

    # Add common options
    cmd.extend(["-m", "not live and not deep", "--tb=short", "-v"])

    # Set environment variables
    env = {
        "OPENDXA_MOCK_LLM": "true",
        "OPENDXA_USE_REAL_LLM": "false",
    }

    try:
        # Run the main command
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)

        # Run extra command if specified (e.g., struct tests for dana-core)
        if "extra_cmd" in group_config and result.returncode == 0:
            extra_cmd = ["uv", "run", "pytest"] + group_config["extra_cmd"] + ["-v", "--tb=short"]
            extra_result = subprocess.run(extra_cmd, capture_output=True, text=True, env=env)
            if extra_result.returncode != 0:
                result = extra_result

        elapsed = time.time() - start_time
        success = result.returncode == 0

        if success:
            print(f"✅ {group_name} completed successfully in {elapsed:.1f}s")
        else:
            print(f"❌ {group_name} failed in {elapsed:.1f}s")

        return group_name, success, result.stdout + result.stderr, elapsed

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"💥 {group_name} crashed in {elapsed:.1f}s: {e}")
        return group_name, False, str(e), elapsed


def main():
    """Run all test groups in parallel."""
    print("🧪 Running OpenDXA tests in parallel (matching CI workflow)")
    print("=" * 60)

    # Check if uv is available
    try:
        subprocess.run(["uv", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Error: 'uv' command not found. Please install uv first.")
        sys.exit(1)

    start_time = time.time()
    results = []

    # Run all test groups in parallel
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(run_test_group, name, config): name for name, config in TEST_GROUPS.items()}

        for future in as_completed(futures):
            group_name, success, output, elapsed = future.result()
            results.append((group_name, success, output, elapsed))

    total_elapsed = time.time() - start_time

    # Print summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)

    successful_groups = []
    failed_groups = []

    for group_name, success, output, elapsed in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {group_name:<20} ({elapsed:.1f}s)")

        if success:
            successful_groups.append(group_name)
        else:
            failed_groups.append((group_name, output))

    print(f"\nTotal runtime: {total_elapsed:.1f}s")
    print(f"Successful: {len(successful_groups)}/{len(TEST_GROUPS)}")

    # Print failure details
    if failed_groups:
        print("\n" + "=" * 60)
        print("❌ Failure Details")
        print("=" * 60)

        for group_name, output in failed_groups:
            print(f"\n🔴 {group_name}:")
            print("-" * 40)
            # Show last 50 lines of output
            lines = output.split("\n")
            for line in lines[-50:]:
                print(line)

        sys.exit(1)
    else:
        print("\n🎉 All tests passed!")


if __name__ == "__main__":
    main()
