from fastapi import APIRouter
from .prompts import router as prompts_router

router = APIRouter(prefix="/settings", tags=["settings"])

router.include_router(prompts_router)
