"""AST Execution Result Cache"""

import hashlib
import time
from collections import OrderedDict
from typing import Any

from dana.common.mixins.loggable import Loggable
from dana.core.lang.sandbox_context import SandboxContext


class ASTExecutionCache(Loggable):
    """LRU cache for AST node execution results with context-aware invalidation."""

    def __init__(self, max_size: int = 1000):
        super().__init__()
        self._cache: OrderedDict[tuple, tuple[Any, float]] = OrderedDict()
        self._max_size = max_size
        self._hit_count = 0
        self._miss_count = 0
        self._eviction_count = 0
        self._context_dependent_keys: set[tuple] = set()
        self._last_context_hash: str | None = None

    def get_cache_key(self, node: Any, context: SandboxContext) -> tuple:
        """Generate cache key from node and context state."""
        try:
            # Use node content instead of object ID for better cache granularity
            node_type = type(node).__name__
            context_hash = self._generate_context_hash(context)
            node_info = self._extract_node_info(node)

            # Create cache key based on content, not object identity
            cache_key = (node_type, context_hash, node_info)

            if context_hash:
                self._context_dependent_keys.add(cache_key)

            return cache_key
        except Exception as e:
            self.warning(f"Cache key generation failed for {type(node).__name__}: {e}")
            return (type(node).__name__, str(time.time()), "uncacheable")

    def _generate_context_hash(self, context: SandboxContext) -> str:
        """Generate hash of context state relevant for caching."""
        try:
            context_data = []

            for scope in ["local", "private", "public", "system"]:
                try:
                    scope_state = context._state.get(scope, {})
                    if scope_state:
                        # FIXED: Include actual values in hash, not just types, for accurate cache keys
                        scope_info = {k: str(v) for k, v in scope_state.items() if not callable(v)}
                        context_data.append((scope, tuple(sorted(scope_info.items()))))
                except Exception:
                    continue

            if context_data:
                context_str = str(sorted(context_data))
                return hashlib.md5(context_str.encode()).hexdigest()[:16]
            else:
                return "empty_context"
        except Exception as e:
            self.warning(f"Context hash generation failed: {e}")
            return "context_error"

    def _extract_node_info(self, node: Any) -> tuple:
        """Extract cacheable information from AST node."""
        try:
            if hasattr(node, "value") and isinstance(node.value, int | float | str | bool) or node.value is None:
                return ("literal", node.value)

            if hasattr(node, "name") and isinstance(node.name, str):
                return ("identifier", node.name)

            if hasattr(node, "operator") and isinstance(node.operator, str):
                return ("binary_op", node.operator)

            if hasattr(node, "name") and hasattr(node.name, "name"):
                return ("function_call", node.name.name)

            if hasattr(node, "items") and isinstance(node.items, list):
                return ("collection", len(node.items))

            return ("node_type", type(node).__name__)
        except Exception:
            return ("basic", type(node).__name__)

    def get(self, node: Any, context: SandboxContext) -> tuple[bool, Any]:
        """Get cached result for node execution."""
        cache_key = self.get_cache_key(node, context)

        if cache_key in self._cache:
            result, timestamp = self._cache.pop(cache_key)
            self._cache[cache_key] = (result, timestamp)

            self._hit_count += 1
            self.debug(f"Cache HIT for {type(node).__name__} (hit rate: {self.hit_rate:.1%})")
            return True, result
        else:
            self._miss_count += 1
            self.debug(f"Cache MISS for {type(node).__name__} (hit rate: {self.hit_rate:.1%})")
            return False, None

    def put(self, node: Any, context: SandboxContext, result: Any) -> None:
        """Cache execution result with LRU eviction."""
        try:
            if not self._is_cacheable_result(result):
                return

            cache_key = self.get_cache_key(node, context)
            timestamp = time.time()

            if cache_key in self._cache:
                self._cache.pop(cache_key)

            self._cache[cache_key] = (result, timestamp)

            while len(self._cache) > self._max_size:
                oldest_key = next(iter(self._cache))
                self._cache.pop(oldest_key)
                self._context_dependent_keys.discard(oldest_key)
                self._eviction_count += 1

            self.debug(f"Cached result for {type(node).__name__} (cache size: {len(self._cache)})")
        except Exception as e:
            self.warning(f"Failed to cache result for {type(node).__name__}: {e}")

    def _is_cacheable_result(self, result: Any) -> bool:
        """Check if a result should be cached."""
        if hasattr(result, "__len__") and len(result) > 1000:
            return False

        if isinstance(result, list | dict | set) and len(result) > 100:
            return False

        if hasattr(result, "__dict__") and callable(result):
            return False

        return True

    def invalidate_context_dependent(self, context: SandboxContext) -> None:
        """Invalidate cache entries dependent on modified context variables."""
        try:
            current_context_hash = self._generate_context_hash(context)

            if current_context_hash == self._last_context_hash:
                return

            invalidated_keys = []
            for cache_key in list(self._context_dependent_keys):
                if cache_key in self._cache:
                    _, _, cached_context_hash, _ = cache_key
                    if cached_context_hash != current_context_hash:
                        invalidated_keys.append(cache_key)

            for key in invalidated_keys:
                self._cache.pop(key, None)
                self._context_dependent_keys.discard(key)

            if invalidated_keys:
                self.debug(f"Invalidated {len(invalidated_keys)} context-dependent cache entries")

            self._last_context_hash = current_context_hash
        except Exception as e:
            self.warning(f"Context-dependent cache invalidation failed: {e}")

    def clear(self) -> None:
        """Clear all cached results."""
        cache_size = len(self._cache)
        self._cache.clear()
        self._context_dependent_keys.clear()
        self._last_context_hash = None
        self.info(f"Cleared {cache_size} cached results")

    @property
    def hit_rate(self) -> float:
        """Calculate current cache hit rate."""
        total_requests = self._hit_count + self._miss_count
        return self._hit_count / total_requests if total_requests > 0 else 0.0

    def get_statistics(self) -> dict[str, Any]:
        """Get comprehensive cache statistics."""
        total_requests = self._hit_count + self._miss_count

        return {
            "cache_size": len(self._cache),
            "max_size": self._max_size,
            "hit_count": self._hit_count,
            "miss_count": self._miss_count,
            "total_requests": total_requests,
            "hit_rate": self.hit_rate,
            "eviction_count": self._eviction_count,
            "context_dependent_entries": len(self._context_dependent_keys),
            "memory_efficiency": len(self._cache) / self._max_size if self._max_size > 0 else 0.0,
        }

    def log_statistics(self) -> None:
        """Log current cache statistics."""
        stats = self.get_statistics()
        self.info(
            f"AST Cache Stats: {stats['hit_count']}/{stats['total_requests']} hits "
            f"({stats['hit_rate']:.1%}), {stats['cache_size']} entries, "
            f"{stats['eviction_count']} evictions"
        )
