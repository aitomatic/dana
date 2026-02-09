"""Resource for file search and discovery.

Provides grep() and glob() tools mirroring Claude Code's search signatures.
"""

import asyncio
from enum import StrEnum
import fnmatch
from pathlib import Path
import re

from dana.common.protocols.war import named_tool
from dana.core.resource.base_resource import BaseResource


class GREPMode(StrEnum):
    PYTHON_NATIVE = "python_native"
    RIPGREP = "ripgrep"
    GREP = "grep"
    AUTO = "auto"


class SearchResource(BaseResource):
    """Resource for file search and discovery."""

    def __init__(self, resource_id: str, base_path: str | Path | None = None, mode: GREPMode = GREPMode.AUTO, **kwargs):
        """Initialize the SearchResource.

        Args:
            resource_id: Unique identifier for this resource instance.
            base_path: Base directory for search operations.
            mode: Mode to use for grep operations.
            **kwargs: Additional arguments passed to the base resource.
        """
        super().__init__(resource_id=resource_id, **kwargs)
        self._base_path = Path(base_path) if base_path else Path.cwd()
        self._base_path.mkdir(parents=True, exist_ok=True)
        self._mode = mode

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

    @named_tool(name="Grep")
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
        args = (
            pattern,
            path,
            output_mode,
            file_type,
            glob,
            case_insensitive,
            show_line_numbers,
            context_after,
            context_before,
            context,
            multiline,
            head_limit,
            offset,
        )

        if self._mode == GREPMode.RIPGREP:
            return await self._grep_ripgrep(*args)
        elif self._mode == GREPMode.GREP:
            return await self._grep_system_grep(*args)
        elif self._mode == GREPMode.PYTHON_NATIVE:
            return await self._grep_python_native(*args)
        else:
            e1, e2, e3 = None, None, None
            try:
                return await self._grep_ripgrep(*args)
            except Exception as e:
                e1 = e

            try:
                return await self._grep_system_grep(*args)
            except Exception as e:
                e2 = e

            try:
                return await self._grep_python_native(*args)
            except Exception as e:
                e3 = e

            raise ValueError(
                f"No grep implementation found for mode: {self._mode}. \nRipgrep error: {e1}\nSystem grep error: {e2}\nPython native error: {e3}"
            )

    async def _grep_python_native(
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

    # File type to extension mapping for system grep (which doesn't have --type)
    _FILE_TYPE_EXTENSIONS: dict[str, list[str]] = {
        "py": ["py", "pyi"],
        "js": ["js", "jsx", "mjs", "cjs"],
        "ts": ["ts", "tsx", "mts", "cts"],
        "json": ["json"],
        "md": ["md", "markdown"],
        "yaml": ["yaml", "yml"],
        "html": ["html", "htm"],
        "css": ["css"],
        "rust": ["rs"],
        "go": ["go"],
        "java": ["java"],
        "c": ["c", "h"],
        "cpp": ["cpp", "cc", "cxx", "hpp", "hh", "hxx"],
        "rb": ["rb"],
        "php": ["php"],
        "sh": ["sh", "bash"],
        "sql": ["sql"],
        "xml": ["xml"],
        "txt": ["txt"],
    }

    async def _grep_ripgrep(
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
        """Search file contents using ripgrep (rg).

        Args:
            pattern: Regular expression pattern to search
            path: File or directory to search (default: base directory)
            output_mode: "content", "files_with_matches", or "count"
            file_type: File type filter (e.g., "py", "js") - uses rg's --type
            glob: Glob pattern to filter files (e.g., "*.json")
            case_insensitive: Case insensitive search (-i)
            show_line_numbers: Show line numbers in output (-n)
            context_after: Lines to show after match (-A)
            context_before: Lines to show before match (-B)
            context: Lines to show before and after (-C)
            multiline: Enable multiline mode (-U)
            head_limit: Limit output to first N entries
            offset: Skip first N entries

        Returns:
            Formatted search results based on output_mode.
        """
        resolved_path = self._resolve_path(path)

        if not resolved_path.exists():
            return f"Error: Path does not exist: {resolved_path}"

        cmd = ["rg"]

        # Output mode
        if output_mode == "files_with_matches":
            cmd.append("-l")
        elif output_mode == "count":
            cmd.append("-c")
        # "content" is the default behavior

        # Flags
        if case_insensitive:
            cmd.append("-i")
        if show_line_numbers and output_mode == "content":
            cmd.append("-n")
        if multiline:
            cmd.extend(["-U", "--multiline-dotall"])

        # Context (only meaningful for content mode)
        if output_mode == "content":
            if context:
                cmd.extend(["-C", str(context)])
            else:
                if context_before:
                    cmd.extend(["-B", str(context_before)])
                if context_after:
                    cmd.extend(["-A", str(context_after)])

        # File type filter (rg has built-in type support)
        if file_type:
            cmd.extend(["--type", file_type])

        # Glob filter
        if glob:
            cmd.extend(["--glob", glob])

        # For files_with_matches and count modes, we can use -m to limit matches per file
        # But for limiting total output, we process after
        # Note: rg -m limits matches PER FILE, not total

        # Pattern and path
        cmd.append(pattern)
        cmd.append(str(resolved_path))

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
        except FileNotFoundError:
            return "Error: ripgrep (rg) is not installed. Install it or use mode=GREPMode.PYTHON_NATIVE"

        # ripgrep returns exit code 1 for no matches (not an error)
        output = stdout.decode("utf-8", errors="replace")

        # Log any stderr warnings (but don't fail)
        if stderr:
            stderr_text = stderr.decode("utf-8", errors="replace").strip()
            if stderr_text and process.returncode not in (0, 1):
                return f"Error from ripgrep: {stderr_text}"

        if not output.strip():
            return f"No matches found for pattern: {pattern}"

        # Apply offset and head_limit
        lines = output.strip().splitlines()
        if offset:
            lines = lines[offset:]
        if head_limit:
            lines = lines[:head_limit]

        return "\n".join(lines) if lines else f"No matches found for pattern: {pattern}"

    async def _grep_system_grep(
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
        """Search file contents using system grep.

        Args:
            pattern: Regular expression pattern to search
            path: File or directory to search (default: base directory)
            output_mode: "content", "files_with_matches", or "count"
            file_type: File type filter (e.g., "py", "js") - converted to --include
            glob: Glob pattern to filter files (e.g., "*.json")
            case_insensitive: Case insensitive search (-i)
            show_line_numbers: Show line numbers in output (-n)
            context_after: Lines to show after match (-A)
            context_before: Lines to show before match (-B)
            context: Lines to show before and after (-C)
            multiline: Enable multiline mode (limited support with grep -z)
            head_limit: Limit output to first N entries
            offset: Skip first N entries

        Returns:
            Formatted search results based on output_mode.
        """
        resolved_path = self._resolve_path(path)

        if not resolved_path.exists():
            return f"Error: Path does not exist: {resolved_path}"

        cmd = ["grep", "-E", "-r"]  # Extended regex, recursive

        # Output mode
        if output_mode == "files_with_matches":
            cmd.append("-l")
        elif output_mode == "count":
            cmd.append("-c")
        # "content" is the default behavior

        # Flags
        if case_insensitive:
            cmd.append("-i")
        if show_line_numbers and output_mode == "content":
            cmd.append("-n")

        # Skip binary files
        cmd.append("--binary-files=without-match")

        # Multiline support is limited in grep, use -z for null-separated
        if multiline:
            cmd.append("-z")

        # Context (only meaningful for content mode)
        if output_mode == "content":
            if context:
                cmd.extend(["-C", str(context)])
            else:
                if context_before:
                    cmd.extend(["-B", str(context_before)])
                if context_after:
                    cmd.extend(["-A", str(context_after)])

        # File type filter - grep doesn't have --type, convert to --include
        if file_type:
            extensions = self._FILE_TYPE_EXTENSIONS.get(file_type, [file_type])
            for ext in extensions:
                cmd.extend(["--include", f"*.{ext}"])

        # Glob filter - use --include
        if glob:
            cmd.extend(["--include", glob])

        # Pattern and path
        cmd.append(pattern)
        cmd.append(str(resolved_path))

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
        except FileNotFoundError:
            return "Error: grep is not installed. Use mode=GREPMode.PYTHON_NATIVE"

        # grep returns exit code 1 for no matches (not an error)
        output = stdout.decode("utf-8", errors="replace")

        # Log any stderr warnings (but don't fail)
        if stderr:
            stderr_text = stderr.decode("utf-8", errors="replace").strip()
            if stderr_text and process.returncode not in (0, 1):
                return f"Error from grep: {stderr_text}"

        if not output.strip():
            return f"No matches found for pattern: {pattern}"

        # Apply offset and head_limit
        lines = output.strip().splitlines()
        if offset:
            lines = lines[offset:]
        if head_limit:
            lines = lines[:head_limit]

        return "\n".join(lines) if lines else f"No matches found for pattern: {pattern}"

    @named_tool(name="Glob")
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
