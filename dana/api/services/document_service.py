"""
Document Service Module

This module provides business logic for document management and processing.
"""

import logging
import os
from datetime import datetime, UTC
import uuid
from typing import BinaryIO

from dana.api.core.models import Document
from dana.api.core.schemas import DocumentCreate, DocumentRead, DocumentUpdate

logger = logging.getLogger(__name__)


class DocumentService:
    """
    Service for handling document operations and file management.
    """

    def __init__(self, upload_directory: str = "./uploads"):
        """
        Initialize the document service.

        Args:
            upload_directory: Directory where uploaded files will be stored
        """
        self.upload_directory = upload_directory
        os.makedirs(upload_directory, exist_ok=True)

    async def upload_document(
        self, file: BinaryIO, filename: str, topic_id: int | None = None, agent_id: int | None = None, db_session=None
    ) -> DocumentRead:
        """
        Upload and store a document.

        Args:
            file: The file binary data
            filename: Original filename
            topic_id: Optional topic ID to associate with
            agent_id: Optional agent ID to associate with
            db_session: Database session

        Returns:
            DocumentRead object with the stored document information
        """
        try:
            # Generate unique filename
            file_extension = os.path.splitext(filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = os.path.join(self.upload_directory, unique_filename)

            # Save file to disk
            with open(file_path, "wb") as f:
                content = file.read()
                f.write(content)
                file_size = len(content)

            # Determine MIME type
            mime_type = self._get_mime_type(filename)

            # Create document record
            document_data = DocumentCreate(original_filename=filename, topic_id=topic_id, agent_id=agent_id)

            document = Document(
                filename=unique_filename,
                original_filename=document_data.original_filename,
                file_path=file_path,
                file_size=file_size,
                mime_type=mime_type,
                topic_id=document_data.topic_id,
                agent_id=document_data.agent_id,
            )

            if db_session:
                db_session.add(document)
                db_session.commit()
                db_session.refresh(document)

            return DocumentRead(
                id=document.id,
                filename=document.filename,
                original_filename=document.original_filename,
                file_size=document.file_size,
                mime_type=document.mime_type,
                topic_id=document.topic_id,
                agent_id=document.agent_id,
                created_at=document.created_at,
                updated_at=document.updated_at,
            )

        except Exception as e:
            logger.error(f"Error uploading document: {e}")
            raise

    async def get_document(self, document_id: int, db_session) -> DocumentRead | None:
        """
        Get a document by ID.

        Args:
            document_id: The document ID
            db_session: Database session

        Returns:
            DocumentRead object or None if not found
        """
        try:
            document = db_session.query(Document).filter(Document.id == document_id).first()
            if not document:
                return None

            return DocumentRead(
                id=document.id,
                filename=document.filename,
                original_filename=document.original_filename,
                file_size=document.file_size,
                mime_type=document.mime_type,
                topic_id=document.topic_id,
                agent_id=document.agent_id,
                created_at=document.created_at,
                updated_at=document.updated_at,
            )

        except Exception as e:
            logger.error(f"Error getting document {document_id}: {e}")
            raise

    async def update_document(self, document_id: int, document_data: DocumentUpdate, db_session) -> DocumentRead | None:
        """
        Update a document.

        Args:
            document_id: The document ID
            document_data: Document update data
            db_session: Database session

        Returns:
            DocumentRead object or None if not found
        """
        try:
            document = db_session.query(Document).filter(Document.id == document_id).first()
            if not document:
                return None

            # Update fields if provided
            if document_data.original_filename is not None:
                document.original_filename = document_data.original_filename
            if document_data.topic_id is not None:
                document.topic_id = document_data.topic_id
            if document_data.agent_id is not None:
                document.agent_id = document_data.agent_id

            # Update timestamp
            document.updated_at = datetime.now(UTC)

            db_session.commit()
            db_session.refresh(document)

            return DocumentRead(
                id=document.id,
                filename=document.filename,
                original_filename=document.original_filename,
                file_size=document.file_size,
                mime_type=document.mime_type,
                topic_id=document.topic_id,
                agent_id=document.agent_id,
                created_at=document.created_at,
                updated_at=document.updated_at,
            )

        except Exception as e:
            logger.error(f"Error updating document {document_id}: {e}")
            raise

    async def delete_document(self, document_id: int, db_session) -> bool:
        """
        Delete a document.

        Args:
            document_id: The document ID
            db_session: Database session

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            document = db_session.query(Document).filter(Document.id == document_id).first()
            if not document:
                return False

            # Delete file from disk
            import os

            if document.file_path and os.path.exists(document.file_path):
                os.remove(document.file_path)

            # Delete database record
            db_session.delete(document)
            db_session.commit()

            return True

        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            raise

    async def list_documents(
        self, topic_id: int | None = None, agent_id: int | None = None, limit: int = 100, offset: int = 0, db_session=None
    ) -> list[DocumentRead]:
        """
        List documents with optional filtering.

        Args:
            topic_id: Optional topic ID filter
            agent_id: Optional agent ID filter
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            db_session: Database session

        Returns:
            List of DocumentRead objects
        """
        try:
            query = db_session.query(Document)

            if topic_id is not None:
                query = query.filter(Document.topic_id == topic_id)
            if agent_id is not None:
                query = query.filter(Document.agent_id == agent_id)

            documents = query.offset(offset).limit(limit).all()

            return [
                DocumentRead(
                    id=doc.id,
                    filename=doc.filename,
                    original_filename=doc.original_filename,
                    file_size=doc.file_size,
                    mime_type=doc.mime_type,
                    topic_id=doc.topic_id,
                    agent_id=doc.agent_id,
                    created_at=doc.created_at,
                    updated_at=doc.updated_at,
                )
                for doc in documents
            ]

        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            raise

    async def get_file_path(self, document_id: int, db_session) -> str | None:
        """
        Get the file path for a document.

        Args:
            document_id: The document ID
            db_session: Database session

        Returns:
            File path string or None if not found
        """
        try:
            document = db_session.query(Document).filter(Document.id == document_id).first()
            if not document:
                return None

            return document.file_path

        except Exception as e:
            logger.error(f"Error getting file path for document {document_id}: {e}")
            raise

    def _get_mime_type(self, filename: str) -> str:
        """
        Determine MIME type from filename extension.

        Args:
            filename: The filename

        Returns:
            MIME type string
        """
        extension = os.path.splitext(filename)[1].lower()

        mime_map = {
            ".pdf": "application/pdf",
            ".txt": "text/plain",
            ".md": "text/markdown",
            ".doc": "application/msword",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".csv": "text/csv",
            ".json": "application/json",
            ".xml": "application/xml",
        }

        return mime_map.get(extension, "application/octet-stream")


# Global service instance
_document_service: DocumentService | None = None


def get_document_service() -> DocumentService:
    """Get or create the global document service instance."""
    global _document_service
    if _document_service is None:
        _document_service = DocumentService()
    return _document_service
