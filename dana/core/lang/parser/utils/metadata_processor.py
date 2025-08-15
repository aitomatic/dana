"""
Metadata processing utilities for Dana parser.

This module handles extraction and attachment of metadata comments (## comments)
to AST nodes during parsing.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import re
from typing import Any

from dana.core.lang.ast import Program


class MetadataProcessor:
    """Processes metadata comments and attaches them to AST nodes."""

    def __init__(self):
        """Initialize the metadata processor."""
        self.metadata_comments: dict[int, str] = {}

    def extract_metadata_comments(self, program_text: str) -> dict[int, str]:
        """Extract ## comments from source text with their line numbers.

        Args:
            program_text: The source text to extract metadata from

        Returns:
            Dictionary mapping line numbers to metadata strings
        """
        metadata = {}
        lines = program_text.splitlines()

        for line_num, line in enumerate(lines, 1):
            # Look for ## comments - the text after ## becomes metadata
            match = re.search(r"#\s*#\s*(.*)$", line)
            if match:
                metadata_text = match.group(1).strip()
                if metadata_text:  # Only store non-empty metadata
                    metadata[line_num] = metadata_text

        self.metadata_comments = metadata
        return metadata

    def attach_metadata_to_ast(self, ast: Program) -> None:
        """Attach extracted metadata to AST nodes on matching lines.

        Args:
            ast: The AST to attach metadata to
        """
        if not self.metadata_comments:
            return

        # Recursively traverse AST and attach metadata to nodes on matching lines
        visited = set()
        self._traverse_and_attach_metadata(ast, visited)

    def _traverse_and_attach_metadata(self, node: Any, visited: set) -> None:
        """Recursively traverse AST nodes and attach metadata based on line numbers.

        Args:
            node: The AST node to process
            visited: Set of already visited nodes to prevent cycles
        """
        if node is None or id(node) in visited:
            return

        visited.add(id(node))

        # Check if this node has location information
        if hasattr(node, "location") and node.location and hasattr(node.location, "line"):
            line_num = node.location.line
            if line_num in self.metadata_comments:
                # Attach metadata to this node
                if not hasattr(node, "metadata"):
                    node.metadata = {}
                node.metadata["comment"] = self.metadata_comments[line_num]

        # Recursively process child nodes
        if hasattr(node, "__dict__"):
            for attr_name, attr_value in node.__dict__.items():
                # Skip private attributes and avoid cycles
                if attr_name.startswith("_"):
                    continue
                if isinstance(attr_value, list):
                    for item in attr_value:
                        self._traverse_and_attach_metadata(item, visited)
                elif hasattr(attr_value, "__dict__") and not isinstance(attr_value, str | int | float | bool):
                    self._traverse_and_attach_metadata(attr_value, visited)

    def clear_metadata(self) -> None:
        """Clear stored metadata comments."""
        self.metadata_comments.clear()
