from fastapi import APIRouter
from .kp_prompt_settings import router as kp_prompt_settings_router

router = APIRouter(prefix="/knowledge", tags=["knowledge-pack"])

router.include_router(kp_prompt_settings_router)
