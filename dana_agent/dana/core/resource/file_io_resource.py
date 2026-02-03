"""Resource for file read/write operations.

Provides read() and write() tools mirroring Claude Code's file I/O signatures.
"""

from pathlib import Path

from dana.common.protocols.war import named_tool
from dana.core.resource.base_resource import BaseResource


class FileIOResource(BaseResource):
    """Resource for file read/write operations."""

    def __init__(self, resource_id: str, base_path: str | Path | None = None, **kwargs):
        """Initialize the FileIOResource.

        Args:
            resource_id: Unique identifier for this resource instance.
            base_path: Base directory for relative path resolution.
            **kwargs: Additional arguments passed to the base resource.
        """
        super().__init__(resource_id=resource_id, **kwargs)
        self._base_path = Path(base_path) if base_path else Path.cwd()
        self._base_path.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, file_path: str) -> Path:
        """Resolve file path, supporting both absolute and relative paths.

        Args:
            file_path: Path to resolve (absolute or relative to base_path).

        Returns:
            Resolved absolute Path.
        """
        path = Path(file_path)
        if path.is_absolute():
            return path
        return self._base_path / path

    @named_tool(name="Read")
    async def read(self, file_path: str, offset: int | None = None, limit: int | None = 2000) -> str:
        """Read file contents with line numbers (cat -n format).

        Args:
            file_path: Absolute path to the file to read
            offset: Line number to start reading from (1-indexed)
            limit: Maximum number of lines to read (default: 2000)

        Returns:
            File contents with line numbers, or error message.
        """
        resolved_path = self._resolve_path(file_path)

        if not resolved_path.exists():
            return f"Error: File does not exist: {resolved_path}"

        if not resolved_path.is_file():
            return f"Error: Path is not a file: {resolved_path}"

        try:
            content = resolved_path.read_text(encoding="utf-8")
            lines = content.splitlines()

            # Apply offset (1-indexed)
            start_line = 0
            if offset is not None:
                start_line = max(0, offset - 1)  # Convert to 0-indexed

            # Apply limit
            end_line = len(lines)
            if limit is not None:
                end_line = min(start_line + limit, len(lines))

            # Format with line numbers (cat -n style)
            result_lines = []
            for i in range(start_line, end_line):
                line_num = i + 1  # Convert back to 1-indexed for display
                # Truncate lines longer than 2000 characters
                line_content = lines[i]
                if len(line_content) > 2000:
                    line_content = line_content[:2000] + "..."
                result_lines.append(f"{line_num:6}\t{line_content}")

            if not result_lines:
                return f"File is empty: {resolved_path}"

            return "\n".join(result_lines)

        except UnicodeDecodeError:
            return f"Error: Cannot read file as text (binary file?): {resolved_path}"
        except PermissionError:
            return f"Error: Permission denied: {resolved_path}"
        except Exception as e:
            return f"Error reading file: {e}"
