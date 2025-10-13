from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from dana.lang.api.core.models import InterviewTemplate
from dana.lang.api.core.schemas_v2 import (
    InterviewTemplateCreate,
    InterviewTemplateRead,
    InterviewTemplateUpdate,
    InterviewTemplateListResponse,
)
from datetime import datetime
from pathlib import Path


class AbstractInterviewTemplateRepo(ABC):
    @classmethod
    @abstractmethod
    async def create_template(cls, template_data: InterviewTemplateCreate, **kwargs) -> InterviewTemplateRead:
        pass

    @classmethod
    @abstractmethod
    async def get_template(cls, template_id: int, **kwargs) -> InterviewTemplateRead | None:
        pass

    @classmethod
    @abstractmethod
    async def get_template_by_kp_id(cls, kp_id: int, is_master: bool = True, **kwargs) -> InterviewTemplateRead | None:
        pass

    @classmethod
    @abstractmethod
    async def update_template(cls, template_id: int, update_data: InterviewTemplateUpdate, **kwargs) -> InterviewTemplateRead:
        pass

    @classmethod
    @abstractmethod
    async def list_templates_by_kp(cls, kp_id: int, skip: int = 0, limit: int = 100, **kwargs) -> InterviewTemplateListResponse:
        pass

    @classmethod
    @abstractmethod
    async def delete_template(cls, template_id: int, **kwargs) -> None:
        pass

    @classmethod
    @abstractmethod
    async def duplicate_template(cls, template_data: InterviewTemplateCreate, **kwargs) -> InterviewTemplateRead:
        pass


class SQLInterviewTemplateRepo(AbstractInterviewTemplateRepo):
    @classmethod
    def _get_db(cls, **kwargs) -> Session:
        db = kwargs.get("db")
        if db is None:
            raise ValueError(f"Missing db of type {Session} in kwargs: {kwargs}")
        return db

    @classmethod
    async def create_template(cls, template_data: InterviewTemplateCreate, **kwargs) -> InterviewTemplateRead:
        db = cls._get_db(**kwargs)
        template = InterviewTemplate(**template_data.model_dump())
        db.add(template)
        db.commit()
        db.refresh(template)
        return InterviewTemplateRead.model_validate(template)

    @classmethod
    async def get_template(cls, template_id: int, **kwargs) -> InterviewTemplateRead | None:
        db = cls._get_db(**kwargs)
        template = db.query(InterviewTemplate).filter(InterviewTemplate.id == template_id).first()
        return InterviewTemplateRead.model_validate(template) if template else None

    @classmethod
    async def get_template_by_kp_id(cls, kp_id: int, is_master: bool = True, **kwargs) -> InterviewTemplateRead | None:
        db = cls._get_db(**kwargs)
        query = db.query(InterviewTemplate).filter(InterviewTemplate.kp_id == kp_id)
        if is_master:
            query = query.filter(InterviewTemplate.is_master)
        template = query.first()
        return InterviewTemplateRead.model_validate(template) if template else None

    @classmethod
    async def update_template(cls, template_id: int, update_data: InterviewTemplateUpdate, **kwargs) -> InterviewTemplateRead:
        db = cls._get_db(**kwargs)
        template = db.query(InterviewTemplate).filter(InterviewTemplate.id == template_id).first()
        if not template:
            raise ValueError(f"Template {template_id} not found")

        for key, value in update_data.model_dump(exclude_unset=True).items():
            setattr(template, key, value)

        db.commit()
        db.refresh(template)
        return InterviewTemplateRead.model_validate(template)

    @classmethod
    async def list_templates_by_kp(cls, kp_id: int, skip: int = 0, limit: int = 100, **kwargs) -> InterviewTemplateListResponse:
        db = cls._get_db(**kwargs)

        # Get total count for pagination
        total = db.query(InterviewTemplate).filter(InterviewTemplate.kp_id == kp_id).count()

        # Get paginated results
        templates = db.query(InterviewTemplate).filter(InterviewTemplate.kp_id == kp_id).offset(skip).limit(limit).all()

        # Convert to response format
        template_reads = [InterviewTemplateRead.model_validate(template) for template in templates]

        return InterviewTemplateListResponse(
            success=True, message=f"Retrieved {len(template_reads)} templates for knowledge pack {kp_id}", data=template_reads, total=total
        )

    @classmethod
    async def delete_template(cls, template_id: int, **kwargs) -> None:
        db = cls._get_db(**kwargs)
        template = db.query(InterviewTemplate).filter(InterviewTemplate.id == template_id).first()
        if not template:
            raise ValueError(f"Template {template_id} not found")

        db.delete(template)
        db.commit()

    @classmethod
    async def duplicate_template(cls, template_data: InterviewTemplateCreate, **kwargs) -> InterviewTemplateRead:
        db = cls._get_db(**kwargs)

        # Get source template (master if source_template_id is None)
        if template_data.source_template_id is None:
            source_template = (
                db.query(InterviewTemplate).filter(InterviewTemplate.kp_id == template_data.kp_id, InterviewTemplate.is_master).first()
            )
            if not source_template:
                raise ValueError(f"No master template found for knowledge pack {template_data.kp_id}")
        else:
            source_template = db.query(InterviewTemplate).filter(InterviewTemplate.id == template_data.source_template_id).first()
            if not source_template:
                raise ValueError(f"Source template {template_data.source_template_id} not found")

        # Create new template with copied data
        new_template_data = source_template.__dict__.copy()

        # Remove fields that should be auto-generated or are SQLAlchemy internal
        for field in ["id", "created_at", "updated_at", "_sa_instance_state"]:
            new_template_data.pop(field, None)

        # Update with new template data (use provided values or defaults from source)
        new_template_data.update(
            {
                "name": template_data.name or f"{source_template.name} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "description": template_data.description or source_template.description,
                "version": template_data.version or source_template.version,
                "is_active": source_template.is_active,  # Use source template's is_active
                "is_master": False,  # Duplicated templates are never master
                "kp_id": template_data.kp_id,
            }
        )

        # Transform metadata
        metadata = new_template_data.get("template_metadata", {}).copy()
        metadata.update(
            {
                "status": "draft",  # Set to DRAFT
                "source_template_id": source_template.id,  # Track source
            }
        )
        # Clear fields that should be reset
        metadata.pop("last_modified_by", None)
        metadata.pop("modification_history", None)

        new_template_data["template_metadata"] = metadata

        # Create new template (folder_path will be set after we get the ID)
        new_template = InterviewTemplate(**new_template_data)
        db.add(new_template)
        db.commit()
        db.refresh(new_template)

        # Update folder_path with ID-based naming
        current_template_path = Path(str(source_template.folder_path)).parent
        new_template.folder_path = f"{current_template_path}/template_{new_template.id}"
        db.commit()
        db.refresh(new_template)

        return InterviewTemplateRead.model_validate(new_template)


if __name__ == "__main__":
    from dana.lang.api.core.database import get_db
    from dana.lang.common.utils.misc import Misc

    for db in get_db():
        # Get the master template for this knowledge pack
        master_template = Misc.safe_asyncio_run(SQLInterviewTemplateRepo.get_template_by_kp_id, kp_id=1, is_master=True, db=db)

        if master_template:
            # Update the template to set is_active=True
            from dana.lang.api.core.schemas_v2 import InterviewTemplateUpdate

            update_data = InterviewTemplateUpdate(is_active=True)

            Misc.safe_asyncio_run(SQLInterviewTemplateRepo.update_template, template_id=master_template.id, update_data=update_data, db=db)
