"""
Document Service Module

This module provides business logic for document management and processing.
"""

import logging
import os
import asyncio
from datetime import datetime, UTC
import uuid
from typing import BinaryIO

from dana.api.core.models import Document, Agent
from dana.api.core.schemas import DocumentCreate, DocumentRead, DocumentUpdate
from dana.common.sys_resource.rag.rag_resource import RAGResource

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
        self,
        file: BinaryIO,
        filename: str,
        topic_id: int | None = None,
        agent_id: int | None = None,
        db_session=None,
        upload_directory: str | None = None,
        build_index: bool = True,
    ) -> DocumentRead:
        """
        Upload and store a document.

        Args:
            file: The file binary data
            filename: Original filename
            topic_id: Optional topic ID to associate with
            agent_id: Optional agent ID to associate with
            db_session: Database session
            upload_directory: Optional directory to store the file (overrides default)
            build_index: Whether to build RAG index immediately after upload

        Returns:
            DocumentRead object with the stored document information
        """
        try:
            # Use original filename, handle conflicts by appending timestamp/counter
            target_dir = upload_directory if upload_directory else self.upload_directory
            os.makedirs(target_dir, exist_ok=True)

            # Try original filename first
            file_path = os.path.join(target_dir, filename)

            # If file exists, append timestamp to avoid conflicts
            if os.path.exists(file_path):
                name_without_ext, file_extension = os.path.splitext(filename)
                timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
                filename_with_timestamp = f"{name_without_ext}_{timestamp}{file_extension}"
                file_path = os.path.join(target_dir, filename_with_timestamp)

                # If still exists (very rare), add UUID as fallback
                if os.path.exists(file_path):
                    unique_id = str(uuid.uuid4())[:8]
                    filename_with_uuid = f"{name_without_ext}_{timestamp}_{unique_id}{file_extension}"
                    file_path = os.path.join(target_dir, filename_with_uuid)

            # Save file to disk
            with open(file_path, "wb") as f:
                content = file.read()
                f.write(content)
                file_size = len(content)

            # Determine MIME type
            mime_type = self._get_mime_type(filename)

            # Get the actual filename that was used (could be modified due to conflicts)
            actual_filename = os.path.basename(file_path)

            # Create document record
            document_data = DocumentCreate(original_filename=filename, topic_id=topic_id, agent_id=agent_id)

            document = Document(
                filename=actual_filename,
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

            # Build RAG index immediately after successful upload
            if build_index and agent_id:
                asyncio.create_task(self._build_index_for_agent(agent_id, file_path, db_session))
                logger.info(f"Started background index building for agent {agent_id} with document {filename}")

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
        Delete a document and its related extraction files.

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

            import os

            # First, find and delete any extraction files that reference this document
            extraction_files = db_session.query(Document).filter(Document.source_document_id == document_id).all()

            if extraction_files:
                logger.info("Found %d extraction files to delete for document %d", len(extraction_files), document_id)
                for extraction_file in extraction_files:
                    # Delete extraction file from disk
                    if extraction_file.file_path:
                        # Extraction files store relative paths, so always join with upload directory
                        file_path = os.path.join(self.upload_directory, extraction_file.file_path)

                        if os.path.exists(file_path):
                            try:
                                os.remove(file_path)
                                logger.info("Deleted extraction file: %s", file_path)
                            except Exception as file_error:
                                logger.warning("Could not delete extraction file %s: %s", file_path, file_error)
                        else:
                            logger.warning("Extraction file not found: %s", file_path)

                    # Delete extraction file database record
                    db_session.delete(extraction_file)

                logger.info("Deleted %d extraction files for document %d", len(extraction_files), document_id)

            # Delete the main document file from disk
            if document.file_path:
                # Main documents store absolute paths, so use as-is
                file_path = document.file_path

                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info("Deleted main document file: %s", file_path)
                else:
                    logger.warning("Main document file not found: %s", file_path)

            # Delete the main document database record
            db_session.delete(document)
            db_session.commit()

            logger.info("Successfully deleted document %d and %d related extraction files", document_id, len(extraction_files))
            return True

        except Exception as e:
            logger.error("Error deleting document %d: %s", document_id, e)
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

            # Exclude documents that have source_document_id (extraction files)
            query = query.filter(Document.source_document_id.is_(None))

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

    async def _build_index_for_agent(self, agent_id: int, file_path: str, db_session) -> None:
        """
        Build RAG index for an agent's documents in the background.

        Args:
            agent_id: The agent ID
            file_path: Path to the newly uploaded file
            db_session: Database session (create new session for background task)
        """
        try:
            logger.info(f"Building index for agent {agent_id} with new document {file_path}")

            # Get agent configuration to determine folder path
            from sqlalchemy.orm import sessionmaker
            from dana.api.core.database import engine

            # Create new session for background task
            SessionLocal = sessionmaker(bind=engine)
            with SessionLocal() as session:
                agent = session.query(Agent).filter(Agent.id == agent_id).first()
                if not agent:
                    logger.error(f"Agent {agent_id} not found for index building")
                    return

                # Get or create agent folder path and cache directory
                folder_path = agent.config.get("folder_path") if agent.config else None
                if not folder_path:
                    folder_path = os.path.join("agents", f"agent_{agent.id}")

                # Update agent config with folder path if not set
                if not agent.config or not agent.config.get("folder_path"):
                    config = dict(agent.config) if agent.config else {}
                    config["folder_path"] = folder_path
                    agent.config = config
                    session.commit()

                # Ensure folder exists
                os.makedirs(folder_path, exist_ok=True)

                # Get all document paths for this agent
                agent_documents = session.query(Document).filter(Document.agent_id == agent_id).all()
                source_paths = [doc.file_path for doc in agent_documents if doc.file_path and os.path.exists(doc.file_path)]

                if not source_paths:
                    logger.warning(f"No valid documents found for agent {agent_id}")
                    return

                logger.info(f"Building RAG index for agent {agent_id} with {len(source_paths)} documents")

                # Create agent-specific cache directory
                cache_dir = os.path.abspath(os.path.join(folder_path, ".cache/rag"))

                # Create RAG resource with force_reload to rebuild index
                rag_resource = RAGResource(
                    sources=source_paths,
                    name=f"agent_{agent_id}_rag",
                    cache_dir=cache_dir,
                    force_reload=True,  # Force rebuild to include new document
                    debug=True,
                )

                # Initialize the RAG resource (this builds the index)
                await rag_resource.initialize()

                logger.info(f"Successfully built RAG index for agent {agent_id}")

        except Exception as e:
            logger.error(f"Error building index for agent {agent_id}: {e}", exc_info=True)


# Global service instance
_document_service: DocumentService | None = None


def get_document_service() -> DocumentService:
    """Get or create the global document service instance."""
    global _document_service
    if _document_service is None:
        _document_service = DocumentService()
    return _document_service
