from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from dana.api.core.models import KnowledgePack
from dana.api.core.schemas import KnowledgePackOutput, DomainKnowledgeTree, DomainNode
from pathlib import Path
from threading import Lock
from collections import defaultdict

DOMAIN_TREE_FN = "domain_knowledge.json"


class AbstractDomainKnowledgeRepo(ABC):
    @classmethod
    def get_knowledge_pack_folder(cls, kp_id: int) -> Path:
        _folder = Path(f"knowledge_packs/{kp_id}")
        _folder.mkdir(parents=True, exist_ok=True)
        (_folder / "knows").mkdir(parents=True, exist_ok=True)
        return _folder

    @classmethod
    def get_knowledge_tree_path(cls, kp_id: int) -> Path:
        _fn = cls.get_knowledge_pack_folder(kp_id) / DOMAIN_TREE_FN
        return _fn

    @classmethod
    @abstractmethod
    async def get_kp_tree(cls, kp_id: int, **kwargs) -> DomainKnowledgeTree:
        pass

    @classmethod
    @abstractmethod
    async def get_kp(cls, kp_id: int, **kwargs) -> KnowledgePackOutput | None:
        pass

    @classmethod
    @abstractmethod
    async def create_kp(cls, kp_metadata: dict, **kwargs) -> KnowledgePackOutput:
        pass

    @classmethod
    @abstractmethod
    async def update_kp(cls, kp_id: int, kp_metadata: dict, **kwargs) -> KnowledgePackOutput:
        pass


class SQLDomainKnowledgeRepo(AbstractDomainKnowledgeRepo):
    _locks = defaultdict(Lock)

    @classmethod
    def _get_db(cls, **kwargs) -> Session:
        db = kwargs.get("db")
        if db is None:
            raise ValueError(f"Missing db of type {Session} in kwargs: {kwargs}")
        return db

    @classmethod
    def _ensure_tree_is_valid(cls, folder_path: Path, kp: KnowledgePack) -> None:
        domain_tree_path = folder_path / DOMAIN_TREE_FN
        domain = kp.kp_metadata.get("domain")
        if not domain:
            raise ValueError(f"Domain not found in kp_metadata: {kp.kp_metadata}")
        if not domain_tree_path.exists():
            tree = DomainKnowledgeTree(root=DomainNode(topic=domain))
            domain_tree_path.write_text(tree.model_dump_json(indent=4))
        else:
            tree = DomainKnowledgeTree.model_validate_json(domain_tree_path.read_text())
            if tree.root.topic != kp.kp_metadata.get("domain"):
                tree.root.topic = domain
                domain_tree_path.write_text(tree.model_dump_json(indent=4))

    @classmethod
    def _format_kp_response(cls, kp: KnowledgePack) -> KnowledgePackOutput:
        folder_path = cls.get_knowledge_pack_folder(kp.id).absolute()
        with cls._locks[kp.id]:
            cls._ensure_tree_is_valid(folder_path, kp)
        return KnowledgePackOutput(
            id=kp.id,
            kp_metadata=kp.kp_metadata,
            folder_path=cls.get_knowledge_pack_folder(kp.id).absolute(),
            created_at=kp.created_at,
            updated_at=kp.updated_at,
        )

    @classmethod
    async def get_kp_tree(cls, kp_id: int, **kwargs) -> DomainKnowledgeTree:
        with cls._locks[kp_id]:
            folder = cls.get_knowledge_pack_folder(kp_id)
            domain_tree_path = folder / "domain_knowledge.json"
            return DomainKnowledgeTree.model_validate_json(domain_tree_path.read_text())

    @classmethod
    async def get_kp(cls, kp_id: int, **kwargs) -> KnowledgePackOutput | None:
        db = cls._get_db(**kwargs)
        kp = db.query(KnowledgePack).filter(KnowledgePack.id == kp_id).first()
        return cls._format_kp_response(kp) if kp else None

    @classmethod
    async def create_kp(cls, kp_metadata: dict, **kwargs) -> KnowledgePackOutput:
        db = cls._get_db(**kwargs)
        kp = KnowledgePack(kp_metadata=kp_metadata)
        db.add(kp)
        db.commit()
        db.refresh(kp)
        return cls._format_kp_response(kp)

    @classmethod
    async def update_kp(cls, kp_id: int, kp_metadata: dict, **kwargs) -> KnowledgePackOutput:
        db = cls._get_db(**kwargs)
        kp = db.query(KnowledgePack).filter(KnowledgePack.id == kp_id).first()
        if not kp:
            raise ValueError(f"Knowledge pack {kp_id} not found")
        kp.kp_metadata.update(kp_metadata)
        flag_modified(kp, "kp_metadata")
        db.commit()
        db.refresh(kp)
        return cls._format_kp_response(kp)
