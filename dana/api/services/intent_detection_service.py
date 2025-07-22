"""LLM-based Intent Detection Service for domain knowledge management."""

import json
import logging

from dana.api.core.schemas import (
    IntentDetectionRequest,
    IntentDetectionResponse,
    DomainKnowledgeTree,
    MessageData
)
from dana.common.mixins.loggable import Loggable
from dana.common.resource.llm.llm_resource import LLMResource
from dana.common.types import BaseRequest

logger = logging.getLogger(__name__)


class IntentDetectionService(Loggable):
    """Service for detecting user intent in chat messages using LLM."""
    
    def __init__(self):
        super().__init__()
        self.llm = LLMResource()
    
    async def detect_intent(self, request: IntentDetectionRequest) -> IntentDetectionResponse:
        """Detect user intent using LLM analysis."""
        try:
            # Build the LLM prompt
            prompt = self._build_intent_detection_prompt(
                request.user_message,
                request.chat_history,
                request.current_domain_tree
            )
            
            # Create LLM request
            llm_request = BaseRequest(
                arguments={
                    "messages": [
                        {"role": "system", "content": "You are an expert at understanding user intent in agent conversations."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,  # Lower temperature for more consistent intent detection
                    "max_tokens": 500
                }
            )
            
            # Call LLM
            response = await self.llm.query(llm_request)
            
            # Parse the response
            try:
                content = response.content
                if isinstance(content, str):
                    result = json.loads(content)
                elif isinstance(content, dict):
                    result = content
                else:
                    raise ValueError(f"Unexpected LLM response type: {type(content)}")
                
                intent_result: dict = json.loads(result.get("choices")[0].get("message").get("content"))
                
                return IntentDetectionResponse(
                    intent=intent_result.get("intent", "general_query"),
                    entities=intent_result.get("entities", {}),
                    confidence=intent_result.get("confidence"),
                    explanation=intent_result.get("explanation")
                )
            except json.JSONDecodeError:
                print(response)
                # Fallback parsing if LLM doesn't return valid JSON
                return self._fallback_intent_detection(request.user_message)
                
        except Exception as e:
            self.error(f"Error detecting intent: {e}")
            # Return fallback intent
            return IntentDetectionResponse(
                intent="general_query",
                entities={},
                explanation=f"Error in intent detection: {str(e)}"
            )
    
    def _build_intent_detection_prompt(
        self,
        user_message: str,
        chat_history: list[MessageData],
        domain_tree: DomainKnowledgeTree | None
    ) -> str:
        """Build the LLM prompt for intent detection."""
        
        # Convert domain tree to JSON for context
        tree_json = "null"
        if domain_tree:
            try:
                tree_json = json.dumps(domain_tree.model_dump(), indent=2)
            except Exception:
                tree_json = "null"
        
        # Build chat history context
        history_context = ""
        if chat_history:
            recent_messages = chat_history[-3:]  # Only include recent context
            history_context = "\\n".join([
                f"{msg.role}: {msg.content}" 
                for msg in recent_messages
            ])
        
        prompt = f"""You are an assistant managing an agent's domain knowledge. 
Given the following user message and context, classify the user's intent as one of:

1. "add_information" - User wants to add a new topic or knowledge area to the agent's expertise
2. "refresh_domain_knowledge" - User wants to update, reorganize, or regenerate the knowledge structure  
3. "general_query" - User is asking a question or making a request unrelated to knowledge management

Extract any relevant entities (e.g., topic to add, parent category, etc.).

Recent chat history:
{history_context}

Current domain knowledge tree:
{tree_json}

User message: "{user_message}"

Analyze the message and respond in this exact JSON format:
{{
  "intent": "add_information|refresh_domain_knowledge|general_query",
  "entities": {{
    "topic": "topic name if adding information",
    "parent": "parent topic if specified", 
    "details": "additional details if provided"
  }},
  "confidence": 0.0-1.0,
  "explanation": "brief explanation of why this intent was detected"
}}

Examples:
- "Can you help me with financial modeling?" → general_query
- "Add dividend analysis to your knowledge" → add_information with topic="dividend analysis"
- "Update your knowledge about stock analysis" → refresh_domain_knowledge  
- "I want you to know about cryptocurrency" → add_information with topic="cryptocurrency"
"""
        return prompt
    
    def _fallback_intent_detection(self, user_message: str) -> IntentDetectionResponse:
        """Fallback intent detection using simple keyword matching."""
        message_lower = user_message.lower()
        
        # Simple keyword-based detection
        add_keywords = ["add", "learn", "know about", "include", "teach", "understand"]
        refresh_keywords = ["update", "refresh", "regenerate", "restructure", "organize"]
        
        if any(keyword in message_lower for keyword in add_keywords):
            # Try to extract topic
            topic = self._extract_topic_from_message(user_message)
            return IntentDetectionResponse(
                intent="add_information",
                entities={"topic": topic} if topic else {},
                confidence=0.7,
                explanation="Detected add intent using keyword matching"
            )
        
        if any(keyword in message_lower for keyword in refresh_keywords):
            return IntentDetectionResponse(
                intent="refresh_domain_knowledge", 
                entities={},
                confidence=0.7,
                explanation="Detected refresh intent using keyword matching"
            )
        
        return IntentDetectionResponse(
            intent="general_query",
            entities={},
            confidence=0.5,
            explanation="Defaulted to general query"
        )
    
    def _extract_topic_from_message(self, message: str) -> str | None:
        """Extract potential topic from user message using simple heuristics."""
        # Simple extraction - look for patterns like "about X", "know X", etc.
        message_lower = message.lower()
        
        patterns = [
            "about ",
            "regarding ",
            "concerning ",
            "on ",
            "with "
        ]
        
        for pattern in patterns:
            if pattern in message_lower:
                # Extract text after pattern
                start = message_lower.find(pattern) + len(pattern)
                remaining = message[start:].strip()
                
                # Take first few words as topic
                words = remaining.split()[:3]
                if words:
                    return " ".join(words).rstrip(".,!?")
        
        return None


def get_intent_detection_service() -> IntentDetectionService:
    """Dependency injection for intent detection service."""
    return IntentDetectionService()