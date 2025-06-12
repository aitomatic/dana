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
            if hasattr(args[0], '_debug') and args[0]._debug:
                print(f"PERF: {func.__name__} took {elapsed_ms:.3f}ms")
            
            return result
        except Exception as e:
            end_time = time.perf_counter()
            elapsed_ms = (end_time - start_time) * 1000
            
            if hasattr(args[0], '_debug') and args[0]._debug:
                print(f"PERF: {func.__name__} failed after {elapsed_ms:.3f}ms: {e}")
            
            raise
    
    return wrapper 