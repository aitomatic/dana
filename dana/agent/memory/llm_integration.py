"""
LLM Integration for Dana Agent Memory System

This module provides LLM-powered memory operations using Dana's LLMResource:
- Memory extraction from conversations
- Memory classification and storage routing
- Intent detection for memory retrieval
- Memory reranking and relevance scoring
"""

import json
import re
from typing import Any

from dana.common.resource.llm.llm_resource import LLMResource
from dana.common.types import BaseRequest
from dana.common.utils.misc import Misc

from .domain import MemoryItem


class LLMMemoryExtractor:
    """LLM-powered memory extraction and classification"""

    def __init__(self, llm_resource: LLMResource | None = None):
        self.llm = llm_resource or LLMResource(name="memory_llm", temperature=0.1)
        self._initialized = False

    async def initialize(self):
        """Initialize the LLM resource"""
        if not self._initialized:
            await self.llm.initialize()
            self._initialized = True

    async def extract_memories(self, conversation_content: str, user_id: str) -> list[dict[str, Any]]:
        """Extract structured memories from conversation content using LLM"""
        await self.initialize()

        prompt = self._build_extraction_prompt(conversation_content)

        request = BaseRequest(
            arguments={
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a memory extraction expert. Extract memories from conversations and classify them appropriately.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.1,
                "max_tokens": 2000,
            }
        )

        response = await self.llm.query(request)

        if response.success:
            return self._parse_memory_response(response, conversation_content)
        else:
            # Fallback to simple extraction
            return self._fallback_extraction(conversation_content)

    def _build_extraction_prompt(self, content: str) -> str:
        """Build the memory extraction prompt"""
        return f"""Extract memories from the following conversation content from the user's perspective.

Conversation: "{content}"

Classify each memory with TWO dimensions:

**Storage Type** - Where to store the memory:
- "LongTermMemory": Factual events, experiences, and objective information
  - Meetings, conversations, and interactions
  - Temporal events with specific dates/times  
  - Procedural knowledge and instructions
  - External facts and observations
- "UserMemory": Personal attributes, preferences, and characteristics
  - Goals, aspirations, and plans
  - Preferences and opinions
  - Personality traits and behavioral patterns
  - Emotional states and reactions
  - Personal restrictions (allergies, dietary needs, etc.)

**Semantic Type** - What kind of memory it is:
- "FACT": Objective, verifiable information (allergies, birthdate, job title)
- "OPINION": Subjective views, preferences, beliefs (likes pizza, thinks X is good)
- "PROCEDURE": Step-by-step processes, instructions, how-to knowledge
- "EVENT": Temporal occurrences, meetings, experiences, interactions
- "TOPIC": General knowledge, concepts, themes not fitting other categories

Return ONLY valid JSON in this exact format:
{{
  "memory_list": [
    {{
      "key": "unique_memory_title",
      "memory_type": "LongTermMemory|UserMemory",
      "semantic_type": "FACT|OPINION|PROCEDURE|EVENT|TOPIC",
      "value": "detailed memory statement from user perspective",
      "tags": ["relevant", "keywords"],
      "confidence": 0.95
    }}
  ]
}}

Requirements:
- Extract 1-3 most important memories
- Use clear, descriptive keys
- Include both memory_type and semantic_type
- Include relevant tags
- Confidence between 0.0-1.0
- Return valid JSON only"""

    def _parse_memory_response(self, response_content: Any, original_content: str) -> list[dict[str, Any]]:
        """Parse LLM response and extract memory data"""
        try:
            # Use Misc.get_response_content to properly extract content from BaseResponse
            response_text = Misc.get_response_content(response_content)
            if not isinstance(response_text, str):
                response_text = str(response_text)

            # Extract JSON from response
            json_match = re.search(r"\{[\s\S]*\}", response_text)
            if json_match:
                json_str = json_match.group(0)
                parsed = json.loads(json_str)

                if "memory_list" in parsed:
                    memories = parsed["memory_list"]
                    # Validate and clean up memories
                    return self._validate_memories(memories)

        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
            print(f"Error parsing LLM response: {e}")

        # Fallback to simple extraction
        return self._fallback_extraction(original_content)

    def _validate_memories(self, memories: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Validate and clean extracted memories"""
        validated = []
        valid_storage_types = {"LongTermMemory", "UserMemory"}
        valid_semantic_types = {"FACT", "OPINION", "PROCEDURE", "EVENT", "TOPIC"}

        for memory in memories:
            if not isinstance(memory, dict):
                continue

            # Required fields
            if not all(key in memory for key in ["key", "memory_type", "value"]):
                continue

            # Validate storage type
            if memory["memory_type"] not in valid_storage_types:
                memory["memory_type"] = "LongTermMemory"  # Default

            # Validate semantic type (new field)
            if "semantic_type" not in memory or memory["semantic_type"] not in valid_semantic_types:
                # Fallback classification if semantic_type is missing or invalid
                content_lower = memory["value"].lower()
                if any(word in content_lower for word in ["procedure", "step", "how to", "process"]):
                    memory["semantic_type"] = "PROCEDURE"
                elif any(word in content_lower for word in ["opinion", "think", "believe", "prefer", "like"]):
                    memory["semantic_type"] = "OPINION"
                elif any(word in content_lower for word in ["meeting", "event", "happened", "occurred"]):
                    memory["semantic_type"] = "EVENT"
                elif any(word in content_lower for word in ["fact", "allergy", "born", "age", "job"]):
                    memory["semantic_type"] = "FACT"
                else:
                    memory["semantic_type"] = "TOPIC"

            # Ensure other fields have defaults
            memory.setdefault("tags", [])
            memory.setdefault("confidence", 0.8)

            # Validate confidence range
            try:
                confidence = float(memory["confidence"])
                memory["confidence"] = max(0.0, min(1.0, confidence))
            except (ValueError, TypeError):
                memory["confidence"] = 0.8

            validated.append(memory)

        return validated

    def _fallback_extraction(self, content: str) -> list[dict[str, Any]]:
        """Fallback memory extraction when LLM fails"""
        # Simple rule-based extraction as fallback
        if len(content.strip()) < 10:
            return []

        # Basic classification logic
        content_lower = content.lower()

        # Determine storage type
        if any(word in content_lower for word in ["prefer", "like", "dislike", "goal", "want", "allergy"]):
            memory_type = "UserMemory"
        else:
            memory_type = "LongTermMemory"

        # Determine semantic type
        if any(word in content_lower for word in ["procedure", "step", "how to", "process"]):
            semantic_type = "PROCEDURE"
        elif any(word in content_lower for word in ["opinion", "think", "believe", "prefer", "like"]):
            semantic_type = "OPINION"
        elif any(word in content_lower for word in ["meeting", "event", "happened", "occurred"]):
            semantic_type = "EVENT"
        elif any(word in content_lower for word in ["fact", "allergy", "born", "age", "job"]):
            semantic_type = "FACT"
        else:
            semantic_type = "TOPIC"

        return [
            {
                "key": "fallback_memory",
                "memory_type": memory_type,
                "semantic_type": semantic_type,
                "value": content.strip(),
                "tags": ["fallback"],
                "confidence": 0.5,
            }
        ]


class LLMIntentDetector:
    """LLM-powered intent detection for memory retrieval"""

    def __init__(self, llm_resource: LLMResource | None = None):
        self.llm = llm_resource or LLMResource(name="intent_llm", temperature=0.0)
        self._initialized = False

    async def initialize(self):
        """Initialize the LLM resource"""
        if not self._initialized:
            await self.llm.initialize()
            self._initialized = True

    async def detect_intent(self, query: str, working_memory: list[MemoryItem]) -> dict[str, Any]:
        """Detect if memory retrieval is needed for the query"""
        await self.initialize()

        memory_context = self._format_memory_context(working_memory)
        prompt = self._build_intent_prompt(query, memory_context)

        request = BaseRequest(
            arguments={
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an intent detection expert. Determine if current memory context is sufficient to answer queries.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.0,
                "max_tokens": 500,
            }
        )

        response = await self.llm.query(request)

        if response.success:
            return self._parse_intent_response(response, query)
        else:
            # Fallback to simple rule-based detection
            return self._fallback_intent_detection(query, working_memory)

    def _format_memory_context(self, memories: list[MemoryItem]) -> str:
        """Format memory context for intent detection"""
        if not memories:
            return "No memories available"

        context_lines = []
        for i, memory in enumerate(memories[-10:], 1):  # Last 10 memories
            context_lines.append(f"{i}. {memory.memory}")

        return "\n".join(context_lines)

    def _build_intent_prompt(self, query: str, memory_context: str) -> str:
        """Build intent detection prompt"""
        return f"""Analyze if the current memory context is sufficient to answer the user's query.

User Query: "{query}"

Current Memory Context:
{memory_context}

Determine if memory retrieval is needed by analyzing:
1. Does the current context contain information relevant to the query?
2. Are there gaps in knowledge that would require additional memories?
3. What specific information is missing?

Return ONLY valid JSON in this format:
{{
  "trigger_retrieval": true|false,
  "confidence": 0.95,
  "reasoning": "explanation of decision",
  "missing_evidence": ["specific information needed"] 
}}

If trigger_retrieval is true, specify what evidence is missing."""

    def _parse_intent_response(self, response_content: Any, query: str) -> dict[str, Any]:
        """Parse LLM intent detection response"""
        try:
            # Use Misc.get_response_content to properly extract content from BaseResponse
            response_text = Misc.get_response_content(response_content)
            if not isinstance(response_text, str):
                response_text = str(response_text)

            # Extract JSON from response
            json_match = re.search(r"\{[\s\S]*\}", response_text)
            if json_match:
                json_str = json_match.group(0)
                parsed = json.loads(json_str)

                # Validate required fields
                result = {
                    "trigger_retrieval": parsed.get("trigger_retrieval", False),
                    "confidence": parsed.get("confidence", 0.5),
                    "reasoning": parsed.get("reasoning", ""),
                    "missing_evidence": parsed.get("missing_evidence", [query]),
                }

                return result

        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
            print(f"Error parsing intent response: {e}")

        # Fallback
        return self._fallback_intent_detection(query, [])

    def _fallback_intent_detection(self, query: str, working_memory: list[MemoryItem]) -> dict[str, Any]:
        """Fallback intent detection when LLM fails"""
        # Simple rule-based detection
        if len(working_memory) < 3:
            return {"trigger_retrieval": True, "confidence": 0.8, "reasoning": "Insufficient memory context", "missing_evidence": [query]}

        # Check keyword coverage
        query_words = set(query.lower().split())
        memory_words = set()
        for memory in working_memory:
            memory_words.update(memory.memory.lower().split())

        coverage = len(query_words & memory_words) / len(query_words) if query_words else 0

        return {
            "trigger_retrieval": coverage < 0.3,
            "confidence": 0.7,
            "reasoning": f"Keyword coverage: {coverage:.2f}",
            "missing_evidence": [query] if coverage < 0.3 else [],
        }


class LLMMemoryRanker:
    """LLM-powered memory ranking and relevance scoring"""

    def __init__(self, llm_resource: LLMResource | None = None):
        self.llm = llm_resource or LLMResource(name="ranking_llm", temperature=0.0)
        self._initialized = False

    async def initialize(self):
        """Initialize the LLM resource"""
        if not self._initialized:
            await self.llm.initialize()
            self._initialized = True

    async def rank_memories(self, query: str, memories: list[MemoryItem]) -> list[MemoryItem]:
        """Rank memories by relevance to query using LLM"""
        if not memories:
            return []

        if len(memories) <= 1:
            return memories

        await self.initialize()

        # For large memory sets, use simple ranking to avoid token limits
        if len(memories) > 20:
            return self._simple_rank_memories(query, memories)

        memory_texts = [f"{i + 1}. {mem.memory}" for i, mem in enumerate(memories)]
        prompt = self._build_ranking_prompt(query, memory_texts)

        request = BaseRequest(
            arguments={
                "messages": [
                    {"role": "system", "content": "You are a memory ranking expert. Rank memories by relevance to the query."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.0,
                "max_tokens": 1000,
            }
        )

        response = await self.llm.query(request)

        if response.success:
            return self._parse_ranking_response(response, memories)
        else:
            # Fallback to simple ranking
            return self._simple_rank_memories(query, memories)

    def _build_ranking_prompt(self, query: str, memory_texts: list[str]) -> str:
        """Build memory ranking prompt"""
        memories_str = "\n".join(memory_texts)

        return f"""Rank the following memories by relevance to the user's query.

Query: "{query}"

Memories:
{memories_str}

Return ONLY a JSON array of memory indices (1-based) ordered by relevance (most relevant first):
[1, 3, 2, 4, ...]

Consider:
- Direct relevance to query topics
- Contextual importance
- Temporal relevance
- Personal significance"""

    def _parse_ranking_response(self, response_content: Any, memories: list[MemoryItem]) -> list[MemoryItem]:
        """Parse LLM ranking response"""
        try:
            # Use Misc.get_response_content to properly extract content from BaseResponse
            response_text = Misc.get_response_content(response_content)
            if not isinstance(response_text, str):
                response_text = str(response_text)

            # Extract JSON array from response
            json_match = re.search(r"\[[\s\S]*\]", response_text)
            if json_match:
                json_str = json_match.group(0)
                indices = json.loads(json_str)

                # Reorder memories based on indices
                ranked_memories = []
                for idx in indices:
                    if isinstance(idx, int) and 1 <= idx <= len(memories):
                        ranked_memories.append(memories[idx - 1])

                # Add any missing memories
                included_indices = set(idx for idx in indices if isinstance(idx, int) and 1 <= idx <= len(memories))
                for i, memory in enumerate(memories):
                    if (i + 1) not in included_indices:
                        ranked_memories.append(memory)

                return ranked_memories

        except (json.JSONDecodeError, IndexError, TypeError, ValueError) as e:
            print(f"Error parsing ranking response: {e}")

        # Fallback to simple ranking
        return self._simple_rank_memories("", memories)

    def _simple_rank_memories(self, query: str, memories: list[MemoryItem]) -> list[MemoryItem]:
        """Simple keyword-based memory ranking"""
        if not query:
            # Sort by timestamp (most recent first)
            return sorted(memories, key=lambda x: x.timestamp, reverse=True)

        query_words = set(query.lower().split())

        def relevance_score(memory: MemoryItem) -> float:
            memory_words = set(memory.memory.lower().split())
            overlap = len(query_words & memory_words)
            return overlap / len(query_words) if query_words else 0

        return sorted(memories, key=relevance_score, reverse=True)
