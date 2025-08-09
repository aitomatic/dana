#!/usr/bin/env python3
"""
Phase 8 Integration Tests Runner
Automated test runner for Dana integration tests covering:
- MCP Integration (4 tests)
- Python Interoperability (4 tests)
- Agent System (5 tests)

Usage:
    python run_phase8_tests.py [options]

Options:
    --verbose, -v      Enable verbose output
    --category, -c     Run specific category (mcp, python, agent)
    --test, -t         Run specific test file
    --timeout          Set timeout per test (default: 300 seconds)
    --continue         Continue running tests after failures
    --summary          Show only summary results
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path


class Phase8TestRunner:
    """Test runner for Phase 8 integration tests."""

    def __init__(self, verbose: bool = False, timeout: int = 300):
        self.verbose = verbose
        self.timeout = timeout
        self.test_directory = Path(__file__).parent
        self.results: dict[str, dict] = {}

        # Define test categories and files
        self.test_categories = {
            "mcp": ["test_mcp_basic.na", "test_mcp_tools.na", "test_mcp_resources.na", "test_mcp_error_handling.na"],
            "python": ["test_python_import.na", "test_python_functions.na", "test_python_objects.na", "test_python_types.na"],
            "agent": [
                "test_agent_definition.na",
                "test_agent_methods.na",
                "test_agent_memory.na",
                "test_agent_communication.na",
                "test_agent_pools.na",
            ],
        }

        # Flatten all tests
        self.all_tests = []
        for category_tests in self.test_categories.values():
            self.all_tests.extend(category_tests)

    def print_header(self):
        """Print test runner header."""
        print("=" * 80)
        print("🚀 DANA PHASE 8 INTEGRATION TEST RUNNER")
        print("=" * 80)
        print(f"📁 Test Directory: {self.test_directory}")
        print(f"⏱️  Timeout per test: {self.timeout} seconds")
        print(f"📊 Total tests: {len(self.all_tests)}")
        print()

        # Show test categories
        for category, tests in self.test_categories.items():
            print(f"📋 {category.upper()}: {len(tests)} tests")
            if self.verbose:
                for test in tests:
                    print(f"   - {test}")
        print()

    def check_prerequisites(self) -> bool:
        """Check if prerequisites are met."""
        print("🔍 Checking prerequisites...")

        # Check if dana command is available
        try:
            result = subprocess.run(["dana", "--version"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✅ Dana available: {result.stdout.strip()}")
            else:
                print("❌ Dana command not available or failed")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("❌ Dana command not found in PATH")
            return False

        # Check if test files exist
        missing_files = []
        for test_file in self.all_tests:
            test_path = self.test_directory / test_file
            if not test_path.exists():
                missing_files.append(test_file)

        if missing_files:
            print(f"❌ Missing test files: {missing_files}")
            return False
        else:
            print(f"✅ All {len(self.all_tests)} test files found")

        # Check virtual environment
        venv_path = Path(".venv/bin/activate")
        if venv_path.exists():
            print("✅ Virtual environment found")
        else:
            print("⚠️  Virtual environment not found (.venv/bin/activate)")
            print("   Tests will run in current environment")

        print()
        return True

    def run_single_test(self, test_file: str) -> dict:
        """Run a single test file and return results."""
        test_path = self.test_directory / test_file

        if self.verbose:
            print(f"🧪 Running {test_file}...")
        else:
            print(f"🧪 {test_file:<30} ", end="", flush=True)

        start_time = time.time()

        try:
            # Activate virtual environment and run test
            cmd = f"source .venv/bin/activate 2>/dev/null || true; dana {test_path}"

            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=self.test_directory.parent.parent.parent,  # Go to project root
            )

            end_time = time.time()
            duration = end_time - start_time

            # Analyze results
            success = result.returncode == 0

            # Count test assertions/checks from output
            output_lines = result.stdout.split("\n") if result.stdout else []
            error_lines = result.stderr.split("\n") if result.stderr else []

            # Count success/failure indicators
            success_count = sum(1 for line in output_lines if "✓" in line)
            failure_count = sum(1 for line in output_lines if "✗" in line)
            warning_count = sum(1 for line in output_lines if "⚠" in line)

            test_result = {
                "file": test_file,
                "success": success,
                "duration": duration,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success_count": success_count,
                "failure_count": failure_count,
                "warning_count": warning_count,
            }

            if success:
                if self.verbose:
                    print(f"   ✅ PASSED ({duration:.2f}s, {success_count} checks)")
                else:
                    print(f"✅ PASSED ({duration:.2f}s)")
            else:
                if self.verbose:
                    print(f"   ❌ FAILED ({duration:.2f}s)")
                    if result.stderr:
                        print(f"   Error: {result.stderr.strip()}")
                else:
                    print(f"❌ FAILED ({duration:.2f}s)")

            return test_result

        except subprocess.TimeoutExpired:
            end_time = time.time()
            duration = end_time - start_time

            if self.verbose:
                print(f"   ⏰ TIMEOUT ({duration:.2f}s)")
            else:
                print(f"⏰ TIMEOUT ({duration:.2f}s)")

            return {
                "file": test_file,
                "success": False,
                "duration": duration,
                "return_code": -1,
                "stdout": "",
                "stderr": f"Test timed out after {self.timeout} seconds",
                "success_count": 0,
                "failure_count": 1,
                "warning_count": 0,
            }

        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time

            if self.verbose:
                print(f"   💥 ERROR ({duration:.2f}s): {str(e)}")
            else:
                print(f"💥 ERROR ({duration:.2f}s)")

            return {
                "file": test_file,
                "success": False,
                "duration": duration,
                "return_code": -2,
                "stdout": "",
                "stderr": str(e),
                "success_count": 0,
                "failure_count": 1,
                "warning_count": 0,
            }

    def run_category_tests(self, category: str, continue_on_failure: bool = False) -> dict:
        """Run all tests in a specific category."""
        if category not in self.test_categories:
            raise ValueError(f"Unknown category: {category}")

        category_tests = self.test_categories[category]
        print(f"📋 Running {category.upper()} tests ({len(category_tests)} tests)")
        print("-" * 50)

        category_results = {"category": category, "tests": [], "total": len(category_tests), "passed": 0, "failed": 0, "total_duration": 0}

        for test_file in category_tests:
            result = self.run_single_test(test_file)
            category_results["tests"].append(result)
            category_results["total_duration"] += result["duration"]

            if result["success"]:
                category_results["passed"] += 1
            else:
                category_results["failed"] += 1
                if not continue_on_failure:
                    break

        print()
        return category_results

    def run_all_tests(self, continue_on_failure: bool = False) -> dict:
        """Run all tests across all categories."""
        print("🚀 Running ALL Phase 8 integration tests")
        print("=" * 50)

        all_results = {
            "categories": {},
            "summary": {
                "total_tests": len(self.all_tests),
                "total_passed": 0,
                "total_failed": 0,
                "total_duration": 0,
                "categories_passed": 0,
                "categories_failed": 0,
            },
        }

        for category in self.test_categories.keys():
            category_result = self.run_category_tests(category, continue_on_failure)
            all_results["categories"][category] = category_result

            # Update summary
            all_results["summary"]["total_passed"] += category_result["passed"]
            all_results["summary"]["total_failed"] += category_result["failed"]
            all_results["summary"]["total_duration"] += category_result["total_duration"]

            if category_result["failed"] == 0:
                all_results["summary"]["categories_passed"] += 1
            else:
                all_results["summary"]["categories_failed"] += 1

            if not continue_on_failure and category_result["failed"] > 0:
                break

        return all_results

    def print_summary(self, results: dict):
        """Print test results summary."""
        print("=" * 80)
        print("📊 PHASE 8 INTEGRATION TEST SUMMARY")
        print("=" * 80)

        if "summary" in results:
            # All tests summary
            summary = results["summary"]
            total = summary["total_tests"]
            passed = summary["total_passed"]
            failed = summary["total_failed"]
            duration = summary["total_duration"]

            print("🎯 Overall Results:")
            print(f"   Total Tests: {total}")
            print(f"   ✅ Passed: {passed} ({passed / total * 100:.1f}%)")
            print(f"   ❌ Failed: {failed} ({failed / total * 100:.1f}%)")
            print(f"   ⏱️  Total Duration: {duration:.2f} seconds")
            print()

            # Category breakdown
            print("📋 Category Results:")
            for category, category_result in results["categories"].items():
                cat_total = category_result["total"]
                cat_passed = category_result["passed"]
                cat_failed = category_result["failed"]
                cat_duration = category_result["total_duration"]

                status = "✅ PASSED" if cat_failed == 0 else "❌ FAILED"
                print(f"   {category.upper():<8} {status} ({cat_passed}/{cat_total}, {cat_duration:.2f}s)")

            print()

            # Failed tests details
            failed_tests = []
            for category_result in results["categories"].values():
                for test_result in category_result["tests"]:
                    if not test_result["success"]:
                        failed_tests.append(test_result)

            if failed_tests:
                print("❌ Failed Tests Details:")
                for test_result in failed_tests:
                    print(f"   {test_result['file']}: {test_result['stderr'][:100]}...")
                print()

        else:
            # Single category or test
            if "category" in results:
                # Single category
                cat_total = results["total"]
                cat_passed = results["passed"]
                cat_failed = results["failed"]
                cat_duration = results["total_duration"]

                print(f"📋 {results['category'].upper()} Results:")
                print(f"   Total Tests: {cat_total}")
                print(f"   ✅ Passed: {cat_passed}")
                print(f"   ❌ Failed: {cat_failed}")
                print(f"   ⏱️  Duration: {cat_duration:.2f} seconds")
            else:
                # Single test
                print("🧪 Single Test Result:")
                print(f"   File: {results['file']}")
                print(f"   Status: {'✅ PASSED' if results['success'] else '❌ FAILED'}")
                print(f"   Duration: {results['duration']:.2f} seconds")
                if not results["success"]:
                    print(f"   Error: {results['stderr']}")

        # Recommendations
        print("💡 Recommendations:")

        if "summary" in results:
            total_failed = results["summary"]["total_failed"]
            if total_failed == 0:
                print("   🎉 All tests passed! Phase 8 integration is working correctly.")
            else:
                print(f"   🔍 {total_failed} tests failed. Check the failed test details above.")
                print("   📚 Refer to test documentation for troubleshooting guidance.")
                print("   🔧 Check prerequisites and dependencies for failed tests.")

        print()
        print("=" * 80)

    def save_results(self, results: dict, output_file: str | None = None):
        """Save test results to file."""
        if not output_file:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_file = f"phase8_test_results_{timestamp}.json"

        import json

        with open(output_file, "w") as f:
            json.dump(results, f, indent=2, default=str)

        print(f"📄 Results saved to: {output_file}")


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Phase 8 Integration Tests Runner", formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")

    parser.add_argument("--category", "-c", choices=["mcp", "python", "agent"], help="Run specific category tests")

    parser.add_argument("--test", "-t", help="Run specific test file")

    parser.add_argument("--timeout", type=int, default=300, help="Timeout per test in seconds (default: 300)")

    parser.add_argument("--continue", action="store_true", dest="continue_on_failure", help="Continue running tests after failures")

    parser.add_argument("--summary", action="store_true", help="Show only summary results")

    parser.add_argument("--output", "-o", help="Output file for results (JSON format)")

    args = parser.parse_args()

    # Create test runner
    runner = Phase8TestRunner(verbose=args.verbose and not args.summary, timeout=args.timeout)

    # Print header unless summary only
    if not args.summary:
        runner.print_header()

        # Check prerequisites
        if not runner.check_prerequisites():
            print("❌ Prerequisites check failed. Please resolve issues and try again.")
            sys.exit(1)

    # Run tests based on arguments
    try:
        if args.test:
            # Run single test
            if args.test not in runner.all_tests:
                print(f"❌ Test file not found: {args.test}")
                sys.exit(1)

            results = runner.run_single_test(args.test)

        elif args.category:
            # Run category tests
            results = runner.run_category_tests(args.category, args.continue_on_failure)

        else:
            # Run all tests
            results = runner.run_all_tests(args.continue_on_failure)

        # Print summary
        runner.print_summary(results)

        # Save results if requested
        if args.output:
            runner.save_results(results, args.output)

        # Exit with appropriate code
        if "summary" in results:
            sys.exit(0 if results["summary"]["total_failed"] == 0 else 1)
        elif "category" in results:
            sys.exit(0 if results["failed"] == 0 else 1)
        else:
            sys.exit(0 if results["success"] else 1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Test execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
