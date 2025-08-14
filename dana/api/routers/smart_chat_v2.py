"""
Smart Chat V2 Router - Enhanced chat API using KnowledgeOpsHandler directly.
"""

import logging
from typing import Any, Literal
from threading import Lock
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from dana.api.core.database import get_db
from dana.api.core.models import Agent, AgentChatHistory
from dana.api.core.schemas import (
    IntentDetectionRequest,
    MessageData,
)
from dana.api.services.domain_knowledge_service import (
    get_domain_knowledge_service,
    DomainKnowledgeService,
)
from dana.api.routers.agents import clear_agent_cache

# Use KnowledgeOpsHandler directly
from dana.api.services.intent_detection.intent_handlers.knowledge_ops_handler import KnowledgeOpsHandler
from dana.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource as LLMResource
from dana.api.services.auto_knowledge_generator import get_auto_knowledge_generator
import os
from fastapi import WebSocket, WebSocketDisconnect
import json
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["smart-chat-v2"])

# Concurrency protection: In-memory locks per agent
_agent_locks = defaultdict(Lock)


class SmartChatWSNotifier:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[websocket_id] = websocket

    def disconnect(self, websocket_id: str):
        if websocket_id in self.active_connections:
            del self.active_connections[websocket_id]

    async def send_chat_update_msg(
        self,
        websocket_id: Any,
        tool_name: str,
        message: str,
        status: Literal["init", "in_progress", "finish"],
        progression: float | None = None,
    ):
        """Send a message via WebSocket"""
        if not isinstance(websocket_id, str):
            websocket_id = str(websocket_id)
        if websocket_id in self.active_connections:
            websocket = self.active_connections[websocket_id]
            try:
                message = {
                    "type": "chat_update",
                    "message": {
                        "tool_name": tool_name,
                        "content": message,
                        "status": status,
                        "progression": progression,
                    },
                    "timestamp": asyncio.get_event_loop().time(),
                }
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send chat update message via WebSocket: {e}")
                # Remove disconnected WebSocket
                self.disconnect(websocket_id)


smart_chat_ws_notifier = SmartChatWSNotifier()


def create_smart_chat_ws_notifier(websocket_id: str | None = None):
    """Create a chat update notifier that sends updates via WebSocket"""

    async def chat_update_notifier(
        tool_name: str, message: str, status: Literal["init", "in_progress", "finish", "error"], progression: float | None = None
    ) -> None:
        # Send via WebSocket if connection exists
        if websocket_id:
            await smart_chat_ws_notifier.send_chat_update_msg(websocket_id, tool_name, message, status, progression)

    return chat_update_notifier


