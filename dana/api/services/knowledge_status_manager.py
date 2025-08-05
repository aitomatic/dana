import os
import json
import asyncio
import uuid
from datetime import datetime


class KnowledgeStatusManager:
    """
    Manages the knowledge_status.json file for an agent.
    Handles atomic read/write, topic status updates, and deduplication.
    """

    def __init__(self, status_path: str, agent_id: str | None = None):
        self.status_path = status_path
        self.agent_id = agent_id
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.status_path):
            initial_data = {"topics": []}
            if self.agent_id is not None:
                initial_data["agent_id"] = self.agent_id
            self._atomic_write(initial_data)
        else:
            # Update existing file with agent_id if missing
            if self.agent_id is not None:
                data = self.load()
                if "agent_id" not in data:
                    data["agent_id"] = self.agent_id
                    self.save(data)

    def _atomic_write(self, data):
        tmp_path = self.status_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, self.status_path)

    def load(self) -> dict:
        with open(self.status_path, encoding="utf-8") as f:
            return json.load(f)

    def save(self, data: dict):
        self._atomic_write(data)

    def get_agent_id(self) -> str | None:
        """Get the agent_id from the status file."""
        try:
            data = self.load()
            return data.get("agent_id")
        except Exception:
            return None

    def get_topic_entry(self, path: str) -> dict | None:
        data = self.load()
        for entry in data["topics"]:
            if entry["path"] == path:
                return entry
        return None

    def add_or_update_topic_by_uuid(
        self, topic_id: str, topic_name: str, path: str, file: str, last_topic_update: str, status: str = "pending"
    ):
        """Add or update topic using UUID reference"""
        data = self.load()

        # Find entry by topic_id
        entry = None
        for topic in data["topics"]:
            if topic.get("topic_id") == topic_id:
                entry = topic
                break

        if entry:
            # Update existing entry
            entry["topic_name"] = topic_name
            entry["path"] = path
            entry["file"] = file
            entry["last_topic_update"] = last_topic_update
            if status is not None and status != "preserve_existing":
                entry["status"] = status
        else:
            # Create new entry with UUID reference
            final_status = "pending" if status == "preserve_existing" else status
            data["topics"].append(
                {
                    "id": str(uuid.uuid4()),
                    "topic_id": topic_id,
                    "topic_name": topic_name,
                    "path": path,
                    "file": file,
                    "status": final_status,
                    "last_generated": None,
                    "last_topic_update": last_topic_update,
                    "error": None,
                }
            )
        self.save(data)

    def get_entry_by_topic_uuid(self, topic_id: str) -> dict | None:
        """Get status entry by topic UUID"""
        data = self.load()
        for entry in data["topics"]:
            if entry.get("topic_id") == topic_id:
                return entry
        return None

    def remove_topics_by_uuids(self, topic_ids: list[str]):
        """Remove multiple topics by their UUIDs"""
        data = self.load()
        topic_ids_set = set(topic_ids)

        # Filter out entries with matching topic_ids
        data["topics"] = [entry for entry in data.get("topics", []) if entry.get("topic_id") not in topic_ids_set]

        self.save(data)

    def add_or_update_topic(self, path: str, file: str, last_topic_update: str, status: str = "pending"):
        data = self.load()
        # Find entry in the loaded data instead of calling get_topic_entry
        entry = None
        for topic in data["topics"]:
            if topic["path"] == path:
                entry = topic
                break

        if entry:
            entry["file"] = file
            entry["last_topic_update"] = last_topic_update
            # Only set status if it's not None and not a special preserve indicator
            if status is not None and status != "preserve_existing":
                entry["status"] = status
            elif entry.get("status") is None:
                # If current status is null and no explicit status provided, set to pending
                entry["status"] = "pending"
        else:
            # For new topics, use the provided status (defaulting to "pending")
            final_status = "pending" if status == "preserve_existing" else status
            data["topics"].append(
                {
                    "id": str(uuid.uuid4()),
                    "path": path,
                    "file": file,
                    "status": final_status,
                    "last_generated": None,
                    "last_topic_update": last_topic_update,
                    "error": None,
                }
            )
        self.save(data)

    def set_status(self, path: str, status: str, error: str | None = None):
        data = self.load()
        for entry in data["topics"]:
            if entry["path"] == path:
                entry["status"] = status
                if status == "success":
                    entry["last_generated"] = datetime.utcnow().isoformat() + "Z"
                    entry["error"] = None
                elif status == "failed":
                    entry["error"] = error
                break
        self.save(data)

    def remove_topic(self, path: str):
        data = self.load()
        data["topics"] = [entry for entry in data["topics"] if entry["path"] != path]
        self.save(data)

    def get_pending_or_failed(self) -> list[dict]:
        data = self.load()
        return [entry for entry in data["topics"] if entry["status"] in ("pending", "failed")]

    def get_in_progress(self) -> list[dict]:
        data = self.load()
        return [entry for entry in data["topics"] if entry["status"] == "in_progress"]

    def is_in_progress(self, path: str) -> bool:
        entry = self.get_topic_entry(path)
        return entry and entry["status"] == "in_progress"

    def is_success(self, path: str) -> bool:
        entry = self.get_topic_entry(path)
        return entry and entry["status"] == "success"

    def get_pending_failed_or_null(self) -> list[dict]:
        """
        Returns all topics with status 'pending', 'failed', or None (not set).
        """
        data = self.load()
        return [entry for entry in data["topics"] if entry.get("status") in ("pending", "failed", None)]

    def recover_stuck_in_progress(self, max_age_seconds=3600):
        """
        Resets topics stuck in 'in_progress' for more than max_age_seconds (default 1 hour) to 'pending'.
        Also resets topics with status None (null) to 'pending'.
        Prints when a topic is reset.
        """
        from datetime import datetime

        data = self.load()
        updated = False
        for entry in data["topics"]:
            if entry.get("status") is None:
                print(f"[status_manager] Resetting null-status topic: {entry['path']} to pending")
                entry["status"] = "pending"
                entry["error"] = None
                updated = True
            elif entry["status"] == "in_progress":
                last_time = entry.get("last_generated") or entry.get("last_topic_update")
                if last_time:
                    try:
                        t = datetime.fromisoformat(last_time.replace("Z", ""))
                        age = (datetime.utcnow() - t).total_seconds()
                        if age > max_age_seconds:
                            print(f"[status_manager] Recovering stuck topic: {entry['path']} (was in_progress for {age / 60:.1f} min)")
                            entry["status"] = "pending"
                            entry["error"] = None
                            updated = True
                    except Exception:
                        continue
        if updated:
            self.save(data)

    def retry_failed_topics(self):
        """
        Sets all topics with status 'failed' back to 'pending' for retry.
        """
        data = self.load()
        updated = False
        for entry in data["topics"]:
            if entry["status"] == "failed":
                entry["status"] = "pending"
                entry["error"] = None
                updated = True
        if updated:
            self.save(data)


