"""Resource for file search and discovery.

Provides grep() and glob() tools mirroring Claude Code's search signatures.
"""

import fnmatch
from pathlib import Path
import re

from dana.common.protocols.war import tool_use
from dana.core.resource.base_resource import BaseResource


class SearchResource(BaseResource):
    """Resource for file search and discovery."""

    def __init__(self, resource_id: str, base_path: str | Path | None = None, **kwargs):
        """Initialize the SearchResource.

        Args:
            resource_id: Unique identifier for this resource instance.
            base_path: Base directory for search operations.
            **kwargs: Additional arguments passed to the base resource.
        """
        super().__init__(resource_id=resource_id, **kwargs)
        self._base_path = Path(base_path) if base_path else Path.cwd()
        self._base_path.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, path: str | None) -> Path:
        """Resolve path, defaulting to base_path.

        Args:
            path: Path to resolve (absolute or relative to base_path).

        Returns:
            Resolved absolute Path.
        """
        if path is None:
            return self._base_path
        p = Path(path)
        if p.is_absolute():
            return p
        return self._base_path / p

    @tool_use
    async def grep(
        self,
        pattern: str,
        path: str | None = None,
        output_mode: str = "files_with_matches",
        file_type: str | None = None,
        glob: str | None = None,
        case_insensitive: bool = False,
        show_line_numbers: bool = True,
        context_after: int | None = None,
        context_before: int | None = None,
        context: int | None = None,
        multiline: bool = False,
        head_limit: int | None = None,
        offset: int | None = None,
    ) -> str:
        """Search file contents using regex (ripgrep-style).

        Args:
            pattern: Regular expression pattern to search
            path: File or directory to search (default: output directory)
            output_mode: "content", "files_with_matches", or "count"
            file_type: File type filter (e.g., "json", "md")
            glob: Glob pattern to filter files (e.g., "*.json")
            case_insensitive: Case insensitive search (-i)
            show_line_numbers: Show line numbers in output (-n)
            context_after: Lines to show after match (-A)
            context_before: Lines to show before match (-B)
            context: Lines to show before and after (-C)
            multiline: Enable multiline mode
            head_limit: Limit output to first N entries
            offset: Skip first N entries

        Returns:
            Formatted search results based on output_mode.
        """
        resolved_path = self._resolve_path(path)

        if not resolved_path.exists():
            return f"Error: Path does not exist: {resolved_path}"

        # Compile regex
        flags = 0
        if case_insensitive:
            flags |= re.IGNORECASE
        if multiline:
            flags |= re.MULTILINE | re.DOTALL

        try:
            regex = re.compile(pattern, flags)
        except re.error as e:
            return f"Error: Invalid regex pattern: {e}"

        # Collect files to search
        files_to_search: list[Path] = []
        if resolved_path.is_file():
            files_to_search = [resolved_path]
        else:
            # Walk directory
            for file_path in resolved_path.rglob("*"):
                if not file_path.is_file():
                    continue

                # Apply file_type filter
                if file_type:
                    if not file_path.suffix.lstrip(".") == file_type:
                        continue

                # Apply glob filter
                if glob:
                    if not fnmatch.fnmatch(file_path.name, glob):
                        continue

                files_to_search.append(file_path)

        # Sort by modification time (newest first)
        files_to_search.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        # Determine context lines
        ctx_before = context_before or context or 0
        ctx_after = context_after or context or 0

        results: list[dict] = []

        for file_path in files_to_search:
            try:
                content = file_path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, PermissionError):
                continue

            lines = content.splitlines()
            file_matches: list[dict] = []

            for line_num, line in enumerate(lines, 1):
                if regex.search(line):
                    match_data = {"file": str(file_path), "line_num": line_num, "line": line, "context_before": [], "context_after": []}

                    # Add context lines
                    if ctx_before > 0:
                        start = max(0, line_num - 1 - ctx_before)
                        match_data["context_before"] = [(i + 1, lines[i]) for i in range(start, line_num - 1)]

                    if ctx_after > 0:
                        end = min(len(lines), line_num + ctx_after)
                        match_data["context_after"] = [(i + 1, lines[i]) for i in range(line_num, end)]

                    file_matches.append(match_data)

            if file_matches:
                results.append({"file": str(file_path), "matches": file_matches, "count": len(file_matches)})

        # Apply offset
        if offset:
            results = results[offset:]

        # Apply head_limit
        if head_limit:
            results = results[:head_limit]

        # Format output based on mode
        if output_mode == "files_with_matches":
            if not results:
                return f"No matches found for pattern: {pattern}"
            return "\n".join(r["file"] for r in results)

        elif output_mode == "count":
            if not results:
                return f"No matches found for pattern: {pattern}"
            output_lines = []
            for r in results:
                output_lines.append(f"{r['file']}: {r['count']}")
            return "\n".join(output_lines)

        elif output_mode == "content":
            if not results:
                return f"No matches found for pattern: {pattern}"

            output_lines = []
            for r in results:
                output_lines.append(f"\n{r['file']}:")
                for match in r["matches"]:
                    # Context before
                    for ln, text in match["context_before"]:
                        prefix = f"{ln}-" if show_line_numbers else "-"
                        output_lines.append(f"{prefix}{text}")

                    # Match line
                    ln = match["line_num"]
                    prefix = f"{ln}:" if show_line_numbers else ":"
                    output_lines.append(f"{prefix}{match['line']}")

                    # Context after
                    for ln, text in match["context_after"]:
                        prefix = f"{ln}-" if show_line_numbers else "-"
                        output_lines.append(f"{prefix}{text}")

            return "\n".join(output_lines)

        else:
            return f"Error: Invalid output_mode: {output_mode}"

    @tool_use
    async def glob(self, pattern: str, path: str | None = None) -> str:
        """Find files matching a glob pattern.

        Args:
            pattern: Glob pattern (e.g., "**/*.json", "*.md")
            path: Directory to search (default: output directory)

        Returns:
            Matching file paths sorted by modification time.
        """
        resolved_path = self._resolve_path(path)

        if not resolved_path.exists():
            return f"Error: Path does not exist: {resolved_path}"

        if not resolved_path.is_dir():
            return f"Error: Path is not a directory: {resolved_path}"

        try:
            matches = list(resolved_path.glob(pattern))

            if not matches:
                return f"No files found matching pattern: {pattern}"

            # Sort by modification time (newest first)
            matches.sort(key=lambda f: f.stat().st_mtime, reverse=True)

            return "\n".join(str(m) for m in matches)

        except Exception as e:
            return f"Error searching for files: {e}"