@router.post("/{agent_id}/smart-chat")
async def smart_chat_v2(
    agent_id: int,
    request: dict[str, Any],
    domain_service: DomainKnowledgeService = Depends(get_domain_knowledge_service),
    db: Session = Depends(get_db),
):
    """
    Smart chat V2 API using KnowledgeOpsHandler directly:
    1. Uses KnowledgeOpsHandler for all knowledge operations
    2. Processes user requests through the handler's tool system
    3. Returns structured response with conversation history

    Args:
        agent_id: Agent ID
        request: {"message": "user message", "conversation_id": optional}

    Returns:
        Response with knowledge operation results and conversation
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

        logger.info(f"Smart chat V2 for agent {agent_id}: {user_message[:100]}...")

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

        # Step 1: Create intent request for processing
        intent_request = IntentDetectionRequest(
            user_message=user_message,
            chat_history=recent_chat_history,
            current_domain_tree=current_domain_tree,
            agent_id=agent_id,
        )

        # Step 2: Use KnowledgeOpsHandler directly for all requests
        # Build agent folder paths for KnowledgeOpsHandler
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

        # Create KnowledgeOpsHandler with proper configuration
        handler = KnowledgeOpsHandler(
            domain_knowledge_path=domain_knowledge_path,
            llm=llm,
            domain=agent.description or "General",
            role=agent.name or "Domain Expert",
            knowledge_status_path=knowledge_status_path,
            notifier=create_smart_chat_ws_notifier(agent_id),
        )

        logger.info(f"🚀 Starting KnowledgeOpsHandler workflow for agent {agent.id}")

        # Execute the handler
        result = await handler.handle(intent_request)

        logger.info(f"✅ KnowledgeOpsHandler completed for agent {agent.id}: status={result.get('status')}")

        # Check if tree was modified and needs reloading
        updated_domain_tree = None
        tree_modified = result.get("tree_modified", False)

        if tree_modified:
            # Clear cache to ensure fresh data
            clear_agent_cache(folder_path)
            logger.info(f"Cleared RAG cache for agent {agent.id} after tree modification")

            # Use the updated tree from handler if provided, otherwise reload
            if result.get("updated_tree"):
                # Convert dict back to DomainKnowledgeTree model
                updated_domain_tree = result.get("updated_tree")
            else:
                # Fallback: reload from database
                updated_domain_tree = await domain_service.get_agent_domain_knowledge(agent_id, db)

        # Convert KnowledgeOpsHandler result to smart_chat format
        if result.get("status") == "success":
            response = {
                "success": True,
                "message": user_message,
                "conversation_id": conversation_id,
                # Intent detection results
                "detected_intent": "knowledge_ops",
                "intent_confidence": 0.95,
                "intent_explanation": "Processed by KnowledgeOpsHandler",
                "entities_extracted": {},
                # Processing results from KnowledgeOpsHandler
                "processor": "knowledge_ops_handler",
                "agent_response": result.get("message", "Knowledge operation completed successfully."),
                "updates_applied": ["Knowledge workflow executed by KnowledgeOpsHandler"],
                "final_result": result.get("final_result", {}),
                "conversation": result.get("conversation", []),
                "follow_up_message": result.get("message", "Knowledge operation completed. What else would you like me to learn?"),
            }

        elif result.get("status") == "user_input_required":
            response = {
                "success": False,
                "message": user_message,
                "conversation_id": conversation_id,
                "detected_intent": "knowledge_ops",
                "intent_confidence": 0.95,
                "intent_explanation": "User input required",
                "entities_extracted": {},
                "processor": "knowledge_ops_handler",
                "agent_response": "I need more information to complete this knowledge operation. Please provide additional details.",
                "updates_applied": [],
                "requires_user_input": True,
                "conversation": result.get("conversation", []),
                "follow_up_message": result.get("message", "I need more information to proceed."),
            }
        else:
            # Handle error case
            response = {
                "success": False,
                "message": user_message,
                "conversation_id": conversation_id,
                "detected_intent": "knowledge_ops",
                "intent_confidence": 0.95,
                "intent_explanation": "Knowledge operation failed",
                "entities_extracted": {},
                "processor": "knowledge_ops_handler",
                "agent_response": f"Sorry, I encountered an error while processing your knowledge request: {result.get('message', 'Unknown error')}",
                "updates_applied": [],
                "conversation": result.get("conversation", []),
                "follow_up_message": "I had trouble processing that request. Could you try rephrasing it?",
            }

        # Only include updated_domain_tree if tree was modified
        if updated_domain_tree:
            response["updated_domain_tree"] = updated_domain_tree.model_dump()

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

        logger.info(f"Smart chat V2 completed for agent {agent_id}: status={result.get('status')}")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in smart chat V2 for agent {agent_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Always release the lock
        agent_lock.release()


@router.get("/{agent_id}/knowledge-generation/status")
async def get_knowledge_generation_status_v2(
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
async def generate_all_knowledge_v2(
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
async def stop_knowledge_generation_v2(
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
async def retry_failed_knowledge_generation_v2(
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
                AgentChatHistory.type.in_(["smart_chat", "smart_chat_v2"]),
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


@router.websocket("/ws/dana-chat/{agent_id}")
async def send_chat_update_msg(agent_id: str, websocket: WebSocket):
    await smart_chat_ws_notifier.connect(agent_id, websocket)
    try:
        while True:
            # Keep the connection alive and listen for client messages
            data = await websocket.receive_text()
            # Echo back for debugging (optional)
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "echo",
                        "message": f"Connected to variable updates for ID: {agent_id}",
                        "data": data,
                    }
                )
            )
    except WebSocketDisconnect:
        smart_chat_ws_notifier.disconnect(agent_id)
    except Exception as e:
        logger.error(f"WebSocket error for {agent_id}: {e}")
        smart_chat_ws_notifier.disconnect(agent_id)
