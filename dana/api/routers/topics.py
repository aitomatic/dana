"""
Topic routers - routing for topic management endpoints.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from dana.api.core.database import get_db
from dana.api.core.schemas import TopicCreate, TopicRead
from dana.api.services.topic_service import get_topic_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/topics", tags=["topics"])


@router.post("/", response_model=TopicRead)
async def create_topic(request: TopicCreate, db: Session = Depends(get_db), topic_service=Depends(get_topic_service)):
    """Create a new topic."""
    try:
        topic = await topic_service.create_topic(request, db)
        return topic

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in create topic endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{topic_id}", response_model=TopicRead)
async def get_topic(topic_id: int, db: Session = Depends(get_db), topic_service=Depends(get_topic_service)):
    """Get a topic by ID."""
    try:
        topic = await topic_service.get_topic(topic_id, db)
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")
        return topic

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get topic endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=list[TopicRead])
async def list_topics(
    search: str | None = None, limit: int = 100, offset: int = 0, db: Session = Depends(get_db), topic_service=Depends(get_topic_service)
):
    """List topics with optional search filtering."""
    try:
        topics = await topic_service.list_topics(limit=limit, offset=offset, search=search, db_session=db)
        return topics

    except Exception as e:
        logger.error(f"Error in list topics endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{topic_id}", response_model=TopicRead)
async def update_topic(topic_id: int, topic_data: TopicCreate, db: Session = Depends(get_db), topic_service=Depends(get_topic_service)):
    """Update a topic."""
    try:
        updated_topic = await topic_service.update_topic(topic_id, topic_data, db)
        if not updated_topic:
            raise HTTPException(status_code=404, detail="Topic not found")
        return updated_topic

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update topic endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{topic_id}")
async def delete_topic(topic_id: int, force: bool = False, db: Session = Depends(get_db), topic_service=Depends(get_topic_service)):
    """Delete a topic. Use force=true to delete associated documents."""
    try:
        success = await topic_service.delete_topic(topic_id, db, force=force)
        if not success:
            raise HTTPException(status_code=404, detail="Topic not found")
        return {"message": "Topic deleted successfully"}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in delete topic endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
