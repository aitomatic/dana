"""
Smart Chat Router - Unified chat API with automatic intent detection and updates.
"""

import logging
from typing import Any
from threading import Lock
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from dana.api.core.database import get_db
from dana.api.core.models import Agent, AgentChatHistory
from dana.api.core.schemas import (
    DomainKnowledgeTree,
    IntentDetectionRequest,
    MessageData,
)
from dana.api.services.domain_knowledge_service import (
    get_domain_knowledge_service,
    DomainKnowledgeService,
)
from dana.api.services.intent_detection_service import (
    get_intent_detection_service,
    IntentDetectionService,
)
from dana.api.services.llm_tree_manager import get_llm_tree_manager, LLMTreeManager
from dana.api.services.knowledge_status_manager import KnowledgeStatusManager
from dana.api.routers.agents import clear_agent_cache
from dana.api.services.intent_detection.intent_handlers.knowledge_ops_handler import KnowledgeOpsHandler
from dana.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource as LLMResource
from dana.api.services.auto_knowledge_generator import get_auto_knowledge_generator
import os
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["smart-chat"])

# Concurrency protection: In-memory locks per agent
_agent_locks = defaultdict(Lock)


def _get_all_topics_from_tree(tree) -> list[str]:
    """Extract all topic names from a domain knowledge tree."""
    if not tree or not hasattr(tree, "root") or not tree.root:
        return []

    topics = []

    def traverse(node):
        if not node:
            return
        if hasattr(node, "topic") and node.topic:
            topics.append(node.topic)
        if hasattr(node, "children") and node.children:
            for child in node.children:
                traverse(child)

    traverse(tree.root)
    return topics


def _is_complex_knowledge_request(entities: dict[str, Any], user_message: str) -> bool:
    """
    Determine if a knowledge request is complex and should use KnowledgeOpsHandler.

    Complex indicators:
    - Multiple topics or complex topic paths
    - Keywords indicating multi-step processes
    - Requests for validation, approval, or generation
    - Complex instructions or detailed requirements
    """
    # Check for complex keywords in user message
    complex_keywords = [
        "generate",
        "create",
        "build",
        "develop",
        "comprehensive",
        "detailed",
        "validate",
        "verify",
        "check",
        "approve",
        "review",
        "analyze",
        "multi-step",
        "workflow",
        "process",
        "plan",
        "strategy",
        "complete",
        "thorough",
        "extensive",
        "in-depth",
        "advanced",
    ]

    message_lower = user_message.lower()
    has_complex_keywords = any(keyword in message_lower for keyword in complex_keywords)

    # Check for multiple topics or complex topic structure
    topics = entities.get("knowledge_path", [])
    has_multiple_topics = isinstance(topics, list) and len(topics) > 2

    # Check for detailed instructions or requirements
    details = entities.get("details", "")
    has_detailed_instructions = len(details) > 100 if details else False

    # Check for instruction text (indicates complex workflow)
    instruction_text = entities.get("instruction_text", "")
    has_instruction_text = len(instruction_text) > 50 if instruction_text else False

    # Check message length (longer messages often indicate complexity)
    is_long_message = len(user_message) > 200

    # Determine complexity
    complexity_score = 0
    if has_complex_keywords:
        complexity_score += 2
    if has_multiple_topics:
        complexity_score += 1
    if has_detailed_instructions:
        complexity_score += 1
    if has_instruction_text:
        complexity_score += 1
    if is_long_message:
        complexity_score += 1

    # Consider complex if score >= 2
    is_complex = complexity_score >= 2

    logger.info(f"Complexity analysis for '{user_message[:50]}...': score={complexity_score}, is_complex={is_complex}")
    logger.info(f"  - Complex keywords: {has_complex_keywords}")
    logger.info(f"  - Multiple topics: {has_multiple_topics}")
    logger.info(f"  - Detailed instructions: {has_detailed_instructions}")
    logger.info(f"  - Instruction text: {has_instruction_text}")
    logger.info(f"  - Long message: {is_long_message}")

    return is_complex


