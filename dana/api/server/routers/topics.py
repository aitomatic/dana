from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import schemas, db
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


@router.get("/", response_model=List[schemas.TopicRead])
def list_topics(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), topic_service: TopicService = Depends(get_topic_service)):
    return topic_service.get_topics(db, skip=skip, limit=limit)


@router.get("/{topic_id}", response_model=schemas.TopicRead)
def get_topic(topic_id: int, db: Session = Depends(get_db), topic_service: TopicService = Depends(get_topic_service)):
    topic = topic_service.get_topic(db, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic


@router.post("/", response_model=schemas.TopicRead)
def create_topic(topic: schemas.TopicCreate, db: Session = Depends(get_db), topic_service: TopicService = Depends(get_topic_service)):
    return topic_service.create_topic(db, topic)


@router.put("/{topic_id}", response_model=schemas.TopicRead)
def update_topic(
    topic_id: int, topic: schemas.TopicCreate, db: Session = Depends(get_db), topic_service: TopicService = Depends(get_topic_service)
):
    updated_topic = topic_service.update_topic(db, topic_id, topic)
    if not updated_topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return updated_topic


@router.delete("/{topic_id}")
def delete_topic(topic_id: int, db: Session = Depends(get_db), topic_service: TopicService = Depends(get_topic_service)):
    success = topic_service.delete_topic(db, topic_id)
    if not success:
        raise HTTPException(status_code=404, detail="Topic not found")
    return {"message": "Topic deleted successfully"}
