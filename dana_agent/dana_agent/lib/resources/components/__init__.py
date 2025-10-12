from .content_extractor import ContentExtractor
from .web_fetcher import WebFetcher


_content_extractor = ContentExtractor()
_web_fetcher = WebFetcher()

__all__ = [
    "ContentExtractor",
    "WebFetcher",
    "_content_extractor",
    "_web_fetcher",
]
