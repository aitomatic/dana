from .agents import WebResearchAgent
from .resources import PingResource
from .workflows.web_research import (
    FactFindingWorkflow,
    GoogleLookupWorkflow,
    ResearchSynthesisWorkflow,
    StructuredDataNavigationWorkflow,
)

# Memory module requires optional dependencies (lancedb, sentence-transformers)
# Import lazily to avoid errors when dependencies aren't installed
try:
    from .memory import Memory, MemoryStore

    _MEMORY_AVAILABLE = True
except ImportError:
    Memory = None  # type: ignore
    MemoryStore = None  # type: ignore
    _MEMORY_AVAILABLE = False


__all__ = [
    "Memory",
    "MemoryStore",
    "WebResearchAgent",
    "PingResource",
    "FactFindingWorkflow",
    "GoogleLookupWorkflow",
    "ResearchSynthesisWorkflow",
    "StructuredDataNavigationWorkflow",
]


def memory_available() -> bool:
    """Check if the memory module is available (dependencies installed)."""
    return _MEMORY_AVAILABLE
