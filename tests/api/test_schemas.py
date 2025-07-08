"""Tests for API server Pydantic schemas."""

import pytest
from pydantic import ValidationError
from dana.api.server.schemas import (
    AgentBase,
    AgentCreate,
    AgentRead,
    TopicBase,
    TopicCreate,
    TopicRead,
    DocumentBase,
    DocumentCreate,
    DocumentRead,
    DocumentUpdate,
)
from datetime import datetime


class TestAgentBase:
    """Test the AgentBase schema."""

    def test_valid_agent_base(self):
        """Test valid agent base data."""
        data = {"name": "Test Agent", "description": "A test agent", "config": {"model": "gpt-4", "temperature": 0.7}}
        agent = AgentBase(**data)

        assert agent.name == "Test Agent"
        assert agent.description == "A test agent"
        assert agent.config == {"model": "gpt-4", "temperature": 0.7}

    def test_agent_base_missing_fields(self):
        """Test that missing required fields raise validation errors."""
        # Missing name
        with pytest.raises(ValidationError) as exc_info:
            AgentBase(description="Test", config={})
        assert "name" in str(exc_info.value)

        # Missing description
        with pytest.raises(ValidationError) as exc_info:
            AgentBase(name="Test", config={})
        assert "description" in str(exc_info.value)

        # Missing config
        with pytest.raises(ValidationError) as exc_info:
            AgentBase(name="Test", description="Test")
        assert "config" in str(exc_info.value)

    def test_agent_base_invalid_types(self):
        """Test that invalid field types raise validation errors."""
        # Invalid name type
        with pytest.raises(ValidationError):
            AgentBase(name=123, description="Test", config={})

        # Invalid description type
        with pytest.raises(ValidationError):
            AgentBase(name="Test", description=123, config={})

        # Invalid config type
        with pytest.raises(ValidationError):
            AgentBase(name="Test", description="Test", config="not a dict")

    def test_agent_base_empty_config(self):
        """Test that empty config dict is valid."""
        agent = AgentBase(name="Test", description="Test", config={})
        assert agent.config == {}

    def test_agent_base_complex_config(self):
        """Test that complex nested config is valid."""
        complex_config = {"model": "gpt-4", "temperature": 0.7, "max_tokens": 1000, "nested": {"key": "value", "array": [1, 2, 3]}}
        agent = AgentBase(name="Test", description="Test", config=complex_config)
        assert agent.config == complex_config


class TestAgentCreate:
    """Test the AgentCreate schema."""

    def test_agent_create_inheritance(self):
        """Test that AgentCreate inherits from AgentBase."""
        data = {"name": "Test Agent", "description": "A test agent", "config": {"model": "gpt-4"}}
        agent = AgentCreate(**data)

        assert isinstance(agent, AgentBase)
        assert agent.name == "Test Agent"
        assert agent.description == "A test agent"
        assert agent.config == {"model": "gpt-4"}

    def test_agent_create_validation(self):
        """Test that AgentCreate has same validation as AgentBase."""
        # Should pass with valid data
        agent = AgentCreate(name="Test", description="Test", config={})
        assert agent.name == "Test"

        # Should fail with missing fields
        with pytest.raises(ValidationError):
            AgentCreate(name="Test", config={})


