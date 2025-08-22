"""
Agent Deletion Service for handling comprehensive agent cleanup operations.
"""

import logging
import shutil
from pathlib import Path
from sqlalchemy.orm import Session

from dana.api.core.models import Agent, Document, Conversation, AgentChatHistory

logger = logging.getLogger(__name__)


class AgentDeletionService:
    """
    Service for handling comprehensive agent deletion operations.

    Handles:
    - Database cleanup (agent, documents, conversations, chat history)
    - File system cleanup (agent folders, document files)
    - Error handling and rollback
    - Logging and audit trail
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def delete_agent_comprehensive(self, agent_id: int, db: Session, force: bool = False) -> dict:
        """
        Comprehensive agent deletion with all associated resources cleanup.

        Args:
            agent_id: The ID of the agent to delete
            db: Database session
            force: If True, skip confirmation checks

        Returns:
            dict: Result message and metadata

        Raises:
            HTTPException: If agent not found or deletion fails
        """
        try:
            # Get agent
            db_agent = db.query(Agent).filter(Agent.id == agent_id).first()
            if not db_agent:
                raise ValueError(f"Agent with ID {agent_id} not found")

            self.logger.info(f"Starting comprehensive deletion of agent {agent_id}: {db_agent.name}")

            # Get agent folder path for cleanup
            agent_folder_path = None
            if db_agent.config and "folder_path" in db_agent.config:
                agent_folder_path = db_agent.config["folder_path"]

            # Track deletion statistics
            deletion_stats = {
                "agent_id": agent_id,
                "agent_name": db_agent.name,
                "documents_deleted": 0,
                "conversations_deleted": 0,
                "chat_history_deleted": 0,
                "files_deleted": 0,
                "folder_deleted": False,
            }

            # Delete associated documents
            try:
                documents = db.query(Document).filter(Document.agent_id == agent_id).all()
                for document in documents:
                    # Delete physical file if it exists
                    if document.file_path and Path(document.file_path).exists():
                        Path(document.file_path).unlink()
                        deletion_stats["files_deleted"] += 1
                        self.logger.info(f"Deleted document file: {document.file_path}")
                    db.delete(document)
                deletion_stats["documents_deleted"] = len(documents)
                self.logger.info(f"Deleted {len(documents)} documents for agent {agent_id}")
            except Exception as e:
                self.logger.warning(f"Error deleting documents for agent {agent_id}: {e}")

            # Delete associated conversations and messages (cascade will handle messages)
            try:
                conversations = db.query(Conversation).filter(Conversation.agent_id == agent_id).all()
                for conversation in conversations:
                    db.delete(conversation)
                deletion_stats["conversations_deleted"] = len(conversations)
                self.logger.info(f"Deleted {len(conversations)} conversations for agent {agent_id}")
            except Exception as e:
                self.logger.warning(f"Error deleting conversations for agent {agent_id}: {e}")

            # Delete associated chat history
            try:
                chat_history = db.query(AgentChatHistory).filter(AgentChatHistory.agent_id == agent_id).all()
                for chat_entry in chat_history:
                    db.delete(chat_entry)
                deletion_stats["chat_history_deleted"] = len(chat_history)
                self.logger.info(f"Deleted {len(chat_history)} chat history entries for agent {agent_id}")
            except Exception as e:
                self.logger.warning(f"Error deleting chat history for agent {agent_id}: {e}")

            # Delete agent folder and files
            if agent_folder_path:
                try:
                    agent_folder = Path(agent_folder_path)
                    if agent_folder.exists():
                        shutil.rmtree(agent_folder)
                        deletion_stats["folder_deleted"] = True
                        self.logger.info(f"Deleted agent folder: {agent_folder_path}")
                    else:
                        self.logger.info(f"Agent folder not found: {agent_folder_path}")
                except Exception as e:
                    self.logger.warning(f"Error deleting agent folder {agent_folder_path}: {e}")

            # Delete the agent from database
            db.delete(db_agent)
            db.commit()

            self.logger.info(f"Successfully deleted agent {agent_id}: {db_agent.name}")

            return {"message": "Agent deleted successfully", "deletion_stats": deletion_stats}

        except Exception as e:
            self.logger.error(f"Error deleting agent {agent_id}: {e}")
            db.rollback()
            raise e

    async def soft_delete_agent(self, agent_id: int, db: Session) -> dict:
        """
        Soft delete an agent by marking it as deleted without removing files.

        Args:
            agent_id: The ID of the agent to soft delete
            db: Database session

        Returns:
            dict: Result message
        """
        try:
            db_agent = db.query(Agent).filter(Agent.id == agent_id).first()
            if not db_agent:
                raise ValueError(f"Agent with ID {agent_id} not found")

            # Mark agent as deleted in config
            if not db_agent.config:
                db_agent.config = {}

            db_agent.config["deleted"] = True
            db_agent.config["deleted_at"] = str(Path().cwd() / "deleted_agents" / f"agent_{agent_id}")

            db.commit()

            self.logger.info(f"Soft deleted agent {agent_id}: {db_agent.name}")
            return {"message": "Agent soft deleted successfully"}

        except Exception as e:
            self.logger.error(f"Error soft deleting agent {agent_id}: {e}")
            db.rollback()
            raise e

    async def cleanup_orphaned_files(self, db: Session) -> dict:
        """
        Clean up orphaned files that don't have corresponding database records.

        Args:
            db: Database session

        Returns:
            dict: Cleanup statistics
        """
        try:
            cleanup_stats = {"orphaned_files_removed": 0, "orphaned_folders_removed": 0}

            # Get all document file paths from database
            documents = db.query(Document).all()

            # Handle path inconsistencies: main documents store absolute paths, extraction files store relative paths
            db_file_paths = set()
            for doc in documents:
                if doc.file_path:
                    if doc.source_document_id is not None:
                        # Extraction files store relative paths, need to join with upload directory
                        db_file_paths.add(str(Path("uploads") / doc.file_path))
                    else:
                        # Main documents store absolute paths
                        db_file_paths.add(doc.file_path)

            # Check for orphaned files in common document directories
            document_dirs = ["uploads", "documents", "files"]

            for doc_dir in document_dirs:
                doc_path = Path(doc_dir)
                if doc_path.exists():
                    for file_path in doc_path.rglob("*"):
                        if file_path.is_file() and str(file_path) not in db_file_paths:
                            try:
                                file_path.unlink()
                                cleanup_stats["orphaned_files_removed"] += 1
                                self.logger.info(f"Removed orphaned file: {file_path}")
                            except Exception as e:
                                self.logger.warning(f"Failed to remove orphaned file {file_path}: {e}")

            # Check for orphaned agent folders
            agents_dir = Path("agents")
            if agents_dir.exists():
                for agent_folder in agents_dir.iterdir():
                    if agent_folder.is_dir():
                        # Check if this folder corresponds to an existing agent
                        folder_name = agent_folder.name
                        if folder_name.startswith("agent_"):
                            try:
                                agent_id = int(folder_name.split("_")[1])
                                agent_exists = db.query(Agent).filter(Agent.id == agent_id).first()
                                if not agent_exists:
                                    shutil.rmtree(agent_folder)
                                    cleanup_stats["orphaned_folders_removed"] += 1
                                    self.logger.info(f"Removed orphaned agent folder: {agent_folder}")
                            except (ValueError, IndexError):
                                # Skip folders that don't follow the naming convention
                                pass

            self.logger.info(f"Cleanup completed: {cleanup_stats}")
            return cleanup_stats

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            raise e


# Dependency injection function
def get_agent_deletion_service() -> AgentDeletionService:
    """Get agent deletion service instance."""
    return AgentDeletionService()
