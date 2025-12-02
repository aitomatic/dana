from fastapi import APIRouter
from .settings import router as settings_router
from .knowledge_pack import router as knowledge_pack_router

router = APIRouter()

router.include_router(settings_router)
router.include_router(knowledge_pack_router)
