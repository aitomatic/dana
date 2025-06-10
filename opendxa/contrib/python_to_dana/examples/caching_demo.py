#!/usr/bin/env python3
"""
Caching Demo for Python-to-Dana Integration

Demonstrates the ReasoningCache functionality integrated with InProcessSandboxInterface.
Shows performance improvements from caching and cache management features.
"""

import time

from opendxa.contrib.python_to_dana.core.inprocess_sandbox import InProcessSandboxInterface


def demo_basic_caching():
    """Demonstrate basic caching functionality."""
    print("=== Basic Caching Demo ===")
    
    # Create sandbox with caching enabled and debug mode
    sandbox = InProcessSandboxInterface(
        debug=True,
        enable_cache=True,
        cache_max_size=100,
        cache_ttl_seconds=60.0
    )
    
    print(f"Cache enabled: {sandbox.cache_enabled}")
    print(f"Initial cache info: {sandbox.get_cache_info()}")
    
    # First call - should miss cache and execute
    print("\n--- First call (cache miss expected) ---")
    start_time = time.perf_counter()
    result1 = sandbox.reason("What is 2+2?")
    end_time = time.perf_counter()
    print(f"Result: {result1}")
    print(f"Time taken: {(end_time - start_time) * 1000:.3f}ms")
    
    # Second call - should hit cache
    print("\n--- Second call (cache hit expected) ---")
    start_time = time.perf_counter()
    result2 = sandbox.reason("What is 2+2?")
    end_time = time.perf_counter()
    print(f"Result: {result2}")
    print(f"Time taken: {(end_time - start_time) * 1000:.3f}ms")
    
    # Show cache statistics
    stats = sandbox.get_cache_stats()
    print(f"\nCache stats: {stats}")
    print(f"Cache info: {sandbox.get_cache_info()}")
    
    sandbox.close()


def demo_cache_with_options():
    """Demonstrate caching with different options."""
    print("\n=== Caching with Options Demo ===")
    
    sandbox = InProcessSandboxInterface(debug=True)
    
    # Same prompt with different options should create separate cache entries
    print("\n--- Same prompt, different temperatures ---")
    result1 = sandbox.reason("Explain gravity", {"temperature": 0.1})
    result2 = sandbox.reason("Explain gravity", {"temperature": 0.9})
    
    print(f"Low temperature result: {result1[:50]}...")
    print(f"High temperature result: {result2[:50]}...")
    
    # Same prompt with same options should hit cache
    print("\n--- Same prompt, same options (should hit cache) ---")
    result3 = sandbox.reason("Explain gravity", {"temperature": 0.1})
    print(f"Cached result: {result3[:50]}...")
    
    stats = sandbox.get_cache_stats()
    print(f"\nCache stats: {stats}")
    
    sandbox.close()


def demo_cache_management():
    """Demonstrate cache management features."""
    print("\n=== Cache Management Demo ===")
    
    sandbox = InProcessSandboxInterface(
        debug=True,
        cache_max_size=3,  # Small cache for demo
        cache_ttl_seconds=1.0  # Short TTL for demo
    )
    
    # Fill cache
    print("\n--- Filling cache ---")
    sandbox.reason("What is 1+1?")
    sandbox.reason("What is 2+2?")
    sandbox.reason("What is 3+3?")
    
    stats = sandbox.get_cache_stats()
    print(f"Cache after filling: {stats}")
    
    # Add one more - should trigger eviction
    print("\n--- Adding one more (should trigger eviction) ---")
    sandbox.reason("What is 4+4?")
    
    stats = sandbox.get_cache_stats()
    print(f"Cache after eviction: {stats}")
    
    # Wait for TTL expiration
    print("\n--- Waiting for TTL expiration ---")
    time.sleep(1.2)
    
    # Try to access - should miss due to TTL
    result = sandbox.reason("What is 1+1?")  # This was cached before
    stats = sandbox.get_cache_stats()
    print(f"Cache after TTL expiration: {stats}")
    
    # Clear cache manually
    print("\n--- Clearing cache manually ---")
    sandbox.clear_cache()
    stats = sandbox.get_cache_stats()
    print(f"Cache after manual clear: {stats}")
    
    sandbox.close()


def demo_cache_disabled():
    """Demonstrate behavior when caching is disabled."""
    print("\n=== Caching Disabled Demo ===")
    
    sandbox = InProcessSandboxInterface(
        debug=True,
        enable_cache=False
    )
    
    print(f"Cache enabled: {sandbox.cache_enabled}")
    print(f"Cache info: {sandbox.get_cache_info()}")
    
    # Multiple calls should all execute (no caching)
    print("\n--- Multiple calls without caching ---")
    for i in range(3):
        start_time = time.perf_counter()
        result = sandbox.reason("What is 2+2?")
        end_time = time.perf_counter()
        print(f"Call {i+1}: {result} ({(end_time - start_time) * 1000:.3f}ms)")
    
    # Cache stats should be None
    stats = sandbox.get_cache_stats()
    print(f"Cache stats (should be None): {stats}")
    
    sandbox.close()


def performance_comparison():
    """Compare performance with and without caching."""
    print("\n=== Performance Comparison ===")
    
    # Test without caching
    print("\n--- Without caching ---")
    sandbox_no_cache = InProcessSandboxInterface(enable_cache=False)
    
    start_time = time.perf_counter()
    for i in range(5):
        sandbox_no_cache.reason("What is 2+2?")
    end_time = time.perf_counter()
    no_cache_time = end_time - start_time
    
    print(f"5 calls without caching: {no_cache_time * 1000:.3f}ms")
    sandbox_no_cache.close()
    
    # Test with caching
    print("\n--- With caching ---")
    sandbox_with_cache = InProcessSandboxInterface(enable_cache=True)
    
    start_time = time.perf_counter()
    for i in range(5):
        sandbox_with_cache.reason("What is 2+2?")
    end_time = time.perf_counter()
    with_cache_time = end_time - start_time
    
    print(f"5 calls with caching: {with_cache_time * 1000:.3f}ms")
    
    stats = sandbox_with_cache.get_cache_stats()
    print(f"Cache stats: {stats}")
    
    # Calculate improvement
    if no_cache_time > 0:
        improvement = (no_cache_time - with_cache_time) / no_cache_time * 100
        print(f"Performance improvement: {improvement:.1f}%")
    
    sandbox_with_cache.close()


def main():
    """Run all demos."""
    print("Python-to-Dana Caching Demo")
    print("=" * 50)
    
    try:
        demo_basic_caching()
        demo_cache_with_options()
        demo_cache_management()
        demo_cache_disabled()
        performance_comparison()
        
        print("\n" + "=" * 50)
        print("Caching demo completed successfully!")
        
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 