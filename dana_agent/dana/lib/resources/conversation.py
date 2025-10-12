"""
Conversation Resource - Comprehensive conversation analysis.

This resource provides unified methods for:
- Summarization: Extract key topics, insights, stage assessment
- Intent detection: Classify message intent with context rewriting
- Topic extraction: Identify topics with terminology preservation
"""

import asyncio
import json
import time

from dana.common.llm.llm import LLM, LLMMessage
from dana.common.observable import observable
from dana.common.protocols import DictParams
from dana.common.protocols.war import tool_use
from dana.core.resource.base_resource import BaseResource


class ConversationResource(BaseResource):
    """
    <PUBLIC_DESCRIPTION>
    Comprehensive conversation analysis resource.

    Provides methods for:
    - **summarize**: Extract key topics, insights, expertise level, conversation stage
    - **detect_intent**: Classify message intent with context-aware rewriting
    - **extract_topics**: Identify topics with original terminology preservation

    All methods share the same LLM client and can leverage conversation context.

    USE CASES:
    - Context-aware dialogue systems
    - Interview and survey applications
    - Customer support session analysis
    - Multi-turn conversation routing
    - Knowledge extraction from conversations

    FEATURES:
    - Configurable intent types for domain-specific classification
    - Automatic terminology preservation
    - Context switch detection
    - Fast path for minimal conversations (no LLM call)
    - Graceful fallback on errors
    </PUBLIC_DESCRIPTION>
    """

    def __init__(
        self,
        llm_provider: str = "anthropic",
        model: str | None = None,
        intent_types: list[str] | None = None,
        resource_id: str | None = None,
        **kwargs,
    ):
        """
        Initialize ConversationResource.

        Args:
            llm_provider: LLM provider (default: "anthropic")
            model: Model name (default: provider's default)
            intent_types: List of intent types for classification (default: standard set)
            resource_id: Resource identifier (default: "conversation")
            **kwargs: Additional arguments for BaseResource
        """
        super().__init__(resource_id=resource_id or "conversation", **kwargs)
        self.llm = LLM(provider=llm_provider, model=model)

        # Configurable intent types
        self.intent_types = intent_types or [
            "question",  # General question
            "sharing",  # Sharing knowledge/experience
            "clarification",  # Needs clarification
            "context_switch",  # Topic change detected
        ]

    # ============================================================================
    # DETECT_INTENT METHOD
    # ============================================================================

    @tool_use
    @observable
    def detect_intent(self, message: str, conversation_history: list[dict[str, str]] | None = None, **kwargs) -> DictParams:
        result = asyncio.run(self._detect_intent(message, conversation_history, **kwargs))
        return result

    async def _detect_intent(self, message: str, conversation_history: list[dict[str, str]] | None = None, **kwargs) -> DictParams:
        """
        Detect user intent and rewrite message with context.

        Args:
            message: The user's message
            conversation_history: Optional list of previous messages
            **kwargs: Additional parameters

        Returns:
            Dictionary with:
                - intent: Detected intent from configured types
                - rewritten_message: Message enhanced with context
                - context_analysis: Topic and context information
                - search_keywords: Terms for document/knowledge search
                - unclear_terms: Terms needing clarification
                - context_switch_detected: Boolean
                - processing_time: Time taken
        """
        start_time = time.time()

        try:
            context = self._format_conversation(conversation_history) if conversation_history else ""
            prompt = self._build_intent_detection_prompt(message, context)

            system_message = """You are an expert conversation analyst specializing in intent detection.
Your task is to analyze user messages and classify their intent accurately."""

            response = await self.llm.chat_response(
                messages=[LLMMessage(role="user", content=prompt)], system_message=system_message, max_tokens=500, temperature=0.1
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
            return self._create_fallback_intent(message, str(e))

    # ============================================================================
    # EXTRACT_TOPICS METHOD
    # ============================================================================

    @tool_use
    @observable
    def extract_topics(
        self, message: str, conversation_history: list[dict[str, str]] | None = None, preserve_terminology: bool = True, **kwargs
    ) -> DictParams:
        result = asyncio.run(self._extract_topics(message, conversation_history, preserve_terminology, **kwargs))
        return result

    async def _extract_topics(
        self, message: str, conversation_history: list[dict[str, str]] | None = None, preserve_terminology: bool = True, **kwargs
    ) -> DictParams:
        """
        Extract topics with original terminology preservation.

        Args:
            message: The user's message
            conversation_history: Optional conversation history for context
            preserve_terminology: Whether to preserve exact terminology (default: True)
            **kwargs: Additional parameters

        Returns:
            Dictionary with:
                - current_focus: Main topic being discussed
                - active_topics: List of topics (with original terminology)
                - key_concepts: Important concepts mentioned
                - terminology: Technical terms identified
                - processing_time: Time taken
        """
        start_time = time.time()

        try:
            context = self._format_conversation(conversation_history) if conversation_history else ""
            prompt = self._build_topic_extraction_prompt(message, context, preserve_terminology)

            system_message = """You are an expert at extracting topics from conversations.
Always preserve the exact terminology used by speakers."""

            response = await self.llm.chat_response(
                messages=[LLMMessage(role="user", content=prompt)],
                system_message=system_message,
                max_tokens=800,
                temperature=0.1,
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
            return self._create_fallback_topics(message, str(e))

    # ============================================================================
    # HELPER METHODS
    # ============================================================================

    def _format_conversation(
        self, history: list[dict[str, str]], current_message: str | None = None, max_messages: int = 6, max_chars_per_message: int = 200
    ) -> str:
        """Format conversation for LLM prompts"""
        formatted_parts = []
        recent_history = history[-max_messages:] if len(history) > max_messages else history

        for msg in recent_history:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:max_chars_per_message]
            formatted_parts.append(f"{role}: {content}")

        if current_message:
            formatted_parts.append(f"user: {current_message[:max_chars_per_message]}")

        return "\n".join(formatted_parts)

    # ============================================================================
    # SUMMARIZE - LLM & FALLBACK
    # ============================================================================

    def _generate_llm_summary(self, conversation_text: str) -> DictParams:
        result = asyncio.run(self.__generate_llm_summary(conversation_text))
        return result

    async def __generate_llm_summary(self, conversation_text: str) -> DictParams:
        """Generate summary using LLM"""
        system_message = "You are an expert conversation analyst. Extract key information efficiently and accurately."

        prompt = f"""CONVERSATION SUMMARY GENERATION

Analyze this conversation and extract key information:

CONVERSATION:
{conversation_text}

OUTPUT FORMAT (JSON):
{{
    "key_topics": ["topic1", "topic2", "topic3"],
    "technical_areas": ["area1", "area2"],
    "expert_insights": ["insight1", "insight2"],
    "terminology_introduced": ["term1", "term2"],
    "context_switches": ["switch1"],
    "conversation_stage": "early|middle|advanced",
    "expertise_level": "beginner|intermediate|expert",
    "conversation_summary": "2-3 sentence summary"
}}

REQUIREMENTS:
- Extract 3-5 most important topics
- Identify 2-4 technical areas
- Note 2-4 key insights
- List new technical terminology
- Note context switches
- Assess stage and expertise
- Provide concise summary (max 50 words)"""

        response = await self.llm.chat_response(
            messages=[LLMMessage(role="user", content=prompt)], system_message=system_message, max_tokens=800, temperature=0.1
        )

        content = response.content if hasattr(response, "content") else str(response)

        json_start = content.find("{")
        json_end = content.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            return json.loads(content[json_start:json_end])
        else:
            raise ValueError("No valid JSON found in response")

    def _create_minimal_summary(self, history: list[dict[str, str]], current_message: str | None = None) -> DictParams:
        """Create minimal summary for short conversations"""
        return {
            "key_topics": [],
            "technical_areas": [],
            "expert_insights": [],
            "terminology_introduced": [],
            "context_switches": [],
            "conversation_stage": "early",
            "expertise_level": "unknown",
            "conversation_summary": "Beginning of conversation",
            "conversation_length": len(history),
            "processing_time": 0.001,
            "timestamp": time.time(),
        }

    def _create_fallback_summary(
        self, history: list[dict[str, str]], current_message: str | None = None, error: str | None = None
    ) -> DictParams:
        """Create fallback summary when LLM fails"""
        return {
            "key_topics": ["general discussion"],
            "technical_areas": ["unknown"],
            "expert_insights": [],
            "terminology_introduced": [],
            "context_switches": [],
            "conversation_stage": "unknown",
            "expertise_level": "unknown",
            "conversation_summary": "Technical discussion in progress",
            "conversation_length": len(history),
            "processing_time": 0.001,
            "timestamp": time.time(),
            "error": error,
        }

    # ============================================================================
    # DETECT_INTENT - PROMPTS & FALLBACK
    # ============================================================================

    def _build_intent_detection_prompt(self, message: str, context: str) -> str:
        """Build prompt for intent detection"""
        intent_list = "\n".join([f"- {intent}" for intent in self.intent_types])

        return f"""TASK: Analyze this message and classify its intent.

CONVERSATION CONTEXT:
{context if context else "No previous context available."}

CURRENT MESSAGE:
{message}

INSTRUCTIONS:
1. Classify the intent from the allowed types
2. Rewrite the message incorporating context if relevant
3. Identify any unclear terms
4. Detect context switches

ALLOWED INTENT TYPES:
{intent_list}

OUTPUT FORMAT (JSON):
{{
    "intent": "one of the allowed types",
    "rewritten_message": "message with context incorporated",
    "context_analysis": "brief analysis",
    "search_keywords": ["keyword1", "keyword2"],
    "unclear_terms": ["term1", "term2"],
    "context_switch_detected": false
}}"""

    def _create_fallback_intent(self, message: str, error: str | None = None) -> DictParams:
        """Fallback when intent detection fails"""
        return {
            "intent": "question",
            "rewritten_message": message,
            "context_analysis": "Unable to analyze context",
            "search_keywords": [],
            "unclear_terms": [],
            "context_switch_detected": False,
            "processing_time": 0.001,
            "error": error,
        }

    # ============================================================================
    # EXTRACT_TOPICS - PROMPTS & FALLBACK
    # ============================================================================

    def _build_topic_extraction_prompt(self, message: str, context: str, preserve_terminology: bool) -> str:
        """Build prompt for topic extraction"""
        preservation_note = (
            """
CRITICAL: Preserve EXACT terminology used by the speaker.
- If they say "centrifuge", use "centrifuge" (not "separator")
- If they say "3000 RPM", use "3000 RPM" (not "3000 revolutions per minute")
- Extract their exact technical terms without translation"""
            if preserve_terminology
            else ""
        )

        return f"""TASK: Extract topics from this message.

CONVERSATION CONTEXT:
{context if context else "No previous context."}

CURRENT MESSAGE:
{message}
{preservation_note}

OUTPUT FORMAT (JSON):
{{
    "current_focus": "main topic being discussed",
    "active_topics": ["topic1", "topic2", "topic3"],
    "key_concepts": ["concept1", "concept2"],
    "terminology": ["technical_term1", "technical_term2"]
}}"""

    def _create_fallback_topics(self, message: str, error: str | None = None) -> DictParams:
        """Fallback when topic extraction fails"""
        return {
            "current_focus": "general discussion",
            "active_topics": ["general"],
            "key_concepts": [],
            "terminology": [],
            "processing_time": 0.001,
            "error": error,
        }
