"""
Context Templates and Instances

Defines the core data structures for context engineering:
- ContextTemplate: Reusable patterns with selectors and constraints
- ContextInstance: Assembled, measured contexts ready for LLM calls
- ContextSpec: Lightweight references that resolve to instances
"""

from dataclasses import dataclass, field
from typing import Any
from enum import Enum
import json
import hashlib
from datetime import datetime

from .registry import KnowledgeAsset


class ContextScope(Enum):
    """Context visibility scope for privacy/security"""

    LOCAL = "local"
    PUBLIC = "public"
    PRIVATE = "private"
    SYSTEM = "system"


class TokenBudget:
    """Token budget management with section allocation"""

    def __init__(self, total: int = 4000):
        self.total = total
        self.sections = {
            "instructions": int(total * 0.15),  # System instructions
            "knowledge": int(total * 0.40),  # Domain knowledge
            "examples": int(total * 0.25),  # Few-shot examples
            "memory": int(total * 0.10),  # Conversation history
            "output": int(total * 0.10),  # Output formatting
        }

        # Support for tokenizer-based estimates
        self._tokenizer = None

    def allocate(self, section: str, tokens: int) -> bool:
        """Check if section has token budget available"""
        return self.sections.get(section, 0) >= tokens

    def consume(self, section: str, tokens: int):
        """Consume tokens from section budget"""
        if section in self.sections:
            self.sections[section] = max(0, self.sections[section] - tokens)

    def set_tokenizer(self, tokenizer_type: str = "default"):
        """Set tokenizer for accurate token estimates"""
        from .tokenizer import get_tokenizer

        self._tokenizer = get_tokenizer(tokenizer_type)

    def estimate_tokens(self, text: str) -> int:
        """Estimate tokens in text using tokenizer if available"""
        if self._tokenizer:
            return self._tokenizer.count_tokens(text)
        else:
            # Fallback to word-based estimate
            return len(text.split()) * 1.3


@dataclass
class KnowledgeSelector:
    """Selects knowledge assets based on metadata filters"""

    domain: str | None = None
    task: str | None = None
    trust_threshold: float = 0.7
    freshness_days: int | None = None
    max_assets: int = 10

    def matches(self, asset: "KnowledgeAsset") -> bool:
        """Check if asset matches selector criteria"""
        if self.domain and asset.domain != self.domain:
            return False
        if self.task and self.task not in asset.tasks:
            return False
        if asset.trust_score < self.trust_threshold:
            return False
        if self.freshness_days and asset.age_days > self.freshness_days:
            return False
        return True


