"""Context builder for assembling LLM context from multiple sources.

Automatically selects access patterns based on source type:
- String sources: included directly if they fit the budget
- RLMResource/LTMemory sources: queried via RLM pattern with the task context
"""

from typing import Protocol, runtime_checkable

from dana.core.context.context import Context


def _estimate_tokens(text: str) -> int:
    """Estimate token count using simple heuristic.

    Uses max(word_count, char_count // 4) as a reasonable approximation.
    """
    if not text:
        return 0
    words = text.split()
    return max(len(words), len(text) // 4)


@runtime_checkable
class Queryable(Protocol):
    """Protocol for sources that support query()."""

    def query(self, question: str) -> str:
        """Query the source with a question."""
        ...


class ContextBuilder:
    """Builds LLM context from multiple sources.

    Sources can be strings (included directly) or Queryable objects
    like RLMResource or LTMemory (queried with the task context).
    """

    def __init__(self, token_budget: int = 100000):
        """Initialize ContextBuilder.

        Args:
            token_budget: Maximum tokens for the assembled context
        """
        self.token_budget = token_budget
        self._sources: dict[str, str | Queryable] = {}

    def add_source(self, name: str, source: str | Queryable) -> None:
        """Register a source for context assembly.

        Args:
            name: Identifier for this source
            source: Either a string (direct inclusion) or a Queryable
                   object like RLMResource or LTMemory (RLM query)
        """
        self._sources[name] = source

    def build(self, task: str = "") -> Context:
        """Assemble context from registered sources.

        For each source:
        - If string and fits budget: include directly
        - If Queryable: query with task, include the answer

        Args:
            task: The current task context for querying RLM sources

        Returns:
            Context with assembled text, token usage, and source info
        """
        parts: list[str] = []
        sources_used: list[str] = []
        tokens_used = 0

        for name, source in self._sources.items():
            if isinstance(source, str):
                # Direct string source
                source_tokens = _estimate_tokens(source)
                if tokens_used + source_tokens <= self.token_budget:
                    parts.append(source)
                    sources_used.append(name)
                    tokens_used += source_tokens
            elif isinstance(source, Queryable):
                # Queryable source - use RLM query with task
                query = task if task else f"What is relevant from {name}?"
                try:
                    result = source.query(query)
                    result_tokens = _estimate_tokens(result)
                    if tokens_used + result_tokens <= self.token_budget:
                        parts.append(result)
                        sources_used.append(name)
                        tokens_used += result_tokens
                except Exception:
                    # Skip sources that fail to query
                    pass

        text = "\n\n".join(parts)
        # Recalculate tokens for joined text (accounts for separators)
        final_tokens = _estimate_tokens(text)

        return Context(
            text=text,
            tokens_used=final_tokens,
            sources_used=sources_used,
            budget=self.token_budget,
        )
