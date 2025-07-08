import pytest
from datetime import datetime
from dana.api.server.schemas import (
    ConversationBase, ConversationCreate, ConversationRead, ConversationWithMessages,
    MessageBase, MessageCreate, MessageRead
)

def test_conversation_base_schema():
    data = {"title": "Chat 1"}
    convo = ConversationBase(**data)
    assert convo.title == "Chat 1"

def test_conversation_create_schema():
    data = {"title": "Chat 2"}
    convo = ConversationCreate(**data)
    assert convo.title == "Chat 2"

def test_conversation_read_schema():
    now = datetime.utcnow()
    data = {"id": 1, "title": "Chat 3", "created_at": now, "updated_at": now}
    convo = ConversationRead(**data)
    assert convo.id == 1
    assert convo.title == "Chat 3"
    assert convo.created_at == now
    assert convo.updated_at == now

def test_message_base_schema():
    data = {"sender": "user", "content": "Hello!"}
    msg = MessageBase(**data)
    assert msg.sender == "user"
    assert msg.content == "Hello!"

def test_message_create_schema():
    data = {"sender": "bot", "content": "Hi!"}
    msg = MessageCreate(**data)
    assert msg.sender == "bot"
    assert msg.content == "Hi!"

def test_message_read_schema():
    now = datetime.utcnow()
    data = {"id": 1, "conversation_id": 2, "sender": "user", "content": "Test", "created_at": now, "updated_at": now}
    msg = MessageRead(**data)
    assert msg.id == 1
    assert msg.conversation_id == 2
    assert msg.sender == "user"
    assert msg.content == "Test"
    assert msg.created_at == now
    assert msg.updated_at == now

def test_conversation_with_messages_schema():
    now = datetime.utcnow()
    convo_data = {"id": 1, "title": "Chat", "created_at": now, "updated_at": now, "messages": [
        {"id": 1, "conversation_id": 1, "sender": "user", "content": "Hi", "created_at": now, "updated_at": now},
        {"id": 2, "conversation_id": 1, "sender": "bot", "content": "Hello", "created_at": now, "updated_at": now}
    ]}
    convo = ConversationWithMessages(**convo_data)
    assert convo.id == 1
    assert len(convo.messages) == 2
    assert convo.messages[0].sender == "user"
    assert convo.messages[1].sender == "bot" 