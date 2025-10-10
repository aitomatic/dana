from fastapi import APIRouter
from .knowledge_pack import router as knowledge_pack_router
from .documents import router as documents_router

router = APIRouter()

router.include_router(knowledge_pack_router)
router.include_router(documents_router)
