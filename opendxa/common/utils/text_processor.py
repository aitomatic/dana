"""Text processing utilities for parsing responses and extracting content."""


class TextProcessor:
    """Utility class for parsing and processing text content."""

    # Constants for code extraction
    CODE_START_TAG = "<CODE>"
    CODE_END_TAG = "</CODE>"

    def __init__(self) -> None:
        """Initialize the TextProcessor."""
        pass

    def parse_by_key(self, response: str, key: str) -> str:
        """Parse a response to extract value by key.

        Args:
            response: The response text to parse
            key: The key to search for

        Returns:
            The value associated with the key, or "Unknown" if not found
        """
        if not response or not key:
            return "Unknown"

        lines = response.split("\n")
        for line in lines:
            if line.startswith(f"{key}:"):
                parts = line.split(": ", 1)
                if len(parts) >= 2:
                    return parts[1]
        return "Unknown"

    def parse_code(self, response: str) -> str | None:
        """Extract code content from response between CODE tags.

        Args:
            response: The response text containing code tags

        Returns:
            The extracted code content, or None if tags not found
        """
        if not response:
            return None

        start_index = response.find(self.CODE_START_TAG)
        end_index = response.find(self.CODE_END_TAG, start_index)

        if start_index == -1 or end_index == -1:
            return None

        # Extract the code between the tags
        code = response[start_index + len(self.CODE_START_TAG) : end_index].strip()
        return code
