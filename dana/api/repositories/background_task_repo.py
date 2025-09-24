from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from dana.api.core.models import BackGroundTask
from dana.api.core.schemas import BackgroundTaskResponse


class AbstractBackgroundTaskRepo(ABC):
    @classmethod
    @abstractmethod
    async def create_task(cls, type: str, data: dict, **kwargs) -> BackgroundTaskResponse:
        pass


class SQLBackgroundTaskRepo(AbstractBackgroundTaskRepo):
    @classmethod
    def _get_db(cls, **kwargs) -> Session:
        db = kwargs.get("db")
        if db is None:
            raise ValueError(f"Missing db of type {Session} in kwargs: {kwargs}")
        return db

    @classmethod
    async def create_task(cls, type: str, data: dict, **kwargs) -> BackgroundTaskResponse:
        db = cls._get_db(**kwargs)
        task = BackGroundTask(type=type, data=data)
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
