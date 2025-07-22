import pytest
from sqlalchemy.orm import Session

from dana.api.core.models import Agent, Conversation
from dana.api.core.schemas import ConversationCreate, MessageCreate
from dana.api.services.conversation_service import ConversationService


@pytest.mark.asyncio
async def test_conversation_crud(db_session: Session):
    # Create an agent first
    agent = Agent(name="Test Agent", description="A test agent", config={})
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)
    
    service = ConversationService()
    # Create
    convo = await service.create_conversation(ConversationCreate(title="Chat", agent_id=agent.id), db_session)
    assert convo.id is not None
    assert convo.agent_id == agent.id
    # Read
    fetched = await service.get_conversation(convo.id, db_session)
    assert fetched is not None
    assert fetched.id == convo.id
    assert fetched.agent_id == agent.id
    # Update
    updated = await service.update_conversation_title(convo.id, "Updated Chat", db_session)
    assert updated is not None
    assert updated.title == "Updated Chat"
    assert updated.agent_id == agent.id
    # Delete
    result = await service.delete_conversation(convo.id, db_session)
    assert result is True
    fetched_after_delete = await service.get_conversation(convo.id, db_session)
    assert fetched_after_delete is None


@pytest.mark.asyncio
async def test_conversation_filtering_by_agent(db_session: Session):
    # Create two agents
    agent1 = Agent(name="Agent 1", description="First agent", config={})
    agent2 = Agent(name="Agent 2", description="Second agent", config={})
    db_session.add_all([agent1, agent2])
    db_session.commit()
    db_session.refresh(agent1)
    db_session.refresh(agent2)
    
    service = ConversationService()
    
    # Create conversations for different agents
    convo1 = await service.create_conversation(ConversationCreate(title="Chat 1", agent_id=agent1.id), db_session)
    convo2 = await service.create_conversation(ConversationCreate(title="Chat 2", agent_id=agent1.id), db_session)
    convo3 = await service.create_conversation(ConversationCreate(title="Chat 3", agent_id=agent2.id), db_session)
    
    # Test filtering by agent_id
    agent1_conversations = await service.list_conversations(agent_id=agent1.id, limit=100, offset=0, db_session=db_session)
    agent2_conversations = await service.list_conversations(agent_id=agent2.id, limit=100, offset=0, db_session=db_session)
    all_conversations = await service.list_conversations(agent_id=None, limit=100, offset=0, db_session=db_session)
    
    assert len(agent1_conversations) == 2
    assert len(agent2_conversations) == 1
    assert len(all_conversations) == 3
    
    # Verify agent associations
    for conv in agent1_conversations:
        assert conv.agent_id == agent1.id
    for conv in agent2_conversations:
        assert conv.agent_id == agent2.id


@pytest.mark.asyncio
async def test_message_crud(db_session: Session):
    # Create an agent first
    agent = Agent(name="Test Agent", description="A test agent", config={})
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)
    
    convo = Conversation(title="Chat", agent_id=agent.id)
    db_session.add(convo)
    db_session.commit()
    db_session.refresh(convo)
    # MessageService functionality is part of ConversationService
    service = ConversationService()
    # Create
    msg = await service.add_message(convo.id, MessageCreate(sender="user", content="Hi"), db_session)
    assert msg.id is not None
    assert msg.sender == "user"
    assert msg.content == "Hi"
    # Read messages for conversation
    messages = await service.get_conversation_messages(convo.id, limit=100, offset=0, db_session=db_session)
    assert len(messages) == 1
    assert messages[0].id == msg.id
    assert messages[0].sender == "user"
    assert messages[0].content == "Hi" 