"""
Chat Service Module

This module provides business logic for chat functionality and conversation management.
"""

import logging
from typing import Any

from dana.api.core.models import Agent, Conversation, Message
from dana.api.core.schemas import ChatRequest, ChatResponse, ConversationCreate, MessageCreate

logger = logging.getLogger(__name__)


class ChatService:
    """
    Service for handling chat operations and conversation management.
    """

    def __init__(self):
        """Initialize the chat service."""
        pass

    async def process_chat_message(
        self, chat_request: ChatRequest, db_session, websocket_id: str | None = None
    ) -> ChatResponse:
        """
        Process a chat message and generate a response.

        Args:
            chat_request: The chat request containing message and context
            db_session: Database session for persistence

        Returns:
            ChatResponse with the agent's reply and conversation details
        """
        try:
            # Validate agent exists
            agent = db_session.query(Agent).filter(Agent.id == chat_request.agent_id).first()
            if not agent:
                raise ValueError(f"Agent {chat_request.agent_id} not found")

            # Get or create conversation
            conversation = await self._get_or_create_conversation(
                chat_request, db_session
            )

            # Save user message
            user_message = await self._save_message(
                conversation.id, "user", chat_request.message, db_session
            )

            # Generate agent response with WebSocket support
            agent_response = await self._generate_agent_response(
                chat_request, conversation, db_session, websocket_id
            )

            # Save agent message
            agent_message = await self._save_message(
                conversation.id, "agent", agent_response, db_session
            )

            return ChatResponse(
                success=True,
                message=chat_request.message,
                conversation_id=conversation.id,
                message_id=user_message.id,
                agent_response=agent_response,
                context=chat_request.context,
                error=None
            )

        except ValueError as e:
            logger.error(f"Validation error in chat message: {e}")
            # For validation errors, return as service error (200 status)
            return ChatResponse(
                success=False,
                message=chat_request.message,
                conversation_id=chat_request.conversation_id or 0,
                message_id=0,
                agent_response="",
                context=chat_request.context,
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Error processing chat message: {e}")
            # For other exceptions, raise as HTTP exception (500 status)
            # This allows the router's exception handler to catch it
            raise e

    async def _get_or_create_conversation(
        self, chat_request: ChatRequest, db_session
    ) -> Conversation:
        """Get existing conversation or create a new one."""
        if chat_request.conversation_id:
            # Get existing conversation
            conversation = db_session.query(Conversation).filter(
                Conversation.id == chat_request.conversation_id
            ).first()
            if conversation:
                return conversation
            else:
                # Conversation not found
                raise ValueError(f"Conversation {chat_request.conversation_id} not found")

        # Create new conversation
        conversation_data = ConversationCreate(
            title=f"Chat with Agent {chat_request.agent_id}",
            agent_id=chat_request.agent_id
        )
        
        conversation = Conversation(
            title=conversation_data.title,
            agent_id=conversation_data.agent_id
        )
        db_session.add(conversation)
        db_session.commit()
        db_session.refresh(conversation)
        
        return conversation

    async def _save_message(
        self, conversation_id: int, sender: str, content: str, db_session
    ) -> Message:
        """Save a message to the database."""
        message_data = MessageCreate(sender=sender, content=content)
        
        message = Message(
            conversation_id=conversation_id,
            sender=message_data.sender,
            content=message_data.content
        )
        db_session.add(message)
        db_session.commit()
        db_session.refresh(message)
        
        return message

    async def _generate_agent_response(
        self, chat_request: ChatRequest, conversation: Conversation, db_session, websocket_id: str | None = None
    ) -> str:
        """Generate agent response using actual Dana execution."""
        try:
            # Get agent details for execution
            agent = db_session.query(Agent).filter(Agent.id == chat_request.agent_id).first()
            if not agent:
                return "Error: Agent not found"
            
            # Import agent test functionality
            from dana.api.routers.agent_test import AgentTestRequest, test_agent
            from dana.core.runtime.modules.core import initialize_module_system, reset_module_system
            
            # Initialize module system
            initialize_module_system()
            reset_module_system()
            
            # Extract agent details
            agent_name = agent.name
            agent_description = agent.description or "A Dana agent"
            folder_path = agent.config.get("folder_path") if agent.config else None
            
            # Create test request for agent execution
            test_request = AgentTestRequest(
                agent_code="",  # Will use folder_path for main.na
                message=chat_request.message,
                agent_name=agent_name,
                agent_description=agent_description,
                context=chat_request.context or {"user_id": "chat_user"},
                folder_path=folder_path,
                websocket_id=websocket_id  # Enable WebSocket for real-time updates
            )
            
            # Execute agent using same logic as test endpoint
            result = await test_agent(test_request)
            
            if result.success:
                return result.agent_response
            else:
                return f"Error executing agent: {result.error or 'Unknown error'}"
                
        except Exception as e:
            logger.error(f"Error generating agent response: {e}")
            return f"Error generating response: {str(e)}"


# Global service instance
_chat_service: ChatService | None = None


def get_chat_service() -> ChatService:
    """Get or create the global chat service instance."""
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service