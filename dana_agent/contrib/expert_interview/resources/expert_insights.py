"""
Expert Insight Analyzer Resource

Extracts expert insights from conversations with exact quote preservation.
Domain-agnostic: works for technical, medical, legal, business experts.
"""

import asyncio
import json
import time

from dana.common.llm.llm import LLM, LLMMessage
from dana.common.observable import observable
from dana.common.protocols import DictParams
from dana.common.protocols.war import tool_use
from dana.core.resource.base_resource import BaseResource


class ExpertInsightAnalyzer(BaseResource):
    """
    <PUBLIC_DESCRIPTION>
    Analyzes expert statements to extract insights with exact quote preservation.

    Identifies key insights, expertise indicators, and knowledge depth while
    preserving the expert's original terminology and phrasing.

    USE CASES:
    - Expert interviews (technical, medical, legal, business)
    - Professional consultation logging
    - Knowledge extraction from meetings
    - Subject matter expert (SME) sessions
    - Testimony analysis

    OUTPUT:
    - expert_insights_original: List of insights with exact quotes
    - key_terms: Technical terms used by expert
    - expertise_indicators: Signals of deep knowledge
    - context: Contextual information about insights
    </PUBLIC_DESCRIPTION>
    """

    def __init__(self, llm_provider: str = "anthropic", model: str | None = None, resource_id: str | None = None, **kwargs):
        """
        Initialize ExpertInsightAnalyzer.

        Args:
            llm_provider: LLM provider (default: "anthropic")
            model: Model name (default: provider's default)
            resource_id: Resource identifier (default: "expert-insights")
            **kwargs: Additional arguments for BaseResource
        """
        super().__init__(resource_id=resource_id or "expert-insights", **kwargs)
        self.llm = LLM(provider=llm_provider, model=model)

    @tool_use
    @observable
    def analyze_insights(
        self, message: str, conversation_history: list[dict[str, str]] | None = None, expert_profile: dict | None = None, **kwargs
    ) -> DictParams:
        """
        Analyze expert insights with exact quote preservation.

        Args:
            message: The expert's message to analyze
            conversation_history: Optional conversation context
            expert_profile: Optional expert profile (name, role, years_experience)
            **kwargs: Additional parameters

        Returns:
            Dictionary with:
                - expert_insights_original: List of insights with exact quotes
                - key_terms: Technical terms from expert
                - expertise_indicators: Signals of expertise level
                - context: Contextual information
                - processing_time: Time taken
        """
        result = asyncio.run(self._analyze_insights(message, conversation_history, expert_profile, **kwargs))
        return result

    async def _analyze_insights(
        self, message: str, conversation_history: list[dict[str, str]] | None = None, expert_profile: dict | None = None, **kwargs
    ) -> DictParams:
        """Internal async implementation"""
        start_time = time.time()

        try:
            # Build context
            context = self._format_context(conversation_history) if conversation_history else ""
            expert_context = self._format_expert_profile(expert_profile) if expert_profile else ""

            prompt = self._build_analysis_prompt(message, context, expert_context)

            system_message = """You are an expert at analyzing professional insights and extracting knowledge.
Your task is to identify key insights while preserving EXACT quotes and terminology."""

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
            return self._create_fallback_response(message, str(e))

    def _format_context(self, history: list[dict[str, str]], max_messages: int = 4) -> str:
        """Format conversation context"""
        recent = history[-max_messages:] if len(history) > max_messages else history
        parts = []
        for msg in recent:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:300]
            parts.append(f"{role}: {content}")
        return "\n".join(parts)

    def _format_expert_profile(self, profile: dict) -> str:
        """Format expert profile"""
        if not profile:
            return ""

        parts = []
        if "name" in profile:
            parts.append(f"Expert: {profile['name']}")
        if "role" in profile:
            parts.append(f"Role: {profile['role']}")
        if "years_experience" in profile:
            parts.append(f"Experience: {profile['years_experience']} years")
        if "domain" in profile:
            parts.append(f"Domain: {profile['domain']}")

        return "\n".join(parts)

    def _build_analysis_prompt(self, message: str, context: str, expert_context: str) -> str:
        """Build prompt for insight analysis"""
        return f"""TASK: Analyze this expert statement and extract insights.

EXPERT PROFILE:
{expert_context if expert_context else "No profile available"}

CONVERSATION CONTEXT:
{context if context else "No previous context"}

EXPERT STATEMENT:
{message}

INSTRUCTIONS:
1. Extract key insights with EXACT quotes (verbatim)
2. Identify technical terms used by expert
3. Note expertise indicators (specific numbers, processes, experience signals)
4. Preserve original terminology - do NOT paraphrase

OUTPUT FORMAT (JSON):
{{
    "expert_insights_original": [
        {{
            "original_quote": "EXACT quote from expert",
            "key_terms": ["term1", "term2"],
            "context": "Why this is significant"
        }}
    ],
    "key_terms": ["all", "technical", "terms"],
    "expertise_indicators": ["specific signals of expertise"],
    "context": "Overall context of the insights"
}}

CRITICAL: Preserve EXACT quotes. Do not paraphrase or translate terminology."""

    def _create_fallback_response(self, message: str, error: str | None = None) -> DictParams:
        """Fallback when analysis fails"""
        return {
            "expert_insights_original": [],
            "key_terms": [],
            "expertise_indicators": [],
            "context": "Analysis failed",
            "processing_time": 0.001,
            "error": error,
        }
