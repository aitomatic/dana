#!/usr/bin/env python3
"""
Demo of IPV (Infer-Process-Validate) Phase 1 Implementation

This demo shows the core IPV infrastructure working with different
input types and configurations.
"""

from opendxa.dana.ipv import IPVConfig, IPVOrchestrator
from opendxa.dana.ipv.base import PrecisionLevel, ReliabilityLevel, SafetyLevel


def demo_basic_ipv():
    """Demo basic IPV pipeline execution."""
    print("=" * 60)
    print("DEMO 1: Basic IPV Pipeline")
    print("=" * 60)

    orchestrator = IPVOrchestrator()

    # Test with different input types
    test_inputs = [
        "Extract the price from: The item costs $29.99",
        {"data": "analyze this dictionary"},
        ["list", "of", "items", "to", "process"],
        42,
        "Write a creative story about a robot",
    ]

    for i, test_input in enumerate(test_inputs, 1):
        print(f"\nTest {i}: {type(test_input).__name__} input")
        print(f"Input: {test_input}")

        result = orchestrator.execute_ipv_pipeline(test_input)

        if result.is_success():
            print(f"✅ Success: {result.result}")
            print(f"⏱️  Execution time: {result.execution_time:.4f}s")
        else:
            print(f"❌ Failed: {result.error}")

        print("-" * 40)


def demo_domain_detection():
    """Demo domain-specific processing."""
    print("\n" + "=" * 60)
    print("DEMO 2: Domain Detection & Processing")
    print("=" * 60)

    orchestrator = IPVOrchestrator()

    domain_tests = [
        ("Financial", "What's the price of this stock: AAPL $150.25"),
        ("Medical", "Patient has symptoms of fever and headache"),
        ("Legal", "Review this contract for compliance issues"),
        ("Creative", "Write a poem about artificial intelligence"),
        ("General", "What's the weather like today?"),
    ]

    for domain, test_input in domain_tests:
        print(f"\n{domain} Domain Test:")
        print(f"Input: {test_input}")

        result = orchestrator.execute_ipv_pipeline(test_input)

        if result.is_success():
            print(f"✅ Result: {result.result}")

            # Show inferred strategy from metadata
            if "infer_metadata" in result.metadata:
                strategy = result.metadata["infer_metadata"].get("strategy", {})
                detected_domain = strategy.get("domain", "unknown")
                print(f"🧠 Detected domain: {detected_domain}")
        else:
            print(f"❌ Failed: {result.error}")

        print("-" * 40)


def demo_configuration_options():
    """Demo different IPV configurations."""
    print("\n" + "=" * 60)
    print("DEMO 3: Configuration Options")
    print("=" * 60)

    orchestrator = IPVOrchestrator()
    test_input = "Analyze the financial performance of our Q4 results"

    configs = [
        ("Default", IPVConfig()),
        ("High Reliability", IPVConfig(reliability=ReliabilityLevel.MAXIMUM)),
        ("Exact Precision", IPVConfig(precision=PrecisionLevel.EXACT)),
        ("Maximum Safety", IPVConfig(safety=SafetyLevel.MAXIMUM)),
        ("Debug Mode", IPVConfig(debug_mode=True)),
        (
            "Custom Mix",
            IPVConfig(reliability=ReliabilityLevel.HIGH, precision=PrecisionLevel.EXACT, safety=SafetyLevel.HIGH, max_iterations=5),
        ),
    ]

    for config_name, config in configs:
        print(f"\n{config_name} Configuration:")
        print(f"Input: {test_input}")

        result = orchestrator.execute_ipv_pipeline(test_input, config=config)

        if result.is_success():
            print(f"✅ Result: {result.result}")
            print(f"⏱️  Execution time: {result.execution_time:.4f}s")
        else:
            print(f"❌ Failed: {result.error}")

        print("-" * 40)


def demo_error_handling():
    """Demo error handling and recovery."""
    print("\n" + "=" * 60)
    print("DEMO 4: Error Handling")
    print("=" * 60)

    from opendxa.dana.ipv.base import IPVExecutionError, IPVPhase, IPVPhaseType, IPVResult

    class FailingPhase(IPVPhase):
        """A phase that always fails for testing."""

        def __init__(self, phase_type):
            super().__init__(phase_type)

        def execute(self, input_data, context, config):
            return IPVResult(success=False, result=None, error=IPVExecutionError(f"{self.phase_type.value} phase intentionally failed"))

    # Test with failing INFER phase
    print("\nTesting with failing INFER phase:")
    failing_orchestrator = IPVOrchestrator(infer_phase=FailingPhase(IPVPhaseType.INFER))

    result = failing_orchestrator.execute_ipv_pipeline("test input")
    print(f"❌ Expected failure: {result.error}")

    # Show execution history
    history = failing_orchestrator.get_execution_history()
    if history:
        print(f"📊 Execution recorded: {history[0]['success']}")

    print("-" * 40)


def demo_performance_stats():
    """Demo performance monitoring."""
    print("\n" + "=" * 60)
    print("DEMO 5: Performance Monitoring")
    print("=" * 60)

    orchestrator = IPVOrchestrator()

    # Execute multiple operations
    test_inputs = ["Quick test 1", "Quick test 2", "Quick test 3", "Quick test 4", "Quick test 5"]

    print("Executing multiple operations...")
    for test_input in test_inputs:
        result = orchestrator.execute_ipv_pipeline(test_input)
        print(f"✅ Processed: {test_input}")

    # Show performance stats
    stats = orchestrator.get_performance_stats()
    print("\n📊 Performance Statistics:")
    print(f"   Total executions: {stats['total_executions']}")
    print(f"   Successful: {stats['successful_executions']}")
    print(f"   Success rate: {stats['success_rate']:.1%}")
    print(f"   Avg execution time: {stats['avg_execution_time']:.4f}s")
    print(f"   Min execution time: {stats['min_execution_time']:.4f}s")
    print(f"   Max execution time: {stats['max_execution_time']:.4f}s")

    print("-" * 40)


def main():
    """Run all IPV demos."""
    print("🚀 IPV (Infer-Process-Validate) Phase 1 Demo")
    print("Demonstrating core IPV infrastructure capabilities")

    try:
        demo_basic_ipv()
        demo_domain_detection()
        demo_configuration_options()
        demo_error_handling()
        demo_performance_stats()

        print("\n" + "=" * 60)
        print("✅ All demos completed successfully!")
        print("🎯 Phase 1 IPV infrastructure is working correctly")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
