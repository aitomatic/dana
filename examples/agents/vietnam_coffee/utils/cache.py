"""
Simple file-based caching system for web requests and API calls.

Reduces redundant fetching and speeds up repeated operations.
"""

import json
import hashlib
import time
from pathlib import Path
from typing import Any


class SimpleCache:
    """
    File-based cache with TTL (time-to-live) support.

    Stores cached data as JSON files in a cache directory.
    Each cache entry includes timestamp for TTL enforcement.
    """

    def __init__(self, cache_dir: str = ".cache", default_ttl: int = 604800):
        """
        Initialize cache.

        Args:
            cache_dir: Directory to store cache files (default: .cache)
            default_ttl: Default time-to-live in seconds (default: 7 days)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl = default_ttl

    def _get_cache_key(self, key: str) -> str:
        """
        Generate cache filename from key.

        Uses SHA256 hash to create safe filenames.

        Args:
            key: Cache key (e.g., URL or operation identifier)

        Returns:
            Hashed filename
        """
        hash_obj = hashlib.sha256(key.encode("utf-8"))
        return hash_obj.hexdigest()

    def _get_cache_path(self, key: str) -> Path:
        """Get full path to cache file."""
        cache_key = self._get_cache_key(key)
        return self.cache_dir / f"{cache_key}.json"

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache.

        Returns None (or default) if:
        - Key doesn't exist
        - Cache entry has expired

        Args:
            key: Cache key
            default: Default value if not found

        Returns:
            Cached value or default
        """
        cache_path = self._get_cache_path(key)

        if not cache_path.exists():
            return default

        try:
            with open(cache_path, encoding="utf-8") as f:
                cache_entry = json.load(f)

            # Check if expired
            cached_time = cache_entry.get("timestamp", 0)
            ttl = cache_entry.get("ttl", self.default_ttl)
            current_time = time.time()

            if current_time - cached_time > ttl:
                # Expired, delete and return default
                cache_path.unlink()
                return default

            return cache_entry.get("value")

        except (OSError, json.JSONDecodeError, KeyError):
            # Corrupted cache entry, delete it
            if cache_path.exists():
                cache_path.unlink()
            return default

    def set(self, key: str, value: Any, ttl: int | None = None):
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache (must be JSON-serializable)
            ttl: Time-to-live in seconds (uses default if None)
        """
        cache_path = self._get_cache_path(key)

        cache_entry = {
            "timestamp": time.time(),
            "ttl": ttl if ttl is not None else self.default_ttl,
            "value": value,
            "key": key,  # Store original key for debugging
        }

        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache_entry, f, indent=2, ensure_ascii=False)
        except (OSError, TypeError) as e:
            print(f"Warning: Failed to cache {key}: {e}")

    def delete(self, key: str):
        """
        Delete cache entry.

        Args:
            key: Cache key to delete
        """
        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            cache_path.unlink()

    def clear(self, older_than: int | None = None):
        """
        Clear cache entries.

        Args:
            older_than: Only delete entries older than N seconds (None = all)
        """
        if older_than is None:
            # Clear all
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            print("✅ Cleared all cache entries")
        else:
            # Clear expired entries
            current_time = time.time()
            cleared_count = 0

            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    with open(cache_file, encoding="utf-8") as f:
                        cache_entry = json.load(f)

                    cached_time = cache_entry.get("timestamp", 0)
                    if current_time - cached_time > older_than:
                        cache_file.unlink()
                        cleared_count += 1

                except (OSError, json.JSONDecodeError):
                    # Corrupted, delete it
                    cache_file.unlink()
                    cleared_count += 1

            print(f"✅ Cleared {cleared_count} expired cache entries")

    def stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dict with cache stats (size, count, oldest entry)
        """
        cache_files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files)
        count = len(cache_files)

        oldest_time = None
        if cache_files:
            try:
                oldest_file = min(cache_files, key=lambda f: f.stat().st_mtime)
                with open(oldest_file, encoding="utf-8") as f:
                    cache_entry = json.load(f)
                    oldest_time = cache_entry.get("timestamp")
            except Exception:
                pass

        return {
            "count": count,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "oldest_entry_timestamp": oldest_time,
            "cache_dir": str(self.cache_dir),
        }


def cached_fetch(cache: SimpleCache, fetch_func: callable, key: str, ttl: int | None = None) -> Any:
    """
    Helper function to fetch data with caching.

    Checks cache first, fetches if miss, then caches result.

    Args:
        cache: SimpleCache instance
        fetch_func: Function to call if cache miss (no arguments)
        key: Cache key
        ttl: Time-to-live for this entry

    Returns:
        Cached or freshly fetched data

    Example:
        cache = SimpleCache()
        result = cached_fetch(
            cache=cache,
            fetch_func=lambda: expensive_api_call(param1, param2),
            key="api_call_unique_identifier",
            ttl=3600  # 1 hour
        )
    """
    # Try cache first
    cached_value = cache.get(key)
    if cached_value is not None:
        print(f"✅ Cache hit: {key[:50]}")
        return cached_value

    # Cache miss, fetch data
    print(f"⏳ Cache miss: {key[:50]}, fetching...")
    value = fetch_func()

    # Cache the result
    cache.set(key, value, ttl=ttl)

    return value
