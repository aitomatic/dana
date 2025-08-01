#!/bin/bash
# Dana Concurrent-by-Default Test Runner
# Copyright © 2025 Aitomatic, Inc.
# 
# This script automatically checks for the 'dana' command availability
# and provides helpful fallback options if not found in PATH.

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if dana command is available
check_dana_command() {
    if ! command -v dana &> /dev/null; then
        echo -e "${RED}Error: 'dana' command not found in PATH${NC}"
        echo
        echo -e "${YELLOW}Please ensure Dana is properly installed and available:${NC}"
        echo "1. Check if Dana is installed:"
        echo "   - Look for dana binary in your installation directory"
        echo "   - Check if it's in your PATH environment variable"
        echo
        echo "2. Common installation locations:"
        echo "   - ./bin/dana (if running from project root)"
        echo "   - /usr/local/bin/dana (system-wide installation)"
        echo "   - ~/.local/bin/dana (user installation)"
        echo
        echo "3. Alternative ways to run Dana:"
        echo "   - Use full path: ./bin/dana (if in project root)"
        echo "   - Use Python module: python -m dana"
        echo "   - Activate virtual environment first"
        echo
        echo -e "${BLUE}Attempting to find Dana installation...${NC}"
        
        # Try to find dana in common locations
        local found_dana=""
        for path in "./bin/dana" "/usr/local/bin/dana" "$HOME/.local/bin/dana" "$(pwd)/bin/dana"; do
            if [ -x "$path" ]; then
                found_dana="$path"
                echo -e "${GREEN}Found Dana at: $path${NC}"
                break
            fi
        done
        
        if [ -n "$found_dana" ]; then
            echo -e "${YELLOW}Using Dana from: $found_dana${NC}"
            echo "You can add this to your PATH or use the full path."
            echo
            # Set DANA_CMD for use in the script
            export DANA_CMD="$found_dana"
        else
            echo -e "${RED}Could not find Dana installation.${NC}"
            echo "Please install Dana or ensure it's properly configured."
            exit 1
        fi
    else
        export DANA_CMD="dana"
        echo -e "${GREEN}✓ Dana command found: $(which dana)${NC}"
    fi
}

echo "=========================================="
echo "Dana Concurrent-by-Default Test Suite"
echo "=========================================="
echo

# Check for dana command availability
check_dana_command
echo

# Function to run a test file
run_test() {
    local test_file="$1"
    local test_name="$2"
    
    echo -e "${YELLOW}Running: $test_name${NC}"
    echo "File: $test_file"
    
    if "$DANA_CMD" "$test_file"; then
        echo -e "${GREEN}✓ PASSED: $test_name${NC}"
        echo
        return 0
    else
        echo -e "${RED}✗ FAILED: $test_name${NC}"
        echo
        return 1
    fi
}

# Track test results
total_tests=0
passed_tests=0
failed_tests=0

# Change to workspace directory
cd /workspace

echo "Phase 1: Unit Tests"
echo "==================="

# Unit tests
unit_tests=(
    "tests/unit/concurrency/basic_deliver_return.na:Basic Deliver/Return Functionality"
    "tests/unit/concurrency/promise_transparency.na:Promise[T] Transparency"
    "tests/unit/concurrency/promise_error_handling.na:Promise[T] Error Handling"
)

for test_spec in "${unit_tests[@]}"; do
    IFS=':' read -r test_file test_name <<< "$test_spec"
    total_tests=$((total_tests + 1))
    
    if run_test "$test_file" "$test_name"; then
        passed_tests=$((passed_tests + 1))
    else
        failed_tests=$((failed_tests + 1))
    fi
done

echo "Phase 2: Functional Tests"
echo "========================="

# Functional tests
functional_tests=(
    "tests/functional/concurrency/concurrent_function_calls.na:Concurrent Function Calls"
    "tests/functional/concurrency/agent_concurrency_integration.na:Agent System Integration"
    "tests/functional/concurrency/performance_scenarios.na:Performance Scenarios"
    "tests/functional/concurrency/backward_compatibility.na:Backward Compatibility"
)

for test_spec in "${functional_tests[@]}"; do
    IFS=':' read -r test_file test_name <<< "$test_spec"
    total_tests=$((total_tests + 1))
    
    if run_test "$test_file" "$test_name"; then
        passed_tests=$((passed_tests + 1))
    else
        failed_tests=$((failed_tests + 1))
    fi
done

echo "Phase 3: Python Integration Tests"
echo "================================="

# Python tests (if they exist and work)
python_tests=(
    "tests/functional/language/test_deliver_return.py:Promise[T] Foundation (Python)"
    "tests/unit/core/interpreter/test_dual_delivery.py:Dual Delivery Mechanism (Python)"
)

for test_spec in "${python_tests[@]}"; do
    IFS=':' read -r test_file test_name <<< "$test_spec"
    
    if [ -f "$test_file" ]; then
        total_tests=$((total_tests + 1))
        echo -e "${YELLOW}Running: $test_name${NC}"
        echo "File: $test_file"
        
        if source .venv/bin/activate && python -m pytest "$test_file" -v; then
            echo -e "${GREEN}✓ PASSED: $test_name${NC}"
            passed_tests=$((passed_tests + 1))
        else
            echo -e "${RED}✗ FAILED: $test_name${NC}"
            failed_tests=$((failed_tests + 1))
        fi
        echo
    else
        echo -e "${YELLOW}Skipping: $test_name (file not found)${NC}"
        echo
    fi
done

# Final results
echo "=========================================="
echo "Test Results Summary"
echo "=========================================="
echo "Total Tests: $total_tests"
echo -e "Passed: ${GREEN}$passed_tests${NC}"
echo -e "Failed: ${RED}$failed_tests${NC}"

if [ $failed_tests -eq 0 ]; then
    echo -e "${GREEN}"
    echo "🎉 ALL TESTS PASSED! 🎉"
    echo "Dana Concurrent-by-Default Implementation is ready!"
    echo -e "${NC}"
    exit 0
else
    echo -e "${RED}"
    echo "❌ Some tests failed. Please review the errors above."
    echo -e "${NC}"
    exit 1
fi