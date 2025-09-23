from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from dana.api.core.models import Conversation, Message
from dana.api.core.schemas import (
    ConversationWithMessages,
    MessageRead,
    ConversationCreate,
    MessageCreate,
)
from threading import Lock
from collections import defaultdict


class AbstractConversationRepo(ABC):
    @classmethod
    @abstractmethod
    async def get_conversation(cls, conversation_id: int, **kwargs) -> ConversationWithMessages | None:
        pass

    @classmethod
    @abstractmethod
    async def get_conversation_by_kp_id(cls, kp_id: int, **kwargs) -> ConversationWithMessages | None:
        pass

    @classmethod
    @abstractmethod
    async def create_conversation(
        cls, conversation_data: ConversationCreate, messages: list[MessageCreate], **kwargs
    ) -> ConversationWithMessages:
        pass

    @classmethod
    @abstractmethod
    async def add_messages_to_conversation(cls, conversation_id: int, messages: list[MessageCreate], **kwargs) -> ConversationWithMessages:
        pass


class SQLConversationRepo(AbstractConversationRepo):
    _locks = defaultdict(Lock)

    @classmethod
    def _get_db(cls, **kwargs) -> Session:
        db = kwargs.get("db")
        if db is None:
            raise ValueError(f"Missing db of type {Session} in kwargs: {kwargs}")
        return db

    @classmethod
    async def get_conversation(cls, conversation_id: int, **kwargs) -> ConversationWithMessages | None:
        db = cls._get_db(**kwargs)
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conversation:
            return None

        message_reads = [
            MessageRead(
                id=msg.id,
                conversation_id=msg.conversation_id,
                sender=msg.sender,
                content=msg.content,
                created_at=msg.created_at,
                updated_at=msg.updated_at,
            )
            for msg in conversation.messages
        ]

        return ConversationWithMessages(
            id=conversation.id,
            title=conversation.title,
            agent_id=conversation.agent_id,
            kp_id=conversation.kp_id,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            messages=message_reads,
        )

    @classmethod
    async def get_conversation_by_kp_id(cls, kp_id: int, **kwargs) -> ConversationWithMessages | None:
        db = cls._get_db(**kwargs)
        conversation = db.query(Conversation).filter(Conversation.kp_id == kp_id).first()
        if not conversation:
            return None
        message_reads = [
            MessageRead(
                id=msg.id,
                conversation_id=msg.conversation_id,
                sender=msg.sender,
                content=msg.content,
                created_at=msg.created_at,
                updated_at=msg.updated_at,
            )
            for msg in conversation.messages
        ]
        return ConversationWithMessages(
            id=conversation.id,
            title=conversation.title,
            agent_id=conversation.agent_id,
            kp_id=conversation.kp_id,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            messages=message_reads,
        )

    @classmethod
    async def create_conversation(
        cls, conversation_data: ConversationCreate, messages: list[MessageCreate], **kwargs
    ) -> ConversationWithMessages:
        db = cls._get_db(**kwargs)
        conversation = Conversation(title=conversation_data.title, agent_id=conversation_data.agent_id, kp_id=conversation_data.kp_id)
        for message in messages:
            conversation.messages.append(
                Message(
                    sender=message.sender,
                    content=message.content,
                    require_user=message.require_user,
                    treat_as_tool=message.treat_as_tool,
                    msg_metadata=message.metadata,
                )
            )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        message_reads = [
            MessageRead(
                id=msg.id,
                conversation_id=msg.conversation_id,
                sender=msg.sender,
                content=msg.content,
                created_at=msg.created_at,
                updated_at=msg.updated_at,
            )
            for msg in conversation.messages
        ]
        return ConversationWithMessages(
            id=conversation.id,
            title=conversation.title,
            agent_id=conversation.agent_id,
            kp_id=conversation.kp_id,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            messages=message_reads,
        )

    @classmethod
    async def add_messages_to_conversation(
        cls, conversation_id: int, messages: list[MessageCreate], **kwargs
    ) -> ConversationWithMessages | None:
        db = cls._get_db(**kwargs)
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conversation:
            return None
        for message in messages:
            conversation.messages.append(
                Message(
                    sender=message.sender,
                    content=message.content,
                    require_user=message.require_user,
                    treat_as_tool=message.treat_as_tool,
                    msg_metadata=message.metadata,
                )
            )
        db.commit()
        db.refresh(conversation)
        message_reads = [
            MessageRead(
                id=msg.id,
                conversation_id=msg.conversation_id,
                sender=msg.sender,
                content=msg.content,
                created_at=msg.created_at,
                updated_at=msg.updated_at,
            )
            for msg in conversation.messages
        ]
        return ConversationWithMessages(
            id=conversation.id,
            title=conversation.title,
            agent_id=conversation.agent_id,
            kp_id=conversation.kp_id,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            messages=message_reads,
        )


if __name__ == "__main__":
    from dana.api.core.database import get_db
    import asyncio

    for db in get_db():
        print(asyncio.run(SQLConversationRepo.get_conversation(8, db=db)))
