from __future__ import annotations

"""
Templates and Instances for Context Engineering.

This module defines minimal, canonical schemas intended to compile and run.
"""

from dataclasses import dataclass, field, replace
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime
import hashlib
import json


class ContextScope(Enum):
    LOCAL = "local"
    PUBLIC = "public"
    PRIVATE = "private"
    SYSTEM = "system"


class TokenBudget:
    """Simple sectioned token budget."""

    def __init__(self, total: int = 4000, sections: Optional[Dict[str, int]] = None):
        self.total = total
        if sections is None:
            sections = {
                "instructions": int(total * 0.2),
                "knowledge": int(total * 0.5),
                "examples": int(total * 0.2),
                "output": int(total * 0.1),
            }
        self.sections: Dict[str, int] = dict(sections)

    def available(self, section: str) -> int:
        return self.sections.get(section, 0)

    def consume(self, section: str, tokens: int) -> int:
        avail = self.sections.get(section, 0)
        used = min(tokens, avail)
        self.sections[section] = max(0, avail - used)
        return used


@dataclass
class KnowledgeSelector:
    domain: Optional[str] = None
    task: Optional[str] = None
    trust_threshold: float = 0.6
    max_assets: int = 8
    max_age_days: Optional[int] = None

    def to_key(self) -> str:
        return f"{self.domain}:{self.task}:{self.trust_threshold}:{self.max_assets}:{self.max_age_days}"


@dataclass
class ContextTemplate:
    name: str
    version: str
    domain: str
    task: str

    instructions_template: str = ""
    example_templates: List[str] = field(default_factory=list)
    knowledge_selector: KnowledgeSelector = field(default_factory=KnowledgeSelector)
    token_budget: TokenBudget = field(default_factory=TokenBudget)
    scope: ContextScope = ContextScope.LOCAL
    output_schema: Optional[Dict[str, Any]] = None

    # Derived
    signature: str = field(init=False)

    def __post_init__(self) -> None:
        payload = {
            "name": self.name,
            "version": self.version,
            "domain": self.domain,
            "task": self.task,
            "instructions": self.instructions_template,
            "examples": self.example_templates,
            "selector": self.knowledge_selector.__dict__,
        }
        content = json.dumps(payload, sort_keys=True)
        self.signature = hashlib.sha256(content.encode()).hexdigest()[:16]

    def create_spec(self, overrides: Optional[Dict[str, Any]] = None) -> ContextSpec:
        return ContextSpec(
            template_name=self.name,
            template_version=self.version,
            overrides=overrides or {},
        )


@dataclass
class ContextInstance:
    template_signature: str
    domain: str
    task: str
    instructions: str
    knowledge_chunks: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    total_tokens: int = 0
    knowledge_sources: List[str] = field(default_factory=list)
    assembly_time: datetime = field(default_factory=datetime.now)
    cache_key: str = field(default="")

    def __post_init__(self) -> None:
        key_src = f"{self.template_signature}:{len(self.knowledge_chunks)}:{len(self.examples)}:{self.domain}:{self.task}"
        self.cache_key = hashlib.md5(key_src.encode()).hexdigest()[:12]

    def to_prompt_parts(self) -> Dict[str, str]:
        parts = {"instructions": self.instructions}
        if self.knowledge_chunks:
            parts["knowledge"] = "\n\n".join(self.knowledge_chunks)
        if self.examples:
            parts["examples"] = "\n\n".join(self.examples)
        return parts


@dataclass
class ContextSpec:
    template_name: str
    template_version: str = "latest"
    overrides: Dict[str, Any] = field(default_factory=dict)
    input_data: Optional[Any] = None
    additional_context: Optional[Dict[str, Any]] = None

    def resolve_key(self) -> str:
        oh = hashlib.md5(json.dumps(self.overrides, sort_keys=True).encode()).hexdigest()[:8]
        return f"{self.template_name}:{self.template_version}:{oh}"


class ContextMerger:
    @staticmethod
    def apply_overrides(template: ContextTemplate, overrides: Dict[str, Any]) -> ContextTemplate:
        t = replace(template)
        if "instructions_template" in overrides:
            t.instructions_template = overrides["instructions_template"]
        if "example_templates" in overrides and isinstance(overrides["example_templates"], list):
            # append + dedup preserving order
            merged = t.example_templates + list(overrides["example_templates"])  # type: ignore
            seen, out = set(), []
            for e in merged:
                if e not in seen:
                    seen.add(e)
                    out.append(e)
            t.example_templates = out
        if "token_budget" in overrides and isinstance(overrides["token_budget"], dict):
            tb = TokenBudget(template.token_budget.total, sections=overrides["token_budget"])  # type: ignore
            t.token_budget = tb
        return t
