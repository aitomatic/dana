"""
Runtime Context Optimization

Provides performance optimization, caching, and learning capabilities
for context engineering systems.
"""

from dataclasses import dataclass, field
from typing import Any
from datetime import datetime, timedelta
import threading
from collections import defaultdict


@dataclass
class ContextPerformanceMetrics:
    """Performance metrics for a context usage"""

    context_signature: str
    task_type: str
    domain: str

    # Performance metrics
    assembly_time_ms: float
    token_count: int
    success: bool
    quality_score: float | None = None

    # Resource usage
    cache_hit: bool = False
    knowledge_assets_used: int = 0
    tool_calls: int = 0

    # Timing
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging/storage"""
        return {
            "context_signature": self.context_signature,
            "task_type": self.task_type,
            "domain": self.domain,
            "assembly_time_ms": self.assembly_time_ms,
            "token_count": self.token_count,
            "success": self.success,
            "quality_score": self.quality_score,
            "cache_hit": self.cache_hit,
            "knowledge_assets_used": self.knowledge_assets_used,
            "tool_calls": self.tool_calls,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class OptimizationRecommendation:
    """Recommendation for context optimization"""

    context_signature: str
    recommendation_type: str  # 'token_budget', 'knowledge_selection', 'template_change'
    description: str
    impact_estimate: float  # 0.0-1.0 estimated improvement
    confidence: float  # 0.0-1.0 confidence in recommendation

    # Specific changes
    changes: dict[str, Any] = field(default_factory=dict)

    def apply_to_template(self, template: Any) -> Any:
        """Apply this recommendation to a template"""
        # This would modify the template based on the recommendation
        # Implementation depends on specific recommendation type
        return template


class ContextCache:
    """High-performance context caching with TTL and LRU eviction"""

    def __init__(self, max_size: int = 1000, default_ttl: timedelta = timedelta(hours=1)):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: dict[str, tuple[Any, datetime]] = {}
        self._access_times: dict[str, datetime] = {}
        self._lock = threading.RLock()

    def get(self, key: str) -> Any | None:
        """Get cached context if available and fresh"""
        with self._lock:
            if key in self._cache:
                context, expiry = self._cache[key]
                if datetime.now() < expiry:
                    # Update access time for LRU
                    self._access_times[key] = datetime.now()
                    return context
                else:
                    # Expired - remove
                    del self._cache[key]
                    if key in self._access_times:
                        del self._access_times[key]
        return None

    def put(self, key: str, context: Any, ttl: timedelta | None = None):
        """Cache context with TTL"""
        with self._lock:
            # Ensure we don't exceed max size
            if len(self._cache) >= self.max_size:
                self._evict_lru()

            expiry = datetime.now() + (ttl or self.default_ttl)
            self._cache[key] = (context, expiry)
            self._access_times[key] = datetime.now()

    def _evict_lru(self):
        """Evict least recently used item"""
        if not self._access_times:
            return

        lru_key = min(self._access_times.keys(), key=lambda k: self._access_times[k])
        if lru_key in self._cache:
            del self._cache[lru_key]
        del self._access_times[lru_key]

    def clear(self):
        """Clear all cached contexts"""
        with self._lock:
            self._cache.clear()
            self._access_times.clear()

    def stats(self) -> dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            now = datetime.now()
            active_entries = sum(1 for _, expiry in self._cache.values() if now < expiry)

            return {
                "total_entries": len(self._cache),
                "active_entries": active_entries,
                "expired_entries": len(self._cache) - active_entries,
                "max_size": self.max_size,
                "utilization": len(self._cache) / self.max_size,
            }


class RuntimeContextOptimizer:
    """Runtime optimization engine for context performance"""

    def __init__(self, cache_size: int = 1000):
        self.cache = ContextCache(max_size=cache_size)
        self.metrics: list[ContextPerformanceMetrics] = []
        self.recommendations: dict[str, list[OptimizationRecommendation]] = defaultdict(list)
        self._lock = threading.RLock()

        # Performance tracking
        self.hit_rate_window = 100  # Track hit rate over last N requests
        self.recent_hits: list[bool] = []

    def get_cached_context(self, signature: str) -> Any | None:
        """Get cached context instance"""
        context = self.cache.get(signature)

        # Track cache hit/miss
        with self._lock:
            self.recent_hits.append(context is not None)
            if len(self.recent_hits) > self.hit_rate_window:
                self.recent_hits.pop(0)

        return context

    def cache_context(self, signature: str, context: Any, ttl: timedelta | None = None):
        """Cache a context instance"""
        self.cache.put(signature, context, ttl)

    def record_performance(self, metrics: ContextPerformanceMetrics):
        """Record performance metrics for analysis"""
        with self._lock:
            self.metrics.append(metrics)

            # Keep only recent metrics (last 1000 entries)
            if len(self.metrics) > 1000:
                self.metrics = self.metrics[-1000:]

    def get_cache_hit_rate(self) -> float:
        """Get recent cache hit rate"""
        with self._lock:
            if not self.recent_hits:
                return 0.0
            return sum(self.recent_hits) / len(self.recent_hits)

    def analyze_performance(self, domain: str | None = None) -> dict[str, Any]:
        """Analyze recent performance metrics"""
        with self._lock:
            relevant_metrics = self.metrics
            if domain:
                relevant_metrics = [m for m in self.metrics if m.domain == domain]

        if not relevant_metrics:
            return {"error": "No metrics available"}

        # Calculate statistics
        total_requests = len(relevant_metrics)
        successful_requests = sum(1 for m in relevant_metrics if m.success)
        success_rate = successful_requests / total_requests

        assembly_times = [m.assembly_time_ms for m in relevant_metrics]
        token_counts = [m.token_count for m in relevant_metrics]

        cache_hits = sum(1 for m in relevant_metrics if m.cache_hit)
        cache_hit_rate = cache_hits / total_requests

        quality_scores = [m.quality_score for m in relevant_metrics if m.quality_score is not None]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else None

        return {
            "domain": domain or "all",
            "total_requests": total_requests,
            "success_rate": success_rate,
            "cache_hit_rate": cache_hit_rate,
            "avg_assembly_time_ms": sum(assembly_times) / len(assembly_times),
            "avg_token_count": sum(token_counts) / len(token_counts),
            "avg_quality_score": avg_quality,
            "analysis_timestamp": datetime.now().isoformat(),
        }

    def generate_recommendations(self, domain: str | None = None) -> list[OptimizationRecommendation]:
        """Generate optimization recommendations based on performance data"""
        recommendations = []

        with self._lock:
            relevant_metrics = self.metrics
            if domain:
                relevant_metrics = [m for m in self.metrics if m.domain == domain]

        if len(relevant_metrics) < 10:  # Need enough data
            return recommendations

        # Analyze token usage patterns
        token_counts = [m.token_count for m in relevant_metrics]
        avg_tokens = sum(token_counts) / len(token_counts)
        high_token_requests = [m for m in relevant_metrics if m.token_count > avg_tokens * 1.5]

        if len(high_token_requests) > len(relevant_metrics) * 0.3:  # >30% high token usage
            recommendations.append(
                OptimizationRecommendation(
                    context_signature="high_token_usage",
                    recommendation_type="token_budget",
                    description="Consider reducing token budgets - 30%+ of requests use excessive tokens",
                    impact_estimate=0.3,
                    confidence=0.8,
                    changes={"action": "reduce_token_budgets", "factor": 0.8},
                )
            )

        # Analyze cache performance
        cache_hit_rate = sum(1 for m in relevant_metrics if m.cache_hit) / len(relevant_metrics)
        if cache_hit_rate < 0.5:  # Low cache hit rate
            recommendations.append(
                OptimizationRecommendation(
                    context_signature="low_cache_hit_rate",
                    recommendation_type="caching",
                    description=f"Cache hit rate is {cache_hit_rate:.2f} - consider longer TTL or better signatures",
                    impact_estimate=0.4,
                    confidence=0.7,
                    changes={"action": "increase_ttl", "factor": 2.0},
                )
            )

        # Analyze assembly time patterns
        assembly_times = [m.assembly_time_ms for m in relevant_metrics]
        avg_assembly_time = sum(assembly_times) / len(assembly_times)
        if avg_assembly_time > 100:  # Slow assembly
            recommendations.append(
                OptimizationRecommendation(
                    context_signature="slow_assembly",
                    recommendation_type="knowledge_selection",
                    description=f"Average assembly time {avg_assembly_time:.1f}ms is high - reduce knowledge assets",
                    impact_estimate=0.5,
                    confidence=0.6,
                    changes={"action": "reduce_assets", "max_assets": 5},
                )
            )

        return recommendations

    def apply_recommendation(self, recommendation: OptimizationRecommendation, template: Any) -> Any:
        """Apply optimization recommendation to a template"""
        # This is a simplified implementation
        # Real implementation would modify templates based on recommendation type

        if recommendation.recommendation_type == "token_budget":
            if hasattr(template, "token_budget"):
                factor = recommendation.changes.get("factor", 0.8)
                template.token_budget.total = int(template.token_budget.total * factor)
                # Redistribute sections
                for section in template.token_budget.sections:
                    template.token_budget.sections[section] = int(template.token_budget.sections[section] * factor)

        elif recommendation.recommendation_type == "knowledge_selection":
            if hasattr(template, "knowledge_selector"):
                max_assets = recommendation.changes.get("max_assets", 5)
                template.knowledge_selector.max_assets = min(template.knowledge_selector.max_assets, max_assets)

        return template

    def get_stats(self) -> dict[str, Any]:
        """Get comprehensive optimizer statistics"""
        return {
            "cache_stats": self.cache.stats(),
            "performance_stats": self.analyze_performance(),
            "cache_hit_rate": self.get_cache_hit_rate(),
            "total_metrics_recorded": len(self.metrics),
            "recommendations_available": len(self.recommendations),
        }
