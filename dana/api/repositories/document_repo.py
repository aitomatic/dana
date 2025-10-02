from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from dana.api.core.schemas_v2 import ExtractionOutput
from dana.api.core.models import Document
from threading import Lock
from collections import defaultdict
from dana.api.services.extraction_service import get_extraction_service
import os
from pathlib import Path


class AbstractDocumentRepo(ABC):
    @classmethod
    @abstractmethod
    async def get_extraction(cls, document_id: int, deep_extract: bool | None = None, **kwargs) -> ExtractionOutput | None:
        pass


class SQLDocumentRepo(AbstractDocumentRepo):
    _locks = defaultdict(Lock)

    @classmethod
    def _get_db(cls, **kwargs) -> Session:
        db = kwargs.get("db")
        if db is None:
            raise ValueError(f"Missing db of type {Session} in kwargs: {kwargs}")
        return db

    @classmethod
    async def get_extraction(cls, document_id: int, deep_extract: bool | None = None, **kwargs) -> ExtractionOutput | None:
        db = cls._get_db(**kwargs)
        if deep_extract is None:
            original_document = db.query(Document).filter(Document.id == document_id).first()
            if original_document is None:
                raise ValueError(f"Original extraction not found for document_id: {document_id}")
            deep_extract = original_document.doc_metadata.get("deep_extracted")
        extracted_documents = db.query(Document).filter(Document.source_document_id == document_id).all()
        if not extracted_documents:
            return None

        abs_path: Path | None = None
        extraction_service = get_extraction_service()
        for extracted_document in extracted_documents:
            if deep_extract is None or extracted_document.doc_metadata.get("deep_extracted") == deep_extract:
                path = os.path.join(extraction_service.base_upload_directory, str(extracted_document.file_path))
                abs_path = Path(path).absolute()
                break

        if abs_path:
            return ExtractionOutput.model_validate_json(abs_path.read_text())

        return None