@router.post("/{agent_id}/smart-chat")
async def smart_chat(
    agent_id: int,
    request: dict[str, Any],
    intent_service: IntentDetectionService = Depends(get_intent_detection_service),
    domain_service: DomainKnowledgeService = Depends(get_domain_knowledge_service),
    llm_tree_manager: LLMTreeManager = Depends(get_llm_tree_manager),
    db: Session = Depends(get_db),
):
    """
    Smart chat API with modular intent processing:
    1. Detects user intent using LLM (intent_service only detects, doesn't process)
    2. Routes to appropriate processors based on intent
    3. Returns structured response

    Args:
        agent_id: Agent ID
        request: {"message": "user message", "conversation_id": optional}

    Returns:
        Response with intent detection and processing results
    """
    # Concurrency protection: Acquire lock for this agent
    agent_lock = _agent_locks[agent_id]
    if not agent_lock.acquire(blocking=False):
        raise HTTPException(status_code=429, detail="Another operation is in progress for this agent. Please try again.")

    try:
        user_message = request.get("message", "")
        conversation_id = request.get("conversation_id")

        if not user_message:
            raise HTTPException(status_code=400, detail="Message is required")

        logger.info(f"Smart chat for agent {agent_id}: {user_message[:100]}...")

        # Get agent
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        # --- Save user message to AgentChatHistory ---
        user_history = AgentChatHistory(agent_id=agent_id, sender="user", text=user_message, type="smart_chat")
        db.add(user_history)
        db.commit()
        db.refresh(user_history)
        # --- End save user message ---

        # Get current domain knowledge for context
        current_domain_tree = await domain_service.get_agent_domain_knowledge(agent_id, db)

        # Get recent chat history for context (last 10 messages)
        recent_chat_history = await _get_recent_chat_history(agent_id, db, limit=10)

        # Step 1: Intent Detection ONLY (no processing)
        intent_request = IntentDetectionRequest(
            user_message=user_message,
            chat_history=recent_chat_history,
            current_domain_tree=current_domain_tree,
            agent_id=agent_id,
        )

        intent_response = await intent_service.detect_intent(intent_request)
        detected_intent = intent_response.intent
        entities = intent_response.entities

        logger.info(f"Intent detected: {detected_intent} with entities: {entities}")

        # Get all intents for multi-intent processing
        all_intents = intent_response.additional_data.get(
            "all_intents",
            [
                {
                    "intent": detected_intent,
                    "entities": entities,
                    "confidence": intent_response.confidence,
                    "explanation": intent_response.explanation,
                }
            ],
        )

        logger.info(f"Processing {len(all_intents)} intents: {[i.get('intent') for i in all_intents]}")

        # Step 2: Process all detected intents
        processing_results = []
        for intent_data in all_intents:
            result = await _process_based_on_intent(
                intent=intent_data.get("intent"),
                entities=intent_data.get("entities", {}),
                user_message=user_message,
                agent=agent,
                domain_service=domain_service,
                llm_tree_manager=llm_tree_manager,
                current_domain_tree=current_domain_tree,
                chat_history=recent_chat_history,
                db=db,
            )
            processing_results.append(result)

        # Combine results from all intents
        processing_result = _combine_processing_results(processing_results)

        # Step 3: Generate creative LLM-based follow-up message
        # Extract knowledge topics from domain knowledge tree
        def extract_topics(tree):
            if not tree or not hasattr(tree, "root"):
                return []
            topics = []

            def traverse(node):
                if not node:
                    return
                if getattr(node, "topic", None):
                    topics.append(node.topic)
                for child in getattr(node, "children", []) or []:
                    traverse(child)

            traverse(tree.root)
            return topics

        knowledge_topics = extract_topics(current_domain_tree)
        follow_up_message = await intent_service.generate_followup_message(
            user_message=user_message, agent=agent, knowledge_topics=knowledge_topics
        )
        response = {
            "success": True,
            "message": user_message,
            "conversation_id": conversation_id,
            # Intent detection results
            "detected_intent": detected_intent,
            "intent_confidence": intent_response.confidence,
            "intent_explanation": intent_response.explanation,
            "entities_extracted": entities,
            # Processing results
            **processing_result,
            "follow_up_message": follow_up_message,
        }

        # --- Save agent response to AgentChatHistory ---
        agent_response_text = response.get("follow_up_message")
        if agent_response_text:
            agent_history = AgentChatHistory(
                agent_id=agent_id,
                sender="agent",
                text=agent_response_text,
                type="smart_chat",
            )
            db.add(agent_history)
            db.commit()
            db.refresh(agent_history)
        # --- End save agent response ---

        logger.info(f"Smart chat completed for agent {agent_id}: intent={detected_intent}")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in smart chat for agent {agent_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Always release the lock
        agent_lock.release()


@router.get("/{agent_id}/knowledge-generation/status")
async def get_knowledge_generation_status(
    agent_id: int,
    db: Session = Depends(get_db),
):
    """
    Get the current status of knowledge generation for an agent.
    """
    try:
        # Get the agent to find its folder_path
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        folder_path = agent.config.get("folder_path") if agent.config else None
        if not folder_path:
            folder_path = os.path.join("agents", f"agent_{agent_id}")

        # Get the auto knowledge generator
        auto_generator = get_auto_knowledge_generator(agent_id, folder_path)

        # Get generation status
        status = auto_generator.get_generation_status()

        return status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting knowledge generation status for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/knowledge-generation/generate-all")
async def generate_all_knowledge(
    agent_id: int,
    db: Session = Depends(get_db),
):
    """
    Generate knowledge for all pending/failed topics for an agent.
    """
    try:
        # Get the agent to find its folder_path
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        folder_path = agent.config.get("folder_path") if agent.config else None
        if not folder_path:
            folder_path = os.path.join("agents", f"agent_{agent_id}")

        # Get the auto knowledge generator
        auto_generator = get_auto_knowledge_generator(agent_id, folder_path)

        # Generate all knowledge
        result = await auto_generator.generate_all_knowledge()

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating all knowledge for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/knowledge-generation/stop")
async def stop_knowledge_generation(
    agent_id: int,
    db: Session = Depends(get_db),
):
    """
    Stop the current knowledge generation process for an agent.
    """
    try:
        # Get the agent to find its folder_path
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        folder_path = agent.config.get("folder_path") if agent.config else None
        if not folder_path:
            folder_path = os.path.join("agents", f"agent_{agent_id}")

        # Get the auto knowledge generator
        auto_generator = get_auto_knowledge_generator(agent_id, folder_path)

        # Stop generation
        result = auto_generator.stop_generation()

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping knowledge generation for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/knowledge-generation/retry-failed")
async def retry_failed_knowledge_generation(
    agent_id: int,
    db: Session = Depends(get_db),
):
    """
    Retry all failed knowledge generation topics for an agent.
    """
    try:
        # Get the agent to find its folder_path
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        folder_path = agent.config.get("folder_path") if agent.config else None
        if not folder_path:
            folder_path = os.path.join("agents", f"agent_{agent_id}")

        # Get the auto knowledge generator
        auto_generator = get_auto_knowledge_generator(agent_id, folder_path)

        # Retry failed topics
        result = auto_generator.retry_failed_topics()

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrying failed knowledge generation for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _get_recent_chat_history(agent_id: int, db: Session, limit: int = 10) -> list[MessageData]:
    """Get recent chat history for an agent."""
    try:
        from dana.api.core.models import AgentChatHistory

        # Get recent history excluding the current message being processed
        history = (
            db.query(AgentChatHistory)
            .filter(
                AgentChatHistory.agent_id == agent_id,
                AgentChatHistory.type == "smart_chat",
            )
            .order_by(AgentChatHistory.created_at.desc())
            .limit(limit)
            .all()
        )

        # Convert to MessageData format (reverse to get chronological order)
        message_history = []
        for h in reversed(history):
            message_history.append(MessageData(role=h.sender, content=h.text))

        return message_history

    except Exception as e:
        logger.warning(f"Failed to get chat history: {e}")
        return []


async def _process_based_on_intent(
    intent: str,
    entities: dict[str, Any],
    user_message: str,
    agent: Agent,
    domain_service: DomainKnowledgeService,
    llm_tree_manager: LLMTreeManager,
    current_domain_tree: DomainKnowledgeTree | None,
    chat_history: list[MessageData],
    db: Session,
) -> dict[str, Any]:
    """
    Process user intent with appropriate handler.
    Each intent type has its own focused processor.
    """

    if intent == "add_information":
        # Check if this is a complex request that should use KnowledgeOpsHandler
        if _is_complex_knowledge_request(entities, user_message):
            logger.info(f"🔄 Routing complex add_information to KnowledgeOpsHandler for agent {agent.id}")
            return await _process_complex_knowledge_intent(
                entities,
                user_message,
                agent,
                domain_service,
                current_domain_tree,
                chat_history,
                db,
            )
        else:
            logger.info(f"⚡ Using fast path for simple add_information for agent {agent.id}")
            return await _process_add_information_intent(
                entities,
                agent,
                domain_service,
                llm_tree_manager,
                current_domain_tree,
                chat_history,
                db,
            )

    elif intent == "remove_information":
        # Check if this is a complex request that should use KnowledgeOpsHandler
        if _is_complex_knowledge_request(entities, user_message):
            logger.info(f"🔄 Routing complex remove_information to KnowledgeOpsHandler for agent {agent.id}")
            return await _process_complex_knowledge_intent(
                entities,
                user_message,
                agent,
                domain_service,
                current_domain_tree,
                chat_history,
                db,
            )
        else:
            logger.info(f"⚡ Using fast path for simple remove_information for agent {agent.id}")
            return await _process_remove_information_intent(
                entities,
                agent,
                domain_service,
                llm_tree_manager,
                current_domain_tree,
                db,
            )

    elif intent == "instruct":
        return await _process_instruct_intent(
            entities, user_message, agent, domain_service, llm_tree_manager, current_domain_tree, chat_history, db
        )

    elif intent == "refresh_domain_knowledge":
        return await _process_refresh_knowledge_intent(user_message, agent.id, domain_service, db)

    elif intent == "generate_all_knowledge":
        return await _process_generate_all_knowledge_intent(agent, db)

    elif intent == "update_agent_properties":
        return await _process_update_agent_intent(entities, user_message, agent, db)

    elif intent == "test_agent":
        return await _process_test_agent_intent(entities, user_message, agent)

    else:  # general_query
        return await _process_general_query_intent(user_message, agent)


async def _process_complex_knowledge_intent(
    entities: dict[str, Any],
    user_message: str,
    agent: Agent,
    domain_service: DomainKnowledgeService,
    current_domain_tree: DomainKnowledgeTree | None,
    chat_history: list[MessageData],
    db: Session,
) -> dict[str, Any]:
    """
    Process complex knowledge operations using KnowledgeOpsHandler.
    This handles multi-step, LLM-driven knowledge workflows.
    """

    logger.info(f"🔄 Processing complex knowledge request for agent {agent.id}: {user_message[:100]}...")

    try:
        # Build agent folder paths
        folder_path = agent.config.get("folder_path") if agent.config else None
        if not folder_path:
            folder_path = os.path.join("agents", f"agent_{agent.id}")

        # Knowledge file paths
        domain_knowledge_path = os.path.join(folder_path, "domain_knowledge.json")
        knows_folder = os.path.join(folder_path, "knows")
        knowledge_status_path = os.path.join(knows_folder, "knowledge_status.json")

        # Ensure directories exist
        os.makedirs(folder_path, exist_ok=True)
        os.makedirs(knows_folder, exist_ok=True)

        # Create LLM resource
        llm = LLMResource()

        # Create KnowledgeOpsHandler
        handler = KnowledgeOpsHandler(
            domain_knowledge_path=domain_knowledge_path,
            llm=llm,
            domain=agent.description or "General",
            role=agent.name or "Domain Expert",
            knowledge_status_path=knowledge_status_path,
        )

        # Create intent request
        intent_request = IntentDetectionRequest(
            user_message=user_message,
            chat_history=chat_history,
            current_domain_tree=current_domain_tree,
            agent_id=agent.id,
        )

        logger.info(f"🚀 Starting KnowledgeOpsHandler workflow for agent {agent.id}")

        # Execute the handler
        result = await handler.handle(intent_request)

        logger.info(f"✅ KnowledgeOpsHandler completed for agent {agent.id}: status={result.get('status')}")

        # Convert KnowledgeOpsHandler result to smart_chat format
        if result.get("status") == "success":
            return {
                "processor": "complex_knowledge",
                "success": True,
                "agent_response": result.get("message", "Complex knowledge operation completed successfully."),
                "updates_applied": ["Complex knowledge workflow executed"],
                "conversation": result.get("conversation", []),
                "final_result": result.get("final_result", {}),
            }
        elif result.get("status") == "user_input_required":
            return {
                "processor": "complex_knowledge",
                "success": False,
                "agent_response": "I need more information to complete this knowledge operation. Please provide additional details.",
                "updates_applied": [],
                "requires_user_input": True,
                "conversation": result.get("conversation", []),
            }
        else:
            return {
                "processor": "complex_knowledge",
                "success": False,
                "agent_response": f"Complex knowledge operation failed: {result.get('message', 'Unknown error')}",
                "updates_applied": [],
            }

    except Exception as e:
        logger.error(f"❌ Error in complex knowledge processing for agent {agent.id}: {e}", exc_info=True)
        return {
            "processor": "complex_knowledge",
            "success": False,
            "agent_response": f"Sorry, I encountered an error while processing your complex knowledge request: {str(e)}",
            "updates_applied": [],
        }


async def _process_generate_all_knowledge_intent(
    agent: Agent,
    db: Session,
) -> dict[str, Any]:
    """
    Process generate_all_knowledge intent - generates knowledge for all pending/failed topics.
    """

    logger.info(f"🔄 Processing generate_all_knowledge for agent {agent.id}")

    try:
        # Get agent folder path
        folder_path = agent.config.get("folder_path") if agent.config else None
        if not folder_path:
            folder_path = os.path.join("agents", f"agent_{agent.id}")

        # Get the auto knowledge generator
        auto_generator = get_auto_knowledge_generator(agent.id, folder_path)

        # Generate all knowledge
        generation_result = await auto_generator.generate_all_knowledge()

        if generation_result["success"]:
            if generation_result["total_topics"] > 0:
                return {
                    "processor": "generate_all_knowledge",
                    "success": True,
                    "agent_response": f"Started generating knowledge for {generation_result['total_topics']} topics. This will run in the background. You can check the status anytime.",
                    "updates_applied": [f"Started generation for {generation_result['total_topics']} topics"],
                    "generation_details": generation_result,
                }
            else:
                return {
                    "processor": "generate_all_knowledge",
                    "success": True,
                    "agent_response": "All knowledge topics are already up to date. No generation needed.",
                    "updates_applied": [],
                    "generation_details": generation_result,
                }
        else:
            return {
                "processor": "generate_all_knowledge",
                "success": False,
                "agent_response": f"Failed to start knowledge generation: {generation_result['message']}",
                "updates_applied": [],
                "generation_details": generation_result,
            }

    except Exception as e:
        logger.error(f"❌ Error in generate_all_knowledge for agent {agent.id}: {e}", exc_info=True)
        return {
            "processor": "generate_all_knowledge",
            "success": False,
            "agent_response": f"Sorry, I encountered an error while starting knowledge generation: {str(e)}",
            "updates_applied": [],
        }


async def _process_add_information_intent(
    entities: dict[str, Any],
    agent: Agent,
    domain_service: DomainKnowledgeService,
    llm_tree_manager: LLMTreeManager,
    current_domain_tree: DomainKnowledgeTree | None,
    chat_history: list[MessageData],
    db: Session,
) -> dict[str, Any]:
    """Process add_information intent using LLM-powered tree management."""

    topics = entities.get("knowledge_path")
    parent = entities.get("parent")
    details = entities.get("details")

    print("🧠 Processing add_information with LLM tree manager:")
    print(f"  - Topics: {topics}")
    print(f"  - Parent: {parent}")
    print(f"  - Details: {details}")
    print(f"  - Agent: {agent.name}")

    if not topics:
        return {
            "processor": "add_information",
            "success": False,
            "agent_response": "I couldn't identify what topic you want me to learn about. Could you be more specific?",
            "updates_applied": [],
        }

    try:
        # Check for duplicate topics before adding
        existing_topics = _get_all_topics_from_tree(current_domain_tree)
        duplicate_topics = []
        new_topics = []

        for topic in topics:
            # Advanced normalization for robust topic matching
            def normalize_topic(t: str) -> str:
                """Normalize topic for robust comparison."""
                import re

                # Convert to lowercase, strip whitespace
                normalized = t.lower().strip()
                # Replace multiple spaces with single space
                normalized = re.sub(r"\s+", " ", normalized)
                # Remove special characters but keep alphanumeric and spaces
                normalized = re.sub(r"[^\w\s]", "", normalized)
                return normalized

            normalized_topic = normalize_topic(topic)

            # Check if topic already exists (robust matching)
            is_duplicate = any(normalize_topic(existing) == normalized_topic for existing in existing_topics)

            if is_duplicate:
                duplicate_topics.append(topic)
            else:
                new_topics.append(topic)

        # If all topics are duplicates, inform user
        if duplicate_topics and not new_topics:
            duplicate_list = ", ".join(duplicate_topics)
            return {
                "processor": "add_information",
                "success": False,
                "agent_response": f"I already have knowledge about {duplicate_list}. What new topic would you like me to learn about?",
                "updates_applied": [],
                "duplicate_topics": duplicate_topics,
            }

        # If some topics are duplicates, proceed with new ones and inform about duplicates
        if duplicate_topics:
            duplicate_list = ", ".join(duplicate_topics)
            print(f"⚠️ Found duplicate topics: {duplicate_list}")
            print(f"✅ Proceeding with new topics: {new_topics}")
            topics = new_topics  # Only process new topics

        # Use LLM tree manager for intelligent placement
        update_response = await llm_tree_manager.add_topic_to_knowledge(
            current_tree=current_domain_tree,
            paths=topics,
            suggested_parent=parent,
            context_details=details,
            agent_name=agent.name,
            agent_description=agent.description or "",
            chat_history=chat_history,
        )

        print(f"🎯 LLM tree manager response: success={update_response.success}")
        if update_response.error:
            print(f"❌ LLM tree manager error: {update_response.error}")

        if update_response.success and update_response.updated_tree:
            # Save the updated tree
            save_success = await domain_service.save_agent_domain_knowledge(
                agent_id=agent.id, tree=update_response.updated_tree, db=db, agent=agent
            )

            print(f"💾 Save result: {save_success}")

            if save_success:
                # Save version with proper change tracking
                try:
                    from dana.api.services.domain_knowledge_version_service import get_domain_knowledge_version_service

                    version_service = get_domain_knowledge_version_service()
                    version_service.save_version(
                        agent_id=agent.id, tree=update_response.updated_tree, change_summary=f"Added {', '.join(topics)}", change_type="add"
                    )
                except Exception as e:
                    print(f"⚠️ Warning: Could not save version: {e}")

                # Get folder path for cache clearing and knowledge status management
                folder_path = agent.config.get("folder_path") if agent.config else None
                if not folder_path:
                    folder_path = os.path.join("agents", f"agent_{agent.id}")

                # Always clear cache when adding information to ensure consistency
                clear_agent_cache(folder_path)
                logger.info(f"Cleared RAG cache for agent {agent.id} after adding topics")

                # --- Auto-trigger knowledge generation for newly added topics ---
                try:
                    # Get the auto knowledge generator for this agent
                    auto_generator = get_auto_knowledge_generator(agent.id, folder_path)

                    # Collect newly added topics
                    new_topics = []
                    for topic in topics:
                        # Check if this topic was actually newly added (not a duplicate)
                        if topic not in duplicate_topics:
                            # Find the topic in the updated tree to get its full path
                            def find_topic_path(node, target_topic, current_path=None):
                                if current_path is None:
                                    current_path = []

                                if node.topic == target_topic:
                                    return current_path + [node.topic]

                                for child in getattr(node, "children", []):
                                    result = find_topic_path(child, target_topic, current_path + [node.topic])
                                    if result:
                                        return result
                                return None

                            topic_path = find_topic_path(update_response.updated_tree.root, topic)
                            print(f"🔍 Looking for topic '{topic}' in tree")
                            print(f"🔍 Found path: {topic_path}")

                            if topic_path:
                                # Convert path to area name format
                                area_name = " - ".join(topic_path)
                                new_topics.append(area_name)
                                print(f"✅ Added to auto-generation: {area_name}")
                            else:
                                # If we can't find the exact path, use the topic name directly
                                print(f"⚠️ Could not find path for topic '{topic}', using topic name directly")
                                new_topics.append(topic)

                    # Auto-generate knowledge for new topics
                    if new_topics:
                        logger.info(f"Auto-generating knowledge for {len(new_topics)} new topics: {new_topics}")
                        generation_result = await auto_generator.generate_for_new_topics(new_topics)

                        if generation_result["success"]:
                            logger.info(f"Auto-generation started: {generation_result['message']}")
                            if generation_result["topics_generated"]:
                                print(f"🚀 Auto-started generation for: {generation_result['topics_generated']}")
                        else:
                            logger.warning(f"Auto-generation failed: {generation_result['message']}")
                    else:
                        logger.info("No new topics to auto-generate")

                except Exception as e:
                    logger.error(f"Error in auto knowledge generation: {e}")
                    print(f"[smart-chat] Error in auto knowledge generation: {e}")
                # --- End auto-trigger ---

                # Prepare response message considering duplicates
                if duplicate_topics:
                    duplicate_list = ", ".join(duplicate_topics)
                    response_message = f"Great! I've added {topics} to my knowledge. Note: I already knew about {duplicate_list}. What else would you like me to learn?"
                else:
                    response_message = f"Perfect! I've intelligently organized my knowledge to include {topics}. {update_response.changes_summary}. What would you like to know about this topic?"

                return {
                    "processor": "add_information",
                    "success": True,
                    "agent_response": response_message,
                    "updates_applied": [update_response.changes_summary or f"Added {topics}"],
                    "updated_domain_tree": update_response.updated_tree.model_dump(),
                    "duplicate_topics": duplicate_topics if duplicate_topics else [],
                }
            else:
                return {
                    "processor": "add_information",
                    "success": False,
                    "agent_response": "I tried to update my knowledge, but something went wrong saving it.",
                    "updates_applied": [],
                }
        else:
            return {
                "processor": "add_information",
                "success": False,
                "agent_response": update_response.error or "I couldn't update my knowledge tree.",
                "updates_applied": [],
            }
    except Exception as e:
        print(f"❌ Exception in LLM-powered add_information: {e}")
        return {
            "processor": "add_information",
            "success": False,
            "agent_response": f"Sorry, I ran into an error while updating my knowledge: {e}",
            "updates_applied": [],
        }


async def _process_remove_information_intent(
    entities: dict[str, Any],
    agent: Agent,
    domain_service: DomainKnowledgeService,
    llm_tree_manager: LLMTreeManager,
    current_domain_tree: DomainKnowledgeTree | None,
    db: Session,
) -> dict[str, Any]:
    """Process remove_information intent to remove topics from knowledge tree."""

    topics = entities.get("knowledge_path", [])

    print("🗑️ Processing remove_information intent:")
    print(f"  - Topics to remove: {topics}")
    print(f"  - Agent: {agent.name}")

    if not topics:
        return {
            "processor": "remove_information",
            "success": False,
            "agent_response": "I couldn't identify which topic you want me to remove. Could you be more specific?",
            "updates_applied": [],
        }

    if not current_domain_tree:
        return {
            "processor": "remove_information",
            "success": False,
            "agent_response": "I don't have any knowledge topics to remove yet.",
            "updates_applied": [],
        }

    try:
        # Extract only the target topics to remove, not the full path
        # If topics is a path, we only want to remove the last (leaf) topic
        target_topics = []
        if isinstance(topics, list) and len(topics) > 1:
            # If we have a path like ["root", "Finance", ..., "Sentiment Analysis"]
            # Only remove the actual target topic (last non-root item)
            non_root_topics = []
            for topic in topics:
                if topic.lower() not in ["root", "untitled", "domain knowledge"]:
                    non_root_topics.append(topic)

            # Smart detection: if the user mentioned a specific nested topic, remove that
            # Otherwise, remove the last topic in the path
            if len(non_root_topics) > 1:
                # For now, keep the conservative approach of removing the last topic
                # TODO: Enhance with better intent detection
                target_topics = [non_root_topics[-1]] if non_root_topics else topics
            else:
                target_topics = non_root_topics if non_root_topics else topics
        else:
            target_topics = topics

        # Critical validation: Prevent root node removal
        protected_topics = {"root", "untitled", "domain knowledge", ""}
        filtered_targets = []
        for topic in target_topics:
            if topic.lower().strip() not in protected_topics:
                filtered_targets.append(topic)
            else:
                print(f"⚠️ Blocked attempt to remove protected topic: {topic}")

        if not filtered_targets and target_topics:
            return {
                "processor": "remove_information",
                "success": False,
                "agent_response": "I can't remove system topics like 'root' or 'domain knowledge'. Please specify a specific knowledge topic to remove.",
                "updates_applied": [],
            }

        target_topics = filtered_targets

        print(f"🎯 Target topics to remove (filtered): {target_topics}")

        # Find topics that exist in the tree
        existing_topics = _get_all_topics_from_tree(current_domain_tree)
        topics_to_remove = []
        topics_not_found = []

        for topic in target_topics:
            # Advanced normalization for robust topic matching
            def normalize_topic(t: str) -> str:
                """Normalize topic for robust comparison."""
                import re

                # Convert to lowercase, strip whitespace
                normalized = t.lower().strip()
                # Replace multiple spaces with single space
                normalized = re.sub(r"\s+", " ", normalized)
                # Remove special characters but keep alphanumeric and spaces
                normalized = re.sub(r"[^\w\s]", "", normalized)
                return normalized

            normalized_topic = normalize_topic(topic)

            # Find matching existing topic with robust matching
            matching_topic = None
            for existing in existing_topics:
                if normalize_topic(existing) == normalized_topic:
                    matching_topic = existing
                    break

            if matching_topic:
                topics_to_remove.append(matching_topic)
            else:
                topics_not_found.append(topic)

        # If no topics found, inform user
        if not topics_to_remove:
            not_found_list = ", ".join(topics_not_found)
            return {
                "processor": "remove_information",
                "success": False,
                "agent_response": f"I don't have knowledge about {not_found_list}. What topic would you like me to remove?",
                "updates_applied": [],
                "topics_not_found": topics_not_found,
            }

        # Use LLM tree manager to remove topics intelligently
        remove_response = await llm_tree_manager.remove_topic_from_knowledge(
            current_tree=current_domain_tree,
            topics_to_remove=topics_to_remove,
            agent_name=agent.name,
            agent_description=agent.description or "",
        )

        print(f"🗑️ LLM tree manager remove response: success={remove_response.success}")
        if remove_response.error:
            print(f"❌ LLM tree manager error: {remove_response.error}")

        if remove_response.success and remove_response.updated_tree:
            # Save the updated tree
            save_success = await domain_service.save_agent_domain_knowledge(
                agent_id=agent.id, tree=remove_response.updated_tree, db=db, agent=agent
            )

            print(f"💾 Save result: {save_success}")

            if save_success:
                # Save version with proper change tracking
                try:
                    from dana.api.services.domain_knowledge_version_service import get_domain_knowledge_version_service

                    version_service = get_domain_knowledge_version_service()
                    version_service.save_version(
                        agent_id=agent.id,
                        tree=remove_response.updated_tree,
                        change_summary=f"Removed {', '.join(topics_to_remove)}",
                        change_type="remove",
                    )
                except Exception as e:
                    print(f"⚠️ Warning: Could not save version: {e}")

                # Get folder path for cache clearing and knowledge status management
                folder_path = agent.config.get("folder_path") if agent.config else None
                if not folder_path:
                    folder_path = os.path.join("agents", f"agent_{agent.id}")

                # Always clear cache when removing information to ensure consistency
                clear_agent_cache(folder_path)
                logger.info(f"Cleared RAG cache for agent {agent.id} after removing topics")

                # Remove topics from knowledge status manager using UUIDs
                try:
                    knows_folder = os.path.join(folder_path, "knows")
                    if os.path.exists(knows_folder):
                        status_path = os.path.join(knows_folder, "knowledge_status.json")
                        status_manager = KnowledgeStatusManager(status_path, agent_id=str(agent.id))

                        # Collect UUIDs of topics to remove from the updated tree
                        topics_uuids_to_remove = []

                        def collect_removed_topic_uuids(node, target_topics):
                            """Collect UUIDs of topics that match removal criteria"""
                            topic_name = getattr(node, "topic", "")
                            node_id = getattr(node, "id", None)

                            # Check if this topic matches any target for removal
                            for target in target_topics:
                                if target.lower() in topic_name.lower() and node_id:
                                    topics_uuids_to_remove.append(node_id)
                                    print(f"🗑️ Marked UUID {node_id} for removal (topic: {topic_name})")

                            # Recursively check children
                            for child in getattr(node, "children", []):
                                collect_removed_topic_uuids(child, target_topics)

                        # Find UUIDs before removal by comparing original and updated trees
                        if current_domain_tree and remove_response.updated_tree:
                            # Find topics that exist in original but not in updated tree
                            original_uuids = set()
                            updated_uuids = set()

                            def collect_all_uuids(node, uuid_set):
                                node_id = getattr(node, "id", None)
                                if node_id:
                                    uuid_set.add(node_id)
                                for child in getattr(node, "children", []):
                                    collect_all_uuids(child, uuid_set)

                            collect_all_uuids(current_domain_tree.root, original_uuids)
                            collect_all_uuids(remove_response.updated_tree.root, updated_uuids)

                            topics_uuids_to_remove = list(original_uuids - updated_uuids)
                            print(f"🗑️ Found {len(topics_uuids_to_remove)} UUIDs to remove from status")

                        # Remove status entries by UUIDs
                        if topics_uuids_to_remove:
                            status_manager.remove_topics_by_uuids(topics_uuids_to_remove)
                            print(f"🗑️ Removed {len(topics_uuids_to_remove)} topics from knowledge status by UUID")

                        # Remove ALL knowledge files that contain the removed topics in their path
                        for topic in topics_to_remove:
                            # Find and remove files that have the topic as a specific path component
                            if os.path.exists(knows_folder):
                                for filename in os.listdir(knows_folder):
                                    if filename.endswith(".json") and filename != "knowledge_status.json":
                                        # Remove .json extension for pattern matching
                                        filename_without_ext = filename[:-5]  # Remove .json

                                        # Split filename into path components
                                        path_components = filename_without_ext.split("___")

                                        # Check if the removed topic is an exact match in the path
                                        topic_normalized = topic.replace(" ", "_")
                                        should_remove = False

                                        for component in path_components:
                                            if component.lower() == topic_normalized.lower():
                                                should_remove = True
                                                break

                                        if should_remove:
                                            file_path = os.path.join(knows_folder, filename)
                                            try:
                                                os.remove(file_path)
                                                print(f"🗑️ Removed knowledge file: {filename}")
                                            except Exception as file_error:
                                                print(f"⚠️ Warning: Could not remove file {filename}: {file_error}")

                except Exception as e:
                    print(f"⚠️ Warning: Error cleaning up knowledge files: {e}")

                # Prepare response message
                removed_list = ", ".join(topics_to_remove)
                if topics_not_found:
                    not_found_list = ", ".join(topics_not_found)
                    response_message = f"I've removed {removed_list} from my knowledge. Note: I didn't have knowledge about {not_found_list}. What else would you like me to learn about?"
                else:
                    response_message = f"Perfect! I've removed {removed_list} from my knowledge base. {remove_response.changes_summary}. What new topic would you like me to learn?"

                return {
                    "processor": "remove_information",
                    "success": True,
                    "agent_response": response_message,
                    "updates_applied": [remove_response.changes_summary or f"Removed {removed_list}"],
                    "updated_domain_tree": remove_response.updated_tree.model_dump(),
                    "topics_removed": topics_to_remove,
                    "topics_not_found": topics_not_found if topics_not_found else [],
                }
            else:
                return {
                    "processor": "remove_information",
                    "success": False,
                    "agent_response": "I tried to remove the topics, but something went wrong saving the changes.",
                    "updates_applied": [],
                }
        else:
            return {
                "processor": "remove_information",
                "success": False,
                "agent_response": remove_response.error or "I couldn't remove the topics from my knowledge tree.",
                "updates_applied": [],
            }
    except Exception as e:
        print(f"❌ Exception in remove_information: {e}")
        return {
            "processor": "remove_information",
            "success": False,
            "agent_response": f"Sorry, I ran into an error while removing topics: {e}",
            "updates_applied": [],
        }


async def _process_refresh_knowledge_intent(
    user_message: str,
    agent_id: int,
    domain_service: DomainKnowledgeService,
    db: Session,
) -> dict[str, Any]:
    """Process refresh_domain_knowledge intent - focused on restructuring knowledge tree."""

    refresh_response = await domain_service.refresh_domain_knowledge(agent_id=agent_id, context=user_message, db=db)

    return {
        "processor": "refresh_knowledge",
        "success": refresh_response.success,
        "agent_response": "I've reorganized and refreshed my knowledge structure to be more efficient and comprehensive."
        if refresh_response.success
        else "I had trouble refreshing my knowledge structure. Please try again.",
        "updates_applied": [refresh_response.changes_summary] if refresh_response.changes_summary else [],
        "updated_domain_tree": refresh_response.updated_tree.model_dump() if refresh_response.updated_tree else None,
    }


async def _process_update_agent_intent(entities: dict[str, Any], user_message: str, agent: Agent, db: Session) -> dict[str, Any]:
    updated_fields = []
    if "name" in entities and entities["name"]:
        agent.name = entities["name"].strip()
        updated_fields.append("name")
    if "domain" in entities and entities["domain"]:
        agent.description = entities["domain"].strip()
        updated_fields.append("domain")
    # Save topics and tasks to config
    # Create a new dict to ensure SQLAlchemy detects the change
    config = dict(agent.config) if agent.config else {}

    # Handle topics - accumulate instead of overwrite
    if "topics" in entities and entities["topics"]:
        new_topics = entities["topics"]
        if isinstance(new_topics, str):
            # Split comma-separated string into list
            new_topics = [s.strip() for s in new_topics.split(",") if s.strip()]
        elif not isinstance(new_topics, list):
            new_topics = [str(new_topics)]

        # Get existing topics and merge with new ones
        existing_topics = config.get("topics", [])
        if not isinstance(existing_topics, list):
            existing_topics = []

        # Combine and deduplicate (case-insensitive)
        combined_topics = existing_topics.copy()
        for new_topic in new_topics:
            # Check if this topic already exists (case-insensitive)
            if not any(new_topic.lower() == existing.lower() for existing in combined_topics):
                combined_topics.append(new_topic)

        config["topics"] = combined_topics
        updated_fields.append("topics")

    # Handle tasks - accumulate instead of overwrite
    if "tasks" in entities and entities["tasks"]:
        new_tasks = entities["tasks"]
        if isinstance(new_tasks, str):
            # Split comma-separated string into list
            new_tasks = [s.strip() for s in new_tasks.split(",") if s.strip()]
        elif not isinstance(new_tasks, list):
            new_tasks = [str(new_tasks)]

        # Get existing tasks and merge with new ones
        existing_tasks = config.get("tasks", [])
        if not isinstance(existing_tasks, list):
            existing_tasks = []

        # Combine and deduplicate (case-insensitive)
        combined_tasks = existing_tasks.copy()
        for new_task in new_tasks:
            # Check if this task already exists (case-insensitive)
            if not any(new_task.lower() == existing.lower() for existing in combined_tasks):
                combined_tasks.append(new_task)

        config["tasks"] = combined_tasks
        updated_fields.append("tasks")
    agent.config = config
    if updated_fields:
        db.commit()
        db.refresh(agent)
        return {
            "processor": "update_agent",
            "success": True,
            "agent_response": f"Agent information updated: {', '.join(updated_fields)}.",
            "updates_applied": updated_fields,
        }
    else:
        return {
            "processor": "update_agent",
            "success": False,
            "agent_response": "No valid agent property found to update.",
            "updates_applied": [],
        }


async def _process_test_agent_intent(entities: dict[str, Any], user_message: str, agent: Agent) -> dict[str, Any]:
    """Process test_agent intent - focused on testing agent capabilities."""

    # This is a placeholder for future agent testing functionality

    return {
        "processor": "test_agent",
        "success": False,
        "agent_response": "Agent testing functionality is not yet implemented. I can help you with adding knowledge or answering questions instead.",
        "updates_applied": [],
    }


async def _process_instruct_intent(
    entities: dict[str, Any],
    user_message: str,
    agent: Agent,
    domain_service: DomainKnowledgeService,
    llm_tree_manager: LLMTreeManager,
    current_domain_tree: DomainKnowledgeTree | None,
    chat_history: list[MessageData],
    db: Session,
) -> dict[str, Any]:
    """Process instruct intent - focused on instructing the agent to do something."""

    # Extract instruction text and topics from entities
    instruction_text = entities.get("instruction_text", "")
    topics = entities.get("knowledge_path", [])

    print("🎯 Processing instruct intent:")
    print(f"  - Instruction text: {instruction_text}")
    print(f"  - Topics: {topics}")
    print(f"  - Agent: {agent.name}")

    if not instruction_text:
        return {
            "processor": "instruct",
            "success": False,
            "agent_response": "I couldn't identify what instruction you want me to follow. Could you be more specific?",
            "updates_applied": [],
        }

    try:
        # Step 1: Call _process_add_information_intent to create or update existing paths
        # This ensures the topic structure exists in the domain tree
        add_info_result = await _process_add_information_intent(
            entities=entities,
            agent=agent,
            domain_service=domain_service,
            llm_tree_manager=llm_tree_manager,
            current_domain_tree=current_domain_tree,
            chat_history=chat_history,
            db=db,
        )

        print(f"📝 Add information result: success={add_info_result.get('success')}")

        if not add_info_result.get("success"):
            return {
                "processor": "instruct",
                "success": False,
                "agent_response": f"I couldn't set up the knowledge structure for your instruction: {add_info_result.get('agent_response', 'Unknown error')}",
                "updates_applied": [],
            }

        # Step 2: Update the instruction text as answers_by_topics in JSON knowledge files
        instruction_update_success = await _update_instruction_as_knowledge(
            agent=agent, topics=topics, instruction_text=instruction_text, domain_service=domain_service, db=db
        )

        if instruction_update_success:
            return {
                "processor": "instruct",
                "success": True,
                "agent_response": f"Perfect! I've processed your instruction and updated my knowledge accordingly. {instruction_text[:100]}...",
                "updates_applied": ["Updated domain knowledge tree", "Added instruction to knowledge base"],
                "updated_domain_tree": add_info_result.get("updated_domain_tree"),
            }
        else:
            return {
                "processor": "instruct",
                "success": False,
                "agent_response": "I set up the knowledge structure but couldn't save your instruction to my knowledge base. Please try again.",
                "updates_applied": ["Updated domain knowledge tree"],
                "updated_domain_tree": add_info_result.get("updated_domain_tree"),
            }

    except Exception as e:
        print(f"❌ Exception in instruct processing: {e}")
        return {
            "processor": "instruct",
            "success": False,
            "agent_response": f"Sorry, I ran into an error while processing your instruction: {e}",
            "updates_applied": [],
        }


async def _update_instruction_as_knowledge(
    agent: Agent, topics: list[str], instruction_text: str, domain_service: DomainKnowledgeService, db: Session
) -> bool:
    """Update the instruction text as answers_by_topics in JSON knowledge files."""

    try:
        print(f"📚 Updating instruction as knowledge for topics: {topics}")

        # Get agent's folder path
        folder_path = agent.config.get("folder_path") if agent.config else None
        if not folder_path:
            folder_path = os.path.join("agents", f"agent_{agent.id}")

        knows_folder = os.path.join(folder_path, "knows")
        if not os.path.exists(knows_folder):
            print(f"❌ Knows folder does not exist: {knows_folder}")
            return False

        # Get the latest domain tree to find the correct file paths
        # Use the existing domain_service parameter instead of reinitializing
        current_tree = await domain_service.get_agent_domain_knowledge(agent.id, db)

        if not current_tree:
            print("❌ No domain tree found")
            return False

        # This path must exist in the tree
        matching_leaves = [([topic for topic in topics if topic != "root"], None)]
        for path, _ in matching_leaves:
            area_name = " - ".join(path)
            safe_area = area_name.replace("/", "_").replace(" ", "_").replace("-", "_")
            file_name = f"{safe_area}.json"
            file_path = os.path.join(knows_folder, file_name)

            print(f"📝 Updating file: {file_path}")

            # Read existing knowledge file
            if os.path.exists(file_path):
                try:
                    with open(file_path, encoding="utf-8") as f:
                        knowledge_data = json.load(f)
                except Exception as e:
                    print(f"❌ Error reading file {file_path}: {e}")
                    continue
            else:
                # Create new knowledge file structure
                knowledge_data = {
                    "knowledge_area_description": area_name,
                    "questions": [],
                    "questions_by_topics": {},
                    "final_confidence": 90,
                    "confidence_by_topics": {},
                    "iterations_used": 0,
                    "total_questions": 0,
                    "answers_by_topics": {},
                }

            # Add the instruction text as an answer
            knowledge_data.setdefault("user_instructions", [])
            knowledge_data["user_instructions"].append(instruction_text)
            # Save the updated knowledge file
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(knowledge_data, f, indent=2, ensure_ascii=False)
                print(f"✅ Successfully updated: {file_path}")
            except Exception as e:
                print(f"❌ Error writing file {file_path}: {e}")
        return True

    except Exception as e:
        print(f"❌ Exception in _update_instruction_as_knowledge: {e}")
        import traceback

        print(f"📚 Full traceback: {traceback.format_exc()}")
        return False


async def _process_general_query_intent(user_message: str, agent: Agent) -> dict[str, Any]:
    """Process general_query intent - focused on answering questions."""

    return {
        "processor": "general_query",
        "success": True,
        "agent_response": f"I understand your message. How can I help you with {agent.name.lower()} related questions?",
        "updates_applied": [],
    }


def _combine_processing_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Combine multiple intent processing results into a unified response."""
    if not results:
        return {
            "processor": "multi_intent",
            "success": False,
            "agent_response": "No intents were processed.",
            "updates_applied": [],
        }

    # If only one result, return it directly
    if len(results) == 1:
        return results[0]

    # Combine multiple results
    combined_success = all(result.get("success", False) for result in results)
    combined_processors = [result.get("processor", "unknown") for result in results]
    combined_updates = []
    combined_responses = []
    updated_domain_tree = None

    for result in results:
        if result.get("updates_applied"):
            combined_updates.extend(result.get("updates_applied", []))
        if result.get("agent_response"):
            combined_responses.append(result.get("agent_response"))
        # Use the latest updated domain tree
        if result.get("updated_domain_tree"):
            updated_domain_tree = result.get("updated_domain_tree")

    # Create a combined response message
    if combined_responses:
        combined_response = " ".join(combined_responses)
    else:
        combined_response = f"I've processed multiple requests: {', '.join(combined_processors)}."

    return {
        "processor": "multi_intent",
        "processors": combined_processors,
        "success": combined_success,
        "agent_response": combined_response,
        "updates_applied": combined_updates,
        "updated_domain_tree": updated_domain_tree,
    }
