"""
Smart Chat Router - Unified chat API with automatic intent detection and updates.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from dana.api.core.database import get_db
from dana.api.core.models import Agent, AgentChatHistory
from dana.api.core.schemas import (
    DomainKnowledgeTree,
    IntentDetectionRequest,
    MessageData
)
from dana.api.services.domain_knowledge_service import get_domain_knowledge_service, DomainKnowledgeService
from dana.api.services.intent_detection_service import get_intent_detection_service, IntentDetectionService
from dana.api.services.llm_tree_manager import get_llm_tree_manager, LLMTreeManager
from dana.api.services.knowledge_status_manager import KnowledgeStatusManager, KnowledgeGenerationManager
import os
import asyncio
from datetime import datetime, timezone
import sys

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["smart-chat"])


@router.post("/{agent_id}/smart-chat")
async def smart_chat(
    agent_id: int,
    request: dict[str, Any],
    intent_service: IntentDetectionService = Depends(get_intent_detection_service),
    domain_service: DomainKnowledgeService = Depends(get_domain_knowledge_service),
    llm_tree_manager: LLMTreeManager = Depends(get_llm_tree_manager),
    db: Session = Depends(get_db)
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
        user_history = AgentChatHistory(
            agent_id=agent_id,
            sender="user",
            text=user_message,
            type="smart_chat"
        )
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
            agent_id=agent_id
        )
        
        intent_response = await intent_service.detect_intent(intent_request)
        detected_intent = intent_response.intent
        entities = intent_response.entities
        
        logger.info(f"Intent detected: {detected_intent} with entities: {entities}")
        
        # Get all intents for multi-intent processing
        all_intents = intent_response.additional_data.get("all_intents", [
            {
                "intent": detected_intent,
                "entities": entities,
                "confidence": intent_response.confidence,
                "explanation": intent_response.explanation
            }
        ])
        
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
                db=db
            )
            processing_results.append(result)
        
        # Combine results from all intents
        processing_result = _combine_processing_results(processing_results)
        
        # Step 3: Generate creative LLM-based follow-up message
        # Extract knowledge topics from domain knowledge tree
        def extract_topics(tree):
            if not tree or not hasattr(tree, 'root'):
                return []
            topics = []
            def traverse(node):
                if not node:
                    return
                if getattr(node, 'topic', None):
                    topics.append(node.topic)
                for child in getattr(node, 'children', []) or []:
                    traverse(child)
            traverse(tree.root)
            return topics
        knowledge_topics = extract_topics(current_domain_tree)
        follow_up_message = await intent_service.generate_followup_message(
            user_message=user_message,
            agent=agent,
            knowledge_topics=knowledge_topics
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
            "follow_up_message": follow_up_message
        }
        
        # --- Save agent response to AgentChatHistory ---
        agent_response_text = response.get("follow_up_message")
        if agent_response_text:
            agent_history = AgentChatHistory(
                agent_id=agent_id,
                sender="agent",
                text=agent_response_text,
                type="smart_chat"
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


async def _get_recent_chat_history(agent_id: int, db: Session, limit: int = 10) -> list[MessageData]:
    """Get recent chat history for an agent."""
    try:
        from dana.api.core.models import AgentChatHistory
        
        # Get recent history excluding the current message being processed
        history = db.query(AgentChatHistory).filter(
            AgentChatHistory.agent_id == agent_id,
            AgentChatHistory.type == "smart_chat"
        ).order_by(AgentChatHistory.created_at.desc()).limit(limit).all()
        
        # Convert to MessageData format (reverse to get chronological order)
        message_history = []
        for h in reversed(history):
            message_history.append(MessageData(
                role=h.sender,
                content=h.text
            ))
        
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
    db: Session
) -> dict[str, Any]:
    """
    Process user intent with appropriate handler.
    Each intent type has its own focused processor.
    """
    
    if intent == "add_information":
        return await _process_add_information_intent(
            entities, agent, domain_service, llm_tree_manager, current_domain_tree, chat_history, db
        )
    
    elif intent == "refresh_domain_knowledge":
        return await _process_refresh_knowledge_intent(
            user_message, agent.id, domain_service, db
        )
    
    elif intent == "update_agent_properties":
        return await _process_update_agent_intent(
            entities, user_message, agent, db
        )
    
    elif intent == "test_agent":
        return await _process_test_agent_intent(
            entities, user_message, agent
        )
    
    else:  # general_query
        return await _process_general_query_intent(
            user_message, agent
        )


async def _process_add_information_intent(
    entities: dict[str, Any],
    agent: Agent,
    domain_service: DomainKnowledgeService,
    llm_tree_manager: LLMTreeManager,
    current_domain_tree: DomainKnowledgeTree | None,
    chat_history: list[MessageData],
    db: Session
) -> dict[str, Any]:
    """Process add_information intent using LLM-powered tree management."""
    
    topic = entities.get("topic")
    parent = entities.get("parent")
    details = entities.get("details")
    
    print(f"🧠 Processing add_information with LLM tree manager:")
    print(f"  - Topic: {topic}")
    print(f"  - Parent: {parent}")
    print(f"  - Details: {details}")
    print(f"  - Agent: {agent.name}")
    
    if not topic:
        return {
            "processor": "add_information",
            "success": False,
            "agent_response": "I couldn't identify what topic you want me to learn about. Could you be more specific?",
            "updates_applied": []
        }
    
    try:
        # Use LLM tree manager for intelligent placement
        update_response = await llm_tree_manager.smart_add_knowledge(
            current_tree=current_domain_tree,
            new_topic=topic,
            suggested_parent=parent,
            context_details=details,
            agent_name=agent.name,
            agent_description=agent.description or "",
            chat_history=chat_history
        )
        
        print(f"🎯 LLM tree manager response: success={update_response.success}")
        if update_response.error:
            print(f"❌ LLM tree manager error: {update_response.error}")
        
        if update_response.success and update_response.updated_tree:
            # Save the updated tree
            save_success = await domain_service.save_agent_domain_knowledge(
                agent_id=agent.id,
                tree=update_response.updated_tree,
                db=db,
                agent=agent
            )
            
            print(f"💾 Save result: {save_success}")
            
            if save_success:
                # --- Trigger knowledge generation for new/pending topics ---
                try:
                    folder_path = agent.config.get("folder_path") if agent.config else None
                    if not folder_path:
                        folder_path = os.path.join("agents", f"agent_{agent.id}")
                    knows_folder = os.path.join(folder_path, "knows")
                    os.makedirs(knows_folder, exist_ok=True)
                    status_path = os.path.join(knows_folder, "knowledge_status.json")
                    status_manager = KnowledgeStatusManager(status_path)
                    now_str = datetime.now(timezone.utc).isoformat() + "Z"
                    # Get the latest tree
                    leaf_paths = []
                    def collect_leaf_paths(node, path_so_far):
                        path = path_so_far + [node.topic]
                        if not getattr(node, 'children', []):
                            leaf_paths.append((path, node))
                        for child in getattr(node, 'children', []):
                            collect_leaf_paths(child, path)
                    collect_leaf_paths(update_response.updated_tree.root, [])
                    # Add/update all leaves
                    for path, leaf_node in leaf_paths:
                        area_name = " - ".join(path)
                        safe_area = area_name.replace("/", "_").replace(" ", "_").replace("-", "_")
                        file_name = f"{safe_area}.json"
                        status_manager.add_or_update_topic(
                            path=area_name,
                            file=file_name,
                            last_topic_update=now_str,
                            status=None
                        )
                    # Remove topics that are no longer in the tree
                    all_paths = set([" - ".join(path) for path, _ in leaf_paths])
                    for entry in status_manager.load()["topics"]:
                        if entry["path"] not in all_paths:
                            status_manager.remove_topic(entry["path"])
                    # Only queue topics with status 'pending' or 'failed'
                    pending = status_manager.get_pending_or_failed()
                    print(f"[smart-chat] {len(pending)} topics to generate (pending or failed)")
                    manager = KnowledgeGenerationManager(status_manager, max_concurrent=4, ws_manager=None)
                    async def run_queue():
                        for entry in pending:
                            await manager.add_topic(entry)
                        await manager.run()
                        print(f"[smart-chat] All queued topics processed and saved.")
                    # Run in background, works in both async and sync contexts
                    try:
                        loop = asyncio.get_running_loop()
                        print("[smart-chat] Using asyncio.create_task to trigger knowledge generation queue.")
                        asyncio.create_task(run_queue())
                    except RuntimeError:
                        print("[smart-chat] No running event loop, using asyncio.run to trigger knowledge generation queue.")
                        asyncio.run(run_queue())
                except Exception as e:
                    print(f"[smart-chat] Error triggering knowledge generation: {e}")
                # --- End trigger ---
                return {
                    "processor": "add_information",
                    "success": True,
                    "agent_response": f"Perfect! I've intelligently organized my knowledge to include {topic}. {update_response.changes_summary}. What would you like to know about this topic?",
                    "updates_applied": [update_response.changes_summary or f"Added {topic}"],
                    "updated_domain_tree": update_response.updated_tree.model_dump()
                }
            else:
                return {
                    "processor": "add_information",
                    "success": False,
                    "agent_response": "I tried to update my knowledge, but something went wrong saving it.",
                    "updates_applied": []
                }
        else:
            return {
                "processor": "add_information",
                "success": False,
                "agent_response": update_response.error or "I couldn't update my knowledge tree.",
                "updates_applied": []
            }
    except Exception as e:
        print(f"❌ Exception in LLM-powered add_information: {e}")
        return {
            "processor": "add_information",
            "success": False,
            "agent_response": f"Sorry, I ran into an error while updating my knowledge: {e}",
            "updates_applied": []
        }


async def _process_refresh_knowledge_intent(
    user_message: str,
    agent_id: int,
    domain_service: DomainKnowledgeService,
    db: Session
) -> dict[str, Any]:
    """Process refresh_domain_knowledge intent - focused on restructuring knowledge tree."""
    
    refresh_response = await domain_service.refresh_domain_knowledge(
        agent_id=agent_id,
        context=user_message,
        db=db
    )
    
    return {
        "processor": "refresh_knowledge",
        "success": refresh_response.success,
        "agent_response": "I've reorganized and refreshed my knowledge structure to be more efficient and comprehensive." if refresh_response.success else "I had trouble refreshing my knowledge structure. Please try again.",
        "updates_applied": [refresh_response.changes_summary] if refresh_response.changes_summary else [],
        "updated_domain_tree": refresh_response.updated_tree.model_dump() if refresh_response.updated_tree else None
    }


async def _process_update_agent_intent(
    entities: dict[str, Any],
    user_message: str,
    agent: Agent,
    db: Session
) -> dict[str, Any]:
    updated_fields = []
    if 'name' in entities and entities['name']:
        agent.name = entities['name'].strip()
        updated_fields.append('name')
    if 'role' in entities and entities['role']:
        agent.description = entities['role'].strip()
        updated_fields.append('role')
    # Save specialties and skills to config
    # Create a new dict to ensure SQLAlchemy detects the change
    config = dict(agent.config) if agent.config else {}
    
    # Handle specialties - accumulate instead of overwrite
    if 'specialties' in entities and entities['specialties']:
        new_specialties = entities['specialties']
        if isinstance(new_specialties, str):
            # Split comma-separated string into list
            new_specialties = [s.strip() for s in new_specialties.split(',') if s.strip()]
        elif not isinstance(new_specialties, list):
            new_specialties = [str(new_specialties)]
        
        # Get existing specialties and merge with new ones
        existing_specialties = config.get('specialties', [])
        if not isinstance(existing_specialties, list):
            existing_specialties = []
        
        # Combine and deduplicate (case-insensitive)
        combined_specialties = existing_specialties.copy()
        for new_spec in new_specialties:
            # Check if this specialty already exists (case-insensitive)
            if not any(new_spec.lower() == existing.lower() for existing in combined_specialties):
                combined_specialties.append(new_spec)
        
        config['specialties'] = combined_specialties
        updated_fields.append('specialties')
    
    # Handle skills - accumulate instead of overwrite
    if 'skills' in entities and entities['skills']:
        new_skills = entities['skills']
        if isinstance(new_skills, str):
            # Split comma-separated string into list
            new_skills = [s.strip() for s in new_skills.split(',') if s.strip()]
        elif not isinstance(new_skills, list):
            new_skills = [str(new_skills)]
        
        # Get existing skills and merge with new ones
        existing_skills = config.get('skills', [])
        if not isinstance(existing_skills, list):
            existing_skills = []
        
        # Combine and deduplicate (case-insensitive)
        combined_skills = existing_skills.copy()
        for new_skill in new_skills:
            # Check if this skill already exists (case-insensitive)
            if not any(new_skill.lower() == existing.lower() for existing in combined_skills):
                combined_skills.append(new_skill)
        
        config['skills'] = combined_skills
        updated_fields.append('skills')
    agent.config = config
    if updated_fields:
        db.commit()
        db.refresh(agent)
        return {
            "processor": "update_agent",
            "success": True,
            "agent_response": f"Agent information updated: {', '.join(updated_fields)}.",
            "updates_applied": updated_fields
        }
    else:
        return {
            "processor": "update_agent",
            "success": False,
            "agent_response": "No valid agent property found to update.",
            "updates_applied": []
        }


async def _process_test_agent_intent(
    entities: dict[str, Any],
    user_message: str,
    agent: Agent
) -> dict[str, Any]:
    """Process test_agent intent - focused on testing agent capabilities."""
    
    # This is a placeholder for future agent testing functionality
    
    return {
        "processor": "test_agent",
        "success": False,
        "agent_response": "Agent testing functionality is not yet implemented. I can help you with adding knowledge or answering questions instead.",
        "updates_applied": []
    }


async def _process_general_query_intent(
    user_message: str,
    agent: Agent
) -> dict[str, Any]:
    """Process general_query intent - focused on answering questions."""
    
    return {
        "processor": "general_query",
        "success": True,
        "agent_response": f"I understand your message. How can I help you with {agent.name.lower()} related questions?",
        "updates_applied": []
    }


def _combine_processing_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Combine multiple intent processing results into a unified response."""
    if not results:
        return {
            "processor": "multi_intent",
            "success": False,
            "agent_response": "No intents were processed.",
            "updates_applied": []
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
        "updated_domain_tree": updated_domain_tree
    }