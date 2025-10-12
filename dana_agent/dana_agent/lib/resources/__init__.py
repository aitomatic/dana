from .ping_resource import PingResource
from .web_searcher import WebSearcherResource
from .workflow_selector import WorkflowSelectorResource


_web_searcher = WebSearcherResource()
_workflow_selector = WorkflowSelectorResource()

__all__ = [
    "PingResource",
    "WebSearcherResource",
    "_web_searcher",
    "WorkflowSelectorResource",
    "_workflow_selector",
]
