"""Tests for Document and Topic services."""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest
from fastapi import UploadFile
from sqlalchemy.orm import Session

from dana.api.core.models import Document, Topic
from dana.api.core.schemas import DocumentCreate, DocumentUpdate, TopicCreate
from dana.api.services.document_service import DocumentService
from dana.api.services.topic_service import TopicService


@pytest.mark.skip(reason="FileStorageService merged into DocumentService during refactoring")
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

    @pytest.mark.asyncio
    async def test_create_topic(self, db_session: Session):
        """Test topic creation."""
        service = TopicService()
        topic_data = TopicCreate(name="Test Topic", description="A test topic")

        topic = await service.create_topic(topic_data, db_session)

        assert topic.id is not None
        assert topic.name == "Test Topic"
        assert topic.description == "A test topic"
        assert topic.created_at is not None
        assert topic.updated_at is not None

    @pytest.mark.asyncio
    async def test_get_topics(self, db_session: Session):
        """Test getting topics list."""
        service = TopicService()

        # Create some topics
        topic1 = Topic(name="Topic 1", description="First topic")
        topic2 = Topic(name="Topic 2", description="Second topic")
        db_session.add_all([topic1, topic2])
        db_session.commit()

        topics = await service.list_topics(limit=100, offset=0, search=None, db_session=db_session)
        assert len(topics) == 2
        assert topics[0].name == "Topic 1"
        assert topics[1].name == "Topic 2"

    @pytest.mark.asyncio
    async def test_get_topic(self, db_session: Session):
        """Test getting a specific topic."""
        service = TopicService()

        # Create a topic
        topic = Topic(name="Test Topic", description="A test topic")
        db_session.add(topic)
        db_session.commit()
        db_session.refresh(topic)

        retrieved_topic = await service.get_topic(int(topic.id), db_session)
        assert retrieved_topic is not None
        assert retrieved_topic.name == "Test Topic"

    @pytest.mark.asyncio
    async def test_get_topic_not_found(self, db_session: Session):
        """Test getting a non-existent topic."""
        service = TopicService()
        topic = await service.get_topic(999, db_session)
        assert topic is None

    @pytest.mark.asyncio
    async def test_update_topic(self, db_session: Session):
        """Test topic update."""
        service = TopicService()

        # Create a topic
        topic = Topic(name="Original Name", description="Original description")
        db_session.add(topic)
        db_session.commit()
        db_session.refresh(topic)

        # Update it
        update_data = TopicCreate(name="Updated Name", description="Updated description")
        updated_topic = await service.update_topic(int(topic.id), update_data, db_session)

        assert updated_topic is not None
        assert updated_topic.name == "Updated Name"
        assert updated_topic.description == "Updated description"

    @pytest.mark.asyncio
    async def test_delete_topic(self, db_session: Session):
        """Test topic deletion."""
        service = TopicService()

        # Create a topic
        topic = Topic(name="Test Topic", description="A test topic")
        db_session.add(topic)
        db_session.commit()
        db_session.refresh(topic)

        # Delete it
        success = await service.delete_topic(int(topic.id), db_session)
        assert success is True

        # Verify it's gone
        retrieved_topic = await service.get_topic(int(topic.id), db_session)
        assert retrieved_topic is None


@pytest.mark.skip(reason="DocumentService interface changed during refactoring - these tests are obsolete")
class TestDocumentService:
    """Test the DocumentService - DEPRECATED: Service interface completely changed."""
    pass
