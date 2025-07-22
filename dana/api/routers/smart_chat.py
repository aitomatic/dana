"""
Smart Chat Router - Unified chat API with automatic intent detection and updates.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from dana.api.core.database import get_db
from dana.api.core.models import Agent
from dana.api.core.schemas import (
    DomainKnowledgeTree,
    IntentDetectionRequest,
    MessageData
)
from dana.api.services.domain_knowledge_service import get_domain_knowledge_service, DomainKnowledgeService
from dana.api.services.intent_detection_service import get_intent_detection_service, IntentDetectionService
from dana.api.services.llm_tree_manager import get_llm_tree_manager, LLMTreeManager

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
        
        # Get current domain knowledge for context
        current_domain_tree = await domain_service.get_agent_domain_knowledge(agent_id, db)
        
        # Step 1: Intent Detection ONLY (no processing)
        intent_request = IntentDetectionRequest(
            user_message=user_message,
            chat_history=[],  # Could be enhanced with actual chat history
            current_domain_tree=current_domain_tree,
            agent_id=agent_id
        )
        
        intent_response = await intent_service.detect_intent(intent_request)
        detected_intent = intent_response.intent
        entities = intent_response.entities
        
        logger.info(f"Intent detected: {detected_intent} with entities: {entities}")
        
        # Step 2: Route to appropriate processor based on intent
        processing_result = await _process_based_on_intent(
            intent=detected_intent,
            entities=entities,
            user_message=user_message,
            agent=agent,
            domain_service=domain_service,
            llm_tree_manager=llm_tree_manager,
            current_domain_tree=current_domain_tree,
            db=db
        )
        
        # Step 3: Return structured response
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
            **processing_result
        }
        
        logger.info(f"Smart chat completed for agent {agent_id}: intent={detected_intent}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in smart chat for agent {agent_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def _process_based_on_intent(
    intent: str,
    entities: dict[str, Any],
    user_message: str,
    agent: Agent,
    domain_service: DomainKnowledgeService,
    llm_tree_manager: LLMTreeManager,
    current_domain_tree: DomainKnowledgeTree | None,
    db: Session
) -> dict[str, Any]:
    """
    Process user intent with appropriate handler.
    Each intent type has its own focused processor.
    """
    
    if intent == "add_information":
        return await _process_add_information_intent(
            entities, agent, domain_service, llm_tree_manager, current_domain_tree, db
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
            agent_description=agent.description or ""
        )
        
        print(f"🎯 LLM tree manager response: success={update_response.success}")
        if update_response.error:
            print(f"❌ LLM tree manager error: {update_response.error}")
        
        if update_response.success and update_response.updated_tree:
            # Save the updated tree
            save_success = await domain_service.save_agent_domain_knowledge(
                agent_id=agent.id,
                tree=update_response.updated_tree,
                db=db
            )
            
            print(f"💾 Save result: {save_success}")
            
            if save_success:
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
                    "agent_response": "I organized the knowledge structure but had trouble saving it. Please try again.",
                    "updates_applied": []
                }
        else:
            return {
                "processor": "add_information",
                "success": False,
                "agent_response": f"I had trouble organizing my knowledge structure: {update_response.error or 'Unknown error'}. Could you try rephrasing your request?",
                "updates_applied": []
            }
    
    except Exception as e:
        print(f"❌ Exception in LLM-powered add_information: {e}")
        return {
            "processor": "add_information",
            "success": False,
            "agent_response": f"I encountered an error while processing your request: {str(e)}. Please try again.",
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
    """Process update_agent_properties intent - focused on agent metadata updates."""
    
    # This is a placeholder for future agent property updates
    # Could handle: name changes, description updates, config changes, etc.
    
    return {
        "processor": "update_agent",
        "success": False,
        "agent_response": "Agent property updates are not yet implemented. Currently I can only update my domain knowledge.",
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