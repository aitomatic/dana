"""
ReadFileResource - Read file contents with line range and size limit support.

This resource handles:
- Reading entire files or specific line ranges
- File size validation and automatic downgrades
- Character and line limits
- Path validation and security checks
- Error handling for missing files and permissions
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dana.common.protocols.types import DictParams
from dana.common.protocols.war import tool_use
from dana.core.resource.base_resource import BaseResource


class ReadFileResource(BaseResource):
    """
    Resource for reading file contents with flexible options.

    Features:
    - Read entire file or specific line ranges (1-indexed)
    - Automatic downgrade to line ranges for large files
    - Character and line limits for safety
    - Path validation to prevent directory traversal
    - Comprehensive error handling
    """

    def __init__(self, resource_id: str | None = None, workspace_root: str | None = None, **kwargs):
        """
        Initialize the ReadFileResource.

        Args:
            resource_id: Unique identifier for this resource
            workspace_root: Root directory for relative paths (defaults to cwd)
            **kwargs: Additional arguments passed to BaseResource
        """
        super().__init__(resource_type="read-file", resource_id=resource_id or "read-file", **kwargs)
        self.workspace_root = Path(workspace_root) if workspace_root else Path.cwd()

    @tool_use
    def read(
        self,
        relative_workspace_path: str,
        read_entire_file: bool = True,
        start_line_one_indexed: int | None = None,
        end_line_one_indexed_inclusive: int | None = None,
        max_lines: int = 1000,
        max_chars: int = 100000,
        **kwargs,
    ) -> DictParams:
        """
        Read file contents with optional line range and size limits.

        Args:
            relative_workspace_path: Path to file relative to workspace root
            read_entire_file: Whether to read the entire file (default: True)
            start_line_one_indexed: Starting line number (1-indexed, optional)
            end_line_one_indexed_inclusive: Ending line number inclusive (1-indexed, optional)
            max_lines: Maximum number of lines to read (default: 1000)
            max_chars: Maximum number of characters to read (default: 100000)
            **kwargs: Additional parameters (not used)

        Returns:
            {
                "success": bool,
                "contents": str,
                "did_downgrade_to_line_range": bool,
                "did_shorten_line_range": bool,
                "did_shorten_char_range": bool,
                "relative_workspace_path": str,
                "total_lines": int,
                "error": str (if failed)
            }
        """
        try:
            # Validate and resolve file path
            file_path = self._resolve_path(relative_workspace_path)
            if not file_path:
                return {
                    "success": False,
                    "contents": "",
                    "did_downgrade_to_line_range": False,
                    "did_shorten_line_range": False,
                    "did_shorten_char_range": False,
                    "relative_workspace_path": relative_workspace_path,
                    "error": "Invalid file path or path outside workspace",
                }

            # Check if file exists
            if not file_path.exists():
                return {
                    "success": False,
                    "contents": "",
                    "did_downgrade_to_line_range": False,
                    "did_shorten_line_range": False,
                    "did_shorten_char_range": False,
                    "relative_workspace_path": relative_workspace_path,
                    "error": f"File not found: {relative_workspace_path}",
                }

            # Check if it's a file (not directory)
            if not file_path.is_file():
                return {
                    "success": False,
                    "contents": "",
                    "did_downgrade_to_line_range": False,
                    "did_shorten_line_range": False,
                    "did_shorten_char_range": False,
                    "relative_workspace_path": relative_workspace_path,
                    "error": f"Path is not a file: {relative_workspace_path}",
                }

            # Read file
            try:
                with open(file_path, encoding="utf-8") as f:
                    lines = f.readlines()
            except UnicodeDecodeError:
                # Try with different encoding
                try:
                    with open(file_path, encoding="latin-1") as f:
                        lines = f.readlines()
                except Exception as e:
                    return {
                        "success": False,
                        "contents": "",
                        "did_downgrade_to_line_range": False,
                        "did_shorten_line_range": False,
                        "did_shorten_char_range": False,
                        "relative_workspace_path": relative_workspace_path,
                        "error": f"Failed to read file with encoding: {str(e)}",
                    }

            total_lines = len(lines)
            did_downgrade = False
            did_shorten_lines = False
            did_shorten_chars = False

            # Determine line range
            if read_entire_file:
                # Check if file is too large for full read
                if total_lines > max_lines:
                    did_downgrade = True
                    start_line = 1
                    end_line = max_lines
                else:
                    start_line = 1
                    end_line = total_lines
            else:
                # Use specified line range
                start_line = start_line_one_indexed if start_line_one_indexed else 1
                end_line = end_line_one_indexed_inclusive if end_line_one_indexed_inclusive else total_lines

                # Validate line range
                start_line = max(1, start_line)
                end_line = min(total_lines, end_line)

                # Check if range exceeds max_lines
                if (end_line - start_line + 1) > max_lines:
                    did_shorten_lines = True
                    end_line = start_line + max_lines - 1

            # Extract lines (convert to 0-indexed)
            selected_lines = lines[start_line - 1 : end_line]
            contents = "".join(selected_lines)

            # Check character limit
            if len(contents) > max_chars:
                did_shorten_chars = True
                contents = contents[:max_chars]
                # Try to end at a line boundary
                last_newline = contents.rfind("\n")
                if last_newline > max_chars * 0.9:  # If we're close to limit
                    contents = contents[:last_newline]

            return {
                "success": True,
                "contents": contents,
                "did_downgrade_to_line_range": did_downgrade,
                "did_shorten_line_range": did_shorten_lines,
                "did_shorten_char_range": did_shorten_chars,
                "relative_workspace_path": relative_workspace_path,
                "total_lines": total_lines,
                "lines_returned": len(selected_lines),
                "error": None,
            }

        except PermissionError:
            return {
                "success": False,
                "contents": "",
                "did_downgrade_to_line_range": False,
                "did_shorten_line_range": False,
                "did_shorten_char_range": False,
                "relative_workspace_path": relative_workspace_path,
                "error": f"Permission denied: {relative_workspace_path}",
            }
        except Exception as e:
            return {
                "success": False,
                "contents": "",
                "did_downgrade_to_line_range": False,
                "did_shorten_line_range": False,
                "did_shorten_char_range": False,
                "relative_workspace_path": relative_workspace_path,
                "error": f"Failed to read file: {str(e)}",
            }

    def _resolve_path(self, relative_path: str) -> Path | None:
        """
        Resolve and validate file path.

        Args:
            relative_path: Path relative to workspace root

        Returns:
            Resolved Path object or None if invalid
        """
        try:
            # Resolve path relative to workspace root
            file_path = (self.workspace_root / relative_path).resolve()

            # Security check: ensure path is within workspace
            if not str(file_path).startswith(str(self.workspace_root.resolve())):
                return None

            return file_path
        except Exception:
            return None


if __name__ == "__main__":
    """
    Demo usage of ReadFileResource.
    
    Run this script to see examples of how to use the ReadFileResource.
    """
    print("=" * 80)
    print("ReadFileResource Usage Examples")
    print("=" * 80)
    print()
    
    # Initialize the resource
    # By default, workspace_root is the current working directory
    resource = ReadFileResource(workspace_root=".")
    
    print("Example 1: Read entire file")
    print("-" * 80)
    result = resource.read(
        relative_workspace_path="read_file_resource.py",
        read_entire_file=True,
        max_lines=50,  # Limit to first 50 lines for demo
    )
    print(f"Success: {result['success']}")
    print(f"Total lines: {result.get('total_lines', 'N/A')}")
    print(f"Lines returned: {result.get('lines_returned', 'N/A')}")
    print(f"Did downgrade to line range: {result['did_downgrade_to_line_range']}")
    print("Content preview (first 200 chars):")
    print(result['contents'][:200] + "..." if len(result['contents']) > 200 else result['contents'])
    print()
    
    print("Example 2: Read specific line range")
    print("-" * 80)
    result = resource.read(
        relative_workspace_path="read_file_resource.py",
        read_entire_file=False,
        start_line_one_indexed=1,
        end_line_one_indexed_inclusive=20,
        max_lines=1000,
    )
    print(f"Success: {result['success']}")
    print("Lines 1-20:")
    print(result['contents'])
    print()
    
    print("Example 3: Handle file not found")
    print("-" * 80)
    result = resource.read(
        relative_workspace_path="non_existent_file.txt",
        read_entire_file=True,
    )
    print(f"Success: {result['success']}")
    print(f"Error: {result['error']}")
    print()
    
    print("Example 4: Read with character limit")
    print("-" * 80)
    result = resource.read(
        relative_workspace_path="read_file_resource.py",
        read_entire_file=True,
        max_chars=500,  # Limit to 500 characters
    )
    print(f"Success: {result['success']}")
    print(f"Did shorten char range: {result['did_shorten_char_range']}")
    print(f"Content length: {len(result['contents'])} chars")
    print()
    
    print("=" * 80)
    print("Usage in code:")
    print("=" * 80)
    print("""
# Import the resource
from read_file_resource import ReadFileResource

# Initialize
resource = ReadFileResource(workspace_root="/path/to/workspace")

# Read entire file
result = resource.read(
    relative_workspace_path="path/to/file.py",
    read_entire_file=True,
    max_lines=1000,
    max_chars=100000
)

# Read specific lines
result = resource.read(
    relative_workspace_path="path/to/file.py",
    read_entire_file=False,
    start_line_one_indexed=10,
    end_line_one_indexed_inclusive=50
)

# Check result
if result['success']:
    print(result['contents'])
else:
    print(f"Error: {result['error']}")
    """)

