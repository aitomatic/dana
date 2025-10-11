"""
Vision Capture module for transforming parsed document content into structured data
based on predefined templates.
"""

from typing import Any

from .vision_models import VisionModel, create_default_vision_model
from .vision_parser import VisionParser


class VisionCapture:
    """
    Main class for transforming parsed document content into structured data
    using predefined templates.
    """

    def __init__(
        self,
        vision_model: VisionModel | None = None,
        vision_parser: VisionParser | None = None,
    ):
        self.vision_model = vision_model or create_default_vision_model()
        self.vision_parser = vision_parser or VisionParser(vision_model=self.vision_model)
        # self.vision_parser.invalidate_cache = True

    async def _parse_file(self, file_path: str) -> dict[str, Any]:
        """
        Parse the document using the vision parser.
        """
        if file_path.endswith(".pdf"):
            return await self.vision_parser.process_pdf_async(file_path)
        elif file_path.endswith(tuple(self.vision_parser.SUPPORTED_IMAGE_FORMATS)):
            return await self.vision_parser.process_image_async(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_path}")

    async def capture(self, file_path: str, template: str) -> str:
        """
        Capture the document using the vision parser and template.
        """
        doc_json = await self._parse_file(file_path)
        # Extract content from file_object structure
        content = "\n".join(page["page_content"] for page in doc_json["file_object"]["pages"])
        return await self._capture_content(content, template)

    async def _capture_content(self, content: str, template: str) -> str:
        """
        Capture the content using the vision model and template.
        """
        message = (
            f"Extract information and output in the template format: \n"
            f"<template>{template}</template>\n"
            f"Content: \n"
            f"<content>{content}</content>"
        )
        messages = [
            {"role": "user", "content": message},
        ]
        # from pprint import pprint

        # pprint(messages)
        return await self.vision_model.process_text_async(messages)
