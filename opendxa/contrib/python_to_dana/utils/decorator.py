import functools
import time


# Performance monitoring decorator
def monitor_performance(func):
    """Decorator to monitor function performance."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            elapsed_ms = (end_time - start_time) * 1000

            # Log performance if debugging
            if hasattr(args[0], "_debug") and args[0]._debug:
                print(f"PERF: {func.__name__} took {elapsed_ms:.3f}ms")

            return result
        except Exception as e:
            end_time = time.perf_counter()
            elapsed_ms = (end_time - start_time) * 1000

            if hasattr(args[0], "_debug") and args[0]._debug:
                print(f"PERF: {func.__name__} failed after {elapsed_ms:.3f}ms: {e}")

            raise

    return wrapper


# Benchmarking decorator
def benchmark(iterations: int = 10, show_details: bool = True):
    """Decorator to benchmark function performance over multiple iterations.

    Args:
        iterations: Number of times to run the function
        show_details: Whether to print detailed benchmark results

    Returns:
        A decorator that adds benchmark_stats attribute to the function
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            print(f"🔬 Benchmarking {func.__name__} ({iterations} iterations)...")
            times = []

            for _i in range(iterations):
                start_time = time.perf_counter()
                result = func(*args, **kwargs)
                end_time = time.perf_counter()
                elapsed_ms = (end_time - start_time) * 1000
                times.append(elapsed_ms)

            # Calculate statistics
            stats = {
                "mean_ms": sum(times) / len(times),
                "min_ms": min(times),
                "max_ms": max(times),
                "total_ms": sum(times),
                "iterations": iterations,
                "function_name": func.__name__,
            }

            # Store stats on the function for access
            wrapper.benchmark_stats = stats

            if show_details:
                print(f"  📈 Mean time: {stats['mean_ms']:.3f}ms")
                print(f"  ⚡ Fastest:   {stats['min_ms']:.3f}ms")
                print(f"  🐌 Slowest:   {stats['max_ms']:.3f}ms")
                print(f"  🕐 Total:     {stats['total_ms']:.1f}ms")

            return result  # Return the last result

        return wrapper

    return decorator
