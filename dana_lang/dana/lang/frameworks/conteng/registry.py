"""
Domain Registry and Canonical Knowledge Asset Schema

Provides centralized management of domain packs, context templates, and knowledge assets
with versioning, caching, and conflict resolution.
"""

from dataclasses import dataclass, field
from typing import Any
from datetime import datetime, timedelta
import json
from pathlib import Path


@dataclass
class KnowledgeAsset:
    """Canonical knowledge asset schema for consistency across all systems"""

    # Identity
    domain: str  # Domain this asset belongs to
    name: str  # Asset name/identifier
    version: str  # Semantic version

    # Content
    tasks: list[str]  # Tasks this asset applies to
    content: str  # Knowledge content as string
    source: str  # Source system/URL/file

    # Quality metrics (for architect selection)
    trust_score: float  # 0.0-1.0 trust level
    age_days: int  # Age in days for freshness calculation

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate asset on creation"""
        if not (0.0 <= self.trust_score <= 1.0):
            raise ValueError(f"trust_score must be 0.0-1.0, got {self.trust_score}")
        if self.age_days < 0:
            raise ValueError(f"age_days must be non-negative, got {self.age_days}")

    @property
    def recency_score(self) -> float:
        """Calculate recency score (1.0 = today, decays over time)"""
        if self.age_days == 0:
            return 1.0
        return max(0.0, 1.0 - (self.age_days / 365.0))  # Linear decay over 1 year

    @property
    def combined_score(self) -> float:
        """Combined quality score for ranking"""
        return self.trust_score * 0.7 + self.recency_score * 0.3


@dataclass
class DomainPackManifest:
    """Metadata for a domain pack"""

    name: str
    version: str
    description: str
    author: str
    dependencies: list[str] = field(default_factory=list)
    templates: list[str] = field(default_factory=list)
    knowledge_assets: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class DomainRegistry:
    """Central registry for domain packs, templates, and knowledge assets"""

    def __init__(self, base_path: str | None = None):
        self.base_path = Path(base_path) if base_path else Path(__file__).parent / "domain_packs"
        self._template_cache: dict[str, Any] = {}
        self._asset_cache: dict[str, list[KnowledgeAsset]] = {}
        self._domain_packs: dict[str, Any] = {}
        self._cache_ttl = timedelta(hours=1)
        self._last_cache_update: dict[str, datetime] = {}

        # Load available domain packs
        self._discover_domain_packs()

    def _discover_domain_packs(self):
        """Discover and load available domain packs"""
        if not self.base_path.exists():
            return

        for domain_dir in self.base_path.iterdir():
            if domain_dir.is_dir() and not domain_dir.name.startswith("_"):
                try:
                    self._load_domain_pack(domain_dir.name)
                except Exception as e:
                    print(f"Warning: Failed to load domain pack {domain_dir.name}: {e}")

    def _load_domain_pack(self, domain_name: str):
        """Load a specific domain pack"""
        domain_path = self.base_path / domain_name

        # Try to import the domain pack module
        try:
            import importlib.util

            module_path = domain_path / "domain_pack.py"
            if module_path.exists():
                spec = importlib.util.spec_from_file_location(f"domain_pack_{domain_name}", module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Look for DomainPack class
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and hasattr(attr, "domain") and hasattr(attr, "get_context_template"):
                        self._domain_packs[domain_name] = attr()
                        break
        except Exception as e:
            print(f"Warning: Could not load domain pack {domain_name}: {e}")

    def get_template(self, name: str, version: str | None = None) -> Any | None:
        """Get context template by name and version"""
        cache_key = f"{name}:{version or 'latest'}"

        # Check cache
        if cache_key in self._template_cache:
            if self._is_cache_fresh(cache_key):
                return self._template_cache[cache_key]

        # Search domain packs for template
        for domain_name, domain_pack in self._domain_packs.items():
            if hasattr(domain_pack, "workflow_templates"):
                for template_name, template in domain_pack.workflow_templates.items():
                    if template_name == name:
                        # Convert to canonical ContextTemplate
                        canonical_template = self._convert_to_canonical_template(template, domain_name)
                        self._template_cache[cache_key] = canonical_template
                        self._last_cache_update[cache_key] = datetime.now()
                        return canonical_template

        return None

    def get_knowledge_assets(self, domain: str, task: str | None = None) -> list[KnowledgeAsset]:
        """Get knowledge assets for domain and optional task"""
        cache_key = f"{domain}:{task or 'all'}"

        # Check cache
        if cache_key in self._asset_cache:
            if self._is_cache_fresh(cache_key):
                return self._asset_cache[cache_key]

        assets = []

        # Get from domain pack
        if domain in self._domain_packs:
            domain_pack = self._domain_packs[domain]
            if hasattr(domain_pack, "knowledge_assets"):
                for asset_name, asset_data in domain_pack.knowledge_assets.items():
                    # Convert to canonical KnowledgeAsset
                    canonical_asset = self._convert_to_canonical_asset(asset_data, domain, asset_name, task)
                    if canonical_asset:
                        assets.append(canonical_asset)

        # Sort by combined score (trust + recency)
        assets.sort(key=lambda a: a.combined_score, reverse=True)

        # Cache results
        self._asset_cache[cache_key] = assets
        self._last_cache_update[cache_key] = datetime.now()

        return assets

    def _convert_to_canonical_template(self, template: Any, domain: str) -> Any:
        """Convert domain pack template to canonical ContextTemplate"""
        from .templates import ContextTemplate, KnowledgeSelector, TokenBudget

        # Extract basic info
        name = getattr(template, "name", "unknown")
        version = getattr(template, "version", "1.0")

        # Create knowledge selector
        knowledge_selector = KnowledgeSelector(
            domain=domain,
            task=getattr(template, "description", ""),
            trust_threshold=0.7,  # Default threshold
            freshness_days=30,  # Default freshness
        )

        # Create token budget
        token_budget = TokenBudget(total=4000)  # Default budget

        return ContextTemplate(
            name=name,
            version=version,
            domain=domain,
            task=getattr(template, "description", ""),
            knowledge_selector=knowledge_selector,
            token_budget=token_budget,
            instructions_template=f"You are working on {name} in the {domain} domain.",
            example_templates=[],
            output_schema=None,
        )

    def _convert_to_canonical_asset(self, asset_data: Any, domain: str, asset_name: str, task: str | None) -> KnowledgeAsset | None:
        """Convert domain pack asset to canonical KnowledgeAsset"""

        # Handle different asset formats
        if hasattr(asset_data, "content"):
            # It's already structured
            content_dict = asset_data.content
            trust_score = self._map_trust_tier_to_score(getattr(asset_data, "trust_tier", "medium"))
            age_days = self._calculate_age_days(getattr(asset_data, "freshness_ttl", 24))

        elif isinstance(asset_data, dict):
            # It's a dict
            content_dict = asset_data
            trust_score = 0.8  # Default
            age_days = 1  # Default to recent
        else:
            # Can't handle this format
            return None

        # Convert content dict to string
        if isinstance(content_dict, dict):
            content_str = json.dumps(content_dict, indent=2)
        else:
            content_str = str(content_dict)

        # Determine applicable tasks
        tasks = []
        if task:
            tasks.append(task)
        if hasattr(asset_data, "metadata"):
            tasks.extend(asset_data.metadata.get("tasks", []))
        if not tasks:
            tasks = ["general"]  # Default task

        return KnowledgeAsset(
            domain=domain,
            name=asset_name,
            version="1.0",
            tasks=tasks,
            content=content_str,
            source=f"domain_pack_{domain}",
            trust_score=trust_score,
            age_days=age_days,
            metadata={"asset_type": type(asset_data).__name__},
        )

    def _map_trust_tier_to_score(self, trust_tier: str) -> float:
        """Map string trust tier to numeric score"""
        mapping = {"high": 0.9, "medium": 0.7, "low": 0.4}
        return mapping.get(trust_tier.lower(), 0.7)

    def _calculate_age_days(self, freshness_ttl_hours: int) -> int:
        """Calculate age in days from freshness TTL"""
        # Assume assets are as old as their TTL suggests they should be refreshed
        return max(1, freshness_ttl_hours // 24)

    def _is_cache_fresh(self, cache_key: str) -> bool:
        """Check if cache entry is still fresh"""
        if cache_key not in self._last_cache_update:
            return False

        age = datetime.now() - self._last_cache_update[cache_key]
        return age < self._cache_ttl

    def register_domain_pack(self, domain_pack: Any):
        """Register a domain pack programmatically"""
        if hasattr(domain_pack, "domain"):
            self._domain_packs[domain_pack.domain] = domain_pack
        else:
            raise ValueError("Domain pack must have 'domain' attribute")

    def register_knowledge_asset(self, asset: KnowledgeAsset):
        """Register a knowledge asset programmatically"""
        # For now, just add to cache - could be extended to persist
        # Store under 'all' key so it can be retrieved by get_knowledge_assets with no task filter
        cache_key = f"{asset.domain}:all"
        if cache_key not in self._asset_cache:
            self._asset_cache[cache_key] = []
        self._asset_cache[cache_key].append(asset)
        self._last_cache_update[cache_key] = datetime.now()

    def list_domains(self) -> list[str]:
        """List available domains"""
        return list(self._domain_packs.keys())

    def list_templates(self, domain: str | None = None) -> list[dict[str, str]]:
        """List available templates, optionally filtered by domain"""
        templates = []

        for domain_name, domain_pack in self._domain_packs.items():
            if domain and domain_name != domain:
                continue

            if hasattr(domain_pack, "workflow_templates"):
                for template_name in domain_pack.workflow_templates.keys():
                    templates.append(
                        {
                            "name": template_name,
                            "domain": domain_name,
                            "version": "1.0",  # TODO: get actual version
                        }
                    )

        return templates

    def clear_cache(self):
        """Clear all caches"""
        self._template_cache.clear()
        self._asset_cache.clear()
        self._last_cache_update.clear()


# Global registry instance
_global_registry: DomainRegistry | None = None


def get_registry() -> DomainRegistry:
    """Get the global domain registry instance"""
    global _global_registry
    if _global_registry is None:
        _global_registry = DomainRegistry()
    return _global_registry
