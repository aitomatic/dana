"""
FastAPI Routes for POET Service
"""

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from opendxa.dana.poet.errors import POETTranspilationError
from opendxa.dana.poet.transpiler import PoetTranspiler
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
transpiler = PoetTranspiler()


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
        enhanced_implementation = transpiler.transpile(request.code, poet_config)

        return TranspileResponse(
            poet_implementation=enhanced_implementation,
            metadata=enhanced_implementation["metadata"],
        )
    except POETTranspilationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {e}")
