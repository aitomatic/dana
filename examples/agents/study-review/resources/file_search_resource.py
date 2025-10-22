"""
FileSearchResource - Reads study material files from disk.

This resource handles:
- Searching for study material files using glob patterns
- Reading and parsing markdown files
- Extracting sections and content structure
- Returns structured data for other agents to use
"""

import os
import sys
import glob
from pathlib import Path
from typing import Any, Dict, List

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dana.common.protocols.types import DictParams
from dana.common.protocols.war import tool_use
from dana.core.resource.base_resource import BaseResource


class FileSearchResource(BaseResource):
    """
    Resource for searching and reading study material files.

    Features:
    - Glob pattern matching for file discovery
    - Markdown file parsing and section extraction
    - Content structure identification
    - Error handling for missing files
    """

    def __init__(self, resource_id: str | None = None, **kwargs):
        """Initialize the FileSearchResource."""
        super().__init__(resource_type="file-search", resource_id=resource_id or "file-search", **kwargs)

    @tool_use
    def search_and_read(self, file_pattern: str = "study_*.md", **kwargs) -> DictParams:
        """
        Search for and read study material files.

        Args:
            file_pattern: Glob pattern for files (default: "study_*.md")

        Returns:
            {
                "success": bool,
                "content": str,  # Combined content from all files
                "sections": [    # Parsed sections
                    {"title": "Rubber Gasket Design", "content": "..."},
                    {"title": "Air Duct Design", "content": "..."},
                    ...
                ],
                "files_read": ["study_outline.md", "study_material.md"],
                "error": str (if failed)
            }
        """
        try:
            # Get the data directory path
            data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
            search_pattern = os.path.join(data_dir, file_pattern)

            # Find matching files
            matching_files = glob.glob(search_pattern)

            if not matching_files:
                return {
                    "success": False,
                    "content": "",
                    "sections": [],
                    "files_read": [],
                    "error": f"No files found matching pattern: {file_pattern}",
                }

            # Read and combine content from all files
            combined_content = ""
            sections = []
            files_read = []

            for file_path in matching_files:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        combined_content += f"\n\n---\n# {os.path.basename(file_path)}\n\n{content}"

                        # Extract sections from this file
                        file_sections = self._extract_sections(content, os.path.basename(file_path))
                        sections.extend(file_sections)

                        files_read.append(os.path.basename(file_path))

                except Exception as e:
                    return {
                        "success": False,
                        "content": "",
                        "sections": [],
                        "files_read": [],
                        "error": f"Error reading file {file_path}: {str(e)}",
                    }

            return {"success": True, "content": combined_content.strip(), "sections": sections, "files_read": files_read, "error": None}

        except Exception as e:
            return {"success": False, "content": "", "sections": [], "files_read": [], "error": f"File search failed: {str(e)}"}

    def _extract_sections(self, content: str, filename: str) -> List[Dict[str, str]]:
        """
        Extract sections from markdown content.

        Args:
            content: Markdown content to parse
            filename: Name of the file for context

        Returns:
            List of section dictionaries with title and content
        """
        sections = []
        lines = content.split("\n")
        current_section = None
        current_content = []

        for line in lines:
            # Check for section headers (## or ###)
            if line.startswith("##") and not line.startswith("###"):
                # Save previous section if exists
                if current_section:
                    sections.append({"title": current_section, "content": "\n".join(current_content).strip(), "source_file": filename})

                # Start new section
                current_section = line.strip("# ").strip()
                current_content = []
            else:
                current_content.append(line)

        # Add the last section
        if current_section:
            sections.append({"title": current_section, "content": "\n".join(current_content).strip(), "source_file": filename})

        # If no sections found, treat the whole content as one section
        if not sections and content.strip():
            sections.append({"title": f"Content from {filename}", "content": content.strip(), "source_file": filename})

        return sections
