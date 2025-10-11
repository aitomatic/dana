"""
Workflow Execution Router - API endpoints for real-time workflow execution.

This router provides endpoints for starting, monitoring, and controlling
workflow execution with real-time status updates.
"""

import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import json
import asyncio
from typing import AsyncGenerator

from dana.api.core.schemas import (
    WorkflowExecutionRequest,
    WorkflowExecutionResponse,
    WorkflowExecutionStatus,
    WorkflowExecutionControl,
    WorkflowExecutionControlResponse,
)
from dana.api.services.workflow_execution_service import get_workflow_execution_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workflow-execution", tags=["workflow-execution"])


@router.post("/start", response_model=WorkflowExecutionResponse)
async def start_workflow_execution(request: WorkflowExecutionRequest):
    """Start a new workflow execution."""
    try:
        service = get_workflow_execution_service()
        response = service.start_execution(request)

        if not response.success:
            raise HTTPException(status_code=400, detail=response.error)

        return response

    except Exception as e:
        logger.error(f"Failed to start workflow execution: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start workflow execution: {str(e)}")


@router.get("/status/{execution_id}", response_model=WorkflowExecutionStatus)
async def get_execution_status(execution_id: str):
    """Get current execution status."""
    try:
        service = get_workflow_execution_service()
        status = service.get_execution_status(execution_id)

        if not status:
            raise HTTPException(status_code=404, detail="Execution not found")

        return status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get execution status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get execution status: {str(e)}")


@router.post("/control", response_model=WorkflowExecutionControlResponse)
async def control_execution(control: WorkflowExecutionControl):
    """Control workflow execution (stop, pause, resume, cancel)."""
    try:
        service = get_workflow_execution_service()
        response = service.control_execution(control)

        if not response.success:
            raise HTTPException(status_code=400, detail=response.error)

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to control execution: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to control execution: {str(e)}")


@router.get("/stream/{execution_id}")
async def stream_execution_updates(execution_id: str):
    """Stream real-time execution updates using Server-Sent Events."""

    async def generate_updates() -> AsyncGenerator[str, None]:
        service = get_workflow_execution_service()

        try:
            while True:
                # Get current status
                status = service.get_execution_status(execution_id)
                if not status:
                    yield f"data: {json.dumps({'error': 'Execution not found'})}\n\n"
                    break

                # Send status update
                yield f"data: {json.dumps(status.model_dump())}\n\n"

                # Check if execution is complete
                if status.status in ["completed", "failed", "cancelled"]:
                    break

                # Wait before next update
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Error streaming execution updates: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate_updates(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        },
    )


@router.get("/active")
async def get_active_executions():
    """Get list of all active workflow executions."""
    try:
        # NOTE : TEMPORARY COMMENTED OUT NEXT LINE
        # service = get_workflow_execution_service()
        # END NOTE

        # Get all executions from the service
        # This would need to be exposed in the service
        active_executions = []

        # For now, return empty list
        # TODO: Implement get_all_executions method in service

        return {"executions": active_executions}

    except Exception as e:
        logger.error(f"Failed to get active executions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get active executions: {str(e)}")
