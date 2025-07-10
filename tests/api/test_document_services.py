"""Tests for Document and Topic services."""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest
from fastapi import UploadFile
from sqlalchemy.orm import Session

from dana.api.server.models import Document, Topic
from dana.api.server.schemas import DocumentCreate, DocumentUpdate, TopicCreate
from dana.api.server.services import DocumentService, FileStorageService, TopicService


class TestFileStorageService:
    """Test the FileStorageService."""

    @pytest.fixture
    def temp_upload_dir(self):
        """Create a temporary upload directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def file_storage(self, temp_upload_dir):
        """Create FileStorageService with temporary directory."""
        return FileStorageService(upload_dir=temp_upload_dir)

    @pytest.fixture
    def mock_upload_file(self):
        """Create a mock UploadFile."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.size = 1024
        mock_file.file = Mock()
        return mock_file

    def test_file_storage_init(self, temp_upload_dir):
        """Test FileStorageService initialization."""
        storage = FileStorageService(upload_dir=temp_upload_dir)
        assert storage.upload_dir == Path(temp_upload_dir)
        assert storage.max_file_size == 50 * 1024 * 1024
        assert ".pdf" in storage.allowed_extensions

    def test_validate_file_valid(self, file_storage, mock_upload_file):
        """Test file validation with valid file."""
        # Should not raise any exception
        file_storage.validate_file(mock_upload_file)

    def test_validate_file_too_large(self, file_storage, mock_upload_file):
        """Test file validation with file too large."""
        mock_upload_file.size = 100 * 1024 * 1024  # 100MB
        with pytest.raises(Exception) as exc_info:
            file_storage.validate_file(mock_upload_file)
        assert "File too large" in str(exc_info.value)

    def test_validate_file_invalid_extension(self, file_storage, mock_upload_file):
        """Test file validation with invalid file extension."""
        mock_upload_file.filename = "test.exe"
        with pytest.raises(Exception) as exc_info:
            file_storage.validate_file(mock_upload_file)
        assert "File type not allowed" in str(exc_info.value)

    def test_validate_file_no_filename(self, file_storage, mock_upload_file):
        """Test file validation with no filename."""
        mock_upload_file.filename = None
        with pytest.raises(Exception) as exc_info:
            file_storage.validate_file(mock_upload_file)
        assert "Filename is required" in str(exc_info.value)

    def test_save_file(self, file_storage, mock_upload_file):
        """Test file saving."""
        # Create a proper mock file object that works with copyfileobj
        from io import BytesIO
        mock_file_content = b"test content"
        mock_file_obj = BytesIO(mock_file_content)
        mock_upload_file.file = mock_file_obj

        filename, file_path, file_size = file_storage.save_file(mock_upload_file)

        assert filename.endswith(".pdf")
        assert file_size == len(mock_file_content)
        assert Path(file_storage.upload_dir) / file_path in Path(file_storage.upload_dir).rglob("*.pdf")

    def test_get_file_path(self, file_storage):
        """Test getting file path from relative path."""
        relative_path = "2025/01/27/test.pdf"
        file_path = file_storage.get_file_path(relative_path)
        expected_path = file_storage.upload_dir / relative_path
        assert file_path == expected_path

    def test_delete_file(self, file_storage, mock_upload_file):
        """Test file deletion."""
        # Create a proper mock file object that works with copyfileobj
        from io import BytesIO
        mock_file_content = b"test content"
        mock_file_obj = BytesIO(mock_file_content)
        mock_upload_file.file = mock_file_obj
        
        # First save a file
        filename, file_path, file_size = file_storage.save_file(mock_upload_file)

        # Then delete it
        success = file_storage.delete_file(file_path)
        assert success is True

        # Verify file is gone
        full_path = file_storage.get_file_path(file_path)
        assert not full_path.exists()


class TestTopicService:
    """Test the TopicService."""

    def test_create_topic(self, db_session: Session):
        """Test topic creation."""
        service = TopicService()
        topic_data = TopicCreate(name="Test Topic", description="A test topic")

        topic = service.create_topic(db_session, topic_data)

        assert topic.id is not None
        assert topic.name == "Test Topic"
        assert topic.description == "A test topic"
        assert topic.created_at is not None
        assert topic.updated_at is not None

    def test_get_topics(self, db_session: Session):
        """Test getting topics list."""
        service = TopicService()

        # Create some topics
        topic1 = Topic(name="Topic 1", description="First topic")
        topic2 = Topic(name="Topic 2", description="Second topic")
        db_session.add_all([topic1, topic2])
        db_session.commit()

        topics = service.get_topics(db_session)
        assert len(topics) == 2
        assert topics[0].name == "Topic 1"
        assert topics[1].name == "Topic 2"

    def test_get_topic(self, db_session: Session):
        """Test getting a specific topic."""
        service = TopicService()

        # Create a topic
        topic = Topic(name="Test Topic", description="A test topic")
        db_session.add(topic)
        db_session.commit()
        db_session.refresh(topic)

        retrieved_topic = service.get_topic(db_session, int(topic.id))
        assert retrieved_topic is not None
        assert retrieved_topic.name == "Test Topic"

    def test_get_topic_not_found(self, db_session: Session):
        """Test getting a non-existent topic."""
        service = TopicService()
        topic = service.get_topic(db_session, 999)
        assert topic is None

    def test_update_topic(self, db_session: Session):
        """Test topic update."""
        service = TopicService()

        # Create a topic
        topic = Topic(name="Original Name", description="Original description")
        db_session.add(topic)
        db_session.commit()
        db_session.refresh(topic)

        # Update it
        update_data = TopicCreate(name="Updated Name", description="Updated description")
        updated_topic = service.update_topic(db_session, int(topic.id), update_data)

        assert updated_topic is not None
        assert updated_topic.name == "Updated Name"
        assert updated_topic.description == "Updated description"

    def test_delete_topic(self, db_session: Session):
        """Test topic deletion."""
        service = TopicService()

        # Create a topic
        topic = Topic(name="Test Topic", description="A test topic")
        db_session.add(topic)
        db_session.commit()
        db_session.refresh(topic)

        # Delete it
        success = service.delete_topic(db_session, int(topic.id))
        assert success is True

        # Verify it's gone
        retrieved_topic = service.get_topic(db_session, int(topic.id))
        assert retrieved_topic is None


