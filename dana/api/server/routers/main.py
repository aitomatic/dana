import os

from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "healthy", "service": "Dana API"}


@router.get("/api")
def get_root_info():
    """Get root API information"""
    return {
        "service": "Dana API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "agents": "/api/agents",
            "chat": "/api/chat",
            "conversations": "/api/conversations",
            "documents": "/api/documents",
            "topics": "/api/topics",
            "agent-test": "/api/agent-test",
        },
    }


@router.get("/")
def serve_react_index():
    static_dir = os.path.join(os.path.dirname(__file__), "../static")
    index_path = os.path.abspath(os.path.join(static_dir, "index.html"))
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse({"error": "index.html not found"}, status_code=404)
