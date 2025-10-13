"""
Context Architect

Builds optimal context instances from templates and knowledge assets.
Implements the core "knowledge architecture before prompting" principle.
"""

import logging
from typing import Any
from datetime import datetime, timedelta

from .templates import ContextTemplate, ContextInstance, ContextSpec, ContextMerger, KnowledgeSelector, TokenBudget
from .registry import DomainRegistry, KnowledgeAsset
from .tokenizer import get_tokenizer


logger = logging.getLogger(__name__)


class ContextArchitect:
    """Builds optimal contexts by selecting and assembling knowledge assets"""

    def __init__(self, registry: DomainRegistry):
        self.registry = registry
        self.cache: dict[str, ContextInstance] = {}
        self.cache_ttl = timedelta(hours=1)  # Cache assembled contexts

    def build_context(self, spec: ContextSpec) -> ContextInstance:
        """Build context instance from specification"""

        # Check cache first
        cache_key = spec.resolve_key()
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if datetime.now() - cached.assembly_time < self.cache_ttl:
                logger.debug(f"Using cached context: {cache_key}")
                return cached

        # Resolve template
        template = self.registry.get_template(spec.template_name, spec.template_version)
        if not template:
            raise ValueError(f"Template not found: {spec.template_name}:{spec.template_version}")

        # Apply overrides
        if spec.overrides:
            template = ContextMerger.apply_overrides(template, spec.overrides)

        # Build context instance
        instance = self._assemble_context(template, spec)

        # Cache the result
        self.cache[cache_key] = instance

        return instance

    def _assemble_context(self, template: ContextTemplate, spec: ContextSpec) -> ContextInstance:
        """Assemble context from template and knowledge assets"""

        logger.info(f"Assembling context for {template.domain}:{template.task}")

        # Create base instance
        instance = ContextInstance(
            template_signature=template.signature, domain=template.domain, task=template.task, instructions=template.instructions_template
        )

        # Select knowledge assets
        knowledge_assets = self._select_knowledge(template.knowledge_selector)

        # Assemble knowledge chunks within budget
        knowledge_chunks, knowledge_tokens = self._assemble_knowledge(knowledge_assets, template.token_budget)
        instance.knowledge_chunks = knowledge_chunks
        instance.knowledge_sources = [asset.source for asset in knowledge_assets]

        # Assemble examples within budget
        examples, example_tokens = self._assemble_examples(template.example_templates, template.token_budget)
        instance.examples = examples

        # Add any additional context from spec
        if spec.additional_context:
            instance = self._merge_additional_context(instance, spec.additional_context)

        # Calculate total tokens using proper tokenizer
        tokenizer = get_tokenizer("default")
        instruction_tokens = tokenizer.count_tokens(instance.instructions)
        instance.total_tokens = int(instruction_tokens + knowledge_tokens + example_tokens)

        logger.info(
            f"Assembled context: {instance.total_tokens} tokens, "
            f"{len(instance.knowledge_chunks)} knowledge chunks, "
            f"{len(instance.examples)} examples"
        )

        return instance

    def _select_knowledge(self, selector: KnowledgeSelector) -> list[KnowledgeAsset]:
        """Select relevant knowledge assets based on selector criteria"""

        # Get all assets from registry
        all_assets = self.registry.get_knowledge_assets(domain=selector.domain, task=selector.task)

        # Filter based on selector criteria
        relevant_assets = []
        for asset in all_assets:
            if selector.matches(asset):
                relevant_assets.append(asset)

        # Sort by relevance score (trust * recency)
        relevant_assets.sort(key=lambda x: x.trust_score * x.recency_score, reverse=True)

        # Return top assets within limit
        return relevant_assets[: selector.max_assets]

    def _assemble_knowledge(self, assets: list[KnowledgeAsset], budget: TokenBudget) -> tuple[list[str], int]:
        """Assemble knowledge chunks within token budget"""

        chunks = []
        total_tokens = 0
        available_tokens = budget.sections.get("knowledge", 1000)

        for asset in assets:
            # Estimate tokens for this asset using proper tokenizer
            tokenizer = get_tokenizer("technical")  # Knowledge assets are typically technical
            chunk_tokens = tokenizer.count_tokens(asset.content)

            if total_tokens + chunk_tokens <= available_tokens:
                chunks.append(f"[{asset.source}] {asset.content}")
                total_tokens += int(chunk_tokens)
            else:
                # Try to fit truncated version
                remaining_tokens = available_tokens - total_tokens
                if remaining_tokens > 50:  # Minimum useful chunk size
                    words = asset.content.split()
                    # Use tokenizer to estimate word count needed for remaining tokens
                    estimated_words = int(remaining_tokens / 1.3)  # Conservative fallback
                    truncated_words = words[:estimated_words]
                    truncated_content = " ".join(truncated_words) + "..."

                    # Verify the truncated content fits
                    actual_tokens = tokenizer.count_tokens(f"[{asset.source}] {truncated_content}")
                    if actual_tokens <= remaining_tokens:
                        chunks.append(f"[{asset.source}] {truncated_content}")
                        total_tokens += actual_tokens
                    else:
                        # Further truncation needed
                        while len(truncated_words) > 5 and actual_tokens > remaining_tokens:
                            truncated_words = truncated_words[:-5]  # Remove 5 words at a time
                            truncated_content = " ".join(truncated_words) + "..."
                            actual_tokens = tokenizer.count_tokens(f"[{asset.source}] {truncated_content}")

                        if len(truncated_words) > 5:
                            chunks.append(f"[{asset.source}] {truncated_content}")
                            total_tokens += actual_tokens
                break

        return chunks, int(total_tokens)

    def _assemble_examples(self, example_templates: list[str], budget: TokenBudget) -> tuple[list[str], int]:
        """Assemble examples within token budget"""

        examples = []
        total_tokens = 0
        available_tokens = budget.sections.get("examples", 500)

        for template in example_templates:
            # Use default tokenizer for examples (typically English)
            tokenizer = get_tokenizer("default")
            example_tokens = tokenizer.count_tokens(template)

            if total_tokens + example_tokens <= available_tokens:
                examples.append(template)
                total_tokens += int(example_tokens)
            else:
                break

        return examples, int(total_tokens)

    def _merge_additional_context(self, instance: ContextInstance, additional: dict[str, Any]) -> ContextInstance:
        """Merge additional context from spec"""

        if "knowledge" in additional:
            extra_knowledge = additional["knowledge"]
            if isinstance(extra_knowledge, str):
                instance.knowledge_chunks.append(extra_knowledge)
            elif isinstance(extra_knowledge, list):
                instance.knowledge_chunks.extend(extra_knowledge)

        if "examples" in additional:
            extra_examples = additional["examples"]
            if isinstance(extra_examples, str):
                instance.examples.append(extra_examples)
            elif isinstance(extra_examples, list):
                instance.examples.extend(extra_examples)

        if "instructions" in additional:
            # Append additional instructions
            instance.instructions += "\n\n" + additional["instructions"]

        return instance

    def optimize_context(self, instance: ContextInstance, performance_feedback: dict[str, Any]) -> ContextInstance:
        """Optimize context based on performance feedback"""

        # This is a placeholder for more sophisticated optimization
        # Could implement:
        # - Remove low-performing knowledge chunks
        # - Reorder based on relevance
        # - Adjust token allocation between sections

        success_rate = performance_feedback.get("success_rate", 0.5)
        quality_score = performance_feedback.get("quality_score", 0.5)

        # Simple optimization: if performance is poor, try reducing noise
        if success_rate < 0.7 or quality_score < 0.7:
            # Remove least relevant knowledge chunks
            if len(instance.knowledge_chunks) > 3:
                instance.knowledge_chunks = instance.knowledge_chunks[:3]

            # Keep only the best examples
            if len(instance.examples) > 2:
                instance.examples = instance.examples[:2]

        return instance

    def clear_cache(self):
        """Clear the context cache"""
        self.cache.clear()

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics"""
        return {
            "total_entries": len(self.cache),
            "cache_keys": list(self.cache.keys()),
            "avg_tokens": sum(ctx.total_tokens for ctx in self.cache.values()) / len(self.cache) if self.cache else 0,
            "oldest_entry": min((ctx.assembly_time for ctx in self.cache.values()), default=None),
            "newest_entry": max((ctx.assembly_time for ctx in self.cache.values()), default=None),
        }
