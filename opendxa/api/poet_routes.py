"""
FastAPI Routes for POET Service
"""

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from opendxa.dana.poet.errors import POETTranspilationError
from opendxa.dana.poet.transpiler import POETTranspiler
from opendxa.dana.poet.types import POETConfig


class TranspileRequest(BaseModel):
    """Request model for function transpilation"""

    code: str = Field(..., description="Complete function code including @poet decorator")
    config: dict = Field(..., description="POET configuration dictionary")


class TranspileResponse(BaseModel):
    """Response model for function transpilation"""

    poet_implementation: dict[str, Any] = Field(..., description="Generated POET implementation")
    metadata: dict[str, Any] = Field(..., description="Transpilation metadata")


router = APIRouter()
transpiler = POETTranspiler()


@router.post(
    "/transpile",
    response_model=TranspileResponse,
    summary="Transpile Function",
    description="Transpile a function with POET enhancements",
)
async def transpile_function(request: TranspileRequest):
    """Transpile a function with POET P->O->E->(T) phases"""
    try:
        poet_config = POETConfig(**request.config)

        # Create a mock function from the code string for transpilation
        # This is a temporary workaround - in production, the API should receive actual function objects
        import types

        mock_func = types.FunctionType(code=compile(request.code, "<string>", "exec"), globals={}, name="mock_function")

        enhanced_implementation = transpiler.transpile(mock_func, poet_config)

        return TranspileResponse(
            poet_implementation={"code": enhanced_implementation, "language": "dana"},
            metadata={"status": "success", "transpiler": "POETTranspiler"},
        )
    except POETTranspilationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {e}")
