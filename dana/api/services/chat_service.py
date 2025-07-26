"""
Chat Service Module

This module provides business logic for chat functionality and conversation management.
"""

import logging

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

    async def process_chat_message(self, chat_request: ChatRequest, db_session) -> ChatResponse:
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
            conversation = await self._get_or_create_conversation(chat_request, db_session)

            # Save user message
            user_message = await self._save_message(conversation.id, "user", chat_request.message, db_session)

            # Generate agent response (placeholder implementation)
            agent_response = await self._generate_agent_response(chat_request, conversation, db_session)

            # Save agent message
            await self._save_message(conversation.id, "agent", agent_response, db_session)

            return ChatResponse(
                success=True,
                message=chat_request.message,
                conversation_id=conversation.id,
                message_id=user_message.id,
                agent_response=agent_response,
                context=chat_request.context,
                error=None,
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
                error=str(e),
            )
        except Exception as e:
            logger.error(f"Error processing chat message: {e}")
            # For other exceptions, raise as HTTP exception (500 status)
            # This allows the router's exception handler to catch it
            raise e

    async def _get_or_create_conversation(self, chat_request: ChatRequest, db_session) -> Conversation:
        """Get existing conversation or create a new one."""
        if chat_request.conversation_id:
            # Get existing conversation
            conversation = db_session.query(Conversation).filter(Conversation.id == chat_request.conversation_id).first()
            if conversation:
                return conversation
            else:
                # Conversation not found
                raise ValueError(f"Conversation {chat_request.conversation_id} not found")

        # Create new conversation
        conversation_data = ConversationCreate(title=f"Chat with Agent {chat_request.agent_id}", agent_id=chat_request.agent_id)

        conversation = Conversation(title=conversation_data.title, agent_id=conversation_data.agent_id)
        db_session.add(conversation)
        db_session.commit()
        db_session.refresh(conversation)

        return conversation

    async def _save_message(self, conversation_id: int, sender: str, content: str, db_session) -> Message:
        """Save a message to the database."""
        message_data = MessageCreate(sender=sender, content=content)

        message = Message(conversation_id=conversation_id, sender=message_data.sender, content=message_data.content)
        db_session.add(message)
        db_session.commit()
        db_session.refresh(message)

        return message

    async def _generate_agent_response(self, chat_request: ChatRequest, conversation: Conversation, db_session) -> str:
        """Generate agent response (placeholder implementation)."""
        # This is a placeholder implementation
        # In a real system, this would integrate with the agent execution system
        return f"This is a response from agent {chat_request.agent_id} to: {chat_request.message}"


# Global service instance
_chat_service: ChatService | None = None


def get_chat_service() -> ChatService:
    """Get or create the global chat service instance."""
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service
