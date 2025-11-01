"""
LlamaStack Integration Module

Provides access to LlamaStack APIs beyond basic inference:
- Agent API: Agentic decision-making (we PROVIDE a plugin for this)
- VectorIO API: Knowledge and memory (we USE this, convert to Resources)
- Storage API: Telemetry and logging (we USE this, convert to Resources)
- Conversation API: Multi-turn session management (we USE this, convert to Timeline)
"""

from .agent import DanaEngine
from .client import LlamaStackClientManager
from .conversation import ConversationResource
from .resource import VectorIOResource

try:
    from .storage import StorageAPI, LlamaStackStorageAPI, TelemetryResource
except ImportError:
    # storage.py may not exist yet
    StorageAPI = None
    LlamaStackStorageAPI = None
    TelemetryResource = None


__all__ = [
    "DanaEngine",
    "LlamaStackClientManager",
    "ConversationResource",
    "VectorIOResource",
    "StorageAPI",
    "LlamaStackStorageAPI",
    "TelemetryResource",
]
