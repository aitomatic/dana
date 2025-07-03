"""
Reasoning Cache for Dana Operations

Provides intelligent caching of Dana reasoning results to improve performance
for repeated or similar queries.
"""

import hashlib
import time
from threading import Lock
from typing import Any


class ReasoningCache:
    """Cache for Dana reasoning results with TTL and intelligent key generation."""

    def __init__(self, max_size: int = 1000, ttl_seconds: float = 300.0):
        """Initialize the reasoning cache.

        Args:
            max_size: Maximum number of cached results
            ttl_seconds: Time-to-live for cached results in seconds
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds

        # Cache storage: cache_key -> (result, timestamp, access_count)
        self._cache: dict[str, tuple[Any, float, int]] = {}
        self._lock = Lock()

        # Statistics
        self._hit_count = 0
        self._miss_count = 0
        self._eviction_count = 0

    def _generate_cache_key(self, prompt: str, options: dict | None = None) -> str:
        """Generate a deterministic cache key for a reasoning request.

        Uses SHA-256 hash to ensure consistent keys while handling large prompts.
        """
        # Create a canonical representation
        prompt_part = prompt.strip().lower() if isinstance(prompt, str) else str(prompt)

        if options:
            # Validate options is a dict before proceeding
            if not isinstance(options, dict):
                # If options is not a dict, we can't cache this request
                # Return a unique key that will always miss the cache
                return f"uncacheable_{hash(str(options))}_{time.time()}"

            # Sort options for consistent key generation
            options_part = str(sorted(options.items()))
        else:
            options_part = ""

        # Combine and hash
        combined = f"{prompt_part}|{options_part}"
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()

    def _is_cache_entry_valid(self, timestamp: float) -> bool:
        """Check if a cache entry is still valid based on TTL."""
        return time.time() - timestamp <= self.ttl_seconds

    def _cleanup_expired_entries(self) -> int:
        """Remove expired cache entries and return count of removed entries."""
        current_time = time.time()
        expired_keys = []

        for key, (_, timestamp, _) in self._cache.items():
            if current_time - timestamp > self.ttl_seconds:
                expired_keys.append(key)

        for key in expired_keys:
            del self._cache[key]

        return len(expired_keys)

    def _evict_least_recently_used(self, count: int) -> int:
        """Evict least recently used entries and return count of evicted entries."""
        if len(self._cache) <= count:
            evicted = len(self._cache)
            self._cache.clear()
            return evicted

        # Sort by access count (ascending) and timestamp (ascending)
        sorted_items = sorted(
            self._cache.items(),
            key=lambda x: (x[1][2], x[1][1]),  # (access_count, timestamp)
        )

        evicted_count = 0
        for i in range(min(count, len(sorted_items))):
            key = sorted_items[i][0]
            del self._cache[key]
            evicted_count += 1

        return evicted_count

    def get(self, prompt: str, options: dict | None = None) -> Any | None:
        """Get cached result if available and valid.

        Args:
            prompt: The reasoning prompt
            options: Optional parameters used in the reasoning call

        Returns:
            Cached result if found and valid, None otherwise
        """
        cache_key = self._generate_cache_key(prompt, options)

        with self._lock:
            if cache_key in self._cache:
                result, timestamp, access_count = self._cache[cache_key]

                if self._is_cache_entry_valid(timestamp):
                    # Update access count and return result
                    self._cache[cache_key] = (result, timestamp, access_count + 1)
                    self._hit_count += 1
                    return result
                else:
                    # Remove expired entry
                    del self._cache[cache_key]

            self._miss_count += 1
            return None

    def put(self, prompt: str, options: dict | None, result: Any) -> bool:
        """Cache a reasoning result.

        Args:
            prompt: The reasoning prompt
            options: Optional parameters used in the reasoning call
            result: The result to cache

        Returns:
            True if successfully cached, False if rejected (e.g., None result)
        """
        # Don't cache None results or empty strings
        if result is None or (isinstance(result, str) and not result.strip()):
            return False

        cache_key = self._generate_cache_key(prompt, options)
        current_time = time.time()

        with self._lock:
            # Clean up expired entries first
            expired_count = self._cleanup_expired_entries()
            if expired_count > 0 and hasattr(self, "_debug") and self._debug:
                print(f"ReasoningCache: Cleaned up {expired_count} expired entries")

            # Check if we need to evict entries to make space
            if len(self._cache) >= self.max_size:
                # Evict 10% of entries or at least 1
                evict_count = max(1, self.max_size // 10)
                evicted = self._evict_least_recently_used(evict_count)
                self._eviction_count += evicted

            # Cache the new result
            self._cache[cache_key] = (result, current_time, 1)  # access_count starts at 1
            return True

    def clear(self):
        """Clear all cached results and reset statistics."""
        with self._lock:
            self._cache.clear()
            self._hit_count = 0
            self._miss_count = 0
            self._eviction_count = 0

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics and performance metrics."""
        with self._lock:
            total_requests = self._hit_count + self._miss_count
            hit_rate = (self._hit_count / total_requests) if total_requests > 0 else 0.0

            # Calculate memory usage estimation
            avg_entry_size = 0
            if self._cache:
                # Rough estimation of memory per entry
                sample_key = next(iter(self._cache.keys()))
                sample_value = self._cache[sample_key]
                avg_entry_size = len(sample_key) + len(str(sample_value[0])) + 64  # 64 bytes overhead

            return {
                "cache_size": len(self._cache),
                "max_size": self.max_size,
                "hit_count": self._hit_count,
                "miss_count": self._miss_count,
                "hit_rate": hit_rate,
                "eviction_count": self._eviction_count,
                "ttl_seconds": self.ttl_seconds,
                "estimated_memory_bytes": len(self._cache) * avg_entry_size,
                "total_requests": total_requests,
            }

    def get_cache_info(self) -> str:
        """Get a formatted string with cache information for debugging."""
        stats = self.get_stats()
        return (
            f"ReasoningCache(size={stats['cache_size']}/{stats['max_size']}, "
            f"hits={stats['hit_count']}, misses={stats['miss_count']}, "
            f"hit_rate={stats['hit_rate']:.1%}, evictions={stats['eviction_count']})"
        )

    def __repr__(self) -> str:
        """String representation of the cache."""
        return self.get_cache_info()
