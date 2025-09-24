from threading import Queue, ThreadPoolExecutor
from dana.api.repositories.background_task_repo import SQLBackgroundTaskRepo
from dana.api.services.intent_detection.intent_handlers.handler_tools.knowledge_ops_tools.generate_knowledge_tool import (
    GenerateKnowledgeTool,
)
from dana.api.core.database import get_db
import os

MAX_BG_WORKERS = int(os.environ.get("MAX_BG_WORKERS", "3"))


class TaskManager:
    def __init__(self):
        self.queue = Queue()

    async def add_knowledge_gen_task(self, data: dict):
        for db in get_db():
            await SQLBackgroundTaskRepo.create_task(type="knowledge_gen", data=data, db=db)
            self.queue.put({"type": "knowledge_gen", "data": data})

    async def initialize(self):
        with ThreadPoolExecutor(max_workers=MAX_BG_WORKERS) as executor:
            for _ in range(MAX_BG_WORKERS):
                executor.submit(self.worker)

    async def worker(self):
        while True:
            task = self.queue.get()
            if task is None:
                break
            await self.process_task(task)

    async def process_task(self, task: dict):
        if task["type"] == "knowledge_gen":
            knowledge_gen_tool = GenerateKnowledgeTool(
                knowledge_status_path=task["data"]["knowledge_status_path"],
                storage_path=task["data"]["storage_path"],
                tree_structure=task["data"]["tree_structure"],
                domain=task["data"]["domain"],
                role=task["data"]["role"],
            )
            await knowledge_gen_tool.execute(task["data"]["user_message"], task["data"]["counts"], task["data"]["context"])
