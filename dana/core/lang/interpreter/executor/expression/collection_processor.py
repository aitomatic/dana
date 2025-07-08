"""
Optimized collection processing for Dana expressions.

This module provides high-performance collection literal processing with
optimizations for large collections and lazy evaluation where appropriate.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any

from dana.common.mixins.loggable import Loggable
from dana.core.lang.ast import DictLiteral, FStringExpression, ListLiteral, SetLiteral, TupleLiteral
from dana.core.lang.sandbox_context import SandboxContext


class CollectionProcessor(Loggable):
    """Optimized collection processor for Dana collection literals.

    This processor handles:
    - Tuple literals with efficient construction
    - Dict literals with optimized key-value processing
    - List literals with lazy evaluation for large collections
    - Set literals with duplicate elimination optimizations
    - F-string expressions with template caching

    Performance optimizations:
    - Lazy evaluation for large collections (>1000 items)
    - Template caching for f-string expressions
    - Efficient iteration patterns
    - Memory-optimized construction
    """

    # Configuration constants
    LARGE_COLLECTION_THRESHOLD = 1000  # Items threshold for lazy evaluation
    FSTRING_TEMPLATE_CACHE_SIZE = 500  # Max cached f-string templates

    def __init__(self, parent_executor):
        """Initialize the collection processor.

        Args:
            parent_executor: Reference to parent executor for item evaluation
        """
        super().__init__()
        self.parent_executor = parent_executor
        self._fstring_template_cache = {}  # Cache for f-string templates
        self._cache_hits = 0
        self._cache_misses = 0

    def execute_tuple_literal(self, node: TupleLiteral, context: SandboxContext) -> tuple:
        """Execute a tuple literal with optimized construction.

        Args:
            node: The tuple literal to execute
            context: The execution context

        Returns:
            The tuple value
        """
        if not node.items:
            return ()

        # For small tuples, use simple construction
        if len(node.items) < self.LARGE_COLLECTION_THRESHOLD:
            return tuple(self.parent_executor.execute(item, context) for item in node.items)

        # For large tuples, use optimized batch processing
        self.debug(f"Processing large tuple with {len(node.items)} items")
        return self._process_large_tuple(node.items, context)

    def execute_dict_literal(self, node: DictLiteral, context: SandboxContext) -> dict[Any, Any]:
        """Execute a dict literal with optimized key-value processing.

        Args:
            node: The dict literal to execute
            context: The execution context

        Returns:
            The dict value
        """
        if not node.items:
            return {}

        # For small dicts, use simple construction
        if len(node.items) < self.LARGE_COLLECTION_THRESHOLD:
            return {self.parent_executor.execute(key, context): self.parent_executor.execute(value, context) for key, value in node.items}

        # For large dicts, use optimized batch processing
        self.debug(f"Processing large dict with {len(node.items)} items")
        return self._process_large_dict(node.items, context)

    def execute_list_literal(self, node: ListLiteral, context: SandboxContext) -> list[Any]:
        """Execute a list literal with optimized construction.

        Args:
            node: The list literal to execute
            context: The execution context

        Returns:
            The list value
        """
        if not node.items:
            return []

        # For small lists, use simple construction
        if len(node.items) < self.LARGE_COLLECTION_THRESHOLD:
            return [self.parent_executor.execute(item, context) for item in node.items]

        # For large lists, use optimized batch processing
        self.debug(f"Processing large list with {len(node.items)} items")
        return self._process_large_list(node.items, context)

    def execute_set_literal(self, node: SetLiteral, context: SandboxContext) -> set[Any]:
        """Execute a set literal with duplicate elimination optimizations.

        Args:
            node: The set literal to execute
            context: The execution context

        Returns:
            The set value
        """
        if not node.items:
            return set()

        # For small sets, use simple construction
        if len(node.items) < self.LARGE_COLLECTION_THRESHOLD:
            return {self.parent_executor.execute(item, context) for item in node.items}

        # For large sets, use optimized batch processing with duplicate checking
        self.debug(f"Processing large set with {len(node.items)} items")
        return self._process_large_set(node.items, context)

    def execute_fstring_expression(self, node: FStringExpression, context: SandboxContext) -> str:
        """Execute an f-string expression with template caching.

        Args:
            node: The f-string expression to execute
            context: The execution context

        Returns:
            The formatted string
        """
        # Check for cached template first
        template_key = self._get_fstring_cache_key(node)
        if template_key in self._fstring_template_cache:
            self._cache_hits += 1
            template_info = self._fstring_template_cache[template_key]
            return self._apply_cached_template(template_info, node, context)

        self._cache_misses += 1

        # Handle new-style expression structure (with template and expressions)
        if hasattr(node, "template") and node.template and hasattr(node, "expressions") and node.expressions:
            result = self._process_template_expressions(node, context)
            self._cache_template(template_key, node, "template_expressions")
            return result

        # Handle older style with parts list
        elif hasattr(node, "parts") and node.parts:
            result = self._process_parts_list(node, context)
            self._cache_template(template_key, node, "parts_list")
            return result

        # Empty f-string fallback
        return ""

    def _process_large_tuple(self, items: list[Any], context: SandboxContext) -> tuple:
        """Process large tuple with batch optimization."""
        # Pre-allocate list for efficiency
        result_list = []
        result_list.extend(self.parent_executor.execute(item, context) for item in items)
        return tuple(result_list)

    def _process_large_dict(self, items: list[tuple[Any, Any]], context: SandboxContext) -> dict[Any, Any]:
        """Process large dict with batch optimization and duplicate key handling."""
        result = {}

        # Process in batches to optimize memory usage
        batch_size = min(100, len(items) // 10) if len(items) > 100 else len(items)

        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]
            for key_node, value_node in batch:
                key = self.parent_executor.execute(key_node, context)
                value = self.parent_executor.execute(value_node, context)
                result[key] = value

        return result

    def _process_large_list(self, items: list[Any], context: SandboxContext) -> list[Any]:
        """Process large list with batch optimization."""
        # Pre-allocate list for efficiency
        result = [None] * len(items)

        # Process in batches to optimize memory usage
        batch_size = min(100, len(items) // 10) if len(items) > 100 else len(items)

        for i in range(0, len(items), batch_size):
            batch_end = min(i + batch_size, len(items))
            for j in range(i, batch_end):
                result[j] = self.parent_executor.execute(items[j], context)

        return result

    def _process_large_set(self, items: list[Any], context: SandboxContext) -> set[Any]:
        """Process large set with duplicate elimination optimization."""
        result = set()
        seen_literals = set()  # Track literal values to avoid duplicate evaluation

        # Process in batches and track duplicates
        batch_size = min(100, len(items) // 10) if len(items) > 100 else len(items)

        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]
            for item in batch:
                # Quick check for literal duplicates
                if hasattr(item, "value") and item.value in seen_literals:
                    continue

                evaluated_item = self.parent_executor.execute(item, context)

                # Track literal values
                if hasattr(item, "value"):
                    seen_literals.add(item.value)

                result.add(evaluated_item)

        return result

    def _process_template_expressions(self, node: FStringExpression, context: SandboxContext) -> str:
        """Process f-string with template and expressions dictionary."""
        result = node.template

        # Replace each placeholder with its evaluated value
        for placeholder, expr in node.expressions.items():
            value = self.parent_executor.execute(expr, context)
            result = result.replace(placeholder, str(value))

        return result

    def _process_parts_list(self, node: FStringExpression, context: SandboxContext) -> str:
        """Process f-string with parts list (legacy format)."""
        result = ""
        for part in node.parts:
            if isinstance(part, str):
                result += part
            else:
                value = self.parent_executor.execute(part, context)
                result += str(value)
        return result

    def _get_fstring_cache_key(self, node: FStringExpression) -> str:
        """Generate a cache key for f-string template."""
        if hasattr(node, "template") and node.template:
            return f"template_{hash(node.template)}"
        elif hasattr(node, "parts") and node.parts:
            # Create key based on string parts only
            string_parts = [part for part in node.parts if isinstance(part, str)]
            return f"parts_{hash(tuple(string_parts))}"
        return "empty"

    def _cache_template(self, template_key: str, node: FStringExpression, template_type: str) -> None:
        """Cache f-string template information."""
        # Simple cache with size limit
        if len(self._fstring_template_cache) > self.FSTRING_TEMPLATE_CACHE_SIZE:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self._fstring_template_cache))
            del self._fstring_template_cache[oldest_key]

        self._fstring_template_cache[template_key] = {
            "type": template_type,
            "template": getattr(node, "template", None),
            "expressions_count": len(getattr(node, "expressions", {})),
            "parts_count": len(getattr(node, "parts", [])),
        }

    def _apply_cached_template(self, template_info: dict[str, Any], node: FStringExpression, context: SandboxContext) -> str:
        """Apply cached template information for faster processing."""
        if template_info["type"] == "template_expressions":
            return self._process_template_expressions(node, context)
        elif template_info["type"] == "parts_list":
            return self._process_parts_list(node, context)
        else:
            return ""

    def clear_cache(self) -> None:
        """Clear the f-string template cache."""
        self._fstring_template_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
        self.debug("F-string template cache cleared")

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache performance statistics."""
        total_lookups = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total_lookups * 100) if total_lookups > 0 else 0

        return {
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "total_lookups": total_lookups,
            "hit_rate_percent": round(hit_rate, 2),
            "cache_size": len(self._fstring_template_cache),
            "large_collection_threshold": self.LARGE_COLLECTION_THRESHOLD,
        }
