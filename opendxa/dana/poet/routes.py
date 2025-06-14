"""POET FastAPI Routes - REST endpoints for POET service"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from opendxa.common.utils.logging import DXA_LOGGER
from .transpiler import LocalPOETTranspiler
from .feedback import get_default_feedback_system
from .types import POETConfig, POETResult, POETTranspilationError, POETFeedbackError


# Pydantic models for API requests/responses
class TranspileRequest(BaseModel):
    """Request model for function transpilation"""

    function_code: str = Field(..., description="Complete function code including @poet decorator")
    language: str = Field(default="python", description="Source language")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for transpilation")


class POETConfigRequest(BaseModel):
    """POET configuration in request"""

    domain: Optional[str] = None
    optimize_for: Optional[str] = None
    retries: int = 3
    timeout: float = 30.0
    enable_monitoring: bool = True


class TranspileRequestWithConfig(TranspileRequest):
    """Extended transpile request with configuration"""

    config: POETConfigRequest = Field(default_factory=POETConfigRequest)


class TranspileResponse(BaseModel):
    """Response model for function transpilation"""

    poet_implementation: Dict[str, Any] = Field(..., description="Generated POET implementation")
    metadata: Dict[str, Any] = Field(..., description="Transpilation metadata")


class FeedbackRequest(BaseModel):
    """Request model for feedback submission"""

    execution_id: str = Field(..., description="Execution ID from POETResult")
    function_name: str = Field(..., description="Name of the POET function")
    feedback_payload: Any = Field(..., description="Feedback data in any format")


class FeedbackResponse(BaseModel):
    """Response model for feedback submission"""

    status: str = Field(..., description="Processing status")
    message: str = Field(..., description="Status message")


class FunctionStatusResponse(BaseModel):
    """Response model for function status"""

    status: str = Field(..., description="Function status")
    function_name: str = Field(..., description="Function name")
    current_version: Optional[str] = Field(None, description="Current version")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


# Create FastAPI router
router = APIRouter()


@router.get("/", summary="POET Service Information", description="Get information about the POET service")
async def poet_service_info():
    """Get POET service information"""
    return {
        "service": "POET",
        "version": "1.0.0-alpha",
        "status": "active",
        "description": "Perceive-Operate-Enforce-Train function enhancement service",
        "endpoints": {"transpile": "/transpile", "feedback": "/feedback", "functions": "/functions/{function_name}"},
    }


@router.post(
    "/transpile", response_model=TranspileResponse, summary="Transpile Function", description="Transpile a function with POET enhancements"
)
async def transpile_function(request: TranspileRequestWithConfig):
    """
    Transpile a function with POET P→O→E→(T) phases

    The function code should include the @poet decorator with parameters.
    Returns enhanced implementation with metadata about applied enhancements.
    """
    try:
        DXA_LOGGER.info(f"Transpilation request received for {request.language} function")

        # Convert request config to POETConfig
        config = POETConfig(
            domain=request.config.domain,
            optimize_for=request.config.optimize_for,
            retries=request.config.retries,
            timeout=request.config.timeout,
            enable_monitoring=request.config.enable_monitoring,
        )

        # Create transpiler and process
        transpiler = LocalPOETTranspiler()
        result = transpiler.transpile_function(function_code=request.function_code, config=config, context=request.context)

        # Format response
        response = TranspileResponse(poet_implementation={"code": result.code, "language": result.language}, metadata=result.metadata)

        DXA_LOGGER.info("Transpilation completed successfully")
        return response

    except POETTranspilationError as e:
        DXA_LOGGER.error(f"Transpilation failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Transpilation failed: {str(e)}")
    except Exception as e:
        DXA_LOGGER.error(f"Unexpected transpilation error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {str(e)}")


@router.post(
    "/feedback", response_model=FeedbackResponse, summary="Submit Feedback", description="Submit feedback for a POET function execution"
)
async def submit_feedback(request: FeedbackRequest):
    """
    Submit feedback for a POET function execution

    Accepts feedback in any format - the system will use LLM to understand
    and extract learning signals from the feedback.
    """
    try:
        DXA_LOGGER.info(f"Feedback request received for execution {request.execution_id}")

        # Create a mock POETResult for the feedback system
        # In a real implementation, we'd retrieve the actual execution context
        mock_result = POETResult(result={"mock": "result"}, function_name=request.function_name)
        mock_result._poet["execution_id"] = request.execution_id

        # Process feedback
        feedback_system = get_default_feedback_system()
        feedback_system.feedback(mock_result, request.feedback_payload)

        response = FeedbackResponse(status="processed", message=f"Feedback processed successfully for execution {request.execution_id}")

        DXA_LOGGER.info(f"Feedback processed for {request.function_name}")
        return response

    except POETFeedbackError as e:
        DXA_LOGGER.error(f"Feedback processing failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Feedback processing failed: {str(e)}")
    except Exception as e:
        DXA_LOGGER.error(f"Unexpected feedback error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {str(e)}")


@router.get(
    "/functions/{function_name}",
    response_model=FunctionStatusResponse,
    summary="Get Function Status",
    description="Get status and information about a POET function",
)
async def get_function_status(function_name: str):
    """
    Get status information for a POET function

    Returns current version, availability, and metadata about the function.
    """
    try:
        DXA_LOGGER.debug(f"Status request for function: {function_name}")

        # For Alpha: basic file-based status check
        from pathlib import Path

        poet_dir = Path(".poet") / function_name

        if not poet_dir.exists():
            response = FunctionStatusResponse(status="not_found", function_name=function_name)
        else:
            current_link = poet_dir / "current"
            if current_link.exists() and current_link.is_symlink():
                current_version = current_link.readlink().name
                response = FunctionStatusResponse(
                    status="available",
                    function_name=function_name,
                    current_version=current_version,
                    metadata={"local_path": str(poet_dir), "versions_available": [d.name for d in poet_dir.iterdir() if d.is_dir()]},
                )
            else:
                response = FunctionStatusResponse(
                    status="invalid", function_name=function_name, metadata={"error": "Invalid function structure"}
                )

        return response

    except Exception as e:
        DXA_LOGGER.error(f"Function status check failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Status check failed: {str(e)}")


@router.get(
    "/functions/{function_name}/feedback",
    summary="Get Function Feedback Summary",
    description="Get feedback summary and statistics for a function",
)
async def get_function_feedback(function_name: str):
    """
    Get feedback summary for a POET function

    Returns aggregated feedback statistics, sentiment analysis, and recent feedback.
    """
    try:
        DXA_LOGGER.debug(f"Feedback summary request for: {function_name}")

        feedback_system = get_default_feedback_system()
        summary = feedback_system.get_feedback_summary(function_name)

        return summary

    except Exception as e:
        DXA_LOGGER.error(f"Feedback summary failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Feedback summary failed: {str(e)}")


@router.get("/health", summary="Service Health Check", description="Check if POET service is healthy")
async def health_check():
    """Health check endpoint for POET service"""
    try:
        # Basic health checks
        from .transpiler import LocalPOETTranspiler

        transpiler = LocalPOETTranspiler()

        return {
            "status": "healthy",
            "service": "poet",
            "version": "1.0.0-alpha",
            "components": {"transpiler": "available", "feedback_system": "available", "llm_resource": "available"},
        }
    except Exception as e:
        DXA_LOGGER.error(f"Health check failed: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Service unhealthy: {str(e)}")
