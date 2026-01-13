from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from dana.studio.api.core.models import InterviewSession
from dana.studio.api.core.schemas_v2 import (
    InterviewSessionCreate,
    InterviewSessionRead,
    InterviewSessionUpdate,
    InterviewSessionListResponse,
)


class AbstractInterviewSessionRepo(ABC):
    @classmethod
    @abstractmethod
    async def create_session(cls, session_data: InterviewSessionCreate, **kwargs) -> InterviewSessionRead:
        pass

    @classmethod
    @abstractmethod
    async def get_session(cls, session_id: int, **kwargs) -> InterviewSessionRead | None:
        pass

    @classmethod
    @abstractmethod
    async def get_session_by_template_id(cls, template_id: int, skip: int = 0, limit: int = 100, **kwargs) -> InterviewSessionListResponse:
        pass

    @classmethod
    @abstractmethod
    async def update_session(cls, session_id: int, update_data: InterviewSessionUpdate, **kwargs) -> InterviewSessionRead:
        pass

    @classmethod
    @abstractmethod
    async def delete_session(cls, session_id: int, **kwargs) -> None:
        pass


class SQLInterviewSessionRepo(AbstractInterviewSessionRepo):
    @classmethod
    def _get_db(cls, **kwargs) -> Session:
        db = kwargs.get("db")
        if db is None:
            raise ValueError(f"Missing db of type {Session} in kwargs: {kwargs}")
        return db

    @classmethod
    async def create_session(cls, session_data: InterviewSessionCreate, **kwargs) -> InterviewSessionRead:
        db = cls._get_db(**kwargs)
        session = InterviewSession(**session_data.model_dump())
        db.add(session)
        db.commit()
        db.refresh(session)
        return InterviewSessionRead.model_validate(session)

    @classmethod
    async def get_session(cls, session_id: int, **kwargs) -> InterviewSessionRead | None:
        db = cls._get_db(**kwargs)
        session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
        return InterviewSessionRead.model_validate(session) if session else None

    @classmethod
    async def get_session_by_template_id(cls, template_id: int, skip: int = 0, limit: int = 100, **kwargs) -> InterviewSessionListResponse:
        db = cls._get_db(**kwargs)

        # Get total count for pagination
        total = db.query(InterviewSession).filter(InterviewSession.interview_template_id == template_id).count()

        # Get paginated results
        sessions = db.query(InterviewSession).filter(InterviewSession.interview_template_id == template_id).offset(skip).limit(limit).all()

        # Convert to response format
        session_reads = [InterviewSessionRead.model_validate(session) for session in sessions]

        return InterviewSessionListResponse(
            success=True, message=f"Retrieved {len(session_reads)} sessions for template {template_id}", data=session_reads, total=total
        )

    @classmethod
    async def update_session(cls, session_id: int, update_data: InterviewSessionUpdate, **kwargs) -> InterviewSessionRead:
        db = cls._get_db(**kwargs)
        session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Handle session_metadata specially to preserve existing metadata
        update_dict = update_data.model_dump(exclude_unset=True)
        session_metadata = update_dict.pop("session_metadata", None)

        # Update all other fields normally
        for key, value in update_dict.items():
            setattr(session, key, value)

        # Handle session_metadata like update_kp does - preserve existing metadata
        if session_metadata is not None:
            if session.session_metadata is None:
                session.session_metadata = {}
            session.session_metadata.update(session_metadata)
            # Mark the field as modified for SQLAlchemy
            from sqlalchemy.orm.attributes import flag_modified

            flag_modified(session, "session_metadata")

        db.commit()
        db.refresh(session)
        return InterviewSessionRead.model_validate(session)

    @classmethod
    async def delete_session(cls, session_id: int, **kwargs) -> None:
        db = cls._get_db(**kwargs)
        session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
        if not session:
            raise ValueError(f"Session {session_id} not found")

        db.delete(session)
        db.commit()
