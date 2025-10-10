from adana.core.resource.base_resource import BaseResource
from .extract import ExtractResource
from .fetch import FetchResource
from .format import FormatResource
from .process import ProcessResource
from .synthesize import SynthesizeResource
from .search import SearchResource

_resources_for_workflows: dict[str, BaseResource] = {
    "search": SearchResource(resource_id="search"),
    "fetch": FetchResource(resource_id="fetch"),
    "extract": ExtractResource(resource_id="extract"),
    "process": ProcessResource(resource_id="process"),
    "synthesize": SynthesizeResource(resource_id="synthesize"),
    "format": FormatResource(resource_id="format"),
}


__all__ = ["ExtractResource", "FetchResource", "FormatResource", "ProcessResource", "SynthesizeResource", "SearchResource"]
