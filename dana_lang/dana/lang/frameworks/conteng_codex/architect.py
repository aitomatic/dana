from __future__ import annotations

"""
ContextArchitect builds ContextInstance from a template and registry assets.
"""

from datetime import datetime, timedelta
import logging

from .templates import ContextTemplate, ContextInstance, ContextSpec
from .registry import DomainRegistry, KnowledgeAsset

logger = logging.getLogger(__name__)


class ContextArchitect:
    def __init__(self, registry: DomainRegistry):
        self.registry = registry
        self._cache: dict[str, tuple[ContextInstance, datetime]] = {}
        self._ttl = timedelta(minutes=30)

    def build(self, spec: ContextSpec) -> ContextInstance:
        key = spec.resolve_key()
        now = datetime.now()
        if key in self._cache:
            inst, ts = self._cache[key]
            if now - ts < self._ttl:
                logger.debug("CE cache hit: %s", key)
                return inst

        template = self.registry.get_template(spec.template_name, spec.template_version)
        if not template:
            raise ValueError(f"Unknown template {spec.template_name}:{spec.template_version}")

        inst = self._assemble(template, spec)
        self._cache[key] = (inst, now)
        return inst

    # -- internals --
    def _assemble(self, template: ContextTemplate, spec: ContextSpec) -> ContextInstance:
        # Base instance
        inst = ContextInstance(
            template_signature=template.signature,
            domain=template.domain,
            task=template.task,
            instructions=template.instructions_template,
        )

        # Select knowledge assets
        assets = self._select_assets(template)
        chunks, used_tokens, sources = self._pack_assets(assets, template)
        inst.knowledge_chunks = chunks
        inst.knowledge_sources = sources

        # Examples
        ex_chunks, ex_tokens = self._pack_examples(template)
        inst.examples = ex_chunks

        # Token accounting (naive word-count * 1.3)
        inst.total_tokens = int(_approx_tokens(inst.instructions) + used_tokens + ex_tokens)

        return inst

    def _select_assets(self, template: ContextTemplate) -> list[KnowledgeAsset]:
        sel = template.knowledge_selector
        assets = self.registry.get_knowledge_assets(domain=sel.domain or template.domain, task=sel.task or template.task)
        # Filter by trust and age
        out: list[KnowledgeAsset] = []
        for a in assets:
            if a.trust_score < sel.trust_threshold:
                continue
            if sel.max_age_days is not None and a.age_days > sel.max_age_days:
                continue
            out.append(a)
        # Rank by trust * recency
        out.sort(key=lambda a: a.trust_score * a.recency_score, reverse=True)
        return out[: sel.max_assets]

    def _pack_assets(self, assets: list[KnowledgeAsset], template: ContextTemplate) -> tuple[list[str], int, list[str]]:
        max_tokens = template.token_budget.available("knowledge")
        total = 0
        chunks: list[str] = []
        sources: list[str] = []
        for a in assets:
            t = int(_approx_tokens(a.content))
            if total + t <= max_tokens:
                chunks.append(f"[{a.source}] {a.content}")
                sources.append(a.source)
                total += t
            else:
                remaining = max_tokens - total
                if remaining > 40:  # minimal useful chunk
                    # truncate by words approximation
                    words = a.content.split()
                    approx_words = int(remaining / 1.3)
                    chunks.append(f"[{a.source}] {' '.join(words[:approx_words])}...")
                    sources.append(a.source)
                    total = max_tokens
                break
        return chunks, total, sources

    def _pack_examples(self, template: ContextTemplate) -> tuple[list[str], int]:
        max_tokens = template.token_budget.available("examples")
        total = 0
        out: list[str] = []
        for ex in template.example_templates:
            t = int(_approx_tokens(ex))
            if total + t <= max_tokens:
                out.append(ex)
                total += t
            else:
                break
        return out, total


def _approx_tokens(text: str) -> float:
    # naive but fast
    return len(text.split()) * 1.3
