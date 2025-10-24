from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified, set_attribute
from sqlalchemy import JSON, ARRAY
from dana.studio.api.core.models import KnowledgePack, Document
from dana.studio.api.core.schemas import DomainNode
from dana.studio.api.core.schemas_v2 import (
    DomainNodeV2,
    DomainKnowledgeTreeV2,
    KnowledgePackOutput,
    PaginatedKnowledgePackResponse,
    PaginationInfo,
    InterviewTemplateWithSessions,
    InterviewTemplateRead,
    InterviewSessionRead,
    TemplateGenerationStatus,
    KnowledgeGenerationStatus,
)
from pathlib import Path
from threading import Lock
from collections import defaultdict
import shutil
import logging
from dana.studio.api.repositories.config import DEFAULT_TEMPLATE_FOLDER, DOMAIN_TREE_FN, KNOW_FOLDER_NAME


class AbstractDomainKnowledgeRepo(ABC):
    @classmethod
    def get_knowledge_pack_folder(cls, kp_id: int) -> Path:
        _folder = Path(f"knowledge_packs/{kp_id}")
        _folder.mkdir(parents=True, exist_ok=True)
        (_folder / KNOW_FOLDER_NAME).mkdir(parents=True, exist_ok=True)
        return _folder

    @classmethod
    def get_default_interview_template_folder(cls, kp_id: int) -> Path:
        return cls.get_knowledge_pack_folder(kp_id) / DEFAULT_TEMPLATE_FOLDER

    @classmethod
    def get_knowledge_tree_path(cls, kp_id: int) -> Path:
        _fn = cls.get_knowledge_pack_folder(kp_id) / DOMAIN_TREE_FN
        return _fn

    @classmethod
    def save_tree(cls, tree_path: str | Path, tree: DomainKnowledgeTreeV2) -> None:
        Path(tree_path).write_text(tree.model_dump_json(indent=4))

    @classmethod
    @abstractmethod
    async def get_kp_tree(cls, kp_id: int, **kwargs) -> DomainKnowledgeTreeV2:
        pass

    @classmethod
    @abstractmethod
    async def delete_kp_tree_node(cls, kp_id: int, topic_parts: list[str], **kwargs) -> None:
        pass

    @classmethod
    @abstractmethod
    async def update_kp_tree_node_name(cls, kp_id: int, topic_parts: list[str], node_name: str, **kwargs) -> None:
        pass

    @classmethod
    @abstractmethod
    async def add_kp_tree_child_node(cls, kp_id: int, topic_parts: list[str], child_topics: list[str], **kwargs) -> None:
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

    @classmethod
    @abstractmethod
    async def delete_kp(cls, kp_id: int, **kwargs) -> None:
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
    def _resolve_node_folder_path(cls, knows_path: Path, topic_parts: list[str]) -> Path | None:
        """
        Resolve the folder path for a node, trying regular path first, then fallback to fd_name conversion.

        Args:
            knows_path: Path to the knows directory
            topic_parts: List of topic parts to resolve

        Returns:
            Resolved path if found, None otherwise
        """
        # Try regular path first
        node_path = knows_path.joinpath(*topic_parts).resolve()
        if node_path.exists():
            return node_path

        # Try fallback path using fd_name
        fallback_parts = [DomainNode(topic=topic).fd_name for topic in topic_parts]
        fallback_node_path = knows_path.joinpath(*fallback_parts).resolve()
        if fallback_node_path.exists():
            return fallback_node_path

        return None

    @classmethod
    def _delete_node_folder(cls, knows_path: Path, topic_parts: list[str]) -> bool:
        """
        Delete the folder corresponding to a node.

        Args:
            knows_path: Path to the knows directory
            topic_parts: List of topic parts to delete

        Returns:
            True if folder was deleted successfully, False otherwise
        """
        try:
            node_path = cls._resolve_node_folder_path(knows_path, topic_parts)
            if node_path and node_path.exists():
                shutil.rmtree(node_path)
                logging.info(f"Deleted folder: {node_path}")
                return True
            else:
                logging.warning(f"Folder not found for deletion: {topic_parts}")
                return False
        except Exception as e:
            logging.warning(f"Failed to delete folder for {topic_parts}: {e}")
            return False

    @classmethod
    def _rename_node_folder(cls, knows_path: Path, topic_parts: list[str], new_name: str) -> bool:
        """
        Rename the folder corresponding to a node.

        Args:
            knows_path: Path to the knows directory
            topic_parts: List of topic parts to rename
            new_name: New name for the node

        Returns:
            True if folder was renamed successfully, False otherwise
        """
        try:
            old_node_path = cls._resolve_node_folder_path(knows_path, topic_parts)
            if old_node_path and old_node_path.exists():
                # Create new path with updated name
                new_parts = topic_parts[:-1] + [new_name]
                new_node_path = knows_path.joinpath(*new_parts).resolve()
                old_node_path.rename(new_node_path)
                logging.info(f"Renamed folder: {old_node_path} -> {new_node_path}")
                return True
            else:
                logging.warning(f"Folder not found for renaming: {topic_parts}")
                return False
        except Exception as e:
            logging.warning(f"Failed to rename folder for {topic_parts}: {e}")
            return False

    @classmethod
    def _ensure_tree_is_valid(cls, folder_path: Path, kp: KnowledgePack) -> None:
        domain_tree_path = folder_path / DOMAIN_TREE_FN
        domain = kp.kp_metadata.get("domain")
        if not domain:
            raise ValueError(f"Domain not found in kp_metadata: {kp.kp_metadata}")
        if not domain_tree_path.exists():
            tree = DomainKnowledgeTreeV2(root=DomainNodeV2(topic=domain))
            cls.save_tree(domain_tree_path, tree)
        else:
            tree = DomainKnowledgeTreeV2.model_validate_json(domain_tree_path.read_text())
            if tree.root.topic != kp.kp_metadata.get("domain"):
                tree.root.topic = domain
                cls.save_tree(domain_tree_path, tree)

    @classmethod
    def _format_kp_response(cls, kp: KnowledgePack) -> KnowledgePackOutput:
        folder_path = cls.get_knowledge_pack_folder(kp.id).absolute()
        with cls._locks[kp.id]:
            cls._ensure_tree_is_valid(folder_path, kp)

        # Build interview templates with their sessions
        templates_with_sessions = []
        for template in kp.interview_templates:
            # Convert template to InterviewTemplateRead
            template_data = InterviewTemplateRead.model_validate(template)

            # Convert sessions to InterviewSessionRead
            sessions = [InterviewSessionRead.model_validate(session) for session in template.interview_sessions]

            # Create InterviewTemplateWithSessions
            template_with_sessions = InterviewTemplateWithSessions(**template_data.model_dump(), interview_sessions=sessions)
            templates_with_sessions.append(template_with_sessions)

        return KnowledgePackOutput(
            id=kp.id,
            kp_metadata=kp.kp_metadata or {},
            folder_path=str(cls.get_knowledge_pack_folder(kp.id).absolute()),
            created_at=kp.created_at,
            updated_at=kp.updated_at,
            status=kp.status or KnowledgeGenerationStatus.DRAFT,
            generation_task_id=kp.generation_task_id,
            interview_templates=templates_with_sessions,
        )

    @classmethod
    async def get_kp_tree(cls, kp_id: int, **kwargs) -> DomainKnowledgeTreeV2:
        with cls._locks[kp_id]:
            domain_tree_path = cls.get_knowledge_tree_path(kp_id)
            return DomainKnowledgeTreeV2.model_validate_json(domain_tree_path.read_text())

    @classmethod
    async def delete_kp_tree_node(cls, kp_id: int, topic_parts: list[str], **kwargs) -> None:
        with cls._locks[kp_id]:
            domain_tree_path = cls.get_knowledge_tree_path(kp_id)
            tree = DomainKnowledgeTreeV2.model_validate_json(domain_tree_path.read_text())
            tree.delete_node(topic_parts)
            cls.save_tree(domain_tree_path, tree)

            # Also delete the corresponding folder from knows directory
            folder_path = cls.get_knowledge_pack_folder(kp_id)
            knows_path = folder_path / KNOW_FOLDER_NAME
            cls._delete_node_folder(knows_path, topic_parts)

    @classmethod
    async def update_kp_tree_node_name(cls, kp_id: int, topic_parts: list[str], node_name: str, **kwargs) -> None:
        with cls._locks[kp_id]:
            domain_tree_path = cls.get_knowledge_tree_path(kp_id)
            tree = DomainKnowledgeTreeV2.model_validate_json(domain_tree_path.read_text())
            tree.update_node_name(topic_parts, node_name)
            cls.save_tree(domain_tree_path, tree)

            # Also rename the corresponding folder from knows directory
            folder_path = cls.get_knowledge_pack_folder(kp_id)
            knows_path = folder_path / KNOW_FOLDER_NAME
            cls._rename_node_folder(knows_path, topic_parts, node_name)

    @classmethod
    async def add_kp_tree_child_node(cls, kp_id: int, topic_parts: list[str], child_topics: list[str], **kwargs) -> None:
        with cls._locks[kp_id]:
            domain_tree_path = cls.get_knowledge_tree_path(kp_id)
            tree = DomainKnowledgeTreeV2.model_validate_json(domain_tree_path.read_text())
            tree.add_children_to_node(topic_parts, child_topics)
            cls.save_tree(domain_tree_path, tree)

    @classmethod
    async def list_kp(cls, limit: int = 100, offset: int = 0, **kwargs) -> PaginatedKnowledgePackResponse:
        db = cls._get_db(**kwargs)

        # Get total count for pagination metadata
        total = db.query(KnowledgePack).count()

        # Get paginated results with eager loading of interview templates and sessions
        from sqlalchemy.orm import joinedload
        from dana.studio.api.core.models import InterviewTemplate

        kps = (
            db.query(KnowledgePack)
            .options(joinedload(KnowledgePack.interview_templates).joinedload(InterviewTemplate.interview_sessions))
            .offset(offset)
            .limit(limit)
            .all()
        )

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
        from sqlalchemy.orm import joinedload
        from dana.studio.api.core.models import InterviewTemplate

        kp = (
            db.query(KnowledgePack)
            .options(joinedload(KnowledgePack.interview_templates).joinedload(InterviewTemplate.interview_sessions))
            .filter(KnowledgePack.id == kp_id)
            .first()
        )
        return cls._format_kp_response(kp) if kp else None

    @classmethod
    async def _create_default_interview_template(cls, kp_id: int, kp_metadata: dict, **kwargs) -> None:
        """
        Create default interview template for a new knowledge pack.

        Creates:
        1. Database record for the template
        2. Template folder structure in filesystem
        3. Empty template folder with README

        Args:
            kp_id: Knowledge pack ID
            kp_metadata: Knowledge pack metadata containing domain and role info
        """
        from dana.studio.api.repositories import get_interview_template_repo
        from dana.studio.api.core.schemas_v2 import InterviewTemplateCreate

        db = cls._get_db(**kwargs)
        template_repo = get_interview_template_repo()

        # Extract domain and role from kp_metadata
        domain = kp_metadata.get("domain", "General")
        role = kp_metadata.get("role", "Expert")

        # Create template folder structure
        master_template_folder = cls.get_default_interview_template_folder(kp_id)
        master_template_folder.mkdir(parents=True, exist_ok=True)

        # Create empty README file as placeholder
        readme_file = master_template_folder / "README.md"
        readme_file.write_text("# Default Capture Template\n\n*Template will be generated after knowledge generation completes.*\n")

        # Create database record
        template_data = InterviewTemplateCreate(
            kp_id=kp_id,
            name=f"Default Capture Template - {domain} {role}",
            description=f"Primary capture template for {role} in {domain}",
            version="1.0.0",
            folder_path=str(master_template_folder),
            is_active=False,
            is_master=True,
            template_metadata={
                "domain": domain,
                "role": role,
                "estimated_duration": 90,
                "total_topics": 0,
                "status": TemplateGenerationStatus.DRAFT,
            },
        )

        await template_repo.create_template(template_data, db=db)

    @classmethod
    async def create_kp(cls, kp_metadata: dict, **kwargs) -> KnowledgePackOutput:
        db = cls._get_db(**kwargs)
        kp = KnowledgePack(kp_metadata=kp_metadata)
        db.add(kp)
        db.commit()
        db.refresh(kp)

        # Create default interview template
        await cls._create_default_interview_template(kp.id, kp_metadata, db=db)

        return cls._format_kp_response(kp)

    @classmethod
    async def update_kp(cls, kp_id: int, kp_metadata: dict, **other_updates) -> KnowledgePackOutput:
        db = cls._get_db(**other_updates)
        kp = db.query(KnowledgePack).filter(KnowledgePack.id == kp_id).first()
        if not kp:
            raise ValueError(f"Knowledge pack {kp_id} not found")

        # Handle mutable columns (JSON, ARRAY, etc.) safely
        mutable_column_types = (JSON, ARRAY)

        for col, value in other_updates.items():
            if col in kp.__table__.columns:
                column = kp.__table__.columns[col]
                # Only Update immutable columns
                if not isinstance(column.type, mutable_column_types):
                    set_attribute(kp, col, value)

        # Mutable column need to be updated manually
        kp.kp_metadata.update(kp_metadata)
        flag_modified(kp, "kp_metadata")
        db.commit()
        db.refresh(kp)
        return cls._format_kp_response(kp)

    @classmethod
    async def associate_documents_to_kp(cls, kp_id: int, document_ids: list[int], **kwargs) -> KnowledgePackOutput:
        """
        Associate documents with a knowledge pack by updating kp_metadata.

        Args:
            kp_id: The knowledge pack ID
            document_ids: List of document IDs to associate

        Returns:
            Updated KnowledgePackOutput
        """
        db = cls._get_db(**kwargs)

        # Get the knowledge pack
        kp = db.query(KnowledgePack).filter(KnowledgePack.id == kp_id).first()
        if not kp:
            raise ValueError(f"Knowledge pack {kp_id} not found")

        # Validate that all documents exist
        existing_docs = db.query(Document).filter(Document.id.in_(document_ids)).all()
        existing_doc_ids = {doc.id for doc in existing_docs}
        missing_doc_ids = set(document_ids) - existing_doc_ids

        if missing_doc_ids:
            raise ValueError(f"Documents not found: {list(missing_doc_ids)}")

        # Update kp_metadata with associated documents
        if kp.kp_metadata is None:
            kp.kp_metadata = {}

        # Get current associated documents and merge with new ones
        current_associated = set(kp.kp_metadata.get("associated_documents", []))
        new_associated = current_associated.union(set(document_ids))
        kp.kp_metadata["associated_documents"] = list(new_associated)

        flag_modified(kp, "kp_metadata")
        db.commit()
        db.refresh(kp)

        return cls._format_kp_response(kp)

    @classmethod
    async def get_kp_associated_documents(cls, kp_id: int, **kwargs) -> list[int]:
        """
        Get document IDs associated with a knowledge pack.

        Args:
            kp_id: The knowledge pack ID

        Returns:
            List of associated document IDs
        """
        db = cls._get_db(**kwargs)
        kp = db.query(KnowledgePack).filter(KnowledgePack.id == kp_id).first()
        if not kp:
            raise ValueError(f"Knowledge pack {kp_id} not found")

        return kp.kp_metadata.get("associated_documents", []) if kp.kp_metadata else []

    @classmethod
    async def delete_kp(cls, kp_id: int, **kwargs) -> None:
        """
        Delete a knowledge pack and all associated resources.

        Args:
            kp_id: The knowledge pack ID to delete

        Raises:
            ValueError: If knowledge pack not found
        """
        db = cls._get_db(**kwargs)

        with cls._locks[kp_id]:
            # Get the knowledge pack
            kp = db.query(KnowledgePack).filter(KnowledgePack.id == kp_id).first()
            if not kp:
                raise ValueError(f"Knowledge pack {kp_id} not found")

            # Delete the knowledge pack folder from filesystem
            folder_path = cls.get_knowledge_pack_folder(kp_id)
            if folder_path.exists():
                shutil.rmtree(folder_path)
                logging.info(f"Deleted knowledge pack folder: {folder_path}")

            # Delete the database record (conversations will be deleted due to foreign key constraints)
            db.delete(kp)
            db.commit()

            logging.info(f"Deleted knowledge pack {kp_id} and all associated resources")
