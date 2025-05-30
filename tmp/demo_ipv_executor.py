#!/usr/bin/env python3
"""
Demo of IPV Executor Architecture

This script demonstrates the new IPVExecutor inheritance pattern with
different specialized executors for various types of intelligent operations.
"""

from unittest.mock import Mock

from opendxa.dana.ipv import IPVAPIIntegrator, IPVConfig, IPVDataProcessor, IPVReason


def demo_ipv_reason():
    """Demonstrate IPVReason for prompt optimization."""
    print("=== IPV Reason Demo ===")

    executor = IPVReason()

    # Mock context with type information
    mock_context = Mock()
    mock_context.get_assignment_target_type.return_value = float

    # Extract price with type-driven optimization
    result = executor.execute(
        "Extract the price from: The premium subscription costs $29.99 per month", context=mock_context, config=IPVConfig(debug_mode=True)
    )

    print(f"Extracted price: {result} (type: {type(result).__name__})")
    print()


def demo_ipv_data_processor():
    """Demonstrate IPVDataProcessor for data analysis."""
    print("=== IPV Data Processor Demo ===")

    executor = IPVDataProcessor()

    # Analyze sales data
    sales_data = {"sales": [100, 200, 150, 300, 250], "months": ["Jan", "Feb", "Mar", "Apr", "May"]}

    result = executor.execute("Analyze sales trends and identify patterns", data=sales_data, config=IPVConfig(debug_mode=True))

    print(f"Analysis result: {result}")
    print()


def demo_ipv_api_integrator():
    """Demonstrate IPVAPIIntegrator for API calls."""
    print("=== IPV API Integrator Demo ===")

    executor = IPVAPIIntegrator()

    # Simulate API call
    result = executor.execute("Get user profile for ID 12345", user_id=12345, config=IPVConfig(debug_mode=True))

    print(f"API result: {result}")
    print()


def demo_different_domains():
    """Demonstrate domain detection and optimization."""
    print("=== Domain Detection Demo ===")

    executor = IPVReason()

    test_cases = [
        ("Extract the medical diagnosis from this report", "medical"),
        ("Calculate the quarterly revenue", "financial"),
        ("Review this legal contract for compliance", "legal"),
        ("Write a creative story about space", "creative"),
        ("What is the weather today?", "general"),
    ]

    for intent, expected_domain in test_cases:
        result = executor.execute(intent, config=IPVConfig(debug_mode=False))
        print(f"Intent: {intent}")
        print(f"Expected domain: {expected_domain}")
        print(f"Result: {result}")
        print()


def demo_error_handling():
    """Demonstrate error handling across executors."""
    print("=== Error Handling Demo ===")

    # Create a failing executor for demonstration
    class FailingReason(IPVReason):
        def process_phase(self, intent: str, enhanced_context=None, **kwargs):
            raise ValueError("Simulated processing failure")

    executor = FailingReason()

    try:
        executor.execute("This will fail")
    except Exception as e:
        print(f"Caught error: {e}")

        # Show execution history
        history = executor.get_execution_history()
        if history:
            print(f"Execution failed: {not history[0]['success']}")
            print(f"Error details: {history[0]['errors']}")

    print()


def demo_performance_tracking():
    """Demonstrate performance tracking."""
    print("=== Performance Tracking Demo ===")

    executor = IPVReason()

    # Execute multiple operations
    for i in range(3):
        result = executor.execute(f"Process request {i+1}")

    # Get performance statistics
    stats = executor.get_performance_stats()
    print(f"Total executions: {stats['total_executions']}")
    print(f"Success rate: {stats['success_rate']:.2%}")
    print(f"Average time: {stats['average_time']:.4f}s")
    print(f"Total time: {stats['total_time']:.4f}s")

    print()


def main():
    """Run all demonstrations."""
    print("IPV Executor Architecture Demonstration")
    print("=" * 50)
    print()

    demo_ipv_reason()
    demo_ipv_data_processor()
    demo_ipv_api_integrator()
    demo_different_domains()
    demo_error_handling()
    demo_performance_tracking()

    print("=== Summary ===")
    print("The IPV Executor architecture provides:")
    print("1. Specialized executors for different operation types")
    print("2. Automatic domain detection and optimization")
    print("3. Type-driven result validation")
    print("4. Comprehensive error handling")
    print("5. Performance tracking and debugging")
    print("6. Clean inheritance pattern for extensibility")


if __name__ == "__main__":
    main()
