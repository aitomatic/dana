from threading import Thread
from queue import Queue
from dana.api.repositories import get_background_task_repo
from dana.api.services.intent_detection.intent_handlers.handler_tools.knowledge_ops_tools.generate_knowledge_tool import (
    GenerateKnowledgeTool,
)
from dana.api.core.schemas import ExtractionDataRequest
from dana.api.services.extraction_service import get_extraction_service
from dana.common.utils.misc import Misc
from dana.api.core.database import get_db
from datetime import datetime
import logging
import threading
from dana.common.sys_resource.rag import get_global_rag_resource

logger = logging.getLogger(__name__)

# Task type-specific concurrency limits
from dana.api.core.schemas_v2 import BackgroundTaskType

# 1 worker for knowledge gen, 1 worker for deep extract
TASK_TYPE_LIMITS = {BackgroundTaskType.KNOWLEDGE_GEN: 1, BackgroundTaskType.DEEP_EXTRACT: 1}


class TaskManager:
    def __init__(self):
        # Separate queues for different task types
        self.queues = {
            BackgroundTaskType.KNOWLEDGE_GEN: Queue(),
            BackgroundTaskType.DEEP_EXTRACT: Queue(),
        }
        self._initialized = False
        self._workers = {
            BackgroundTaskType.KNOWLEDGE_GEN: [],
            BackgroundTaskType.DEEP_EXTRACT: [],
        }
        self._shutdown_event = threading.Event()

        # Active task tracking per type
        self._active_tasks = {
            BackgroundTaskType.KNOWLEDGE_GEN: set(),
            BackgroundTaskType.DEEP_EXTRACT: set(),
        }

        # Locks for thread safety
        self._locks = {
            BackgroundTaskType.KNOWLEDGE_GEN: threading.Lock(),
            BackgroundTaskType.DEEP_EXTRACT: threading.Lock(),
        }
        self.bg_cls = get_background_task_repo()
        self.extraction_service = get_extraction_service()
        self.rag_resource = get_global_rag_resource()

    async def add_knowledge_gen_task(self, data: dict, check_exist: bool = True) -> int | None:
        for db in get_db():
            if check_exist and await self.bg_cls.check_task_exists(type=BackgroundTaskType.KNOWLEDGE_GEN, data=data, db=db):
                logger.info(f"Knowledge generation task already exists for data: {data}")
                return None
            task_response = await self.bg_cls.create_task(type=BackgroundTaskType.KNOWLEDGE_GEN, data=data, db=db)
            self.queues[BackgroundTaskType.KNOWLEDGE_GEN].put(
                {"type": BackgroundTaskType.KNOWLEDGE_GEN, "data": data, "task_id": task_response.id}
            )
            logger.info(f"Added knowledge generation task to queue (DB ID: {task_response.id})")
            return task_response.id

    async def add_deep_extract_task(self, document_id: int, data: dict | None = None, check_exist: bool = True) -> int | None:
        """Add a deep extraction task to the background queue."""
        if data is None:
            data = {"document_id": document_id}
        else:
            data["document_id"] = document_id

        for db in get_db():
            if check_exist and await self.bg_cls.check_task_exists(type=BackgroundTaskType.DEEP_EXTRACT, data=data, db=db):
                logger.info(f"Deep extraction task already exists for data: {data}")
                return None
            task_response = await self.bg_cls.create_task(type=BackgroundTaskType.DEEP_EXTRACT, data=data, db=db)
            self.queues[BackgroundTaskType.DEEP_EXTRACT].put(
                {"type": BackgroundTaskType.DEEP_EXTRACT, "data": data, "task_id": task_response.id}
            )
            logger.info(f"Added deep extraction task for document {document_id} (DB ID: {task_response.id})")
            return task_response.id

    def initialize(self):
        """Initialize the task manager with task type-specific worker threads (non-blocking)."""
        if not self._initialized:
            # Load existing pending tasks from database
            self._load_pending_tasks()

            # Create workers for each task type
            for task_type, max_workers in TASK_TYPE_LIMITS.items():
                for i in range(max_workers):
                    worker_thread = Thread(
                        target=self._worker, args=(task_type, i + 1), name=f"TaskManager-{task_type}-Worker-{i+1}", daemon=True
                    )
                    worker_thread.start()
                    self._workers[task_type].append(worker_thread)

            self._initialized = True
            total_workers = sum(TASK_TYPE_LIMITS.values())
            logger.info(f"TaskManager initialized with {total_workers} workers: {TASK_TYPE_LIMITS}")

    def _load_pending_tasks(self):
        """Load pending tasks from database and add them to the queue."""
        try:
            for db in get_db():
                # Get pending and running tasks from database
                from dana.api.core.schemas_v2 import BackgroundTaskStatus

                pending_and_running_tasks = Misc.safe_asyncio_run(
                    self.bg_cls.get_tasks, status=[BackgroundTaskStatus.PENDING, BackgroundTaskStatus.RUNNING], db=db
                )

                if pending_and_running_tasks:
                    logger.info(f"Loading {len(pending_and_running_tasks)} pending and running tasks from database")
                    for task in pending_and_running_tasks:
                        # Add task to appropriate queue based on type
                        task_data = {"type": task.type, "data": task.data, "task_id": task.id}
                        # Convert string to enum if needed
                        task_type_enum = BackgroundTaskType(task.type) if isinstance(task.type, str) else task.type
                        if task_type_enum in self.queues:
                            self.queues[task_type_enum].put(task_data)
                            logger.info(f"Loaded pending {task.type} task (ID: {task.id})")
                        else:
                            logger.warning(f"Unknown task type: {task.type}")
                else:
                    logger.info("No pending tasks found in database")

        except Exception as e:
            logger.error(f"Error loading pending tasks: {e}")

    def shutdown(self):
        """Shutdown the task manager and cleanup resources."""
        if self._initialized:
            logger.info("Shutting down TaskManager...")
            self._shutdown_event.set()

            # Signal workers to stop by putting None in each queue
            for task_type, queue in self.queues.items():
                for _ in self._workers[task_type]:
                    queue.put(None)

            # Wait for all workers to finish
            for _, workers in self._workers.items():
                for worker in workers:
                    worker.join(timeout=5.0)

            self._initialized = False
            logger.info("TaskManager shutdown complete")

    def _worker(self, task_type: str, worker_id: int):
        """Worker function for specific task type."""
        # Convert string to enum
        task_type_enum = BackgroundTaskType(task_type)
        thread_name = f"{task_type}-Worker-{worker_id}"
        logger.info(f"{thread_name} started")

        while not self._shutdown_event.is_set():
            try:
                # Get task from type-specific queue
                task = self.queues[task_type_enum].get()
                if task is None:
                    break

                # Check concurrency limit
                with self._locks[task_type_enum]:
                    if len(self._active_tasks[task_type_enum]) >= TASK_TYPE_LIMITS[task_type_enum]:
                        # Put task back and wait
                        self.queues[task_type_enum].put(task)
                        continue

                    # Add to active tasks
                    self._active_tasks[task_type_enum].add(task.get("task_id"))

                try:
                    # Process the task
                    self.process_task(task)
                finally:
                    # Remove from active tasks
                    with self._locks[task_type_enum]:
                        self._active_tasks[task_type_enum].discard(task.get("task_id"))

                    self.queues[task_type_enum].task_done()

            except Exception as e:
                logger.error(f"Error in {thread_name}: {e}")
                continue

        logger.info(f"{thread_name} stopped")

    def process_task(self, task: dict):
        task_id = task.get("task_id")

        try:
            # Update task status to "running" if task_id exists
            if task_id:
                from dana.api.core.schemas_v2 import BackgroundTaskStatus

                self._update_task_status(task_id, BackgroundTaskStatus.RUNNING)

            if task["type"] == BackgroundTaskType.KNOWLEDGE_GEN:
                knowledge_gen_tool = GenerateKnowledgeTool(
                    knowledge_status_path=task["data"]["knowledge_status_path"],
                    storage_path=task["data"]["storage_path"],
                    tree_structure=task["data"]["tree_structure"],
                    domain=task["data"]["domain"],
                    role=task["data"]["role"],
                    tasks=task["data"]["tasks"],
                )
                kwargs_names = knowledge_gen_tool.get_arguments()
                Misc.safe_asyncio_run(knowledge_gen_tool.execute, **{task["data"].get(kwargs_name) for kwargs_name in kwargs_names})
            elif task["type"] == BackgroundTaskType.DEEP_EXTRACT:
                self._process_deep_extract_task(task)

            # Update task status to "completed" if task_id exists
            if task_id:
                from dana.api.core.schemas_v2 import BackgroundTaskStatus

                self._update_task_status(task_id, BackgroundTaskStatus.COMPLETED)

        except Exception as e:
            logger.error(f"Error processing task {task_id}: {e}")
            # Update task status to "failed" if task_id exists
            if task_id:
                from dana.api.core.schemas_v2 import BackgroundTaskStatus

                self._update_task_status(task_id, BackgroundTaskStatus.FAILED, str(e))

    def _process_deep_extract_task(self, task: dict):
        """Process deep extraction task in background."""
        try:
            document_id = task["data"]["document_id"]
            original_filename = task["data"]["original_filename"]
            logger.info(f"Processing deep extraction task for document {document_id}")

            # Import here to avoid circular imports
            from dana.api.routers.v1.extract_documents import deep_extract
            from dana.api.core.schemas import DeepExtractionRequest

            for db in get_db():
                # Perform deep extraction with use_deep_extraction=True
                result = Misc.safe_asyncio_run(
                    deep_extract, DeepExtractionRequest(document_id=document_id, use_deep_extraction=True, config={}), db=db
                )
                pages = result.file_object.pages

                request = ExtractionDataRequest(
                    original_filename=original_filename,
                    source_document_id=document_id,
                    extraction_results={
                        "original_filename": original_filename,
                        "extraction_date": datetime.now().isoformat(),  # Should be "2025-09-16T10:41:01.407Z"
                        "total_pages": result.file_object.total_pages,
                        "documents": [{"text": page.page_content, "page_number": page.page_number} for page in pages],
                    },
                )

                Misc.safe_asyncio_run(self.rag_resource.index_extraction_response, result, overwrite=True)

                Misc.safe_asyncio_run(
                    self.extraction_service.save_extraction_json,
                    original_filename=original_filename,
                    extraction_results=request.extraction_results,
                    source_document_id=document_id,
                    db_session=db,
                    remove_old_extraction_files=False,
                    deep_extracted=True,
                    metadata={},
                )

                logger.info(f"Successfully saved extraction JSON file with ID: {document_id}")

            logger.info(f"Completed deep extraction task for document {document_id}")

        except Exception as e:
            logger.error(f"Error processing deep extraction task: {e}")
            # TODO: Update task status to failed in database

    def _update_task_status(self, task_id: int, status, error: str | None = None):
        """Update task status in database."""
        try:
            from dana.api.core.models import BackGroundTask

            for db in get_db():
                task = db.query(BackGroundTask).filter(BackGroundTask.id == task_id).first()
                if task:
                    # Pydantic will handle enum conversion automatically
                    task.status = status.value if hasattr(status, "value") else str(status)
                    if error:
                        task.error = error
                    db.commit()
                    logger.info(f"Updated task {task_id} status to {task.status}")
                else:
                    logger.warning(f"Task {task_id} not found in database")

        except Exception as e:
            logger.error(f"Error updating task {task_id} status: {e}")

    def get_queue_status(self) -> dict:
        """Get current queue and worker status for monitoring."""
        return {
            task_type: {
                "queue_size": self.queues[task_type].qsize(),
                "active_tasks": len(self._active_tasks[task_type]),
                "max_workers": TASK_TYPE_LIMITS[task_type],
                "worker_count": len(self._workers[task_type]),
            }
            for task_type in TASK_TYPE_LIMITS.keys()
        }

    def wait_forever(self):
        """Wait for all workers to complete (for testing/debugging)."""
        for _, workers in self._workers.items():
            for worker in workers:
                worker.join()


# Global service instance
_task_manager: TaskManager | None = None


def get_task_manager() -> TaskManager:
    """Get or create the global task manager instance."""
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
        _task_manager.initialize()
    return _task_manager


def shutdown_task_manager():
    """Shutdown the global task manager."""
    global _task_manager
    if _task_manager is not None:
        _task_manager.shutdown()
        _task_manager = None


if __name__ == "__main__":
    import asyncio

    task_manager = get_task_manager()
    asyncio.run(task_manager.add_deep_extract_task(document_id=3))
    asyncio.run(task_manager.add_deep_extract_task(document_id=3))
    asyncio.run(task_manager.add_deep_extract_task(document_id=3))
    task_manager.wait_forever()
