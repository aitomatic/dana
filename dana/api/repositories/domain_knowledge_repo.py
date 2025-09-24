from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from dana.api.core.models import KnowledgePack
from dana.api.core.schemas import KnowledgePackOutput, DomainKnowledgeTree, DomainNode, PaginatedKnowledgePackResponse, PaginationInfo
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
    async def list_kp(cls, limit: int = 100, offset: int = 0, **kwargs) -> PaginatedKnowledgePackResponse:
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
    async def list_kp(cls, limit: int = 100, offset: int = 0, **kwargs) -> PaginatedKnowledgePackResponse:
        db = cls._get_db(**kwargs)

        # Get total count for pagination metadata
        total = db.query(KnowledgePack).count()

        # Get paginated results
        kps = db.query(KnowledgePack).offset(offset).limit(limit).all()

        # Calculate pagination metadata
        current_page = (offset // limit) + 1 if limit > 0 else 1
        total_pages = max(1, (total + limit - 1) // limit) if limit > 0 else 1  # Ceiling division, minimum 1

        # Create pagination info
        pagination_info = PaginationInfo(
            page=current_page,
            per_page=limit,
            total=total,
            total_pages=total_pages,
            has_next=current_page < total_pages,
            has_previous=current_page > 1,
            next_page=current_page + 1 if current_page < total_pages else None,
            previous_page=current_page - 1 if current_page > 1 else None,
        )

        # Format the knowledge pack responses
        data = [cls._format_kp_response(kp) for kp in kps]

        return PaginatedKnowledgePackResponse(data=data, pagination=pagination_info)

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
