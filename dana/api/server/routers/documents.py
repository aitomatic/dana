
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from .. import db, schemas
from ..services import DocumentService, FileStorageService

router = APIRouter(prefix="/documents", tags=["documents"])


def get_db():
    db_session = db.SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()


def get_file_storage_service():
    return FileStorageService()


def get_document_service():
    file_storage = FileStorageService()
    return DocumentService(file_storage)


@router.get("/", response_model=list[schemas.DocumentRead])
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    topic_id: int | None = None,
    db: Session = Depends(get_db),
    document_service: DocumentService = Depends(get_document_service),
):
    return document_service.get_documents(db, skip=skip, limit=limit, topic_id=topic_id)


@router.get("/{document_id}", response_model=schemas.DocumentRead)
async def get_document(document_id: int, db: Session = Depends(get_db), document_service: DocumentService = Depends(get_document_service)):
    document = document_service.get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.post("/", response_model=schemas.DocumentRead)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str | None = Form(None),
    topic_id: int | None = Form(None),
    db: Session = Depends(get_db),
    document_service: DocumentService = Depends(get_document_service),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    document_data = schemas.DocumentCreate(original_filename=file.filename, topic_id=topic_id, agent_id=None)

    return document_service.create_document(db, file, document_data)


@router.get("/{document_id}/download")
def download_document(document_id: int, db: Session = Depends(get_db), document_service: DocumentService = Depends(get_document_service)):
    file_path = document_service.get_file_path(document_id, db)
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="Document file not found")

    document = document_service.get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return FileResponse(path=file_path, filename=str(document.original_filename), media_type=str(document.mime_type))


@router.put("/{document_id}", response_model=schemas.DocumentRead)
async def update_document(
    document_id: int,
    document_data: schemas.DocumentUpdate,
    db: Session = Depends(get_db),
    document_service: DocumentService = Depends(get_document_service),
):
    updated_document = document_service.update_document(db, document_id, document_data)
    if not updated_document:
        raise HTTPException(status_code=404, detail="Document not found")
    return updated_document


@router.delete("/{document_id}")
async def delete_document(document_id: int, db: Session = Depends(get_db), document_service: DocumentService = Depends(get_document_service)):
    success = document_service.delete_document(db, document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Document deleted successfully"}
