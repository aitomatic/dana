"""LLM-based Intent Detection Service for domain knowledge management."""

import json
import logging
from typing import Any

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
        """Detect user intent using LLM analysis - now supports multiple intents."""
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
                
                # Handle multiple intents - return the first one for backward compatibility
                # but store all intents in the response
                intents = intent_result.get("intents", [])
                if not intents:
                    # Fallback to single intent format
                    intents = [{
                        "intent": intent_result.get("intent", "general_query"),
                        "entities": intent_result.get("entities", {}),
                        "confidence": intent_result.get("confidence"),
                        "explanation": intent_result.get("explanation")
                    }]
                
                primary_intent = intents[0]
                return IntentDetectionResponse(
                    intent=primary_intent.get("intent", "general_query"),
                    entities=primary_intent.get("entities", {}),
                    confidence=primary_intent.get("confidence"),
                    explanation=primary_intent.get("explanation"),
                    # Store all intents for multi-intent processing
                    additional_data={"all_intents": intents}
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
    
    async def generate_followup_message(self, user_message: str, agent: Any, knowledge_topics: list[str]) -> str:
        """Generate a creative, LLM-based follow-up message for the smart chat flow."""
        agent_name = getattr(agent, 'name', None) or (agent.get('name') if isinstance(agent, dict) else None) or "(no name)"
        agent_description = getattr(agent, 'description', None) or (agent.get('description') if isinstance(agent, dict) else None) or "(no description)"
        agent_config = getattr(agent, 'config', None) or (agent.get('config') if isinstance(agent, dict) else None) or {}
        specialties = agent_config.get('specialties', None) or "(not set)"
        skills = agent_config.get('skills', None) or "(not set)"
        topics_str = ", ".join(knowledge_topics) if knowledge_topics else "(none yet)"
        prompt = f'''
You are a friendly, creative assistant helping a user define and improve an AI agent. The user just sent this message:
"""
{user_message}
"""

Here is the current state of the agent:
- Name: {agent_name}
- Description: {agent_description}
- Specialties: {specialties}
- Skills: {skills}
- Knowledge topics: {topics_str}

Your job is to suggest a friendly, creative follow-up question or suggestion to help the user further define, improve, or expand their agent. Always encourage the user to continue, and never let the conversation end abruptly. If the agent is missing important information (like specialties, description, or knowledge), ask about that. Otherwise, suggest ways the user can make the agent more useful, unique, or interesting. Be conversational and engaging.

Respond with only the follow-up message, no preamble or explanation.
'''
        llm_request = BaseRequest(
            arguments={
                "messages": [
                    {"role": "system", "content": "You are a creative assistant for agent configuration."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 120
            }
        )
        try:
            response = await self.llm.query(llm_request)
            content = response.content
            if isinstance(content, str):
                return content.strip()
            elif isinstance(content, dict):
                # Some LLMs return {"choices": [{"message": {"content": ...}}]}
                try:
                    return content["choices"][0]["message"]["content"].strip()
                except Exception:
                    return str(content)
            else:
                return str(content)
        except Exception as e:
            self.error(f"Error generating follow-up message: {e}")
            return "What else would you like to add or improve about your agent?"
    
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
            history_context = "\n".join([
                f"{msg.role}: {msg.content}" 
                for msg in recent_messages
            ])
        prompt = f"""You are an assistant managing an agent's profile and domain knowledge. 
Given the following user message and context, identify ALL intents present in the message. A single message can have multiple intents.

Available intents:
1. "add_information" - User wants to add a new topic or knowledge area to the agent's expertise
2. "refresh_domain_knowledge" - User wants to update, reorganize, or regenerate the knowledge structure  
3. "update_agent_properties" - User wants to update the agent's name, role, specialties, or skills
4. "general_query" - User is asking a question or making a request unrelated to knowledge management

Extract any relevant entities (e.g., topic, name, role, specialties, skills, etc.).

Recent chat history:
{history_context}

Current domain knowledge tree:
{tree_json}

User message: "{user_message}"

Respond in this exact JSON format with an array of intents (even if just one):
{{
  "intents": [
    {{
      "intent": "add_information|refresh_domain_knowledge|update_agent_properties|general_query",
      "entities": {{
        "topic": "...",
        "name": "...",
        "role": "...",
        "specialties": "...",
        "skills": "..."
      }},
      "confidence": 0.0-1.0,
      "explanation": "brief explanation"
    }}
  ]
}}

Examples:
- "I want to call my agent Jason" → [{{intent: "update_agent_properties", entities: {{name: "Jason"}}}}]
- "I want Jason to be good at anti-money laundering" → [{{intent: "update_agent_properties", entities: {{name: "Jason", specialties: "anti-money laundering"}}}}, {{intent: "add_information", entities: {{topic: "anti-money laundering"}}}}]
- "I want Jason to be an anti-money laundering expert" → [{{intent: "update_agent_properties", entities: {{name: "Jason", role: "anti-money laundering expert", specialties: "anti-money laundering"}}}}, {{intent: "add_information", entities: {{topic: "anti-money laundering"}}}}]
- "Make Jason a financial advisor skilled in portfolio analysis" → [{{intent: "update_agent_properties", entities: {{name: "Jason", role: "financial advisor", skills: "portfolio analysis"}}}}, {{intent: "add_information", entities: {{topic: "portfolio analysis"}}}}]
- "Jason should be a compliance officer with skills in regulatory reporting" → [{{intent: "update_agent_properties", entities: {{name: "Jason", role: "compliance officer", skills: "regulatory reporting"}}}}, {{intent: "add_information", entities: {{topic: "regulatory reporting"}}}}]
- "Add dividend analysis to your knowledge" → [{{intent: "add_information", entities: {{topic: "dividend analysis"}}}}]
- "it's very good add AML compliance" → [{{intent: "add_information", entities: {{topic: "AML compliance"}}}}, {{intent: "update_agent_properties", entities: {{specialties: "AML compliance"}}}}]
- "add risk management to the agent" → [{{intent: "add_information", entities: {{topic: "risk management"}}}}, {{intent: "update_agent_properties", entities: {{specialties: "risk management"}}}}]
- "Update your knowledge about stock analysis" → [{{intent: "refresh_domain_knowledge", entities: {{}}}}]
- "Can you help me with financial modeling?" → [{{intent: "general_query", entities: {{}}}}]

IMPORTANT EXTRACTION RULES:
1. Role extraction: Look for patterns like "be a [role]", "be an [role]", "work as [role]", "[name] is [role]", "[profession] expert", "[domain] specialist"
2. Skills extraction: Look for "skilled in", "good at", "with skills in", "abilities in"  
3. Specialties extraction: Look for domain expertise like "specialist in", "expert in [domain]", "expertise in"
4. When someone wants to give an agent expertise/skills/specialties in a domain, this should ALWAYS trigger BOTH update_agent_properties AND add_information intents - one to update the agent's profile and one to add the topic to domain knowledge.
5. When someone says "add [topic]" or "add [topic] to agent/knowledge", this should trigger BOTH add_information AND update_agent_properties (with specialties) - they want both the knowledge added and the agent to become specialized in it.
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