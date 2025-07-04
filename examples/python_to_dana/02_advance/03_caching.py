#!/usr/bin/env python3
"""
Advanced Tutorial 03: Production-Ready Caching

Master advanced caching strategies for high-performance Dana applications.
Demonstrates cache management, TTL optimization, and production patterns.

Prerequisites: Advanced Tutorials 01-02
Difficulty: ⭐⭐⭐⭐⭐ Expert
Duration: 15-20 minutes
"""

import time

from dana.integrations.python.to_dana.core.inprocess_sandbox import InProcessSandboxInterface


def demo_basic_caching_setup():
    """Demonstrate basic caching configuration and usage."""
    print("🏗️  BASIC CACHING SETUP")
    print("=" * 40)

    # Create sandbox with optimized caching
    sandbox = InProcessSandboxInterface(debug=True, enable_cache=True, cache_max_size=100, cache_ttl_seconds=60.0)

    print(f"✅ Cache enabled: {sandbox.cache_enabled}")
    print(f"📊 Initial cache info: {sandbox.get_cache_info()}")

    # Demonstrate cache miss vs hit
    print("\n🔍 Cache Miss/Hit Demonstration:")

    # First call - cache miss
    print("   First call (cache miss)...")
    start_time = time.perf_counter()
    _result1 = sandbox.reason("What is 2+2?")
    miss_time = (time.perf_counter() - start_time) * 1000

    # Second call - cache hit
    print("   Second call (cache hit)...")
    start_time = time.perf_counter()
    _result2 = sandbox.reason("What is 2+2?")
    hit_time = (time.perf_counter() - start_time) * 1000

    print("\n⚡ Performance Improvement:")
    print(f"   Cache miss: {miss_time:.3f}ms")
    print(f"   Cache hit:  {hit_time:.3f}ms")
    if miss_time > 0:
        speedup = miss_time / hit_time
        print(f"   Speedup: {speedup:.1f}x faster")

    stats = sandbox.get_cache_stats()
    print(f"\n📈 Cache Statistics: {stats}")

    sandbox.close()


def demo_cache_configuration():
    """Demonstrate advanced cache configuration patterns."""
    print("\n⚙️  ADVANCED CACHE CONFIGURATION")
    print("=" * 40)

    # Different configurations for different use cases
    configs = [
        {
            "name": "High-Frequency API",
            "max_size": 1000,
            "ttl": 300.0,  # 5 minutes
            "description": "Large cache, medium TTL for API endpoints",
        },
        {
            "name": "ML Model Cache",
            "max_size": 50,
            "ttl": 1800.0,  # 30 minutes
            "description": "Small cache, long TTL for expensive ML inference",
        },
        {
            "name": "Real-time Analytics",
            "max_size": 100,
            "ttl": 60.0,  # 1 minute
            "description": "Medium cache, short TTL for real-time data",
        },
    ]

    for config in configs:
        print(f"\n📋 {config['name']}:")
        print(f"   Max Size: {config['max_size']} entries")
        print(f"   TTL: {config['ttl']} seconds")
        print(f"   Use Case: {config['description']}")


def demo_performance_optimization():
    """Demonstrate cache performance optimization techniques."""
    print("\n🚀 PERFORMANCE OPTIMIZATION")
    print("=" * 40)

    # Compare performance with different cache settings
    test_cases = [
        {"enable_cache": False, "name": "No Cache"},  # No Cache
        {"enable_cache": True, "cache_max_size": 10, "name": "Small Cache"},  # Small Cache
        {"enable_cache": True, "cache_max_size": 100, "name": "Large Cache"},  # Large Cache
    ]

    query = "What is 2+2?"
    iterations = 5

    print("⚡ Performance comparison:")
    for case in test_cases:
        kwargs = {k: v for k, v in case.items() if k != "name"}
        sandbox = InProcessSandboxInterface(**kwargs)

        start_time = time.perf_counter()
        for _ in range(iterations):
            sandbox.reason(query)
        total_time = (time.perf_counter() - start_time) * 1000

        avg_time = total_time / iterations
        print(f"   {case['name']}: {avg_time:.3f}ms avg ({total_time:.1f}ms total)")

        if case["enable_cache"]:
            stats = sandbox.get_cache_stats()
            print(f"      Cache stats: {stats}")

        sandbox.close()


def main():
    """Run advanced caching demonstrations."""
    print("🚀 ADVANCED TUTORIAL 03: Production-Ready Caching")
    print("=" * 60)
    print("Master advanced caching for high-performance Dana applications")
    print()

    try:
        demo_basic_caching_setup()
        demo_cache_configuration()
        demo_performance_optimization()

        print("\n" + "=" * 60)
        print("✅ Advanced Tutorials Complete!")
        print("\n🎓 Mastery Achieved:")
        print("   • Performance benchmarking and optimization")
        print("   • Cache lifecycle and TTL optimization")
        print("\n🏆 You're now ready for production Dana applications!")

    except Exception as e:
        print(f"❌ Tutorial failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
