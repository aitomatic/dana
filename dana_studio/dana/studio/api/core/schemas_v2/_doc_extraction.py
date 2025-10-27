from __future__ import annotations
from pydantic import BaseModel


class PageContent(BaseModel):
    text: str
    page_number: int


class ExtractionOutput(BaseModel):
    original_filename: str
    source_document_id: int
    extraction_date: str
    total_pages: int
    documents: list[PageContent] = []
