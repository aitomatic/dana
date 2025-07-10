
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import db, schemas
from ..services import TopicService

router = APIRouter(prefix="/topics", tags=["topics"])


def get_db():
    db_session = db.SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()


def get_topic_service():
    return TopicService()


@router.get("/", response_model=list[schemas.TopicRead])
async def list_topics(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), service: TopicService = Depends(get_topic_service)):
    return service.get_topics(db, skip=skip, limit=limit)


@router.get("/{topic_id}", response_model=schemas.TopicRead)
async def get_topic(topic_id: int, db: Session = Depends(get_db), service: TopicService = Depends(get_topic_service)):
    topic = service.get_topic(db, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic


@router.post("/", response_model=schemas.TopicRead)
async def create_topic(topic: schemas.TopicCreate, db: Session = Depends(get_db), service: TopicService = Depends(get_topic_service)):
    return service.create_topic(db, topic)


@router.put("/{topic_id}", response_model=schemas.TopicRead)
async def update_topic(
    topic_id: int, topic: schemas.TopicCreate, db: Session = Depends(get_db), service: TopicService = Depends(get_topic_service)
):
    updated = service.update_topic(db, topic_id, topic)
    if not updated:
        raise HTTPException(status_code=404, detail="Topic not found")
    return updated


@router.delete("/{topic_id}")
async def delete_topic(topic_id: int, db: Session = Depends(get_db), service: TopicService = Depends(get_topic_service)):
    success = service.delete_topic(db, topic_id)
    if not success:
        raise HTTPException(status_code=404, detail="Topic not found")
    return {"message": "Topic deleted successfully"}
