from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from dana.api.core.models import BackGroundTask
from dana.api.core.schemas_v2 import BackgroundTaskResponse, BackgroundTaskStatus
import hashlib


class AbstractBackgroundTaskRepo(ABC):
    @classmethod
    def compute_hash(cls, type: str, data: dict, **kwargs) -> str:
        """
        Compute a hash for a task. Assume all values in data are serializable.
        """
        _data_str = {k: data[k] for k in sorted(data.keys())}
        _str_to_hash = f"{type}:{_data_str}"
        return hashlib.sha256(_str_to_hash.encode()).hexdigest()

    @classmethod
    @abstractmethod
    async def check_task_exists(cls, type: str, data: dict, **kwargs) -> bool:
        pass

    @classmethod
    @abstractmethod
    async def create_task(cls, type: str, data: dict, **kwargs) -> BackgroundTaskResponse:
        pass

    @classmethod
    @abstractmethod
    async def get_tasks(cls, **kwargs) -> list[BackgroundTaskResponse]:
        pass


class SQLBackgroundTaskRepo(AbstractBackgroundTaskRepo):
    @classmethod
    def _get_db(cls, **kwargs) -> Session:
        db = kwargs.get("db")
        if db is None:
            raise ValueError(f"Missing db of type {Session} in kwargs: {kwargs}")
        return db

    @classmethod
    async def check_task_exists(cls, type: str, data: dict, **kwargs) -> bool:
        db = cls._get_db(**kwargs)
        task_hash = cls.compute_hash(type, data)
        return db.query(BackGroundTask).filter(BackGroundTask.task_hash == task_hash).first() is not None

    @classmethod
    async def create_task(cls, type: str, data: dict, **kwargs) -> BackgroundTaskResponse:
        db = cls._get_db(**kwargs)
        task = BackGroundTask(type=type, data=data, task_hash=cls.compute_hash(type, data))
        db.add(task)
        db.commit()
        db.refresh(task)
        return BackgroundTaskResponse(
            id=task.id,
            type=task.type,
            status=task.status,
            data=task.data,
            error=task.error,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )

    @classmethod
    async def get_tasks(cls, status: str | BackgroundTaskStatus = "pending", **kwargs) -> list[BackgroundTaskResponse]:
        """Get tasks from database by status."""
        db = cls._get_db(**kwargs)
        # Convert enum to string if needed
        status_value = status.value if hasattr(status, "value") else str(status)
        tasks = db.query(BackGroundTask).filter(BackGroundTask.status == status_value).all()
        return [
            BackgroundTaskResponse(
                id=task.id,
                type=task.type,
                status=task.status,
                data=task.data,
                error=task.error,
                created_at=task.created_at,
                updated_at=task.updated_at,
            )
            for task in tasks
        ]
