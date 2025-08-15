from __future__ import annotations

"""
In‑memory Domain Registry and Knowledge Asset schema.
"""

from dataclasses import dataclass
from datetime import datetime

from .templates import ContextTemplate


@dataclass
class KnowledgeAsset:
    domain: str
    tasks: list[str]
    source: str
    content: str
    trust_score: float = 0.8  # 0..1
    created_at: datetime = datetime.now()

    @property
    def age_days(self) -> int:
        return max(0, (datetime.now() - self.created_at).days)

    @property
    def recency_score(self) -> float:
        # Simple decay: <=7 days ~ 1.0, 30d ~ 0.5, older ~ lower
        days = self.age_days
        if days <= 7:
            return 1.0
        if days >= 60:
            return 0.2
        # linear between 7 and 60
        return 1.0 - (days - 7) * (0.8 / 53)


class DomainRegistry:
    """Stores templates and assets in memory.

    This is deliberately simple for Phase A: suitable for tests/evals.
    """

    def __init__(self) -> None:
        self._templates: dict[str, dict[str, ContextTemplate]] = {}
        self._assets: list[KnowledgeAsset] = []

    # -- Templates --
    def register_template(self, template: ContextTemplate) -> None:
        self._templates.setdefault(template.name, {})[template.version] = template

    def get_template(self, name: str, version: str = "latest") -> ContextTemplate | None:
        versions = self._templates.get(name, {})
        if not versions:
            return None
        if version == "latest":
            # choose lexicographically last version
            v = sorted(versions.keys())[-1]
            return versions.get(v)
        return versions.get(version)

    # -- Knowledge --
    def register_asset(self, asset: KnowledgeAsset) -> None:
        self._assets.append(asset)

    def get_knowledge_assets(self, domain: str | None = None, task: str | None = None) -> list[KnowledgeAsset]:
        items = [a for a in self._assets if (domain is None or a.domain == domain)]
        if task is not None:
            items = [a for a in items if task in a.tasks]
        return items
