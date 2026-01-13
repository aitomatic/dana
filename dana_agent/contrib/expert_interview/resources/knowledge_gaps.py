"""
Knowledge Gap Detector Resource

Identifies knowledge gaps between two sources (e.g., expert vs. documentation).
Domain-agnostic gap detection with quote comparison.
"""

import asyncio
import json
import time

from dana.common.llm.llm import LLM, LLMMessage
from dana.common.observable import observable
from dana.common.protocols import DictParams
from dana.common.protocols.war import tool_use
from dana.core.resource.base_resource import BaseResource


class KnowledgeGapDetector(BaseResource):
    """
    <PUBLIC_DESCRIPTION>
    Identifies knowledge gaps between two sources using quote comparison.

    Compares expert knowledge with reference materials to identify:
    - Information present in expert knowledge but missing from docs
    - Contradictions between sources
    - Areas needing documentation updates

    USE CASES:
    - Knowledge base gap analysis
    - Documentation validation
    - Training needs assessment
    - Expert vs. novice comparison
    - Policy vs. practice analysis
    - Quality assurance for knowledge capture

    OUTPUT:
    - gaps: List of identified gaps with original quotes
    - gap_types: Classification of gaps (missing, contradiction, enhancement)
    - recommendations: Suggested actions
    </PUBLIC_DESCRIPTION>
    """

    def __init__(self, llm_provider: str = "anthropic", model: str | None = None, resource_id: str | None = None, **kwargs):
        """
        Initialize KnowledgeGapDetector.

        Args:
            llm_provider: LLM provider (default: "anthropic")
            model: Model name (default: provider's default)
            resource_id: Resource identifier (default: "knowledge-gaps")
            **kwargs: Additional arguments for BaseResource
        """
        super().__init__(resource_id=resource_id or "knowledge-gaps", **kwargs)
        self.llm = LLM(provider=llm_provider, model=model)

    @tool_use
    @observable
    def detect_gaps(
        self,
        source1_content: list[dict] | str,
        source2_content: list[dict] | str,
        source1_label: str = "Expert Knowledge",
        source2_label: str = "Documentation",
        topic_context: dict | None = None,
        **kwargs,
    ) -> DictParams:
        """
        Detect knowledge gaps between two sources.

        Args:
            source1_content: First source (typically expert insights)
            source2_content: Second source (typically documentation)
            source1_label: Label for first source
            source2_label: Label for second source
            topic_context: Optional context about the topic being compared
            **kwargs: Additional parameters

        Returns:
            Dictionary with:
                - gaps: List of identified gaps with quotes
                - gap_types: Types of gaps found
                - recommendations: Suggested actions
                - processing_time: Time taken
        """
        result = asyncio.run(self._detect_gaps(source1_content, source2_content, source1_label, source2_label, topic_context, **kwargs))
        return result

    async def _detect_gaps(
        self, source1_content, source2_content, source1_label: str, source2_label: str, topic_context: dict | None = None, **kwargs
    ) -> DictParams:
        """Internal async implementation"""
        start_time = time.time()

        # Check if we have content to compare
        if not source2_content:
            return {
                "gaps": [],
                "gap_types": [],
                "recommendations": [f"No {source2_label.lower()} available for comparison"],
                "processing_time": 0.001,
            }

        if not source1_content:
            return {
                "gaps": [],
                "gap_types": [],
                "recommendations": [f"No {source1_label.lower()} available for comparison"],
                "processing_time": 0.001,
            }

        try:
            # Format sources
            source1_text = self._format_source(source1_content, source1_label)
            source2_text = self._format_source(source2_content, source2_label)

            topic_text = self._format_topic_context(topic_context) if topic_context else ""

            prompt = self._build_gap_detection_prompt(source1_text, source2_text, source1_label, source2_label, topic_text)

            system_message = """You are an expert knowledge analyst specializing in gap detection.
Your task is to identify differences and gaps between knowledge sources."""

            response = await self.llm.chat_response(
                messages=[LLMMessage(role="user", content=prompt)], system_message=system_message, max_tokens=1500, temperature=0.1
            )

            content = response.content if hasattr(response, "content") else str(response)

            # Parse JSON response
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]

            result = json.loads(content.strip())
            result["processing_time"] = time.time() - start_time

            return result

        except Exception as e:
            return self._create_fallback_response(str(e))

    def _format_source(self, content, label: str) -> str:
        """Format source content for comparison"""
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            parts = []
            for item in content[:10]:  # Limit to prevent token overflow
                if isinstance(item, dict):
                    # Handle structured content
                    if "original_quote" in item:
                        parts.append(f"- {item['original_quote']}")
                    elif "content" in item:
                        parts.append(f"- {item['content'][:200]}")
                    elif "text" in item:
                        parts.append(f"- {item['text'][:200]}")
                    else:
                        parts.append(f"- {str(item)[:200]}")
                else:
                    parts.append(f"- {str(item)[:200]}")
            return "\n".join(parts)

        return str(content)[:1000]

    def _format_topic_context(self, context: dict) -> str:
        """Format topic context"""
        if not context:
            return ""

        parts = []
        if "current_focus" in context:
            parts.append(f"Current Focus: {context['current_focus']}")
        if "active_topics" in context:
            parts.append(f"Active Topics: {', '.join(context['active_topics'][:5])}")

        return "\n".join(parts)

    def _build_gap_detection_prompt(
        self, source1_text: str, source2_text: str, source1_label: str, source2_label: str, topic_text: str
    ) -> str:
        """Build prompt for gap detection"""
        return f"""TASK: Identify knowledge gaps between two sources.

TOPIC CONTEXT:
{topic_text if topic_text else "General comparison"}

{source1_label.upper()}:
{source1_text}

{source2_label.upper()}:
{source2_text}

INSTRUCTIONS:
1. Compare the two sources
2. Identify gaps: information in Source 1 missing from Source 2
3. Identify contradictions between sources
4. Provide recommendations for closing gaps

OUTPUT FORMAT (JSON):
{{
    "gaps": [
        {{
            "gap_type": "missing|contradiction|enhancement",
            "source1_quote": "Quote from {source1_label}",
            "source2_quote": "Quote from {source2_label} (if applicable)",
            "description": "Description of the gap",
            "severity": "high|medium|low"
        }}
    ],
    "gap_types": ["types of gaps found"],
    "recommendations": ["suggested actions to close gaps"]
}}

Focus on significant gaps, not minor differences."""

    def _create_fallback_response(self, error: str | None = None) -> DictParams:
        """Fallback when detection fails"""
        return {"gaps": [], "gap_types": [], "recommendations": ["Gap detection failed"], "processing_time": 0.001, "error": error}
