"""
Document Service Module

This module provides business logic for document management and processing.
"""

import json
import logging
import os
import asyncio
from datetime import datetime, UTC
import uuid
from typing import BinaryIO
import shutil

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
        use_original_filename: bool = True,
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
                original_filename=document_data.original_filename if use_original_filename else actual_filename,
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

            # Ensure metadata is a dictionary, not a MetaData object
            metadata = document.doc_metadata
            if metadata is None:
                metadata = {}
            elif hasattr(metadata, '__dict__') and not isinstance(metadata, dict):
                # If it's a MetaData object or similar, convert to dict
                metadata = {}
            elif not isinstance(metadata, dict):
                # If it's not a dict, convert to empty dict
                metadata = {}

            print(metadata)
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
                metadata=metadata if metadata is not None else {},
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

            # Compute metadata
            file_extension = None
            if document.original_filename and '.' in document.original_filename:
                file_extension = document.original_filename.split('.')[-1].lower()

            file_size_mb = None
            if document.file_size:
                file_size_mb = round(document.file_size / (1024 * 1024), 2)

            is_extraction_file = document.source_document_id is not None

            days_since_created = None
            days_since_updated = None
            if document.created_at:
                # Ensure both datetimes are timezone-aware
                if document.created_at.tzinfo is None:
                    created_at_utc = document.created_at.replace(tzinfo=UTC)
                else:
                    created_at_utc = document.created_at.astimezone(UTC)
                days_since_created = (datetime.now(UTC) - created_at_utc).days
            if document.updated_at:
                # Ensure both datetimes are timezone-aware
                if document.updated_at.tzinfo is None:
                    updated_at_utc = document.updated_at.replace(tzinfo=UTC)
                else:
                    updated_at_utc = document.updated_at.astimezone(UTC)
                days_since_updated = (datetime.now(UTC) - updated_at_utc).days

            # Ensure metadata is a dictionary, not a MetaData object
            metadata = document.doc_metadata
            if metadata is None:
                metadata = {}
            elif hasattr(metadata, '__dict__') and not isinstance(metadata, dict):
                # If it's a MetaData object or similar, convert to dict
                metadata = {}
            elif not isinstance(metadata, dict):
                # If it's not a dict, convert to empty dict
                metadata = {}

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
                metadata=metadata,
                file_extension=file_extension,
                file_size_mb=file_size_mb,
                is_extraction_file=is_extraction_file,
                days_since_created=days_since_created,
                days_since_updated=days_since_updated,
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
        Also cleans up agent associations and agent folder files.

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

            # 🆕 STEP 1: Clean up agent associations before deletion
            affected_agents = await self._cleanup_agent_associations(document_id, db_session)
            logger.info(f"Cleaned up associations for document {document_id} from {len(affected_agents)} agents")

            # 🆕 STEP 2: Clean up agent folder files
            await self._cleanup_agent_folder_files(document, affected_agents, db_session)

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
    ) -> tuple[list[DocumentRead], int]:
        """
        List documents with optional filtering.

        Args:
            topic_id: Optional topic ID filter
            agent_id: Optional agent ID filter
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            db_session: Database session

        Returns:
            Tuple of (List of DocumentRead objects, total count)
        """
        try:
            query = db_session.query(Document)

            # Exclude documents that have source_document_id (extraction files)
            query = query.filter(Document.source_document_id.is_(None))

            if topic_id is not None:
                query = query.filter(Document.topic_id == topic_id)

            if agent_id is not None:
                # NOTE : THE ASSOCIATION IS STORED IN THE AGENT CONFIG FOR NOW. IN THE OLD APPROACH, WE CAN ONLY LINK DOCUMENT TO AN SINGLE AGENT (doc.agent_id = agent_id)
                agent = db_session.query(Agent).filter(Agent.id == agent_id).first()
                if agent:
                    associated_documents = agent.config.get("associated_documents", [])
                    query = query.filter(Document.id.in_(associated_documents))

            # Get total count before applying limit/offset
            total_count = query.count()

            documents = query.offset(offset).limit(limit).all()

            document_reads = []
            for doc in documents:
                # Compute metadata
                file_extension = None
                if doc.original_filename and '.' in doc.original_filename:
                    file_extension = doc.original_filename.split('.')[-1].lower()

                file_size_mb = None
                if doc.file_size:
                    file_size_mb = round(doc.file_size / (1024 * 1024), 2)

                is_extraction_file = doc.source_document_id is not None

                days_since_created = None
                days_since_updated = None
                if doc.created_at:
                    # Ensure both datetimes are timezone-aware
                    if doc.created_at.tzinfo is None:
                        created_at_utc = doc.created_at.replace(tzinfo=UTC)
                    else:
                        created_at_utc = doc.created_at.astimezone(UTC)
                    days_since_created = (datetime.now(UTC) - created_at_utc).days
                if doc.updated_at:
                    # Ensure both datetimes are timezone-aware
                    if doc.updated_at.tzinfo is None:
                        updated_at_utc = doc.updated_at.replace(tzinfo=UTC)
                    else:
                        updated_at_utc = doc.updated_at.astimezone(UTC)
                    days_since_updated = (datetime.now(UTC) - updated_at_utc).days

                # Ensure metadata is a dictionary, not a MetaData object
                metadata = doc.doc_metadata
                if metadata is None:
                    metadata = {
                        "upload_source": "api",
                        "processing_status": "completed",
                        "file_type": file_extension or "unknown",
                        "has_extraction": is_extraction_file,
                    }
                elif hasattr(metadata, '__dict__') and not isinstance(metadata, dict):
                    # If it's a MetaData object or similar, use default metadata
                    metadata = {
                        "upload_source": "api",
                        "processing_status": "completed",
                        "file_type": file_extension or "unknown",
                        "has_extraction": is_extraction_file,
                    }
                elif not isinstance(metadata, dict):
                    # If it's not a dict, use default metadata
                    metadata = {
                        "upload_source": "api",
                        "processing_status": "completed",
                        "file_type": file_extension or "unknown",
                        "has_extraction": is_extraction_file,
                    }

                document_reads.append(DocumentRead(
                    id=doc.id,
                    filename=doc.filename,
                    original_filename=doc.original_filename,
                    file_size=doc.file_size,
                    mime_type=doc.mime_type,
                    topic_id=doc.topic_id,
                    agent_id=doc.agent_id,
                    created_at=doc.created_at,
                    updated_at=doc.updated_at,
                    metadata=metadata,
                    file_extension=file_extension,
                    file_size_mb=file_size_mb,
                    is_extraction_file=is_extraction_file,
                    days_since_created=days_since_created,
                    days_since_updated=days_since_updated,
                ))

            return document_reads, total_count

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

    def get_agent_associated_fp(self, agent_folder_path: str, document_original_filename: str, convert_to_md: bool = False):
        """Get the associated file path for a document."""
        original_filename = os.path.splitext(document_original_filename)[0]
        if convert_to_md:
            destination_fp = os.path.join(agent_folder_path, "docs", f"{original_filename}.md")
        else:
            destination_fp = os.path.join(agent_folder_path, "docs", document_original_filename)
        os.makedirs(os.path.dirname(destination_fp), exist_ok=True)
        return destination_fp

    async def _cleanup_agent_associations(self, document_id: int, db_session) -> list[int]:
        """
        Remove document association from all agents.

        Args:
            document_id: The document ID to remove from associations
            db_session: Database session

        Returns:
            List of agent IDs that were affected
        """
        try:
            from dana.api.core.models import Agent
            from sqlalchemy.orm.attributes import flag_modified

            affected_agents = []
            agents = db_session.query(Agent).all()

            for agent in agents:
                if agent.config and "associated_documents" in agent.config:
                    associated_docs = agent.config["associated_documents"]
                    if document_id in associated_docs:
                        # Remove from agent's associated documents
                        agent.config["associated_documents"] = [doc_id for doc_id in associated_docs if doc_id != document_id]
                        flag_modified(agent, "config")
                        affected_agents.append(agent.id)
                        logger.info(f"Removed document {document_id} from agent {agent.id} associations")

            return affected_agents

        except Exception as e:
            logger.error(f"Error cleaning up agent associations for document {document_id}: {e}")
            raise

    async def _cleanup_agent_folder_files(self, document, affected_agent_ids: list[int], db_session):
        """
        Clean up files that were copied to agent folders.

        Args:
            document: The document object being deleted
            affected_agent_ids: List of agent IDs that had this document associated
            db_session: Database session
        """
        try:
            from dana.api.core.models import Agent
            from dana.api.routers.v1.agents import clear_agent_cache

            for agent_id in affected_agent_ids:
                agent = db_session.query(Agent).filter(Agent.id == agent_id).first()
                if not agent or not agent.config:
                    continue

                agent_folder_path = agent.config.get("folder_path")
                if not agent_folder_path:
                    continue

                # Remove the copied document file from agent folder
                for convert_to_md in [True, False]:
                    document_fp = self.get_agent_associated_fp(agent_folder_path, document.original_filename, convert_to_md)

                    if os.path.exists(document_fp):
                        try:
                            os.remove(document_fp)
                            logger.info(f"Removed document from agent folder: {document_fp}")
                        except Exception as file_error:
                            logger.warning(f"Could not remove document from agent folder {document_fp}: {file_error}")

                # Clear RAG cache for this agent
                try:
                    clear_agent_cache(agent_folder_path)
                    logger.info(f"Cleared RAG cache for agent {agent_id}")
                except Exception as cache_error:
                    logger.warning(f"Could not clear RAG cache for agent {agent_id}: {cache_error}")

        except Exception as e:
            logger.error(f"Error cleaning up agent folder files for document {document.id}: {e}")
            raise

    async def disassociate_document_from_all_agents(self, document_id: int, db_session) -> list[int]:
        """
        Remove document association from all agents without deleting the document.

        Args:
            document_id: The document ID to disassociate
            db_session: Database session

        Returns:
            List of agent IDs that were affected
        """
        try:
            from dana.api.core.models import Agent
            from sqlalchemy.orm.attributes import flag_modified

            affected_agents = []
            agents = db_session.query(Agent).all()

            for agent in agents:
                if agent.config and "associated_documents" in agent.config:
                    associated_docs = agent.config["associated_documents"]
                    if document_id in associated_docs:
                        # Remove from agent's associated documents
                        agent.config["associated_documents"] = [doc_id for doc_id in associated_docs if doc_id != document_id]
                        flag_modified(agent, "config")
                        affected_agents.append(agent.id)
                        logger.info(f"Disassociated document {document_id} from agent {agent.id}")

            if affected_agents:
                db_session.commit()
                logger.info(f"Disassociated document {document_id} from {len(affected_agents)} agents")

            return affected_agents

        except Exception as e:
            logger.error(f"Error disassociating document {document_id} from all agents: {e}")
            raise

    async def get_agents_with_document(self, document_id: int, db_session) -> list[int]:
        """
        Get all agent IDs that have a specific document associated.

        Args:
            document_id: The document ID to check
            db_session: Database session

        Returns:
            List of agent IDs that have this document associated
        """
        try:
            from dana.api.core.models import Agent

            agents_with_document = []
            agents = db_session.query(Agent).all()

            for agent in agents:
                if agent.config and "associated_documents" in agent.config:
                    associated_docs = agent.config["associated_documents"]
                    if document_id in associated_docs:
                        agents_with_document.append(agent.id)

            return agents_with_document

        except Exception as e:
            logger.error(f"Error getting agents with document {document_id}: {e}")
            raise

    async def check_document_exists(self, original_filename: str, db_session) -> DocumentRead | None:
        """
        Check if a document with the given original filename already exists.

        Args:
            original_filename: The original filename to check
            db_session: Database session

        Returns:
            DocumentRead object if document exists, None otherwise
        """
        try:
            document = db_session.query(Document).filter(Document.original_filename == original_filename).first()
            if not document:
                return None

            return DocumentRead.model_validate(document)

        except Exception as e:
            logger.error(f"Error checking if document exists with filename {original_filename}: {e}")
            raise

    async def associate_documents_with_agent(
        self, agent_id: int, agent_folder_path: str, document_ids: list[int], db_session, convert_to_md: bool = False
    ) -> list[str]:
        """
        Associate documents with an agent.
        """
        try:
            # 🆕 STEP 1: Validate documents exist
            documents = db_session.query(Document).filter(Document.id.in_(document_ids)).all()
            existing_ids = {doc.id for doc in documents}
            missing_ids = set(document_ids) - existing_ids

            if missing_ids:
                raise ValueError(f"Documents not found: {missing_ids}")

            new_destination_fps = []
            for document in documents:
                document.agent_id = agent_id
                extraction_files = document.extraction_files
                if extraction_files:
                    if convert_to_md:
                        final_md = ""
                        for extraction_file in extraction_files:
                            extract_fp = os.path.join(self.upload_directory, extraction_file.file_path)
                            with open(extract_fp) as f:
                                extract_data = json.load(f)
                            for extraction_doc in extract_data["documents"]:
                                final_md += extraction_doc["text"]
                                final_md += "\n\n"
                        final_md = final_md.strip()
                        if final_md:
                            destination_fp = self.get_agent_associated_fp(agent_folder_path, document.original_filename)
                            with open(destination_fp, "w") as f:
                                f.write(final_md)
                            new_destination_fps.append(destination_fp)
                    else:
                        destination_fp = self.get_agent_associated_fp(
                            agent_folder_path, document.original_filename, convert_to_md=convert_to_md
                        )
                        shutil.copy(document.file_path, destination_fp)
                        new_destination_fps.append(destination_fp)

                else:
                    logger.warning(f"Document {document.id} {document.original_filename} failed to associated with agent {agent_id}")

            if len(new_destination_fps) > 0:
                db_session.commit()

            return new_destination_fps

        except Exception as e:
            logger.error(f"Error associating documents with agent {agent_id}: {e}", exc_info=True)
            raise


# Global service instance
_document_service: DocumentService | None = None


def get_document_service() -> DocumentService:
    """Get or create the global document service instance."""
    global _document_service
    if _document_service is None:
        _document_service = DocumentService()
    return _document_service
