"""
Chat routers - routing for chat and conversation endpoints.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session

from dana.api.core.database import get_db
from dana.api.core.schemas import ChatRequest, ChatResponse
from dana.api.services.chat_service import get_chat_service, ChatService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def send_chat_message(request: ChatRequest, db: Session = Depends(get_db), chat_service: ChatService = Depends(get_chat_service)):
    """Send a chat message and get agent response."""
    try:
        logger.info(f"Received chat message for agent {request.agent_id}")

        response = await chat_service.process_chat_message(request, db, request.websocket_id)

        # Check if the response indicates an error
        if not response.success:
            if "conversation" in response.error.lower() and "not found" in response.error.lower():
                # For conversation not found errors, return 500
                raise HTTPException(status_code=500, detail=response.error)
            elif "not found" in response.error.lower():
                raise HTTPException(status_code=404, detail=response.error)
            elif "conversation" in response.error.lower():
                # For conversation errors, return 500
                raise HTTPException(status_code=500, detail=response.error)
            else:
                # For other errors (including service errors and execution errors), return 200 with success=False
                return response

        return response

    except RequestValidationError as e:
        # Handle Pydantic validation errors
        logger.error(f"Validation error in chat request: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")