@dataclass
class ContextTemplate:
    """Reusable context pattern with assembly rules"""

    name: str
    version: str
    domain: str
    task: str

    # Assembly configuration
    knowledge_selector: KnowledgeSelector = field(default_factory=KnowledgeSelector)
    token_budget: TokenBudget = field(default_factory=TokenBudget)
    scope: ContextScope = ContextScope.LOCAL

    # Template structure
    instructions_template: str = ""
    example_templates: list[str] = field(default_factory=list)
    output_schema: dict[str, Any] | None = None

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = "system"
    tags: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Generate template signature for caching"""
        content = json.dumps(
            {
                "name": self.name,
                "version": self.version,
                "domain": self.domain,
                "task": self.task,
                "instructions": self.instructions_template,
                "examples": self.example_templates,
                "schema": self.output_schema,
            },
            sort_keys=True,
        )
        self.signature = hashlib.sha256(content.encode()).hexdigest()[:16]

    def create_spec(self, overrides: dict[str, Any] | None = None) -> "ContextSpec":
        """Create a specification that can be resolved to instance"""
        return ContextSpec(template_name=self.name, template_version=self.version, overrides=overrides or {})


@dataclass
class ContextInstance:
    """Assembled context ready for LLM consumption"""

    template_signature: str
    domain: str
    task: str

    # Assembled content
    instructions: str
    knowledge_chunks: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)
    memory: list[str] = field(default_factory=list)

    # Metrics and provenance
    total_tokens: int = 0
    knowledge_sources: list[str] = field(default_factory=list)
    assembly_time: datetime = field(default_factory=datetime.now)
    cache_key: str = ""

    # Performance tracking
    usage_count: int = 0
    success_rate: float = 0.0
    avg_quality_score: float = 0.0

    def __post_init__(self):
        """Generate cache key for reuse"""
        content = f"{self.template_signature}:{len(self.knowledge_chunks)}:{len(self.examples)}"
        self.cache_key = hashlib.md5(content.encode()).hexdigest()[:12]

    def to_prompt_parts(self) -> dict[str, str]:
        """Convert to parts suitable for LLM prompt assembly"""
        parts = {"instructions": self.instructions}

        if self.knowledge_chunks:
            parts["knowledge"] = "\n\n".join(self.knowledge_chunks)

        if self.examples:
            parts["examples"] = "\n\n".join(self.examples)

        if self.memory:
            parts["memory"] = "\n\n".join(self.memory)

        return parts

    def update_performance(self, success: bool, quality_score: float = 0.0):
        """Update performance metrics based on usage"""
        self.usage_count += 1

        # Update success rate with exponential moving average
        alpha = 0.1
        self.success_rate = (1 - alpha) * self.success_rate + alpha * (1.0 if success else 0.0)

        # Update quality score
        if quality_score > 0:
            self.avg_quality_score = (1 - alpha) * self.avg_quality_score + alpha * quality_score


@dataclass
class ContextSpec:
    """Lightweight reference to a context template with overrides"""

    template_name: str
    template_version: str = "latest"
    overrides: dict[str, Any] = field(default_factory=dict)

    # Runtime parameters
    input_data: Any | None = None
    additional_context: dict[str, Any] | None = None

    def resolve_key(self) -> str:
        """Generate key for caching resolved instances"""
        override_hash = hashlib.md5(json.dumps(self.overrides, sort_keys=True).encode()).hexdigest()[:8]

        return f"{self.template_name}:{self.template_version}:{override_hash}"


class ContextMerger:
    """Handles context inheritance and composition"""

    @staticmethod
    def merge_templates(base: ContextTemplate, overlay: ContextTemplate) -> ContextTemplate:
        """Merge overlay template over base with conflict resolution"""
        merged = ContextTemplate(
            name=f"{base.name}+{overlay.name}",
            version=f"{base.version}+{overlay.version}",
            domain=overlay.domain or base.domain,
            task=overlay.task or base.task,
        )

        # Merge instructions (overlay wins)
        merged.instructions_template = overlay.instructions_template or base.instructions_template

        # Merge examples (concatenate with dedup)
        all_examples = base.example_templates + overlay.example_templates
        merged.example_templates = list(dict.fromkeys(all_examples))  # Dedup preserving order

        # Merge schemas (deep merge)
        merged.output_schema = base.output_schema or {}
        if overlay.output_schema:
            merged.output_schema.update(overlay.output_schema)

        # Merge token budgets (overlay limits win)
        merged.token_budget = overlay.token_budget

        # Merge selectors (overlay preferences win)
        merged.knowledge_selector = KnowledgeSelector(
            domain=overlay.knowledge_selector.domain or base.knowledge_selector.domain,
            task=overlay.knowledge_selector.task or base.knowledge_selector.task,
            trust_threshold=max(base.knowledge_selector.trust_threshold, overlay.knowledge_selector.trust_threshold),
            freshness_days=min(base.knowledge_selector.freshness_days or 999, overlay.knowledge_selector.freshness_days or 999),
            max_assets=min(base.knowledge_selector.max_assets, overlay.knowledge_selector.max_assets),
        )

        return merged

    @staticmethod
    def apply_overrides(template: ContextTemplate, overrides: dict[str, Any]) -> ContextTemplate:
        """Apply runtime overrides to template"""
        # Create copy to avoid mutation
        modified = ContextTemplate(
            name=template.name,
            version=template.version,
            domain=template.domain,
            task=template.task,
            knowledge_selector=template.knowledge_selector,
            token_budget=template.token_budget,
            scope=template.scope,
            instructions_template=template.instructions_template,
            example_templates=template.example_templates.copy(),
            output_schema=template.output_schema.copy() if template.output_schema else None,
        )

        # Apply overrides
        for key, value in overrides.items():
            if hasattr(modified, key):
                setattr(modified, key, value)

        return modified
