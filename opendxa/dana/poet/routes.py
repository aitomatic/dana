"""POET FastAPI Routes - REST endpoints for POET service"""

import ast
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from opendxa.common.mixins.loggable import Loggable

from .feedback import get_default_feedback_system
from .storage import get_default_storage
from .types import POETConfig, POETFeedbackError, POETResult, POETTranspilationError


# Pydantic models for API requests/responses
class TranspileRequest(BaseModel):
    """Request model for function transpilation"""

    function_code: str = Field(..., description="Complete function code including @poet decorator")
    language: str = Field(default="python", description="Source language")
    context: dict[str, Any] | None = Field(None, description="Additional context for transpilation")


class POETConfigRequest(BaseModel):
    """Request model for POET configuration"""

    domain: str | None = Field(None, description="Domain for function enhancement")
    optimize_for: str | None = Field(None, description="Optimization target")
    retries: int = Field(default=3, description="Number of retries")
    timeout: int = Field(default=30, description="Timeout in seconds")
    enable_monitoring: bool = Field(default=True, description="Enable monitoring")


class TranspileRequestWithConfig(TranspileRequest):
    """Extended transpile request with configuration"""

    config: POETConfigRequest = Field(default_factory=lambda: POETConfigRequest(domain=None, optimize_for=None))


class TranspileResponse(BaseModel):
    """Response model for function transpilation"""

    poet_implementation: dict[str, Any] = Field(..., description="Generated POET implementation")
    metadata: dict[str, Any] = Field(..., description="Transpilation metadata")


class FeedbackRequest(BaseModel):
    """Request model for feedback submission"""

    execution_id: str = Field(..., description="Execution ID")
    function_name: str = Field(..., description="Function name")
    feedback_payload: Any = Field(..., description="Feedback data in any format")


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


def _validate_function_code(code: str) -> tuple[str, str]:
    """Validate function code and extract function name and decorator"""
    try:
        # Parse the code to ensure it's valid Python
        tree = ast.parse(code)

        # Find the function definition
        function_def = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                function_def = node
                break

        if not function_def:
            raise POETTranspilationError("No function definition found in code")

        # Check for @poet decorator
        decorator_found = False
        for decorator in function_def.decorator_list:
            if isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Name) and decorator.func.id == "poet":
                    decorator_found = True
                    break

        if not decorator_found:
            raise POETTranspilationError("Missing @poet decorator")

        return function_def.name, code

    except SyntaxError as e:
        raise POETTranspilationError(f"Invalid Python code: {str(e)}")


