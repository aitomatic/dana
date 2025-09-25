from fastapi import APIRouter
from .domain_knowledge_v2 import router as domain_knowledge_v2_router

router = APIRouter()

router.include_router(domain_knowledge_v2_router)
