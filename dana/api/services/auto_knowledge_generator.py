"""
Auto Knowledge Generator Service

This service automatically triggers knowledge generation for newly added topics
and manages the generation process to prevent duplicates and handle "Generate all knowledge" requests.
"""

import asyncio
import logging
from datetime import datetime, UTC
import os

from dana.api.services.knowledge_status_manager import KnowledgeStatusManager, KnowledgeGenerationManager

logger = logging.getLogger(__name__)


class AutoKnowledgeGenerator:
    """
    Manages automatic knowledge generation for newly added topics.

    Features:
    - Automatically generates knowledge for newly added topics
    - Prevents duplicate generation runs
    - Handles "Generate all knowledge" requests
    - Manages generation queue and status tracking
    - Provides generation status and progress tracking
    """

    def __init__(self, agent_id: int, folder_path: str, max_concurrent: int = 4):
        self.agent_id = agent_id
        self.folder_path = folder_path
        self.knows_folder = os.path.join(folder_path, "knows")
        self.status_path = os.path.join(self.knows_folder, "knowledge_status.json")
        self.max_concurrent = max_concurrent

        # Ensure directories exist
        os.makedirs(self.knows_folder, exist_ok=True)

        # Get WebSocket manager for real-time updates
        try:
            from dana.api.server.server import ws_manager

            self.ws_manager = ws_manager
        except ImportError:
            logger.warning("WebSocket manager not available for real-time updates")
            self.ws_manager = None

        # Initialize managers
        self.status_manager = KnowledgeStatusManager(self.status_path, agent_id=str(agent_id))
        self.generation_manager = KnowledgeGenerationManager(
            status_manager=self.status_manager,
            max_concurrent=max_concurrent,
            ws_manager=self.ws_manager,
            topic="General Topic",
            role="Domain Expert",
            knows_folder=self.knows_folder,
        )

        # Track running generation tasks
        self._running_generation_task: asyncio.Task | None = None
        self._generation_lock = asyncio.Lock()

        logger.info(f"AutoKnowledgeGenerator initialized for agent {agent_id}")

    async def generate_for_new_topics(self, new_topics: list[str]) -> dict[str, any]:
        """
        Automatically generate knowledge for newly added topics.

        Args:
            new_topics: List of topic paths that were newly added

        Returns:
            dict with generation status and details
        """
        if not new_topics:
            return {"success": True, "message": "No new topics to generate", "topics_generated": [], "topics_skipped": []}

        logger.info(f"Auto-generating knowledge for {len(new_topics)} new topics: {new_topics}")

        async with self._generation_lock:
            # Check which topics need generation
            topics_to_generate = []
            topics_skipped = []

            for topic_path in new_topics:
                # Check if topic already exists and has successful generation
                if self.status_manager.is_success(topic_path):
                    topics_skipped.append({"topic": topic_path, "reason": "Already generated successfully"})
                    continue

                # Check if topic is already in progress
                if self.status_manager.is_in_progress(topic_path):
                    topics_skipped.append({"topic": topic_path, "reason": "Already in progress"})
                    continue

                # Get topic entry from status manager
                topic_entry = self.status_manager.get_topic_entry(topic_path)
                if topic_entry:
                    topics_to_generate.append(topic_entry)
                else:
                    # Topic not in status file, create new entry
                    logger.info(f"Creating new topic entry for: {topic_path}")
                    # Generate filename from path
                    filename = topic_path.replace(" - ", "_").replace(" ", "_").replace("/", "_") + ".json"
                    # Add to status manager
                    self.status_manager.add_or_update_topic(
                        path=topic_path, file=filename, last_topic_update=datetime.now(UTC).isoformat(), status="pending"
                    )
                    # Get the newly created entry
                    topic_entry = self.status_manager.get_topic_entry(topic_path)
                    if topic_entry:
                        topics_to_generate.append(topic_entry)

                        # Broadcast status update via WebSocket
                        if self.ws_manager:
                            try:
                                await self.ws_manager.broadcast(
                                    {
                                        "type": "knowledge_status_update",
                                        "topic_id": topic_entry.get("id"),
                                        "path": topic_entry.get("path"),
                                        "status": "pending",
                                    }
                                )
                                logger.info(f"Broadcasted pending status for topic: {topic_path}")
                            except Exception as e:
                                logger.warning(f"Failed to broadcast status update: {e}")

            if not topics_to_generate:
                return {"success": True, "message": "No topics need generation", "topics_generated": [], "topics_skipped": topics_skipped}

            # Start generation for new topics
            try:
                # Add topics to generation queue
                for topic_entry in topics_to_generate:
                    await self.generation_manager.add_topic(topic_entry)

                # Start generation manager if not already running
                if not self._running_generation_task or self._running_generation_task.done():
                    self._running_generation_task = asyncio.create_task(self._run_generation_manager())

                return {
                    "success": True,
                    "message": f"Started generation for {len(topics_to_generate)} topics",
                    "topics_generated": [entry["path"] for entry in topics_to_generate],
                    "topics_skipped": topics_skipped,
                    "generation_task_id": id(self._running_generation_task),
                }

            except Exception as e:
                logger.error(f"Error starting generation for new topics: {e}")
                return {
                    "success": False,
                    "message": f"Error starting generation: {str(e)}",
                    "topics_generated": [],
                    "topics_skipped": topics_skipped,
                }

    async def generate_all_knowledge(self) -> dict[str, any]:
        """
        Generate knowledge for all pending/failed topics.

        Returns:
            dict with generation status and details
        """
        logger.info(f"Starting generation for all pending/failed topics for agent {self.agent_id}")

        async with self._generation_lock:
            try:
                # Get all pending and failed topics
                pending_topics = self.status_manager.get_pending_failed_or_null()

                if not pending_topics:
                    return {
                        "success": True,
                        "message": "No pending or failed topics to generate",
                        "topics_generated": [],
                        "total_topics": 0,
                    }

                logger.info(f"Found {len(pending_topics)} pending/failed topics to generate")

                # Add all topics to generation queue
                for topic_entry in pending_topics:
                    await self.generation_manager.add_topic(topic_entry)

                # Start generation manager if not already running
                if not self._running_generation_task or self._running_generation_task.done():
                    self._running_generation_task = asyncio.create_task(self._run_generation_manager())

                return {
                    "success": True,
                    "message": f"Started generation for {len(pending_topics)} topics",
                    "topics_generated": [entry["path"] for entry in pending_topics],
                    "total_topics": len(pending_topics),
                    "generation_task_id": id(self._running_generation_task),
                }

            except Exception as e:
                logger.error(f"Error starting generation for all topics: {e}")
                return {"success": False, "message": f"Error starting generation: {str(e)}", "topics_generated": [], "total_topics": 0}

    async def _run_generation_manager(self):
        """
        Run the generation manager in the background.
        """
        try:
            logger.info(f"Starting generation manager for agent {self.agent_id}")
            await self.generation_manager.run()
            logger.info(f"Generation manager completed for agent {self.agent_id}")
        except Exception as e:
            logger.error(f"Error in generation manager for agent {self.agent_id}: {e}")

    def get_generation_status(self) -> dict[str, any]:
        """
        Get the current status of knowledge generation.

        Returns:
            dict with generation status information
        """
        try:
            # Load status data
            status_data = self.status_manager.load()

            # Count topics by status
            status_counts = {}
            for entry in status_data.get("topics", []):
                status = entry.get("status", "unknown")
                status_counts[status] = status_counts.get(status, 0) + 1

            # Check if generation is running
            is_running = self._running_generation_task is not None and not self._running_generation_task.done()

            return {
                "agent_id": self.agent_id,
                "is_generation_running": is_running,
                "total_topics": len(status_data.get("topics", [])),
                "status_counts": status_counts,
                "topics": status_data.get("topics", []),
                "last_updated": datetime.now(UTC).isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting generation status: {e}")
            return {"agent_id": self.agent_id, "error": str(e), "is_generation_running": False}

    def stop_generation(self) -> dict[str, any]:
        """
        Stop the current generation process.

        Returns:
            dict with stop status
        """
        try:
            if self._running_generation_task and not self._running_generation_task.done():
                self._running_generation_task.cancel()
                logger.info(f"Stopped generation for agent {self.agent_id}")
                return {"success": True, "message": "Generation stopped successfully"}
            else:
                return {"success": True, "message": "No generation was running"}
        except Exception as e:
            logger.error(f"Error stopping generation: {e}")
            return {"success": False, "message": f"Error stopping generation: {str(e)}"}

    def retry_failed_topics(self) -> dict[str, any]:
        """
        Retry all failed topics.

        Returns:
            dict with retry status
        """
        try:
            self.status_manager.retry_failed_topics()
            failed_count = len([entry for entry in self.status_manager.load()["topics"] if entry.get("status") == "failed"])

            logger.info(f"Retried failed topics for agent {self.agent_id}")
            return {"success": True, "message": f"Retried {failed_count} failed topics", "failed_topics_count": failed_count}
        except Exception as e:
            logger.error(f"Error retrying failed topics: {e}")
            return {"success": False, "message": f"Error retrying failed topics: {str(e)}"}

    def recover_stuck_topics(self, max_age_seconds: int = 3600) -> dict[str, any]:
        """
        Recover topics stuck in 'in_progress' status.

        Args:
            max_age_seconds: Maximum age in seconds before considering a topic stuck

        Returns:
            dict with recovery status
        """
        try:
            self.status_manager.recover_stuck_in_progress(max_age_seconds)
            logger.info(f"Recovered stuck topics for agent {self.agent_id}")
            return {"success": True, "message": f"Recovered stuck topics (max age: {max_age_seconds}s)"}
        except Exception as e:
            logger.error(f"Error recovering stuck topics: {e}")
            return {"success": False, "message": f"Error recovering stuck topics: {str(e)}"}


# Global registry to track generators per agent
_agent_generators: dict[int, AutoKnowledgeGenerator] = {}


def get_auto_knowledge_generator(agent_id: int, folder_path: str) -> AutoKnowledgeGenerator:
    """
    Get or create an AutoKnowledgeGenerator for the specified agent.

    Args:
        agent_id: The agent ID
        folder_path: The agent's folder path

    Returns:
        AutoKnowledgeGenerator instance
    """
    if agent_id not in _agent_generators:
        _agent_generators[agent_id] = AutoKnowledgeGenerator(agent_id, folder_path)

    return _agent_generators[agent_id]


def remove_agent_generator(agent_id: int):
    """
    Remove an agent's generator from the registry.

    Args:
        agent_id: The agent ID
    """
    if agent_id in _agent_generators:
        generator = _agent_generators[agent_id]
        generator.stop_generation()
        del _agent_generators[agent_id]
        logger.info(f"Removed generator for agent {agent_id}")


def get_all_generators() -> dict[int, AutoKnowledgeGenerator]:
    """
    Get all active generators.

    Returns:
        dict of agent_id -> AutoKnowledgeGenerator
    """
    return _agent_generators.copy()
