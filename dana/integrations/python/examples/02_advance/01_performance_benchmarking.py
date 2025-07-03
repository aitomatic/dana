#!/usr/bin/env python3
"""
Advanced Tutorial 01: Performance Benchmarking

Learn how to measure and optimize Python-to-Dana integration performance using decorators.
Demonstrates benchmarking decorators and performance monitoring in production scenarios.

Prerequisites: Complete basic tutorials 01-08
Difficulty: ⭐⭐⭐ Advanced
Duration: 5-10 minutes
"""

from opendxa.contrib.python_to_dana.utils.decorator import benchmark, monitor_performance
from opendxa.dana import dana


class DanaPerformanceAnalyzer:
    """Example class that demonstrates monitor_performance decorator usage."""

    def __init__(self, debug: bool = True):
        self._debug = debug  # Required for monitor_performance decorator

    @monitor_performance
    def simple_reasoning(self, question: str) -> str:
        """Simple reasoning with performance monitoring."""
        return dana.reason(question)

    @monitor_performance
    def complex_reasoning(self, question: str) -> str:
        """Complex reasoning with performance monitoring."""
        return dana.reason(question)

    @monitor_performance
    def batch_reasoning(self, questions: list[str]) -> list[str]:
        """Batch processing with performance monitoring."""
        results = []
        for question in questions:
            result = dana.reason(question)
            results.append(result)
        return results


# Benchmark decorator usage examples
@benchmark(iterations=5, show_details=True)
def benchmark_basic_reasoning():
    """Benchmarked basic reasoning function."""
    return dana.reason("What is 2+2?")


@benchmark(iterations=3, show_details=True)
def benchmark_complex_reasoning():
    """Benchmarked complex reasoning function."""
    return dana.reason("Analyze the economic implications of artificial intelligence on global markets")


@benchmark(iterations=2, show_details=False)  # Quiet benchmarking
def benchmark_quiet_reasoning():
    """Benchmarked function with minimal output."""
    return dana.reason("What is machine learning?")


def demo_monitor_performance_decorator():
    """Demonstrate the monitor_performance decorator for production monitoring."""
    print("🔍 MONITOR_PERFORMANCE DECORATOR DEMO")
    print("=" * 50)

    analyzer = DanaPerformanceAnalyzer(debug=True)

    print("📊 Individual call monitoring:")
    print("   Testing simple reasoning...")
    result1 = analyzer.simple_reasoning("What is 1+1?")
    print(f"   Result: {result1}")

    print("\n   Testing complex reasoning...")
    result2 = analyzer.complex_reasoning("Explain quantum computing")
    print(f"   Result: {result2[:50]}...")

    print("\n   Testing batch processing...")
    questions = ["What is AI?", "What is ML?", "What is data science?"]
    results = analyzer.batch_reasoning(questions)
    print(f"   Processed {len(results)} questions")

    print("\n💡 Use Case: Production monitoring, debug logging, error tracking")


def demo_benchmark_decorator():
    """Demonstrate the benchmark decorator for performance testing."""
    print("\n⚡ BENCHMARK DECORATOR DEMO")
    print("=" * 50)

    print("📊 Benchmarking with detailed output:")
    # Run benchmarked functions
    benchmark_basic_reasoning()

    print("\n📊 Benchmarking complex operations:")
    benchmark_complex_reasoning()

    print("\n📊 Quiet benchmarking (stats only):")
    benchmark_quiet_reasoning()

    # Access stored benchmark statistics
    print("\n📈 Accessing benchmark statistics:")
    basic_stats = benchmark_basic_reasoning.benchmark_stats
    complex_stats = benchmark_complex_reasoning.benchmark_stats
    quiet_stats = benchmark_quiet_reasoning.benchmark_stats

    print(f"   Basic reasoning: {basic_stats['mean_ms']:.1f}ms avg")
    print(f"   Complex reasoning: {complex_stats['mean_ms']:.1f}ms avg")
    print(f"   Quiet reasoning: {quiet_stats['mean_ms']:.1f}ms avg")

    # Performance comparison
    if basic_stats["mean_ms"] > 0:
        ratio = complex_stats["mean_ms"] / basic_stats["mean_ms"]
        print(f"   Performance ratio: {ratio:.2f}x (complex vs basic)")

    print("\n💡 Use Case: Performance testing, regression detection, optimization")


def demo_decorator_composition():
    """Demonstrate combining multiple decorators."""
    print("\n🔗 DECORATOR COMPOSITION")
    print("=" * 50)

    # Note: This is a conceptual example - actual composition would need careful design
    print("💡 Combining decorators for comprehensive monitoring:")
    print("   @benchmark(iterations=3)")
    print("   @monitor_performance")
    print("   def comprehensive_test():")
    print("       return dana.reason('test')")
    print("\n   Use case: Development testing with both individual call")
    print("   monitoring AND multi-iteration benchmarking")


def main():
    """Run performance demonstrations with decorators."""
    print("🚀 ADVANCED TUTORIAL 01: Performance Benchmarking with Decorators")
    print("=" * 70)
    print("Learn to use decorators for performance measurement and monitoring")
    print()

    try:
        demo_monitor_performance_decorator()
        demo_benchmark_decorator()
        demo_decorator_composition()

        print("\n" + "=" * 70)
        print("✅ Tutorial Complete!")
        print("\n💡 Key Learnings:")
        print("   • Use @monitor_performance for production monitoring & debug logging")
        print("   • Use @benchmark(iterations=N) for performance testing & regression detection")
        print("   • Access benchmark statistics via function.benchmark_stats")
        print("   • Combine decorators for comprehensive performance analysis")
        print("   • Apply conditional monitoring based on debug/production modes")
        print("\n🎯 Next: Learn modular architecture with nested imports")

    except Exception as e:
        print(f"❌ Tutorial failed: {e}")
        raise


if __name__ == "__main__":
    main()
