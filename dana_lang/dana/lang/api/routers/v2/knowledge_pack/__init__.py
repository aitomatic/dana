"""
Domain Knowledge routers - API endpoints for managing agent domain knowledge trees.
"""

import logging
from fastapi import APIRouter
from .kp_managing import router as kp_managing_router
from .kp_structuring import router as kp_structuring_router
from .kp_generation import router as kp_generation_router
from .kp_interview_template import router as kp_interview_template_router

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/knowledge")
router.include_router(kp_managing_router, tags=["knowledge-pack-mgmt"])
router.include_router(kp_structuring_router, tags=["knowledge-pack-structuring"])
router.include_router(kp_generation_router, tags=["knowledge-pack-generation"])
router.include_router(kp_interview_template_router, tags=["knowledge-pack-interview-template"])