class TestAgentRead:
    """Test the AgentRead schema."""

    def test_agent_read_with_id(self):
        """Test AgentRead with valid ID."""
        data = {"id": 1, "name": "Test Agent", "description": "A test agent", "config": {"model": "gpt-4"}}
        agent = AgentRead(**data)

        assert agent.id == 1
        assert agent.name == "Test Agent"
        assert agent.description == "A test agent"
        assert agent.config == {"model": "gpt-4"}

    def test_agent_read_missing_id(self):
        """Test that missing ID raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            AgentRead(name="Test", description="Test", config={})
        assert "id" in str(exc_info.value)

    def test_agent_read_invalid_id_type(self):
        """Test that invalid ID type raises validation error."""
        with pytest.raises(ValidationError):
            AgentRead(id="not an int", name="Test", description="Test", config={})

    def test_agent_read_from_attributes(self):
        """Test creating AgentRead from object with attributes."""

        # Mock ORM object
        class MockAgent:
            def __init__(self):
                self.id = 1
                self.name = "Test Agent"
                self.description = "A test agent"
                self.config = {"model": "gpt-4"}

        orm_agent = MockAgent()
        agent_read = AgentRead.model_validate(orm_agent)

        assert agent_read.id == 1
        assert agent_read.name == "Test Agent"
        assert agent_read.description == "A test agent"
        assert agent_read.config == {"model": "gpt-4"}


def test_topic_base_schema():
    """Test TopicBase schema."""
    data = {"name": "Test Topic", "description": "A test topic"}
    topic = TopicBase(**data)
    assert topic.name == "Test Topic"
    assert topic.description == "A test topic"


def test_topic_create_schema():
    """Test TopicCreate schema."""
    data = {"name": "Test Topic", "description": "A test topic"}
    topic = TopicCreate(**data)
    assert topic.name == "Test Topic"
    assert topic.description == "A test topic"


def test_topic_read_schema():
    """Test TopicRead schema."""
    now = datetime.utcnow()
    data = {"id": 1, "name": "Test Topic", "description": "A test topic", "created_at": now, "updated_at": now}
    topic = TopicRead(**data)
    assert topic.id == 1
    assert topic.name == "Test Topic"
    assert topic.description == "A test topic"
    assert topic.created_at == now
    assert topic.updated_at == now


def test_document_base_schema():
    """Test DocumentBase schema."""
    data = {"original_filename": "test.pdf", "topic_id": 1, "agent_id": 2}
    document = DocumentBase(**data)
    assert document.original_filename == "test.pdf"
    assert document.topic_id == 1
    assert document.agent_id == 2


def test_document_base_schema_optional_fields():
    """Test DocumentBase schema with optional fields."""
    data = {"original_filename": "test.pdf"}
    document = DocumentBase(**data)
    assert document.original_filename == "test.pdf"
    assert document.topic_id is None
    assert document.agent_id is None


def test_document_create_schema():
    """Test DocumentCreate schema."""
    data = {"original_filename": "test.pdf", "topic_id": 1, "agent_id": 2}
    document = DocumentCreate(**data)
    assert document.original_filename == "test.pdf"
    assert document.topic_id == 1
    assert document.agent_id == 2


def test_document_read_schema():
    """Test DocumentRead schema."""
    now = datetime.utcnow()
    data = {
        "id": 1,
        "original_filename": "test.pdf",
        "filename": "uuid-test.pdf",
        "file_size": 1024,
        "mime_type": "application/pdf",
        "topic_id": 1,
        "agent_id": 2,
        "created_at": now,
        "updated_at": now,
    }
    document = DocumentRead(**data)
    assert document.id == 1
    assert document.original_filename == "test.pdf"
    assert document.filename == "uuid-test.pdf"
    assert document.file_size == 1024
    assert document.mime_type == "application/pdf"
    assert document.topic_id == 1
    assert document.agent_id == 2
    assert document.created_at == now
    assert document.updated_at == now


def test_document_update_schema():
    """Test DocumentUpdate schema."""
    data = {"original_filename": "updated.pdf", "topic_id": 3, "agent_id": 4}
    document = DocumentUpdate(**data)
    assert document.original_filename == "updated.pdf"
    assert document.topic_id == 3
    assert document.agent_id == 4


def test_document_update_schema_partial():
    """Test DocumentUpdate schema with partial data."""
    data = {"original_filename": "updated.pdf"}
    document = DocumentUpdate(**data)
    assert document.original_filename == "updated.pdf"
    assert document.topic_id is None
    assert document.agent_id is None


def test_document_update_schema_empty():
    """Test DocumentUpdate schema with empty data."""
    data = {}
    document = DocumentUpdate(**data)
    assert document.original_filename is None
    assert document.topic_id is None
    assert document.agent_id is None


def test_schema_validation_errors():
    """Test schema validation errors."""
    # Test required fields
    with pytest.raises(ValueError):
        AgentBase(name="Test")  # Missing description and config

    with pytest.raises(ValueError):
        TopicBase(name="Test")  # Missing description

    with pytest.raises(ValueError):
        DocumentBase()  # Missing original_filename


def test_schema_from_attributes():
    """Test that schemas can be created from model attributes."""

    # This tests the ConfigDict(from_attributes=True) setting
    class MockAgent:
        def __init__(self):
            self.id = 1
            self.name = "Test Agent"
            self.description = "A test agent"
            self.config = {"model": "gpt-4"}

    mock_agent = MockAgent()
    agent_read = AgentRead.model_validate(mock_agent)
    assert agent_read.id == 1
    assert agent_read.name == "Test Agent"
    assert agent_read.description == "A test agent"
    assert agent_read.config == {"model": "gpt-4"}
