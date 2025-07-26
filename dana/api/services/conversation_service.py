"""
Conversation Service Module

This module provides business logic for conversation management and message handling.
"""

import logging

from dana.api.core.models import Conversation, Message
from dana.api.core.schemas import ConversationCreate, ConversationRead, ConversationWithMessages, MessageCreate, MessageRead

logger = logging.getLogger(__name__)


class ConversationService:
    """
    Service for handling conversation operations and message management.
    """

    def __init__(self):
        """Initialize the conversation service."""
        pass

    async def create_conversation(self, conversation_data: ConversationCreate, db_session) -> ConversationRead:
        """
        Create a new conversation.

        Args:
            conversation_data: Conversation creation data
            db_session: Database session

        Returns:
            ConversationRead object with the created conversation
        """
        try:
            conversation = Conversation(title=conversation_data.title, agent_id=conversation_data.agent_id)

            db_session.add(conversation)
            db_session.commit()
            db_session.refresh(conversation)

            return ConversationRead(
                id=conversation.id,
                title=conversation.title,
                agent_id=conversation.agent_id,
                created_at=conversation.created_at,
                updated_at=conversation.updated_at,
            )

        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            raise

    async def get_conversation(
        self, conversation_id: int, db_session, include_messages: bool = False
    ) -> ConversationRead | ConversationWithMessages | None:
        """
        Get a conversation by ID.

        Args:
            conversation_id: The conversation ID
            db_session: Database session
            include_messages: Whether to include messages in the response

        Returns:
            Conversation object or None if not found
        """
        try:
            conversation = db_session.query(Conversation).filter(Conversation.id == conversation_id).first()

            if not conversation:
                return None

            if include_messages:
                messages = db_session.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at).all()

                message_reads = [
                    MessageRead(
                        id=msg.id,
                        conversation_id=msg.conversation_id,
                        sender=msg.sender,
                        content=msg.content,
                        created_at=msg.created_at,
                        updated_at=msg.updated_at,
                    )
                    for msg in messages
                ]

                return ConversationWithMessages(
                    id=conversation.id,
                    title=conversation.title,
                    agent_id=conversation.agent_id,
                    created_at=conversation.created_at,
                    updated_at=conversation.updated_at,
                    messages=message_reads,
                )
            else:
                return ConversationRead(
                    id=conversation.id,
                    title=conversation.title,
                    agent_id=conversation.agent_id,
                    created_at=conversation.created_at,
                    updated_at=conversation.updated_at,
                )

        except Exception as e:
            logger.error(f"Error getting conversation {conversation_id}: {e}")
            raise

    async def list_conversations(
        self, agent_id: int | None = None, limit: int = 100, offset: int = 0, db_session=None
    ) -> list[ConversationRead]:
        """
        List conversations with optional filtering.

        Args:
            agent_id: Optional agent ID filter
            limit: Maximum number of conversations to return
            offset: Number of conversations to skip
            db_session: Database session

        Returns:
            List of ConversationRead objects
        """
        try:
            query = db_session.query(Conversation)

            if agent_id is not None:
                query = query.filter(Conversation.agent_id == agent_id)

            conversations = query.order_by(Conversation.updated_at.desc()).offset(offset).limit(limit).all()

            return [
                ConversationRead(
                    id=conv.id, title=conv.title, agent_id=conv.agent_id, created_at=conv.created_at, updated_at=conv.updated_at
                )
                for conv in conversations
            ]

        except Exception as e:
            logger.error(f"Error listing conversations: {e}")
            raise

    async def update_conversation_title(self, conversation_id: int, new_title: str, db_session) -> ConversationRead | None:
        """
        Update a conversation's title.

        Args:
            conversation_id: The conversation ID
            new_title: New title for the conversation
            db_session: Database session

        Returns:
            Updated ConversationRead object or None if not found
        """
        try:
            conversation = db_session.query(Conversation).filter(Conversation.id == conversation_id).first()

            if not conversation:
                return None

            conversation.title = new_title
            db_session.commit()
            db_session.refresh(conversation)

            return ConversationRead(
                id=conversation.id,
                title=conversation.title,
                agent_id=conversation.agent_id,
                created_at=conversation.created_at,
                updated_at=conversation.updated_at,
            )

        except Exception as e:
            logger.error(f"Error updating conversation {conversation_id}: {e}")
            raise

    async def update_conversation(self, conversation_id: int, conversation_data: ConversationCreate, db_session) -> ConversationRead | None:
        """
        Update a conversation.

        Args:
            conversation_id: The conversation ID
            conversation_data: Updated conversation data
            db_session: Database session

        Returns:
            Updated ConversationRead object or None if not found
        """
        try:
            conversation = db_session.query(Conversation).filter(Conversation.id == conversation_id).first()

            if not conversation:
                return None

            conversation.title = conversation_data.title
            conversation.agent_id = conversation_data.agent_id
            db_session.commit()
            db_session.refresh(conversation)

            return ConversationRead(
                id=conversation.id,
                title=conversation.title,
                agent_id=conversation.agent_id,
                created_at=conversation.created_at,
                updated_at=conversation.updated_at,
            )

        except Exception as e:
            logger.error(f"Error updating conversation {conversation_id}: {e}")
            raise

    async def create_message(self, conversation_id: int, message_data: MessageCreate, db_session) -> MessageRead:
        """
        Create a new message in a conversation.

        Args:
            conversation_id: The conversation ID
            message_data: Message creation data
            db_session: Database session

        Returns:
            MessageRead object with the created message
        """
        try:
            message = Message(conversation_id=conversation_id, sender=message_data.sender, content=message_data.content)

            db_session.add(message)
            db_session.commit()
            db_session.refresh(message)

            return MessageRead(
                id=message.id,
                conversation_id=message.conversation_id,
                sender=message.sender,
                content=message.content,
                created_at=message.created_at,
                updated_at=message.updated_at,
            )

        except Exception as e:
            logger.error(f"Error creating message: {e}")
            raise

    async def list_messages(self, conversation_id: int, limit: int = 100, offset: int = 0, db_session=None) -> list[MessageRead]:
        """
        List messages in a conversation.

        Args:
            conversation_id: The conversation ID
            limit: Maximum number of messages to return
            offset: Number of messages to skip
            db_session: Database session

        Returns:
            List of MessageRead objects
        """
        try:
            messages = (
                db_session.query(Message)
                .filter(Message.conversation_id == conversation_id)
                .order_by(Message.created_at)
                .offset(offset)
                .limit(limit)
                .all()
            )

            return [
                MessageRead(
                    id=msg.id,
                    conversation_id=msg.conversation_id,
                    sender=msg.sender,
                    content=msg.content,
                    created_at=msg.created_at,
                    updated_at=msg.updated_at,
                )
                for msg in messages
            ]

        except Exception as e:
            logger.error(f"Error listing messages: {e}")
            raise

    async def get_message(self, conversation_id: int, message_id: int, db_session) -> MessageRead | None:
        """
        Get a specific message in a conversation.

        Args:
            conversation_id: The conversation ID
            message_id: The message ID
            db_session: Database session

        Returns:
            MessageRead object or None if not found
        """
        try:
            message = db_session.query(Message).filter(Message.id == message_id, Message.conversation_id == conversation_id).first()

            if not message:
                return None

            return MessageRead(
                id=message.id,
                conversation_id=message.conversation_id,
                sender=message.sender,
                content=message.content,
                created_at=message.created_at,
                updated_at=message.updated_at,
            )

        except Exception as e:
            logger.error(f"Error getting message {message_id}: {e}")
            raise

    async def update_message(self, conversation_id: int, message_id: int, message_data: MessageCreate, db_session) -> MessageRead | None:
        """
        Update a message in a conversation.

        Args:
            conversation_id: The conversation ID
            message_id: The message ID
            message_data: Updated message data
            db_session: Database session

        Returns:
            Updated MessageRead object or None if not found
        """
        try:
            message = db_session.query(Message).filter(Message.id == message_id, Message.conversation_id == conversation_id).first()

            if not message:
                return None

            message.sender = message_data.sender
            message.content = message_data.content
            db_session.commit()
            db_session.refresh(message)

            return MessageRead(
                id=message.id,
                conversation_id=message.conversation_id,
                sender=message.sender,
                content=message.content,
                created_at=message.created_at,
                updated_at=message.updated_at,
            )

        except Exception as e:
            logger.error(f"Error updating message {message_id}: {e}")
            raise

    async def delete_message(self, conversation_id: int, message_id: int, db_session) -> bool:
        """
        Delete a message from a conversation.

        Args:
            conversation_id: The conversation ID
            message_id: The message ID
            db_session: Database session

        Returns:
            True if message was deleted, False if not found
        """
        try:
            message = db_session.query(Message).filter(Message.id == message_id, Message.conversation_id == conversation_id).first()

            if not message:
                return False

            db_session.delete(message)
            db_session.commit()
            return True

        except Exception as e:
            logger.error(f"Error deleting message {message_id}: {e}")
            raise

    async def delete_conversation(self, conversation_id: int, db_session) -> bool:
        """
        Delete a conversation and all its messages.

        Args:
            conversation_id: The conversation ID
            db_session: Database session

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            conversation = db_session.query(Conversation).filter(Conversation.id == conversation_id).first()

            if not conversation:
                return False

            # Delete all messages first
            db_session.query(Message).filter(Message.conversation_id == conversation_id).delete()

            # Delete the conversation
            db_session.delete(conversation)
            db_session.commit()

            return True

        except Exception as e:
            logger.error(f"Error deleting conversation {conversation_id}: {e}")
            raise

    async def add_message(self, conversation_id: int, message_data: MessageCreate, db_session) -> MessageRead:
        """
        Add a message to a conversation.

        Args:
            conversation_id: The conversation ID
            message_data: Message creation data
            db_session: Database session

        Returns:
            MessageRead object with the created message
        """
        try:
            message = Message(conversation_id=conversation_id, sender=message_data.sender, content=message_data.content)

            db_session.add(message)
            db_session.commit()
            db_session.refresh(message)

            return MessageRead(
                id=message.id,
                conversation_id=message.conversation_id,
                sender=message.sender,
                content=message.content,
                created_at=message.created_at,
                updated_at=message.updated_at,
            )

        except Exception as e:
            logger.error(f"Error adding message to conversation {conversation_id}: {e}")
            raise

    async def get_conversation_messages(
        self, conversation_id: int, limit: int = 100, offset: int = 0, db_session=None
    ) -> list[MessageRead]:
        """
        Get messages for a conversation.

        Args:
            conversation_id: The conversation ID
            limit: Maximum number of messages to return
            offset: Number of messages to skip
            db_session: Database session

        Returns:
            List of MessageRead objects
        """
        try:
            messages = (
                db_session.query(Message)
                .filter(Message.conversation_id == conversation_id)
                .order_by(Message.created_at)
                .offset(offset)
                .limit(limit)
                .all()
            )

            return [
                MessageRead(
                    id=msg.id,
                    conversation_id=msg.conversation_id,
                    sender=msg.sender,
                    content=msg.content,
                    created_at=msg.created_at,
                    updated_at=msg.updated_at,
                )
                for msg in messages
            ]

        except Exception as e:
            logger.error(f"Error getting messages for conversation {conversation_id}: {e}")
            raise


# Global service instance
_conversation_service: ConversationService | None = None


def get_conversation_service() -> ConversationService:
    """Get or create the global conversation service instance."""
    global _conversation_service
    if _conversation_service is None:
        _conversation_service = ConversationService()
    return _conversation_service
