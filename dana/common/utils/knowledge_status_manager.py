import os
import json
import asyncio
import uuid
from datetime import datetime
from typing import List, Dict, Optional
import time

class KnowledgeStatusManager:
    """
    Manages the knowledge_status.json file for an agent.
    Handles atomic read/write, topic status updates, and deduplication.
    """
    def __init__(self, status_path: str):
        self.status_path = status_path
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.status_path):
            self._atomic_write({"topics": []})

    def _atomic_write(self, data):
        tmp_path = self.status_path + '.tmp'
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, self.status_path)

    def load(self) -> Dict:
        with open(self.status_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save(self, data: Dict):
        self._atomic_write(data)

    def get_topic_entry(self, path: str) -> Optional[Dict]:
        data = self.load()
        for entry in data["topics"]:
            if entry["path"] == path:
                return entry
        return None

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
            # Set status if provided, or if current status is null/None, set to pending
            if status is not None:
                entry["status"] = status
            elif entry.get("status") is None:
                entry["status"] = "pending"
        else:
            data["topics"].append({
                "id": str(uuid.uuid4()),
                "path": path,
                "file": file,
                "status": status,
                "last_generated": None,
                "last_topic_update": last_topic_update,
                "error": None
            })
        self.save(data)

    def set_status(self, path: str, status: str, error: Optional[str] = None):
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

    def get_pending_or_failed(self) -> List[Dict]:
        data = self.load()
        return [entry for entry in data["topics"] if entry["status"] in ("pending", "failed")]

    def get_in_progress(self) -> List[Dict]:
        data = self.load()
        return [entry for entry in data["topics"] if entry["status"] == "in_progress"]

    def is_in_progress(self, path: str) -> bool:
        entry = self.get_topic_entry(path)
        return entry and entry["status"] == "in_progress"

    def is_success(self, path: str) -> bool:
        entry = self.get_topic_entry(path)
        return entry and entry["status"] == "success"

class KnowledgeGenerationManager:
    """
    Manages the asyncio queue and worker pool for knowledge generation.
    Uses KnowledgeStatusManager for status tracking and deduplication.
    Broadcasts status changes via WebSocket.
    Provides error recovery and retry logic.
    """
    def __init__(self, status_manager: KnowledgeStatusManager, max_concurrent: int = 4, ws_manager=None, 
                 topic: str = "General Topic", role: str = "Domain Expert", knows_folder: str = "knows"):
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
            self._broadcast_status(topic_entry, "in_progress")
            try:
                await self.generate_knowledge_for_topic(topic_entry)
                self.status_manager.set_status(path, "success")
                self._broadcast_status(topic_entry, "success")
            except Exception as e:
                self.status_manager.set_status(path, "failed", error=str(e))
                self._broadcast_status(topic_entry, "failed")
            finally:
                self.in_progress.remove(path)
                self.queue.task_done()

    async def generate_knowledge_for_topic(self, topic_entry):
        """Generate knowledge for a specific topic using ManagerAgent."""
        try:
            from dana.frameworks.knows.corral.curate_general_kb.py.manager_agent import ManagerAgent
            
            # Extract the area name and create key topics from the path
            area_name = topic_entry["path"]
            # Parse the path to extract key topics (e.g., "Manufacturing Processes - etching process - Types of Etching")
            path_parts = area_name.split(" - ")
            key_topics = [part.strip() for part in path_parts]
            
            print(f"[KnowledgeGeneration] Generating knowledge for area: {area_name}")
            print(f"[KnowledgeGeneration] Key topics: {key_topics}")
            
            # Create ManagerAgent instance
            manager_agent = ManagerAgent(self.topic, self.role)
            
            # Generate knowledge for this area
            loop = asyncio.get_event_loop()
            knowledge = await loop.run_in_executor(
                None, 
                manager_agent.generate_knowledge_for_area, 
                area_name, 
                key_topics
            )
            
            # Save knowledge to JSON file in the knows folder
            import os
            file_path = os.path.join(self.knows_folder, topic_entry["file"])
            
            # Ensure knows folder exists
            os.makedirs(self.knows_folder, exist_ok=True)
            
            # Save the knowledge as JSON
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(knowledge, f, indent=2, ensure_ascii=False)
                
            print(f"[KnowledgeGeneration] Successfully saved knowledge to: {file_path}")
            
        except Exception as e:
            print(f"[KnowledgeGeneration] Error generating knowledge for {topic_entry['path']}: {e}")
            raise e

    async def add_topic(self, topic_entry):
        path = topic_entry["path"]
        if (not self.status_manager.is_in_progress(path)
            and not self.status_manager.is_success(path)
            and path not in self.in_progress
            and topic_entry not in self.queue._queue):
            await self.queue.put(topic_entry)
            self.status_manager.set_status(path, "in_progress")
            self._broadcast_status(topic_entry, "in_progress")

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

    def _broadcast_status(self, topic_entry, status):
        """
        Broadcasts a status update for a topic via WebSocket manager (if available).
        """
        if self.ws_manager:
            msg = {
                "type": "knowledge_status_update",
                "topic_id": topic_entry.get("id"),
                "path": topic_entry.get("path"),
                "status": status
            }
            self.ws_manager.broadcast(msg)

    def recover_stuck_in_progress(self, max_age_seconds=3600):
        """
        Resets topics stuck in 'in_progress' for more than max_age_seconds (default 1 hour) to 'pending'.
        """
        now = time.time()
        data = self.status_manager.load()
        updated = False
        for entry in data["topics"]:
            if entry["status"] == "in_progress":
                # Use last_generated or last_topic_update as a proxy for when it started
                last_time = entry.get("last_generated") or entry.get("last_topic_update")
                if last_time:
                    try:
                        t = datetime.fromisoformat(last_time.replace("Z", ""))
                        age = (datetime.utcnow() - t).total_seconds()
                        if age > max_age_seconds:
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
status_manager = KnowledgeStatusManager(status_path)
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