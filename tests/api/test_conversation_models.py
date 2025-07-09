import pytest
from sqlalchemy.orm import Session
from dana.api.server.models import Conversation, Message
from datetime import datetime

@pytest.fixture(scope="function")
def db_session(setup_test_database):
    test_engine, TestSessionLocal = setup_test_database
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_conversation_model(db_session: Session):
    convo = Conversation(title="Test Conversation")
    db_session.add(convo)
    db_session.commit()
    db_session.refresh(convo)
    assert convo.id is not None
    assert convo.title == "Test Conversation"
    assert convo.created_at is not None
    assert convo.updated_at is not None

def test_message_model(db_session: Session):
    convo = Conversation(title="Test Conversation")
    db_session.add(convo)
    db_session.commit()
    db_session.refresh(convo)
    msg = Message(conversation_id=convo.id, sender="user", content="Hello!")
    db_session.add(msg)
    db_session.commit()
    db_session.refresh(msg)
    assert msg.id is not None
    assert msg.conversation_id == convo.id
    assert msg.sender == "user"
    assert msg.content == "Hello!"
    assert msg.created_at is not None
    assert msg.updated_at is not None
    assert msg.conversation == convo
    assert msg in convo.messages

def test_cascade_delete_conversation_deletes_messages(db_session: Session):
    convo = Conversation(title="Cascade Test")
    db_session.add(convo)
    db_session.commit()
    db_session.refresh(convo)
    msg = Message(conversation_id=convo.id, sender="user", content="Bye!")
    db_session.add(msg)
    db_session.commit()
    db_session.refresh(msg)
    db_session.delete(convo)
    db_session.commit()
    assert db_session.query(Message).filter(Message.id == msg.id).first() is None 