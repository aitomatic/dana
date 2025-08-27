"""
Topic Service Module

This module provides business logic for topic management and categorization.
"""

import logging
from typing import Any
from datetime import datetime, UTC

from dana.api.core.models import Topic
from dana.api.core.schemas import TopicCreate, TopicRead

logger = logging.getLogger(__name__)


class TopicService:
    """
    Service for handling topic operations and categorization management.
    """

    def __init__(self):
        """Initialize the topic service."""
        pass

    async def create_topic(self, topic_data: TopicCreate, db_session) -> TopicRead:
        """
        Create a new topic.

        Args:
            topic_data: Topic creation data
            db_session: Database session

        Returns:
            TopicRead object with the created topic
        """
        try:
            # Check if topic with same name already exists
            existing_topic = db_session.query(Topic).filter(Topic.name == topic_data.name).first()

            if existing_topic:
                raise ValueError(f"Topic with name '{topic_data.name}' already exists")

            topic = Topic(name=topic_data.name, description=topic_data.description)

            db_session.add(topic)
            db_session.commit()
            db_session.refresh(topic)

            return TopicRead(
                id=topic.id, name=topic.name, description=topic.description, created_at=topic.created_at, updated_at=topic.updated_at
            )

        except Exception as e:
            logger.error(f"Error creating topic: {e}")
            raise

    async def get_topic(self, topic_id: int, db_session) -> TopicRead | None:
        """
        Get a topic by ID.

        Args:
            topic_id: The topic ID
            db_session: Database session

        Returns:
            TopicRead object or None if not found
        """
        try:
            topic = db_session.query(Topic).filter(Topic.id == topic_id).first()

            if not topic:
                return None

            return TopicRead(
                id=topic.id, name=topic.name, description=topic.description, created_at=topic.created_at, updated_at=topic.updated_at
            )

        except Exception as e:
            logger.error(f"Error getting topic {topic_id}: {e}")
            raise

    async def get_topic_by_name(self, name: str, db_session) -> TopicRead | None:
        """
        Get a topic by name.

        Args:
            name: The topic name
            db_session: Database session

        Returns:
            TopicRead object or None if not found
        """
        try:
            topic = db_session.query(Topic).filter(Topic.name == name).first()

            if not topic:
                return None

            return TopicRead(
                id=topic.id, name=topic.name, description=topic.description, created_at=topic.created_at, updated_at=topic.updated_at
            )

        except Exception as e:
            logger.error(f"Error getting topic by name '{name}': {e}")
            raise

    async def list_topics(self, limit: int = 100, offset: int = 0, search: str | None = None, db_session=None) -> list[TopicRead]:
        """
        List topics with optional search filtering.

        Args:
            limit: Maximum number of topics to return
            offset: Number of topics to skip
            search: Optional search term to filter by name
            db_session: Database session

        Returns:
            List of TopicRead objects
        """
        try:
            query = db_session.query(Topic)

            if search:
                query = query.filter(Topic.name.ilike(f"%{search}%"))

            topics = query.offset(offset).limit(limit).all()

            return [
                TopicRead(
                    id=topic.id, name=topic.name, description=topic.description, created_at=topic.created_at, updated_at=topic.updated_at
                )
                for topic in topics
            ]

        except Exception as e:
            logger.error(f"Error listing topics: {e}")
            raise

    async def update_topic(self, topic_id: int, topic_data: TopicCreate, db_session) -> TopicRead | None:
        """
        Update a topic.

        Args:
            topic_id: The topic ID
            topic_data: Topic update data
            db_session: Database session

        Returns:
            TopicRead object or None if not found
        """
        try:
            topic = db_session.query(Topic).filter(Topic.id == topic_id).first()
            if not topic:
                return None

            # Check if new name conflicts with existing topic
            if topic_data.name != topic.name:
                existing_topic = db_session.query(Topic).filter(Topic.name == topic_data.name, Topic.id != topic_id).first()

                if existing_topic:
                    raise ValueError(f"Topic with name '{topic_data.name}' already exists")

            # Update fields
            topic.name = topic_data.name
            topic.description = topic_data.description

            # Update timestamp
            topic.updated_at = datetime.now(UTC)

            db_session.commit()
            db_session.refresh(topic)

            return TopicRead(
                id=topic.id, name=topic.name, description=topic.description, created_at=topic.created_at, updated_at=topic.updated_at
            )

        except Exception as e:
            logger.error(f"Error updating topic {topic_id}: {e}")
            raise

    async def delete_topic(self, topic_id: int, db_session, force: bool = False) -> bool:
        """
        Delete a topic.

        Args:
            topic_id: The topic ID
            db_session: Database session
            force: If True, delete associated documents first

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            topic = db_session.query(Topic).filter(Topic.id == topic_id).first()

            if not topic:
                return False

            # Check if topic has associated documents
            from dana.api.core.models import Document
            import os

            documents = db_session.query(Document).filter(Document.topic_id == topic_id).all()

            if documents:
                if not force:
                    raise ValueError(f"Cannot delete topic '{topic.name}' because it has {len(documents)} associated documents")

                # Force delete: remove associated documents first
                logger.info(f"Force deleting {len(documents)} documents associated with topic '{topic.name}'")

                # Import DocumentService to use its delete method which handles extraction files
                from dana.api.services.document_service import DocumentService

                document_service = DocumentService()

                for document in documents:
                    # Use document service delete method which handles extraction files cascade
                    try:
                        await document_service.delete_document(document.id, db_session)
                        logger.info(f"Deleted document {document.id} and its extraction files")
                    except Exception as doc_error:
                        logger.warning(f"Could not delete document {document.id}: {doc_error}")
                        # Fallback to manual deletion
                        if document.file_path and os.path.exists(document.file_path):
                            try:
                                os.remove(document.file_path)
                                logger.info(f"Manually deleted file: {document.file_path}")
                            except Exception as file_error:
                                logger.warning(f"Could not delete file {document.file_path}: {file_error}")
                        db_session.delete(document)

                logger.info(f"Deleted {len(documents)} documents for topic '{topic.name}'")

            # Delete the topic
            db_session.delete(topic)
            db_session.commit()

            logger.info(f"Successfully deleted topic '{topic.name}' (ID: {topic_id})")
            return True

        except Exception as e:
            logger.error(f"Error deleting topic {topic_id}: {e}")
            raise

    async def get_topic_statistics(self, topic_id: int, db_session) -> dict[str, Any]:
        """
        Get statistics for a topic.

        Args:
            topic_id: The topic ID
            db_session: Database session

        Returns:
            Dictionary with topic statistics
        """
        try:
            topic = db_session.query(Topic).filter(Topic.id == topic_id).first()

            if not topic:
                return {}

            # Count associated documents
            from dana.api.core.models import Document

            document_count = db_session.query(Document).filter(Document.topic_id == topic_id).count()

            return {
                "topic_id": topic_id,
                "topic_name": topic.name,
                "document_count": document_count,
                "created_at": topic.created_at,
                "updated_at": topic.updated_at,
            }

        except Exception as e:
            logger.error(f"Error getting topic statistics for {topic_id}: {e}")
            raise


# Global service instance
_topic_service: TopicService | None = None


def get_topic_service() -> TopicService:
    """Get or create the global topic service instance."""
    global _topic_service
    if _topic_service is None:
        _topic_service = TopicService()
    return _topic_service
