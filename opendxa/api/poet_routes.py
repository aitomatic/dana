"""
FastAPI Routes for POET Service
"""

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from opendxa.dana.poet.types import POETConfig


class POETRequest(BaseModel):
    """Request model for POET decorator configuration"""

    domain: str | None = Field(None, description="Domain context for POET enhancement")
    retries: int = Field(1, description="Number of retries for failed operations")
    timeout: float | None = Field(None, description="Timeout for operations in seconds")
    enable_training: bool = Field(True, description="Enable training phase")


class POETResponse(BaseModel):
    """Response model for POET configuration"""

    message: str = Field(..., description="Response message")
    config: dict[str, Any] = Field(..., description="POET configuration applied")


router = APIRouter(prefix="/poet", tags=["POET"])


@router.post("/configure", response_model=POETResponse)
async def configure_poet(request: POETRequest) -> POETResponse:
    """
    Configure POET decorator with specified parameters.

    This endpoint creates a POET configuration that can be used
    to enhance Dana functions with domain-specific intelligence.
    """
    try:
        # Create POET configuration
        config = POETConfig(
            domain=request.domain, retries=request.retries, timeout=request.timeout, enable_training=request.enable_training
        )

        return POETResponse(
            message="POET configuration created successfully",
            config={
                "domain": config.domain,
                "retries": config.retries,
                "timeout": config.timeout,
                "enable_training": config.enable_training,
            },
        )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to configure POET: {str(e)}")


@router.get("/domains")
async def list_domains() -> dict[str, list[str]]:
    """
    List available POET domains.

    Returns predefined domains that can be used with POET decorators
    for domain-specific enhancements.
    """
    return {
        "domains": [
            "healthcare",
            "finance",
            "manufacturing",
            "building_management",
            "text_classification",
            "mathematical_operations",
            "data_processing",
        ]
    }
