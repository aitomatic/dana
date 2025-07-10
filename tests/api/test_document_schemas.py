"""Tests for Document and Topic Pydantic schemas."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from dana.api.server.schemas import DocumentBase, DocumentCreate, DocumentRead, DocumentUpdate, TopicBase, TopicCreate, TopicRead


class TestTopicBase:
    """Test the TopicBase schema."""

    def test_valid_topic_base(self):
        """Test valid topic base data."""
        data = {"name": "Test Topic", "description": "A test topic"}
        topic = TopicBase(**data)

        assert topic.name == "Test Topic"
        assert topic.description == "A test topic"

    def test_topic_base_missing_fields(self):
        """Test that missing required fields raise validation errors."""
        # Missing name
        with pytest.raises(ValidationError) as exc_info:
            TopicBase(description="Test")
        assert "name" in str(exc_info.value)

        # Missing description
        with pytest.raises(ValidationError) as exc_info:
            TopicBase(name="Test")
        assert "description" in str(exc_info.value)

    def test_topic_base_invalid_types(self):
        """Test that invalid field types raise validation errors."""
        # Invalid name type
        with pytest.raises(ValidationError):
            TopicBase(name=123, description="Test")

        # Invalid description type
        with pytest.raises(ValidationError):
            TopicBase(name="Test", description=123)


class TestTopicCreate:
    """Test the TopicCreate schema."""

    def test_topic_create_inheritance(self):
        """Test that TopicCreate inherits from TopicBase."""
        data = {"name": "Test Topic", "description": "A test topic"}
        topic = TopicCreate(**data)

        assert isinstance(topic, TopicBase)
        assert topic.name == "Test Topic"
        assert topic.description == "A test topic"


class TestTopicRead:
    """Test the TopicRead schema."""

    def test_topic_read_with_all_fields(self):
        """Test TopicRead with all valid fields."""
        now = datetime.utcnow()
        data = {"id": 1, "name": "Test Topic", "description": "A test topic", "created_at": now, "updated_at": now}
        topic = TopicRead(**data)

        assert topic.id == 1
        assert topic.name == "Test Topic"
        assert topic.description == "A test topic"
        assert topic.created_at == now
        assert topic.updated_at == now

    def test_topic_read_missing_id(self):
        """Test that missing ID raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            TopicRead(name="Test", description="Test")
        assert "id" in str(exc_info.value)

    def test_topic_read_from_attributes(self):
        """Test creating TopicRead from object with attributes."""

        class MockTopic:
            def __init__(self):
                self.id = 1
                self.name = "Test Topic"
                self.description = "A test topic"
                self.created_at = datetime.utcnow()
                self.updated_at = datetime.utcnow()

        orm_topic = MockTopic()
        topic_read = TopicRead.model_validate(orm_topic)

        assert topic_read.id == 1
        assert topic_read.name == "Test Topic"
        assert topic_read.description == "A test topic"


class TestDocumentBase:
    """Test the DocumentBase schema."""

    def test_valid_document_base(self):
        """Test valid document base data."""
        data = {"original_filename": "test.pdf", "topic_id": 1, "agent_id": 2}
        document = DocumentBase(**data)

        assert document.original_filename == "test.pdf"
        assert document.topic_id == 1
        assert document.agent_id == 2

    def test_document_base_optional_fields(self):
        """Test document base with optional fields."""
        data = {"original_filename": "test.pdf"}
        document = DocumentBase(**data)

        assert document.original_filename == "test.pdf"
        assert document.topic_id is None
        assert document.agent_id is None

    def test_document_base_missing_filename(self):
        """Test that missing filename raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentBase(topic_id=1)
        assert "original_filename" in str(exc_info.value)

    def test_document_base_invalid_types(self):
        """Test that invalid field types raise validation errors."""
        # Invalid topic_id type
        with pytest.raises(ValidationError):
            DocumentBase(original_filename="test.pdf", topic_id="not an int")

        # Invalid agent_id type
        with pytest.raises(ValidationError):
            DocumentBase(original_filename="test.pdf", agent_id="not an int")


class TestDocumentCreate:
    """Test the DocumentCreate schema."""

    def test_document_create_inheritance(self):
        """Test that DocumentCreate inherits from DocumentBase."""
        data = {"original_filename": "test.pdf", "topic_id": 1, "agent_id": 2}
        document = DocumentCreate(**data)

        assert isinstance(document, DocumentBase)
        assert document.original_filename == "test.pdf"
        assert document.topic_id == 1
        assert document.agent_id == 2


class TestDocumentRead:
    """Test the DocumentRead schema."""

    def test_document_read_with_all_fields(self):
        """Test DocumentRead with all valid fields."""
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

    def test_document_read_missing_required_fields(self):
        """Test that missing required fields raise validation errors."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentRead(original_filename="test.pdf")
        assert "id" in str(exc_info.value)

    def test_document_read_from_attributes(self):
        """Test creating DocumentRead from object with attributes."""

        class MockDocument:
            def __init__(self):
                self.id = 1
                self.original_filename = "test.pdf"
                self.filename = "uuid-test.pdf"
                self.file_size = 1024
                self.mime_type = "application/pdf"
                self.topic_id = 1
                self.agent_id = 2
                self.created_at = datetime.utcnow()
                self.updated_at = datetime.utcnow()

        orm_document = MockDocument()
        document_read = DocumentRead.model_validate(orm_document)

        assert document_read.id == 1
        assert document_read.original_filename == "test.pdf"
        assert document_read.filename == "uuid-test.pdf"
        assert document_read.file_size == 1024
        assert document_read.mime_type == "application/pdf"


class TestDocumentUpdate:
    """Test the DocumentUpdate schema."""

    def test_document_update_with_all_fields(self):
        """Test DocumentUpdate with all fields."""
        data = {"original_filename": "updated.pdf", "topic_id": 3, "agent_id": 4}
        document = DocumentUpdate(**data)

        assert document.original_filename == "updated.pdf"
        assert document.topic_id == 3
        assert document.agent_id == 4

    def test_document_update_partial(self):
        """Test DocumentUpdate with partial data."""
        data = {"original_filename": "updated.pdf"}
        document = DocumentUpdate(**data)

        assert document.original_filename == "updated.pdf"
        assert document.topic_id is None
        assert document.agent_id is None

    def test_document_update_empty(self):
        """Test DocumentUpdate with empty data."""
        data = {}
        document = DocumentUpdate(**data)

        assert document.original_filename is None
        assert document.topic_id is None
        assert document.agent_id is None

    def test_document_update_invalid_types(self):
        """Test that invalid field types raise validation errors."""
        # Invalid topic_id type
        with pytest.raises(ValidationError):
            DocumentUpdate(topic_id="not an int")

        # Invalid agent_id type
        with pytest.raises(ValidationError):
            DocumentUpdate(agent_id="not an int")
