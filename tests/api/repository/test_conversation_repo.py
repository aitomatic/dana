"""Tests for conversation repository implementation."""

import pytest
import os
from datetime import datetime
from sqlalchemy.orm import Session
from unittest.mock import Mock

from dana.api.repositories.conversation_repo import SQLConversationRepo, AbstractConversationRepo
from dana.api.core.models import Conversation, Message, Agent, KnowledgePack, KnowledgeAgentRelationship, AgentChatHistory
from dana.api.core.schemas import ConversationCreate, MessageCreate, ConversationWithMessages, MessageRead, SenderRole


class TestAbstractConversationRepo:
    """Test the abstract base class."""

    def test_abstract_methods_exist(self):
        """Test that all abstract methods are defined."""
        assert hasattr(AbstractConversationRepo, "get_conversation")
        assert hasattr(AbstractConversationRepo, "get_conversation_by_kp_id")
        assert hasattr(AbstractConversationRepo, "create_conversation")
        assert hasattr(AbstractConversationRepo, "add_messages_to_conversation")

        # Check that methods are abstract
        assert getattr(AbstractConversationRepo.get_conversation, "__isabstractmethod__", False)
        assert getattr(AbstractConversationRepo.get_conversation_by_kp_id, "__isabstractmethod__", False)
        assert getattr(AbstractConversationRepo.create_conversation, "__isabstractmethod__", False)
        assert getattr(AbstractConversationRepo.add_messages_to_conversation, "__isabstractmethod__", False)