class KnowledgeGenerationManager:
    """
    Manages the asyncio queue and worker pool for knowledge generation.
    Uses KnowledgeStatusManager for status tracking and deduplication.
    Broadcasts status changes via WebSocket.
    Provides error recovery and retry logic.
    """

    def __init__(
        self,
        status_manager: KnowledgeStatusManager,
        max_concurrent: int = 4,
        ws_manager=None,
        topic: str = "General Topic",
        role: str = "Domain Expert",
        knows_folder: str = "knows",
    ):
        self.status_manager = status_manager
        self.queue = asyncio.Queue()
        self.in_progress = set()
        self.max_concurrent = max_concurrent
        self.workers = []
        self.running = False
        self.ws_manager = ws_manager  # Should have .broadcast(topic_id, status) or similar
        self.topic = topic
        self.role = role
        self.knows_folder = knows_folder

    async def _broadcast_status(self, topic_entry, status):
        """
        Broadcasts a status update for a topic via WebSocket manager (if available).
        """
        if self.ws_manager:
            msg = {
                "type": "knowledge_status_update",
                "topic_id": topic_entry.get("id"),
                "path": topic_entry.get("path"),
                "status": status,
            }
            await self.ws_manager.broadcast(msg)

    async def worker(self):
        while True:
            topic_entry = await self.queue.get()
            if topic_entry is None:
                break
            path = topic_entry["path"]
            if path in self.in_progress:
                self.queue.task_done()
                continue
            self.in_progress.add(path)
            self.status_manager.set_status(path, "in_progress")
            await self._broadcast_status(topic_entry, "in_progress")
            print(f"[KNOWLEDGE GEN] Set status to in_progress for {path}")
            try:
                await self.generate_knowledge_for_topic(topic_entry)
                self.status_manager.set_status(path, "success")
                await self._broadcast_status(topic_entry, "success")
                print(f"[KNOWLEDGE GEN] Set status to success for {path}")
            except Exception as e:
                self.status_manager.set_status(path, "failed", error=str(e))
                await self._broadcast_status(topic_entry, "failed")
                print(f"[KNOWLEDGE GEN] Set status to failed for {path}: {e}")
            finally:
                self.in_progress.remove(path)
                self.queue.task_done()

    async def generate_knowledge_for_topic(self, topic_entry):
        """
        Generate knowledge for a specific topic using ManagerAgent and save as JSON.
        """
        import os
        import json
        from dana.frameworks.knows.corral.curate_general_kb.py.manager_agent import (
            ManagerAgent,
        )

        print(f"[KNOWLEDGE GEN] Generating for {topic_entry['path']}")

        # Parse area_name and key_topics
        area_name = topic_entry["path"]
        # Use path parts as key topics (or customize as needed)
        key_topics = [part.strip() for part in area_name.split(" - ")]

        # Get agent information from status manager if agent_id is available
        agent_id = self.status_manager.get_agent_id()
        topic = getattr(self, "topic", "General Topic")
        role = getattr(self, "role", "Domain Expert")

        if agent_id:
            try:
                # Try to get agent info from database
                from dana.api.core.database import get_db_session
                from dana.api.core.models import Agent

                with get_db_session() as db:
                    agent = db.query(Agent).filter(Agent.id == int(agent_id)).first()
                    if agent:
                        topic = agent.name or topic
                        role = agent.description or role
                        print(f"[KNOWLEDGE GEN] Using agent info - Topic: {topic}, Role: {role}")
            except Exception as e:
                print(f"[KNOWLEDGE GEN] Could not fetch agent info for agent_id {agent_id}: {e}")

        # Create ManagerAgent instance
        manager_agent = ManagerAgent(topic, role)
        # Run in executor to avoid blocking event loop
        loop = asyncio.get_event_loop()
        knowledge = await loop.run_in_executor(None, manager_agent.generate_knowledge_for_area, area_name, key_topics)
        # Save knowledge to JSON file in knows folder
        knows_folder = os.path.dirname(self.status_manager.status_path)
        file_path = os.path.join(knows_folder, topic_entry["file"])
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(knowledge, f, indent=2, ensure_ascii=False)
        print(f"[KNOWLEDGE GEN] Saved knowledge to: {file_path}")

    async def add_topic(self, topic_entry):
        path = topic_entry["path"]
        if (
            not self.status_manager.is_in_progress(path)
            and not self.status_manager.is_success(path)
            and path not in self.in_progress
            and topic_entry not in self.queue._queue
        ):
            await self.queue.put(topic_entry)
            self.status_manager.set_status(path, "in_progress")
            await self._broadcast_status(topic_entry, "in_progress")

    async def run(self):
        if self.running:
            return
        self.running = True
        self.workers = [asyncio.create_task(self.worker()) for _ in range(self.max_concurrent)]
        await self.queue.join()
        for _ in self.workers:
            await self.queue.put(None)
        await asyncio.gather(*self.workers)
        self.running = False

    def recover_stuck_in_progress(self, max_age_seconds=3600):
        """
        Resets topics stuck in 'in_progress' for more than max_age_seconds (default 1 hour) to 'pending'.
        Also resets topics with status None (null) to 'pending'.
        Prints when a topic is reset.
        """
        from datetime import datetime

        data = self.status_manager.load()
        updated = False
        for entry in data["topics"]:
            if entry.get("status") is None:
                print(f"[status_manager] Resetting null-status topic: {entry['path']} to pending")
                entry["status"] = "pending"
                entry["error"] = None
                updated = True
            elif entry["status"] == "in_progress":
                last_time = entry.get("last_generated") or entry.get("last_topic_update")
                if last_time:
                    try:
                        t = datetime.fromisoformat(last_time.replace("Z", ""))
                        age = (datetime.utcnow() - t).total_seconds()
                        if age > max_age_seconds:
                            print(f"[status_manager] Recovering stuck topic: {entry['path']} (was in_progress for {age / 60:.1f} min)")
                            entry["status"] = "pending"
                            entry["error"] = None
                            updated = True
                    except Exception:
                        continue
        if updated:
            self.status_manager.save(data)

    def retry_failed_topics(self):
        """
        Sets all topics with status 'failed' back to 'pending' for retry.
        """
        data = self.status_manager.load()
        updated = False
        for entry in data["topics"]:
            if entry["status"] == "failed":
                entry["status"] = "pending"
                entry["error"] = None
                updated = True
        if updated:
            self.status_manager.save(data)


"""
Sample usage:

status_path = 'agents/agent_8/knows/knowledge_status.json'
status_manager = KnowledgeStatusManager(status_path, agent_id="8")
manager = KnowledgeGenerationManager(status_manager, max_concurrent=4)

# Add topics to status file and queue
status_manager.add_or_update_topic('Finance/Market Analysis/Technical Analysis', 'Finance_Market_Analysis_Technical_Analysis.json', '2024-07-01T12:00:00Z')

pending = status_manager.get_pending_or_failed()

async def main():
    for entry in pending:
        await manager.add_topic(entry)
    await manager.run()

# asyncio.run(main())
"""
