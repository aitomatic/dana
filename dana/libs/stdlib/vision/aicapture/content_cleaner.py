import re
from typing import Any


class ContentCleaner:
    """
    Simple content cleaner for VisionParser output.

    Handles two specific issues:
    1. Base64 encoded text from images
    2. Repetitive HTML spaces (&nbsp;)
    """

    def __init__(self) -> None:
        """Initialize with regex patterns for the two specific issues."""
        # Base64 pattern: matches long sequences of base64 characters (50+ chars)
        self.base64_pattern = re.compile(r"[A-Za-z0-9+/]{50,}={0,2}", re.MULTILINE)

        # Repetitive &nbsp; pattern: 5 or more consecutive
        self.nbsp_pattern = re.compile(r"(?:&nbsp;){5,}", re.IGNORECASE)

    def clean_content(self, content: str) -> str:
        """
        Clean content by removing base64 text and repetitive HTML spaces.

        Args:
            content (str): The content to clean

        Returns:
            str: Cleaned content
        """
        if not content or not isinstance(content, str):
            return content

        # Remove base64 strings
        cleaned = self.base64_pattern.sub("", content)

        # Remove repetitive &nbsp; sequences
        cleaned = self.nbsp_pattern.sub(" ", cleaned)

        return cleaned.strip()

    def clean_page_content(self, page_content: str) -> str:
        """
        Clean a single page's content.

        Args:
            page_content (str): Page content to clean

        Returns:
            str: Cleaned page content
        """
        return self.clean_content(page_content)


def clean_vision_parser_output(result: dict[str, Any]) -> dict[str, Any]:
    """
    Clean VisionParser output by removing base64 and repetitive spaces.

    Args:
        result (Dict): VisionParser result dictionary

    Returns:
        Dict: Cleaned result dictionary
    """
    if not result or "file_object" not in result:
        return result

    cleaner = ContentCleaner()

    # Clean all pages
    if "pages" in result["file_object"]:
        for page in result["file_object"]["pages"]:
            if "page_content" in page:
                page["page_content"] = cleaner.clean_page_content(page["page_content"])

    return result
