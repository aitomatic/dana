import os

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse

router = APIRouter()


# --- WebSocket Connection Manager ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo the message back for now
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)


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
            "extract-documents": "/api/extract-documents",
        },
    }


@router.get("/")
def serve_react_index():
    static_dir = os.path.join(os.path.dirname(__file__), "../server/static")
    index_path = os.path.abspath(os.path.join(static_dir, "index.html"))
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse({"error": "index.html not found"}, status_code=404)
