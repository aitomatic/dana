"""
POET routers - handles POET service configuration and domain management.
Thin routing layer that delegates business logic to services.
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/poet", tags=["poet"])


@router.post("/configure")
async def configure_poet(config: dict[str, Any]):
    """
    Configure POET service settings.

    Args:
        config: Configuration request with domain, retries, timeout, enable_training

    Returns:
        Configuration response with updated settings
    """
    try:
        logger.info("Received POET configuration request")

        # Extract configuration parameters
        domain = config.get("domain")
        retries = config.get("retries", 3)
        timeout = config.get("timeout", 30)
        enable_training = config.get("enable_training", False)

        # Apply configuration (placeholder implementation)
        # In a real implementation, this would configure the POET service

        return {
            "message": "POET configuration updated successfully",
            "config": {"domain": domain, "retries": retries, "timeout": timeout, "enable_training": enable_training},
        }

    except Exception as e:
        logger.error(f"Error configuring POET: {e}")
        raise HTTPException(status_code=500, detail=f"POET configuration failed: {str(e)}")


@router.get("/domains")
async def get_poet_domains():
    """
    Get available POET domains.

    Returns:
        List of available domains
    """
    try:
        logger.info("Received request for POET domains")

        # Return available domains (placeholder implementation)
        # In a real implementation, this would query the POET service for available domains
        domains = ["general", "technical", "business", "creative", "educational", "healthcare", "finance", "legal"]

        return {"domains": domains}

    except Exception as e:
        logger.error(f"Error getting POET domains: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get domains: {str(e)}")
