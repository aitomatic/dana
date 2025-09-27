from fastapi import APIRouter
from .knowledge_pack import router as knowledge_pack_router

router = APIRouter()

router.include_router(knowledge_pack_router)