class TestDocumentService:
    """Test the DocumentService."""

    @pytest.fixture
    def temp_upload_dir(self):
        """Create a temporary upload directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def document_service(self, temp_upload_dir):
        """Create DocumentService with temporary storage."""
        file_storage = FileStorageService(upload_dir=temp_upload_dir)
        return DocumentService(file_storage)

    @pytest.fixture
    def mock_upload_file(self):
        """Create a mock UploadFile."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.size = 1024
        mock_file.file = Mock()
        return mock_file

    def test_create_document(self, db_session: Session, document_service, mock_upload_file):
        """Test document creation."""
        # Create a proper mock file object that works with copyfileobj
        from io import BytesIO
        mock_file_content = b"test content"
        mock_file_obj = BytesIO(mock_file_content)
        mock_upload_file.file = mock_file_obj
        
        document_data = DocumentCreate(original_filename="test.pdf", topic_id=None, agent_id=None)

        document = document_service.create_document(db_session, mock_upload_file, document_data)

        assert document.id is not None
        assert document.original_filename == "test.pdf"
        assert document.filename.endswith(".pdf")
        assert document.file_size == len(mock_file_content)
        assert document.mime_type == "application/pdf"
        assert document.topic_id is None
        assert document.agent_id is None

    def test_get_documents(self, db_session: Session, document_service):
        """Test getting documents list."""
        # Create some documents
        doc1 = Document(
            filename="test1.pdf",
            original_filename="test1.pdf",
            file_path="2025/01/27/test1.pdf",
            file_size=1024,
            mime_type="application/pdf",
        )
        doc2 = Document(
            filename="test2.pdf",
            original_filename="test2.pdf",
            file_path="2025/01/27/test2.pdf",
            file_size=2048,
            mime_type="application/pdf",
        )
        db_session.add_all([doc1, doc2])
        db_session.commit()

        documents = document_service.get_documents(db_session)
        assert len(documents) == 2
        assert documents[0].original_filename == "test1.pdf"
        assert documents[1].original_filename == "test2.pdf"

    def test_get_documents_with_topic_filter(self, db_session: Session, document_service):
        """Test getting documents filtered by topic."""
        # Create a topic
        topic = Topic(name="Test Topic", description="A test topic")
        db_session.add(topic)
        db_session.commit()
        db_session.refresh(topic)

        # Create documents with and without topic
        doc1 = Document(
            filename="test1.pdf",
            original_filename="test1.pdf",
            file_path="2025/01/27/test1.pdf",
            file_size=1024,
            mime_type="application/pdf",
            topic_id=topic.id,
        )
        doc2 = Document(
            filename="test2.pdf",
            original_filename="test2.pdf",
            file_path="2025/01/27/test2.pdf",
            file_size=2048,
            mime_type="application/pdf",
        )
        db_session.add_all([doc1, doc2])
        db_session.commit()

        # Get documents with topic filter
        documents = document_service.get_documents(db_session, topic_id=topic.id)
        assert len(documents) == 1
        assert documents[0].original_filename == "test1.pdf"

    def test_get_document(self, db_session: Session, document_service):
        """Test getting a specific document."""
        # Create a document
        document = Document(
            filename="test.pdf", original_filename="test.pdf", file_path="2025/01/27/test.pdf", file_size=1024, mime_type="application/pdf"
        )
        db_session.add(document)
        db_session.commit()
        db_session.refresh(document)

        retrieved_document = document_service.get_document(db_session, document.id)
        assert retrieved_document is not None
        assert retrieved_document.original_filename == "test.pdf"

    def test_update_document(self, db_session: Session, document_service):
        """Test document update."""
        # Create a document
        document = Document(
            filename="test.pdf",
            original_filename="original.pdf",
            file_path="2025/01/27/test.pdf",
            file_size=1024,
            mime_type="application/pdf",
        )
        db_session.add(document)
        db_session.commit()
        db_session.refresh(document)

        # Update it
        update_data = DocumentUpdate(original_filename="updated.pdf")
        updated_document = document_service.update_document(db_session, document.id, update_data)

        assert updated_document is not None
        assert updated_document.original_filename == "updated.pdf"

    def test_delete_document(self, db_session: Session, document_service):
        """Test document deletion."""
        # Create a document
        document = Document(
            filename="test.pdf", original_filename="test.pdf", file_path="2025/01/27/test.pdf", file_size=1024, mime_type="application/pdf"
        )
        db_session.add(document)
        db_session.commit()
        db_session.refresh(document)

        # Delete it
        success = document_service.delete_document(db_session, document.id)
        assert success is True

        # Verify it's gone
        retrieved_document = document_service.get_document(db_session, document.id)
        assert retrieved_document is None

    def test_get_file_path(self, db_session: Session, document_service):
        """Test getting file path for download."""
        # Create a document
        document = Document(
            filename="test.pdf", original_filename="test.pdf", file_path="2025/01/27/test.pdf", file_size=1024, mime_type="application/pdf"
        )
        db_session.add(document)
        db_session.commit()
        db_session.refresh(document)

        file_path = document_service.get_file_path(document.id, db_session)
        assert file_path is not None
        assert file_path.name == "test.pdf"
