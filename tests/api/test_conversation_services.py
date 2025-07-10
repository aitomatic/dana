from sqlalchemy.orm import Session

from dana.api.server.models import Conversation, Agent
from dana.api.server.schemas import ConversationCreate, MessageCreate
from dana.api.server.services import ConversationService, MessageService


def test_conversation_crud(db_session: Session):
    # Create an agent first
    agent = Agent(name="Test Agent", description="A test agent", config={})
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)
    
    service = ConversationService()
    # Create
    convo = service.create_conversation(db_session, ConversationCreate(title="Chat", agent_id=agent.id))
    assert convo.id is not None
    assert convo.agent_id == agent.id
    # Read
    fetched = service.get_conversation(db_session, convo.id)
    assert fetched is not None
    assert fetched.id == convo.id
    assert fetched.agent_id == agent.id
    # Update
    updated = service.update_conversation(db_session, convo.id, ConversationCreate(title="Updated Chat", agent_id=agent.id))
    assert updated is not None
    assert updated.title == "Updated Chat"
    assert updated.agent_id == agent.id
    # Delete
    assert service.delete_conversation(db_session, convo.id) is True
    assert service.get_conversation(db_session, convo.id) is None


def test_conversation_filtering_by_agent(db_session: Session):
    # Create two agents
    agent1 = Agent(name="Agent 1", description="First agent", config={})
    agent2 = Agent(name="Agent 2", description="Second agent", config={})
    db_session.add_all([agent1, agent2])
    db_session.commit()
    db_session.refresh(agent1)
    db_session.refresh(agent2)
    
    service = ConversationService()
    
    # Create conversations for different agents
    convo1 = service.create_conversation(db_session, ConversationCreate(title="Chat 1", agent_id=agent1.id))
    convo2 = service.create_conversation(db_session, ConversationCreate(title="Chat 2", agent_id=agent1.id))
    convo3 = service.create_conversation(db_session, ConversationCreate(title="Chat 3", agent_id=agent2.id))
    
    # Test filtering by agent_id
    agent1_conversations = service.get_conversations(db_session, agent_id=agent1.id)
    agent2_conversations = service.get_conversations(db_session, agent_id=agent2.id)
    all_conversations = service.get_conversations(db_session)
    
    assert len(agent1_conversations) == 2
    assert len(agent2_conversations) == 1
    assert len(all_conversations) == 3
    
    # Verify agent associations
    for conv in agent1_conversations:
        assert conv.agent_id == agent1.id
    for conv in agent2_conversations:
        assert conv.agent_id == agent2.id


def test_message_crud(db_session: Session):
    # Create an agent first
    agent = Agent(name="Test Agent", description="A test agent", config={})
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)
    
    convo = Conversation(title="Chat", agent_id=agent.id)
    db_session.add(convo)
    db_session.commit()
    db_session.refresh(convo)
    service = MessageService()
    # Create
    msg = service.create_message(db_session, convo.id, MessageCreate(sender="user", content="Hi"))
    assert msg.id is not None
    # Read
    fetched = service.get_message(db_session, convo.id, msg.id)
    assert fetched.id == msg.id
    # Update
    updated = service.update_message(db_session, convo.id, msg.id, MessageCreate(sender="bot", content="Hello"))
    assert updated.sender == "bot"
    assert updated.content == "Hello"
    # Delete
    assert service.delete_message(db_session, convo.id, msg.id) is True
    assert service.get_message(db_session, convo.id, msg.id) is None 