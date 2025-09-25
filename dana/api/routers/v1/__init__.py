from fastapi import APIRouter
from .agent_test import router as agent_test_router
from .agents import router as agents_router

# Legacy routers (for endpoints not yet migrated)
from .api import router as api_router
from .chat import router as new_chat_router
from .conversations import router as new_conversations_router
from .documents import router as new_documents_router
from .domain_knowledge import router as domain_knowledge_router
from .extract_documents import router as extract_documents_router
from .smart_chat import router as smart_chat_router
from .topics import router as new_topics_router
from .workflow_execution import router as workflow_execution_router
from .smart_chat_v2 import router as smart_chat_v2_router
import os

router = APIRouter()

router.include_router(agents_router)
router.include_router(new_chat_router)
router.include_router(new_conversations_router)
router.include_router(new_documents_router)
router.include_router(new_topics_router)
router.include_router(domain_knowledge_router)
if os.getenv("USE_SMART_CHAT_V2", "true").lower() == "true":
    router.include_router(smart_chat_v2_router)
else:
    router.include_router(smart_chat_router)
router.include_router(extract_documents_router)
router.include_router(workflow_execution_router)
router.include_router(agent_test_router)
# Keep legacy api router for endpoints not yet migrated:
# - /run-na-file - Run Dana files
# - /write-files - Write multi-file projects to disk
# - /write-files-temp - Write multi-file projects to temp directory
# - /validate-multi-file - Validate multi-file project structure
# - /open-agent-folder - Open agent folder in file explorer
# - /task-status/{task_id} - Get background task status
# - /deep-train - Perform deep training on agents
router.include_router(api_router, prefix="/legacy")
