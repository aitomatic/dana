from sqlalchemy.orm import Session

from dana.api.server.models import Agent, Conversation, Message


def test_conversation_model(db_session: Session):
    # Create an agent first
    agent = Agent(name="Test Agent", description="A test agent", config={})
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)
    
    convo = Conversation(title="Test Conversation", agent_id=agent.id)
    db_session.add(convo)
    db_session.commit()
    db_session.refresh(convo)
    assert convo.id is not None
    assert convo.title == "Test Conversation"
    assert convo.agent_id == agent.id
    assert convo.created_at is not None
    assert convo.updated_at is not None

def test_message_model(db_session: Session):
    # Create an agent first
    agent = Agent(name="Test Agent", description="A test agent", config={})
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)
    
    convo = Conversation(title="Test Conversation", agent_id=agent.id)
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
    # Create an agent first
    agent = Agent(name="Test Agent", description="A test agent", config={})
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)
    
    convo = Conversation(title="Cascade Test", agent_id=agent.id)
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