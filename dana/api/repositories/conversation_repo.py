from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from dana.api.core.models import Conversation, Message
from dana.api.core.schemas import (
    ConversationWithMessages,
    MessageRead,
    ConversationCreate,
)
from dana.api.core.schemas_v2 import BaseMessage
from threading import Lock
from collections import defaultdict


class AbstractConversationRepo(ABC):
    @classmethod
    def convert_message_to_message_model(cls, message: BaseMessage) -> Message:
        return Message(
            sender=message.sender,
            content=message.content,
            require_user=getattr(message, "require_user", False),
            treat_as_tool=getattr(message, "treat_as_tool", False),
            msg_metadata=getattr(message, "metadata", {}),
        )

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
    async def get_conversation_by_kp_id_and_type(cls, kp_id: int, type: str | None = None, **kwargs) -> ConversationWithMessages | None:
        pass

    @classmethod
    @abstractmethod
    async def create_conversation(
        cls, conversation_data: ConversationCreate, messages: list[BaseMessage], type: str | None = None, **kwargs
    ) -> ConversationWithMessages:
        pass

    @classmethod
    @abstractmethod
    async def add_messages_to_conversation(cls, conversation_id: int, messages: list[BaseMessage], **kwargs) -> ConversationWithMessages:
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
                require_user=msg.require_user,
                treat_as_tool=msg.treat_as_tool,
                metadata=msg.msg_metadata,
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
            type=conversation.type,
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
                require_user=msg.require_user,
                treat_as_tool=msg.treat_as_tool,
                metadata=msg.msg_metadata,
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
            type=conversation.type,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            messages=message_reads,
        )

    @classmethod
    async def get_conversation_by_kp_id_and_type(cls, kp_id: int, type: str | None = None, **kwargs) -> ConversationWithMessages | None:
        db = cls._get_db(**kwargs)
        conversation = db.query(Conversation).filter(Conversation.kp_id == kp_id, Conversation.type == type).first()
        if not conversation:
            return None
        message_reads = [
            MessageRead(
                id=msg.id,
                conversation_id=msg.conversation_id,
                sender=msg.sender,
                content=msg.content,
                require_user=msg.require_user,
                treat_as_tool=msg.treat_as_tool,
                metadata=msg.msg_metadata,
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
            type=conversation.type,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            messages=message_reads,
        )

    @classmethod
    async def create_conversation(
        cls, conversation_data: ConversationCreate, messages: list[BaseMessage], type: str | None = None, **kwargs
    ) -> ConversationWithMessages:
        db = cls._get_db(**kwargs)
        conversation = Conversation(
            title=conversation_data.title, agent_id=conversation_data.agent_id, kp_id=conversation_data.kp_id, type=type
        )
        for message in messages:
            conversation.messages.append(cls.convert_message_to_message_model(message))
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        message_reads = [
            MessageRead(
                id=msg.id,
                conversation_id=msg.conversation_id,
                sender=msg.sender,
                content=msg.content,
                require_user=msg.require_user,
                treat_as_tool=msg.treat_as_tool,
                metadata=msg.msg_metadata,
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
            type=conversation.type,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            messages=message_reads,
        )

    @classmethod
    async def add_messages_to_conversation(cls, conversation_id: int, messages: list[BaseMessage], **kwargs) -> ConversationWithMessages:
        db = cls._get_db(**kwargs)
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conversation:
            raise ValueError(f"Conversation with id {conversation_id} not found")
        for message in messages:
            conversation.messages.append(cls.convert_message_to_message_model(message))
        db.commit()
        db.refresh(conversation)
        message_reads = [
            MessageRead(
                id=msg.id,
                conversation_id=msg.conversation_id,
                sender=msg.sender,
                content=msg.content,
                require_user=msg.require_user,
                treat_as_tool=msg.treat_as_tool,
                metadata=msg.msg_metadata,
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
            type=conversation.type,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            messages=message_reads,
        )


if __name__ == "__main__":
    from dana.api.core.database import get_db
    import asyncio

    for db in get_db():
        print(asyncio.run(SQLConversationRepo.get_conversation(1, db=db)))