def _generate_enhanced_code(function_name: str, original_code: str, config: POETConfig, context: dict[str, Any] | None) -> dict[str, Any]:
    """Generate enhanced function code with POET phases"""
    # TODO: Implement actual code generation
    # For now, return a placeholder implementation
    enhanced_code = f"""
# Enhanced implementation of {function_name}
# Original code:
{original_code}

# Perceive phase
def perceive_{function_name}(data: dict) -> dict:
    \"\"\"Perceive phase: Validate and preprocess input data\"\"\"
    # TODO: Implement domain-specific validation
    return data

# Operate phase (original function)
def operate_{function_name}(data: dict) -> Any:
    \"\"\"Operate phase: Core function logic\"\"\"
    {original_code}

# Enforce phase
def enforce_{function_name}(result: Any) -> Any:
    \"\"\"Enforce phase: Validate and postprocess output\"\"\"
    # TODO: Implement domain-specific validation
    return result

# Main enhanced function
def {function_name}(data: dict) -> Any:
    \"\"\"Enhanced function with POET phases\"\"\"
    # Perceive phase
    validated_data = perceive_{function_name}(data)
    
    # Operate phase
    result = operate_{function_name}(validated_data)
    
    # Enforce phase
    final_result = enforce_{function_name}(result)
    
    return final_result
"""

    # Generate train code if optimize_for is specified
    train_code = None
    if config.optimize_for:
        train_code = f"""
# Train phase for {function_name}
def train_{function_name}(feedback_data: dict) -> None:
    \"\"\"Train phase: Learn from feedback\"\"\"
    # TODO: Implement optimization for {config.optimize_for}
    pass
"""

    return {
        "enhanced_code": enhanced_code,
        "train_code": train_code,
        "metadata": {
            "function_name": function_name,
            "domain": config.domain,
            "optimize_for": config.optimize_for,
            "retries": config.retries,
            "timeout": config.timeout,
            "enable_monitoring": config.enable_monitoring,
            "context": context,
        },
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
    logger = Loggable.get_class_logger()
    try:
        logger.info(f"Transpilation request received for {request.language} function")

        # Convert request config to POETConfig
        config = POETConfig(
            domain=request.config.domain,
            optimize_for=request.config.optimize_for,
            retries=request.config.retries,
            timeout=request.config.timeout,
            enable_monitoring=request.config.enable_monitoring,
        )

        # Validate function code and extract function name
        function_name, original_code = _validate_function_code(request.function_code)

        # Generate enhanced code
        enhanced_implementation = _generate_enhanced_code(
            function_name=function_name, original_code=original_code, config=config, context=request.context
        )

        # Determine module file path for per-module .dana cache collocation
        module_file = None
        if request.context and "module_file" in request.context:
            module_file = request.context["module_file"]

        # Store enhanced function in per-module .dana/poet directory
        storage = get_default_storage(module_file=module_file)
        version = "v1"  # TODO: Implement proper versioning
        storage.store_enhanced_function(
            function_name=function_name,
            version=version,
            enhanced_code=enhanced_implementation["enhanced_code"],
            metadata=enhanced_implementation["metadata"],
            train_code=enhanced_implementation["train_code"],
        )

        return TranspileResponse(poet_implementation=enhanced_implementation, metadata=enhanced_implementation["metadata"])

    except POETTranspilationError as e:
        logger.error(f"Transpilation failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during transpilation: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/feedback", summary="Submit Feedback", description="Submit feedback for POET function execution")
async def submit_feedback(request: FeedbackRequest):
    """Submit feedback for POET function execution"""
    try:
        logger = Loggable.get_class_logger()
        logger.info(f"Feedback received for {request.function_name} execution {request.execution_id}")

        # Get feedback system
        feedback_system = get_default_feedback_system()

        # Create POETResult for feedback processing
        result = POETResult(
            result=None,  # We don't have the original result
            function_name=request.function_name,
            version="unknown",  # Version will be loaded from storage if available
        )

        # Process feedback
        feedback_system.feedback(result, request.feedback_payload)
        return {"status": "success", "message": "Feedback processed successfully"}

    except POETFeedbackError as e:
        logger.error(f"Feedback processing failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Feedback processing failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected feedback error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {str(e)}")


@router.get("/functions/{function_name}", summary="Get Function Status", description="Get status information for a POET function")
async def get_function_status(function_name: str):
    """Get status information for a POET function"""
    logger = Loggable.get_class_logger()
    try:
        storage = get_default_storage()
        feedback_system = get_default_feedback_system()

        # Get all versions for the function
        versions = storage.list_function_versions(function_name)
        if not versions:
            raise HTTPException(status_code=404, detail=f"Function '{function_name}' not found")
        latest_version = versions[-1]
        metadata = storage.load_metadata(function_name, latest_version)

        # Get feedback summary
        feedback_summary = feedback_system.get_feedback_summary(function_name)

        return {
            "function_name": function_name,
            "latest_version": latest_version,
            "metadata": metadata,
            "feedback_summary": feedback_summary,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get function status: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {str(e)}")


@router.get("/health", summary="Service Health Check", description="Check if POET service is healthy")
async def health_check():
    """Health check endpoint for POET service"""
    try:
        # Basic health checks
        return {
            "status": "healthy",
            "service": "poet",
            "version": "1.0.0-alpha",
            "components": {"api": "available"},
        }
    except Exception as e:
        logger = Loggable.get_class_logger()
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Service unhealthy: {str(e)}")
