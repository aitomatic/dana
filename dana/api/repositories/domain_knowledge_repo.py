from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from dana.api.core.models import KnowledgePack
from dana.api.core.schemas import KnowledgePackResponse


class AbstractDomainKnowledgeRepo(ABC):
    @abstractmethod
    @staticmethod
    async def get_kp(kp_id: int, **kwargs) -> KnowledgePackResponse:
        pass

    @abstractmethod
    @staticmethod
    async def create_kp(folder_path: str, kp_metadata: dict, **kwargs) -> KnowledgePackResponse:
        pass


class SQLDomainKnowledgeRepo(AbstractDomainKnowledgeRepo):
    @staticmethod
    def _get_db(**kwargs) -> Session:
        db = kwargs.get("db")
        if db is None:
            raise ValueError(f"Missing db of type {Session} in kwargs: {kwargs}")
        return db

    @staticmethod
    async def get_kp(kp_id: int, **kwargs):
        db = SQLDomainKnowledgeRepo._get_db(**kwargs)
        kp = db.query(KnowledgePack).filter(KnowledgePack.id == kp_id).first()
        return KnowledgePackResponse(
            id=kp.id, folder_path=kp.folder_path, kp_metadata=kp.kp_metadata, created_at=kp.created_at, updated_at=kp.updated_at
        )

    @staticmethod
    async def create_kp(folder_path: str, kp_metadata: dict, **kwargs):
        db = SQLDomainKnowledgeRepo._get_db(**kwargs)
        kp = KnowledgePack(folder_path=folder_path, kp_metadata=kp_metadata)
        db.add(kp)
        db.commit()
        db.refresh(kp)
        return KnowledgePackResponse(
            id=kp.id, folder_path=kp.folder_path, kp_metadata=kp.kp_metadata, created_at=kp.created_at, updated_at=kp.updated_at
        )
