"""Tests for API server models."""

import pytest
from sqlalchemy.orm import Session

from dana.api.core.models import Agent, Document, Topic


class TestAgentModel:
    """Test the Agent SQLAlchemy model."""

    def test_agent_creation(self):
        """Test basic agent creation with all fields."""
        agent = Agent(name="Test Agent", description="A test agent for unit testing", config={"model": "gpt-4", "temperature": 0.7})

        assert agent.name == "Test Agent"
        assert agent.description == "A test agent for unit testing"
        assert agent.config == {"model": "gpt-4", "temperature": 0.7}
        assert agent.id is None  # Not set until committed to DB

    def test_agent_creation_minimal(self):
        """Test agent creation with minimal required fields."""
        agent = Agent(name="Minimal Agent", description="", config={})

        assert agent.name == "Minimal Agent"
        assert agent.description == ""
        assert agent.config == {}

    def test_agent_table_name(self):
        """Test that the table name is correctly set."""
        assert Agent.__tablename__ == "agents"

    def test_agent_fields_exist(self):
        """Test that all expected fields exist on the model."""
        agent = Agent()

        # Check that fields exist (they should be SQLAlchemy Column objects)
        assert hasattr(agent, "id")
        assert hasattr(agent, "name")
        assert hasattr(agent, "description")
        assert hasattr(agent, "config")

    def test_agent_id_auto_increment(self, db_session: Session):
        """Test that ID is auto-incrementing integer."""
        # Create first agent
        agent1 = Agent(name="First Agent", description="First test agent", config={"test": True})
        db_session.add(agent1)
        db_session.commit()
        db_session.refresh(agent1)

        # Create second agent
        agent2 = Agent(name="Second Agent", description="Second test agent", config={"test": False})
        db_session.add(agent2)
        db_session.commit()
        db_session.refresh(agent2)

        # Check that IDs are integers and incrementing
        assert isinstance(agent1.id, int)
        assert isinstance(agent2.id, int)
        assert agent2.id > agent1.id


def test_agent_model(db_session: Session):
    """Test Agent model creation and relationships."""
    agent = Agent(name="Test Agent", description="A test agent", config={"model": "gpt-4", "temperature": 0.7})
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)

    assert agent.id is not None
    assert agent.name == "Test Agent"
    assert agent.description == "A test agent"
    assert agent.config == {"model": "gpt-4", "temperature": 0.7}


def test_topic_model(db_session: Session):
    """Test Topic model creation."""
    topic = Topic(name="Test Topic", description="A test topic")
    db_session.add(topic)
    db_session.commit()
    db_session.refresh(topic)

    assert topic.id is not None
    assert topic.name == "Test Topic"
    assert topic.description == "A test topic"
    assert topic.created_at is not None
    assert topic.updated_at is not None


def test_document_model(db_session: Session):
    """Test Document model creation."""
    document = Document(
        filename="test-uuid.pdf",
        original_filename="test.pdf",
        file_path="2025/01/27/test-uuid.pdf",
        file_size=1024,
        mime_type="application/pdf",
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)

    assert document.id is not None
    assert document.filename == "test-uuid.pdf"
    assert document.original_filename == "test.pdf"
    assert document.file_path == "2025/01/27/test-uuid.pdf"
    assert document.file_size == 1024
    assert document.mime_type == "application/pdf"
    assert document.created_at is not None
    assert document.updated_at is not None


def test_document_topic_relationship(db_session: Session):
    """Test Document-Topic relationship."""
    topic = Topic(name="Research Papers", description="Academic papers")
    db_session.add(topic)
    db_session.commit()
    db_session.refresh(topic)

    document = Document(
        filename="paper-uuid.pdf",
        original_filename="research_paper.pdf",
        file_path="2025/01/27/paper-uuid.pdf",
        file_size=2048,
        mime_type="application/pdf",
        topic_id=topic.id,
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)

    assert document.topic_id == topic.id
    assert document.topic == topic
    assert document in topic.documents


def test_document_agent_relationship(db_session: Session):
    """Test Document-Agent relationship."""
    agent = Agent(name="Research Agent", description="Agent for research tasks", config={"model": "gpt-4"})
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)

    document = Document(
        filename="data-uuid.json",
        original_filename="research_data.json",
        file_path="2025/01/27/data-uuid.json",
        file_size=512,
        mime_type="application/json",
        agent_id=agent.id,
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)

    assert document.agent_id == agent.id
    assert document.agent == agent
    assert document in agent.documents


def test_document_without_associations(db_session: Session):
    """Test Document without topic or agent associations."""
    document = Document(
        filename="standalone-uuid.txt",
        original_filename="notes.txt",
        file_path="2025/01/27/standalone-uuid.txt",
        file_size=256,
        mime_type="text/plain",
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)

    assert document.topic_id is None
    assert document.agent_id is None
    assert document.topic is None
    assert document.agent is None


def test_topic_unique_name_constraint(db_session: Session):
    """Test that topic names must be unique."""
    topic1 = Topic(name="Unique Topic", description="First topic")
    db_session.add(topic1)
    db_session.commit()

    topic2 = Topic(name="Unique Topic", description="Second topic")
    db_session.add(topic2)

    with pytest.raises(Exception):  # noqa: B017 SQLAlchemy will raise an integrity error
        db_session.commit()
