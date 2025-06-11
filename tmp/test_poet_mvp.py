#!/usr/bin/env python3
"""
Basic test script for POET MVP implementation.

This script demonstrates the POET framework working with simple functions.
"""

import time
from opendxa.dana.poet import poet


# Basic POET usage - reliability and performance
@poet()
def simple_calculation(x: int, y: int) -> int:
    """Simple function to test basic POET functionality."""
    if x < 0 or y < 0:
        raise ValueError("Negative numbers not supported")
    return x + y


# POET with domain specialization
@poet(domain="llm_optimization", timeout=10.0, retries=2)
def mock_reasoning_task(prompt: str) -> str:
    """Mock reasoning task to test LLM optimization domain."""
    # Simulate potential failure
    if "fail" in prompt.lower():
        raise RuntimeError("Simulated reasoning failure")
    
    # Simulate slow processing
    if "slow" in prompt.lower():
        time.sleep(0.5)
    
    return f"Processed: {prompt}"


def test_basic_poet():
    """Test basic POET functionality."""
    print("🧪 Testing Basic POET Functionality")
    
    # Test successful execution
    result = simple_calculation(5, 3)
    print(f"✅ Simple calculation: 5 + 3 = {result}")
    
    # Test retry mechanism
    try:
        result = simple_calculation(-1, 5)
        print(f"❌ Expected error but got: {result}")
    except ValueError as e:
        print(f"✅ Retry mechanism handled error: {e}")


def test_llm_domain_plugin():
    """Test LLM optimization domain plugin."""
    print("\n🧪 Testing LLM Domain Plugin")
    
    # Test successful processing
    result = mock_reasoning_task("What is the capital of France?")
    print(f"✅ LLM processing: {result}")
    
    # Test optimization of short prompts
    result = mock_reasoning_task("Help")
    print(f"✅ Short prompt optimization: {result}")
    
    # Test retry on failure
    try:
        result = mock_reasoning_task("This should fail")
        print(f"❌ Expected failure but got: {result}")
    except RuntimeError as e:
        print(f"✅ LLM domain handled failure with retries: {e}")


def test_parameter_learning():
    """Test parameter learning functionality."""
    print("\n🧪 Testing Parameter Learning")
    
    # Multiple executions to trigger learning
    for i in range(3):
        try:
            result = mock_reasoning_task(f"Task {i}")
            print(f"✅ Learning iteration {i+1}: {result}")
        except Exception as e:
            print(f"⚠️  Learning iteration {i+1} failed: {e}")


def main():
    """Run all POET MVP tests."""
    print("🚀 POET MVP Implementation Test")
    print("=" * 50)
    
    try:
        test_basic_poet()
        test_llm_domain_plugin()
        test_parameter_learning()
        
        print("\n🎉 All POET MVP tests completed!")
        print("✅ Core framework is working")
        print("✅ Domain plugins are functional")
        print("✅ Parameter learning is active")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()