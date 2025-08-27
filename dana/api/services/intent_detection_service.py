"""LLM-based Intent Detection Service for domain knowledge management."""

import json
import logging
from typing import Any

import yaml
from dana.api.core.schemas import IntentDetectionRequest, IntentDetectionResponse, DomainKnowledgeTree, MessageData
from dana.common.mixins.loggable import Loggable
from dana.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource as LLMResource
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
            prompt = self._build_intent_detection_prompt(request.user_message, request.chat_history, request.current_domain_tree)

            # Create LLM request
            llm_request = BaseRequest(
                arguments={
                    "messages": [
                        {"role": "system", "content": "You are an expert at understanding user intent in agent conversations."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.1,  # Lower temperature for more consistent intent detection
                    "max_tokens": 500,
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
                    intents = [
                        {
                            "intent": intent_result.get("intent", "general_query"),
                            "entities": intent_result.get("entities", {}),
                            "confidence": intent_result.get("confidence"),
                            "explanation": intent_result.get("explanation"),
                        }
                    ]

                primary_intent = intents[0]
                return IntentDetectionResponse(
                    intent=primary_intent.get("intent", "general_query"),
                    entities=primary_intent.get("entities", {}),
                    confidence=primary_intent.get("confidence"),
                    explanation=primary_intent.get("explanation"),
                    # Store all intents for multi-intent processing
                    additional_data={"all_intents": intents},
                )
            except json.JSONDecodeError:
                print(response)
                # Fallback parsing if LLM doesn't return valid JSON
                return self._fallback_intent_detection(request.user_message)

        except Exception as e:
            self.error(f"Error detecting intent: {e}")
            # Return fallback intent
            return IntentDetectionResponse(intent="general_query", entities={}, explanation=f"Error in intent detection: {str(e)}")

    async def generate_followup_message(self, user_message: str, agent: Any, knowledge_topics: list[str]) -> str:
        """Generate a contextually aware, empathetic follow-up message for the smart chat flow."""
        agent_name = getattr(agent, "name", None) or (agent.get("name") if isinstance(agent, dict) else None) or "your agent"
        agent_config = getattr(agent, "config", None) or (agent.get("config") if isinstance(agent, dict) else None) or {}
        domain = agent_config.get("domain", "")
        recent_topics = knowledge_topics[-2:] if len(knowledge_topics) > 1 else knowledge_topics  # Last 2 topics

        # Determine user's progress stage for empathetic response
        progress_stage = "starting" if len(knowledge_topics) < 3 else "developing" if len(knowledge_topics) < 8 else "advanced"

        # Build contextual prompt with empathy
        context_prompt = f"""
User just said: "{user_message}"
Agent name: {agent_name}
Agent domain: {domain or "not set yet"}
Recent topics added: {", ".join(recent_topics) if recent_topics else "none yet"}
Progress stage: {progress_stage}

Generate a supportive follow-up message that:
1. Acknowledges what they just accomplished
2. Asks ONE helpful next step question (20-30 words)
3. Shows understanding of their agent-building journey
4. Relates to their specific domain/topics when possible

Be encouraging and specific to their context.
"""

        llm_request = BaseRequest(
            arguments={
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an encouraging agent-building coach. Acknowledge progress, then ask one specific, helpful question about their next step.",
                    },
                    {"role": "user", "content": context_prompt},
                ],
                "temperature": 0.5,
                "max_tokens": 80,
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
            # Return contextual fallback messages
            if not knowledge_topics:
                return f"Great start! What domain would you like {agent_name} to specialize in?"
            elif len(knowledge_topics) < 3:
                return f"Nice work building {agent_name}'s knowledge! What related topic should we add next?"
            else:
                return f"Your {domain or 'agent'} is looking good! What aspect would you like to deepen?"

    def _build_intent_detection_prompt(
        self, user_message: str, chat_history: list[MessageData], domain_tree: DomainKnowledgeTree | None
    ) -> str:
        """Build the LLM prompt for intent detection."""
        # Convert domain tree to JSON for context
        tree_json = "null"
        if domain_tree:
            try:
                tree_json = yaml.safe_dump(domain_tree.model_dump(), sort_keys=False).replace("children: []", "")
            except Exception:
                tree_json = "null"
        # Build chat history context
        history_context = ""
        if chat_history:
            recent_messages = chat_history[-3:]  # Only include recent context
            history_context = "\n".join([f"{msg.role}: {msg.content}" for msg in recent_messages])
        prompt = f"""
You are an assistant in charge of managing an agent’s profile **and** its hierarchical domain-knowledge tree.

────────────────────────────────────────────────────────
TASK
────────────────────────────────────────────────────────
1. **Intent Extraction** – Detect **every** intent in the user’s latest message.  
2. **Entity & Instruction Extraction** – Pull any relevant entities (knowledge_path for tree navigation, name, domain, topics for agent specialties, tasks for agent responsibilities) and, for an `instruct` intent, capture the full instruction text.  
3. **Path Construction** – For each new topic, return the **exact path** that already exists in
   `tree_json`; append only the truly new node(s).

────────────────────────────────────────────────────────
AVAILABLE INTENTS
────────────────────────────────────────────────────────
• `add_information`            – user adds a new topic / knowledge area  
• `remove_information`         – user wants to remove/delete a topic from the knowledge tree
• `refresh_domain_knowledge`   – user wants to rebuild / reorganize the tree  
• `update_agent_properties`    – user changes agent name, domain, topics, tasks  
• `instruct`                   – user issues a command **about a specific topic's content**  
• `general_query`              – any other question or request  

A single message may contain multiple intents.

────────────────────────────────────────────────────────
INPUT VARIABLES
────────────────────────────────────────────────────────
• `history_context`          – recent chat (plain text)  
• `tree_json`                – **current** knowledge tree (YAML-like dict; see example)  
• `user_message`             – latest user utterance (plain text)

────────────────────────────────────────────────────────
RULES
────────────────────────────────────────────────────────
1. **Traverse the tree**  
   • Treat each `topic` in `tree_json` as one node.  
   • Find the deepest existing node(s) that match the user’s requested topic
     (case-insensitive, ignore punctuation).  
   • Only create **new** node(s) for the missing remainder of the path.  
   • The returned `knowledge_path` list MUST start with `"root"` and follow the
     *exact* topic names found in `tree_json`, preserving capitalization and spacing.

2. **No duplicate branches**  
   • If the topic already exists anywhere in the tree, point to that exact path;
     do **not** create a parallel branch.
   • Search the entire tree structure (not just immediate children) for existing topics.
   • Use case-insensitive matching to find existing topics.

3. **Coupled updates**  
   • If the user wants the agent to *gain expertise* (topics or tasks)
     **and** add that topic to knowledge, output **two** intents:
       `update_agent_properties` **and** `add_information`.  
   • `instruct` is **never coupled** with any other intent.

4. **`instruct` specifics**  
   • Choose the most relevant existing `knowledge_path`; create a new branch only if the subject is absent.  
   • Add an `"instruction_text"` field that contains the user’s command verbatim (trim greetings/pleasantries).  
   • Do **not** modify agent properties when handling `instruct`.

5. **Entity heuristics**  
   • **Domain** → patterns like "be a[n] <domain>", "work in <domain>", "<name> is <domain>", "<domain> expert".  
   • **Tasks** → "skilled in", "good at", "with tasks in", "abilities in", "responsible for".  
   • **Topics** → "specialist in", "expert in <topic>", "expertise in", "knowledge of", "specific to <topic>", "focused on <topic>", "specializes in <topic>".

6. **Confidence**  
   • Float 0–1 (≥ 0.80 only when extraction is obvious).

7. **Response shape** – Return **only** the JSON structure below.  
   Do *not* wrap it in markdown and do *not* echo any other text.

────────────────────────────────────────────────────────
OUTPUT JSON SCHEMA
────────────────────────────────────────────────────────
{{
  "intents": [
    {{
      "intent": "add_information|remove_information|refresh_domain_knowledge|update_agent_properties|instruct|general_query",
      "entities": {{
        "knowledge_path": ["root", ...],   // knowledge tree path - list or empty []
        "name": "",                        // agent name or ""
        "domain": "",                      // agent domain or ""
        "topics": "",                      // agent specialty topics or ""
        "tasks": "",                       // agent responsibilities or ""
        "instruction_text": ""             // present only for `instruct`, else ""
      }},
      "confidence": 0.00,
      "explanation": "… ≤ 25 words"
    }}
    // …additional intents
  ]
}}

────────────────────────────────────────────────────────
ILLUSTRATIVE EXAMPLES  (*not hard rules – always follow tree_json*)
────────────────────────────────────────────────────────
1. **Add existing leaf**  
   *tree_json contains* → … → Risk Management  
   **User**: “Add risk management to the agent.”  
   → `add_information` with `"knowledge_path": ["root","Finance and Analytics","quantitative analyst","Risk Management"]`  
   → `update_agent_properties` with `"topics": "Risk Management"`

2. **Add completely new branch**  
   **User**: “Add dividend analysis.”  
   → `add_information` with `"knowledge_path": ["root","Finance and Analytics","dividend analysis"]`

3. **Rename agent (properties-only)**  
   **User**: “Please rename my agent to Athena.”  
   → `update_agent_properties` with `"name": "Athena"`

4. **Change domain & tasks, no new topic needed**  
   *tree_json already has "Statistical Analysis"*  
   **User**: "Make Athena a senior quantitative analyst skilled in statistical analysis."  
   → `update_agent_properties` with `"domain": "senior quantitative analyst", "tasks": "statistical analysis"`

5. **Combined: domain change + brand-new topic**  
   **User**: "Make Jason a climate-risk analyst and add climate risk modeling."  
   → `update_agent_properties` with `"domain": "climate-risk analyst", "topics": "climate risk modeling"`  
   → `add_information` with `"knowledge_path": ["root","Environment analysis","climate risk modeling"]`

6. **Refresh the whole tree**  
   **User**: “Regenerate your finance knowledge structure.”  
   → `refresh_domain_knowledge` (entities can be empty)

7. **Remove existing topic**  
   *tree_json contains* → … → Sentiment Analysis  
   **User**: "I want to remove Sentiment Analysis topic"  
   → `remove_information` with `"knowledge_path": ["Sentiment Analysis"]`

8. **Instruction about existing topic**  
   *tree_json contains* → … → Credit Analysis  
   **User**: "Update the credit analysis section with Basel III compliance details."  
   → `instruct` with  
     `"knowledge_path": ["root","Finance and Analytics","Credit Analysis"],  
       "instruction_text": "Update the credit analysis section with Basel III compliance details."`

9. **Agent specialization**  
   **User**: "I want sofia is specific to personal finance"  
   → `update_agent_properties` with `"topics": "personal finance"`

10. **General query**  
   **User**: "What's the difference between VaR and CVaR?"  
   → `general_query` (entities empty)

────────────────────────────────────────────────────────
BEGIN
────────────────────────────────────────────────────────
Given:
Recent chat history: {history_context}

Current domain knowledge tree:
{tree_json}

User message: "{user_message}"

Produce the JSON response described above – nothing else.
"""
        return prompt

    def _fallback_intent_detection(self, user_message: str) -> IntentDetectionResponse:
        """Fallback intent detection using simple keyword matching."""
        message_lower = user_message.lower()

        # Simple keyword-based detection
        add_keywords = ["add", "learn", "know about", "include", "teach", "understand"]
        remove_keywords = ["remove", "delete", "get rid of", "take away", "eliminate"]
        refresh_keywords = ["update", "refresh", "regenerate", "restructure", "organize"]

        if any(keyword in message_lower for keyword in add_keywords):
            # Try to extract topic
            topic = self._extract_topic_from_message(user_message)
            return IntentDetectionResponse(
                intent="add_information",
                entities={"topic": topic} if topic else {},
                confidence=0.7,
                explanation="Detected add intent using keyword matching",
            )

        if any(keyword in message_lower for keyword in remove_keywords):
            # Try to extract topic to remove
            topic = self._extract_topic_from_message(user_message)
            return IntentDetectionResponse(
                intent="remove_information",
                entities={"topics": [topic]} if topic else {},
                confidence=0.7,
                explanation="Detected remove intent using keyword matching",
            )

        if any(keyword in message_lower for keyword in refresh_keywords):
            return IntentDetectionResponse(
                intent="refresh_domain_knowledge", entities={}, confidence=0.7, explanation="Detected refresh intent using keyword matching"
            )

        return IntentDetectionResponse(intent="general_query", entities={}, confidence=0.5, explanation="Defaulted to general query")

    def _extract_topic_from_message(self, message: str) -> str | None:
        """Extract potential topic from user message using simple heuristics."""
        # Simple extraction - look for patterns like "about X", "know X", etc.
        message_lower = message.lower()

        patterns = ["about ", "regarding ", "concerning ", "on ", "with "]

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