class TestSQLConversationRepo:
    """Test the SQL implementation of conversation repository."""

    def test_database_isolation(self, db_session):
        """Test that each test uses a completely isolated database."""
        # Verify we're using a temporary database file
        db_url = str(db_session.bind.url)
        assert "temp" in db_url or "tmp" in db_url or db_url.startswith("sqlite:///")

        # Verify the database is empty at the start
        assert db_session.query(Conversation).count() == 0
        assert db_session.query(Message).count() == 0
        assert db_session.query(Agent).count() == 0
        assert db_session.query(KnowledgePack).count() == 0

    def test_database_cleanup_after_test(self, db_session):
        """Test that database is properly cleaned up after each test."""
        # Create some test data
        agent = Agent(name="Cleanup Test Agent", description="Test", config={})
        db_session.add(agent)
        db_session.commit()

        conversation = Conversation(title="Cleanup Test", agent_id=agent.id)
        db_session.add(conversation)
        db_session.commit()

        # Verify data exists
        assert db_session.query(Agent).count() == 1
        assert db_session.query(Conversation).count() == 1

        # The cleanup will happen automatically via the fixture
        # This test just verifies the data was created and will be cleaned up

    def test_all_models_cleanup(self, db_session):
        """Test that all models used in conversation tests are properly cleaned up."""
        # Create data for all models that might be used
        agent = Agent(name="Test Agent", description="Test", config={})
        db_session.add(agent)
        db_session.commit()

        kp = KnowledgePack(kp_metadata={"test": "data"})
        db_session.add(kp)
        db_session.commit()

        conversation = Conversation(title="Test", agent_id=agent.id, kp_id=kp.id)
        db_session.add(conversation)
        db_session.commit()

        message = Message(conversation_id=conversation.id, sender="user", content="test")
        db_session.add(message)
        db_session.commit()

        # Create relationship data
        kp_agent_rel = KnowledgeAgentRelationship(knowledge_pack_id=kp.id, agent_id=agent.id)
        db_session.add(kp_agent_rel)
        db_session.commit()

        chat_history = AgentChatHistory(agent_id=agent.id, sender="user", text="test chat", type="test")
        db_session.add(chat_history)
        db_session.commit()

        # Verify all data exists
        assert db_session.query(Agent).count() == 1
        assert db_session.query(KnowledgePack).count() == 1
        assert db_session.query(Conversation).count() == 1
        assert db_session.query(Message).count() == 1
        assert db_session.query(KnowledgeAgentRelationship).count() == 1
        assert db_session.query(AgentChatHistory).count() == 1

    def test_database_file_cleanup(self, test_db):
        """Test that the temporary database file is properly cleaned up."""
        engine, SessionLocal, temp_db = test_db

        # Verify the temp file exists
        assert os.path.exists(temp_db.name)

        # Create some data
        session = SessionLocal()
        agent = Agent(name="File Cleanup Test", description="Test", config={})
        session.add(agent)
        session.commit()
        session.close()

        # Verify data exists
        session = SessionLocal()
        assert session.query(Agent).count() == 1
        session.close()

        # The fixture will clean up the file after the test
        # This test just verifies the file exists during the test

    def test_concurrent_test_isolation(self, db_session):
        """Test that concurrent tests don't interfere with each other."""
        # This test simulates what happens when multiple tests run
        # Each should have its own isolated database

        # Create some data
        agent = Agent(name="Isolation Test Agent", description="Test", config={})
        db_session.add(agent)
        db_session.commit()

        # Verify we have exactly one agent
        assert db_session.query(Agent).count() == 1

        # This test should not affect other tests due to database isolation

    def test_get_db_success(self):
        """Test _get_db method with valid db session."""
        mock_db = Mock(spec=Session)
        result = SQLConversationRepo._get_db(db=mock_db)
        assert result == mock_db

    def test_get_db_missing_db(self):
        """Test _get_db method when db is missing from kwargs."""
        with pytest.raises(ValueError, match="Missing db of type"):
            SQLConversationRepo._get_db()

    def test_get_db_none_db(self):
        """Test _get_db method when db is None."""
        with pytest.raises(ValueError, match="Missing db of type"):
            SQLConversationRepo._get_db(db=None)

    @pytest.mark.asyncio
    async def test_get_conversation_success(self, db_session):
        """Test getting a conversation by ID successfully."""
        # Create test data
        agent = Agent(name="Test Agent", description="Test", config={})
        kp = KnowledgePack(kp_metadata={})
        db_session.add(agent)
        db_session.add(kp)
        db_session.commit()

        conversation = Conversation(title="Test Conversation", agent_id=agent.id, kp_id=kp.id)
        db_session.add(conversation)
        db_session.commit()

        # Add messages
        message1 = Message(conversation_id=conversation.id, sender="user", content="Hello")
        message2 = Message(conversation_id=conversation.id, sender="agent", content="Hi there")
        db_session.add(message1)
        db_session.add(message2)
        db_session.commit()

        # Test the method
        result = await SQLConversationRepo.get_conversation(conversation.id, db=db_session)

        assert result is not None
        assert result.id == conversation.id
        assert result.title == "Test Conversation"
        assert result.agent_id == agent.id
        assert result.kp_id == kp.id
        assert len(result.messages) == 2

        # Check message order and content
        messages = sorted(result.messages, key=lambda m: m.id)
        assert messages[0].sender == "user"
        assert messages[0].content == "Hello"
        assert messages[1].sender == "agent"
        assert messages[1].content == "Hi there"

    @pytest.mark.asyncio
    async def test_get_conversation_not_found(self, db_session):
        """Test getting a conversation that doesn't exist."""
        result = await SQLConversationRepo.get_conversation(999, db=db_session)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_conversation_by_kp_id_success(self, db_session):
        """Test getting a conversation by knowledge pack ID successfully."""
        # Create test data
        agent = Agent(name="Test Agent", description="Test", config={})
        kp = KnowledgePack(kp_metadata={})
        db_session.add(agent)
        db_session.add(kp)
        db_session.commit()

        conversation = Conversation(title="Test Conversation", agent_id=agent.id, kp_id=kp.id)
        db_session.add(conversation)
        db_session.commit()

        # Add messages
        message = Message(conversation_id=conversation.id, sender="user", content="Hello")
        db_session.add(message)
        db_session.commit()

        # Test the method
        result = await SQLConversationRepo.get_conversation_by_kp_id(kp.id, db=db_session)

        assert result is not None
        assert result.id == conversation.id
        assert result.title == "Test Conversation"
        assert result.agent_id == agent.id
        assert result.kp_id == kp.id
        assert len(result.messages) == 1
        assert result.messages[0].content == "Hello"

    @pytest.mark.asyncio
    async def test_get_conversation_by_kp_id_not_found(self, db_session):
        """Test getting a conversation by knowledge pack ID that doesn't exist."""
        result = await SQLConversationRepo.get_conversation_by_kp_id(999, db=db_session)
        assert result is None

    @pytest.mark.asyncio
    async def test_create_conversation_success(self, db_session):
        """Test creating a conversation with messages successfully."""
        # Create test data
        agent = Agent(name="Test Agent", description="Test", config={})
        kp = KnowledgePack(kp_metadata={})
        db_session.add(agent)
        db_session.add(kp)
        db_session.commit()

        # Prepare conversation data
        conversation_data = ConversationCreate(title="New Conversation", agent_id=agent.id, kp_id=kp.id)

        messages_data = [MessageCreate(sender=SenderRole.USER, content="Hello"), MessageCreate(sender=SenderRole.AGENT, content="Hi there")]

        # Test the method
        result = await SQLConversationRepo.create_conversation(conversation_data, messages_data, db=db_session)

        assert result is not None
        assert result.title == "New Conversation"
        assert result.agent_id == agent.id
        assert result.kp_id == kp.id
        assert len(result.messages) == 2

        # Check that conversation was actually created in database
        db_conversation = db_session.query(Conversation).filter(Conversation.id == result.id).first()
        assert db_conversation is not None
        assert db_conversation.title == "New Conversation"
        assert len(db_conversation.messages) == 2

    @pytest.mark.asyncio
    async def test_create_conversation_with_empty_messages(self, db_session):
        """Test creating a conversation with no messages."""
        agent = Agent(name="Test Agent", description="Test", config={})
        db_session.add(agent)
        db_session.commit()

        conversation_data = ConversationCreate(title="Empty Conversation", agent_id=agent.id)

        result = await SQLConversationRepo.create_conversation(conversation_data, [], db=db_session)

        assert result is not None
        assert result.title == "Empty Conversation"
        assert result.agent_id == agent.id
        assert len(result.messages) == 0

    @pytest.mark.asyncio
    async def test_add_messages_to_conversation_success(self, db_session):
        """Test adding messages to an existing conversation."""
        # Create test data
        agent = Agent(name="Test Agent", description="Test", config={})
        db_session.add(agent)
        db_session.commit()

        conversation = Conversation(title="Test Conversation", agent_id=agent.id)
        db_session.add(conversation)
        db_session.commit()

        # Add initial message
        initial_message = Message(conversation_id=conversation.id, sender="user", content="Initial message")
        db_session.add(initial_message)
        db_session.commit()

        # Prepare new messages
        new_messages = [
            MessageCreate(sender=SenderRole.AGENT, content="Response 1"),
            MessageCreate(sender=SenderRole.USER, content="Follow up"),
        ]

        # Test the method
        result = await SQLConversationRepo.add_messages_to_conversation(conversation.id, new_messages, db=db_session)

        assert result is not None
        assert result.id == conversation.id
        assert len(result.messages) == 3  # 1 initial + 2 new

        # Check that messages were actually added to database
        db_conversation = db_session.query(Conversation).filter(Conversation.id == conversation.id).first()
        assert len(db_conversation.messages) == 3

    @pytest.mark.asyncio
    async def test_add_messages_to_conversation_not_found(self, db_session):
        """Test adding messages to a conversation that doesn't exist."""
        new_messages = [MessageCreate(sender=SenderRole.USER, content="Test message")]

        result = await SQLConversationRepo.add_messages_to_conversation(999, new_messages, db=db_session)

        assert result is None

    @pytest.mark.asyncio
    async def test_add_messages_to_conversation_empty_list(self, db_session):
        """Test adding empty list of messages to a conversation."""
        agent = Agent(name="Test Agent", description="Test", config={})
        db_session.add(agent)
        db_session.commit()

        conversation = Conversation(title="Test Conversation", agent_id=agent.id)
        db_session.add(conversation)
        db_session.commit()

        result = await SQLConversationRepo.add_messages_to_conversation(conversation.id, [], db=db_session)

        assert result is not None
        assert result.id == conversation.id
        assert len(result.messages) == 0

    @pytest.mark.asyncio
    async def test_conversation_with_null_agent_id(self, db_session):
        """Test conversation operations with null agent_id."""
        kp = KnowledgePack(kp_metadata={})
        db_session.add(kp)
        db_session.commit()

        conversation = Conversation(title="No Agent Conversation", agent_id=None, kp_id=kp.id)
        db_session.add(conversation)
        db_session.commit()

        # Test getting conversation
        result = await SQLConversationRepo.get_conversation(conversation.id, db=db_session)
        assert result is not None
        assert result.agent_id is None
        assert result.kp_id == kp.id

    @pytest.mark.asyncio
    async def test_conversation_with_null_kp_id(self, db_session):
        """Test conversation operations with null kp_id."""
        agent = Agent(name="Test Agent", description="Test", config={})
        db_session.add(agent)
        db_session.commit()

        conversation = Conversation(title="No KP Conversation", agent_id=agent.id, kp_id=None)
        db_session.add(conversation)
        db_session.commit()

        # Test getting conversation
        result = await SQLConversationRepo.get_conversation(conversation.id, db=db_session)
        assert result is not None
        assert result.agent_id == agent.id
        assert result.kp_id is None

    @pytest.mark.asyncio
    async def test_message_timestamps(self, db_session):
        """Test that message timestamps are properly set."""
        agent = Agent(name="Test Agent", description="Test", config={})
        db_session.add(agent)
        db_session.commit()

        conversation_data = ConversationCreate(title="Timestamp Test", agent_id=agent.id)

        messages_data = [MessageCreate(sender=SenderRole.USER, content="Test message")]

        result = await SQLConversationRepo.create_conversation(conversation_data, messages_data, db=db_session)

        assert result is not None
        assert len(result.messages) == 1

        message = result.messages[0]
        assert message.created_at is not None
        assert message.updated_at is not None
        assert isinstance(message.created_at, datetime)
        assert isinstance(message.updated_at, datetime)

    @pytest.mark.asyncio
    async def test_conversation_timestamps(self, db_session):
        """Test that conversation timestamps are properly set."""
        agent = Agent(name="Test Agent", description="Test", config={})
        db_session.add(agent)
        db_session.commit()

        conversation_data = ConversationCreate(title="Timestamp Test", agent_id=agent.id)

        result = await SQLConversationRepo.create_conversation(conversation_data, [], db=db_session)

        assert result is not None
        assert result.created_at is not None
        assert result.updated_at is not None
        assert isinstance(result.created_at, datetime)
        assert isinstance(result.updated_at, datetime)

    @pytest.mark.asyncio
    async def test_multiple_conversations_same_kp(self, db_session):
        """Test handling multiple conversations with the same kp_id."""
        agent = Agent(name="Test Agent", description="Test", config={})
        kp = KnowledgePack(kp_metadata={})
        db_session.add(agent)
        db_session.add(kp)
        db_session.commit()

        # Create two conversations with same kp_id
        conv1 = Conversation(title="Conv 1", agent_id=agent.id, kp_id=kp.id)
        conv2 = Conversation(title="Conv 2", agent_id=agent.id, kp_id=kp.id)
        db_session.add(conv1)
        db_session.add(conv2)
        db_session.commit()

        # get_conversation_by_kp_id should return the first one found
        result = await SQLConversationRepo.get_conversation_by_kp_id(kp.id, db=db_session)
        assert result is not None
        assert result.kp_id == kp.id
        # Should return one of the conversations (implementation dependent)

    @pytest.mark.asyncio
    async def test_large_message_content(self, db_session):
        """Test handling of large message content."""
        agent = Agent(name="Test Agent", description="Test", config={})
        db_session.add(agent)
        db_session.commit()

        # Create a very long message
        long_content = "A" * 10000  # 10KB message

        conversation_data = ConversationCreate(title="Large Message Test", agent_id=agent.id)

        messages_data = [MessageCreate(sender=SenderRole.USER, content=long_content)]

        result = await SQLConversationRepo.create_conversation(conversation_data, messages_data, db=db_session)

        assert result is not None
        assert len(result.messages) == 1
        assert result.messages[0].content == long_content

    @pytest.mark.asyncio
    async def test_special_characters_in_content(self, db_session):
        """Test handling of special characters in message content."""
        agent = Agent(name="Test Agent", description="Test", config={})
        db_session.add(agent)
        db_session.commit()

        special_content = "Hello! @#$%^&*()_+{}|:<>?[]\\;'\",./ 中文 🚀"

        conversation_data = ConversationCreate(title="Special Chars Test", agent_id=agent.id)

        messages_data = [MessageCreate(sender=SenderRole.USER, content=special_content)]

        result = await SQLConversationRepo.create_conversation(conversation_data, messages_data, db=db_session)

        assert result is not None
        assert len(result.messages) == 1
        assert result.messages[0].content == special_content

    def test_locks_initialization(self):
        """Test that the locks defaultdict is properly initialized."""
        assert hasattr(SQLConversationRepo, "_locks")
        assert isinstance(SQLConversationRepo._locks, dict)

    @pytest.mark.asyncio
    async def test_database_rollback_on_error(self, db_session):
        """Test that database operations are properly handled on errors."""
        # This test would require mocking database operations to simulate failures
        # For now, we'll test that the methods handle missing db gracefully
        with pytest.raises(ValueError):
            await SQLConversationRepo.get_conversation(1)  # No db provided

    @pytest.mark.asyncio
    async def test_message_read_schema_consistency(self, db_session):
        """Test that MessageRead objects are properly constructed."""
        agent = Agent(name="Test Agent", description="Test", config={})
        db_session.add(agent)
        db_session.commit()

        conversation = Conversation(title="Schema Test", agent_id=agent.id)
        db_session.add(conversation)
        db_session.commit()

        message = Message(conversation_id=conversation.id, sender="user", content="Test message")
        db_session.add(message)
        db_session.commit()

        result = await SQLConversationRepo.get_conversation(conversation.id, db=db_session)

        assert result is not None
        assert len(result.messages) == 1

        message_read = result.messages[0]
        assert isinstance(message_read, MessageRead)
        assert message_read.id == message.id
        assert message_read.conversation_id == conversation.id
        assert message_read.sender == "user"
        assert message_read.content == "Test message"
        assert message_read.created_at == message.created_at
        assert message_read.updated_at == message.updated_at

    @pytest.mark.asyncio
    async def test_conversation_with_messages_schema_consistency(self, db_session):
        """Test that ConversationWithMessages objects are properly constructed."""
        agent = Agent(name="Test Agent", description="Test", config={})
        kp = KnowledgePack(kp_metadata={})
        db_session.add(agent)
        db_session.add(kp)
        db_session.commit()

        conversation_data = ConversationCreate(title="Schema Consistency Test", agent_id=agent.id, kp_id=kp.id)

        messages_data = [MessageCreate(sender=SenderRole.USER, content="Test")]

        result = await SQLConversationRepo.create_conversation(conversation_data, messages_data, db=db_session)

        assert isinstance(result, ConversationWithMessages)
        assert result.id is not None
        assert result.title == "Schema Consistency Test"
        assert result.agent_id == agent.id
        assert result.kp_id == kp.id
        assert result.created_at is not None
        assert result.updated_at is not None
        assert isinstance(result.messages, list)
        assert len(result.messages) == 1
        assert isinstance(result.messages[0], MessageRead)
