"""Resource for file editing via string replacement.

Provides edit() tool mirroring Claude Code's exact string replacement signature.
"""

from pathlib import Path

from dana.common.protocols.war import named_tool
from dana.core.resource.base_resource import BaseResource


class FileEditResource(BaseResource):
    """Resource for file editing via string replacement."""

    def __init__(self, resource_id: str, base_path: str | Path | None = None, **kwargs):
        """Initialize the FileEditResource.

        Args:
            resource_id: Unique identifier for this resource instance.
            base_path: Base directory for relative path resolution.
            **kwargs: Additional arguments passed to the base resource.
        """
        super().__init__(resource_id=resource_id, **kwargs)
        self._base_path = Path(base_path) if base_path else Path.cwd()
        self._base_path.mkdir(parents=True, exist_ok=True)

    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace for fuzzy matching.

        Normalizations applied:
        - Convert \\r\\n and \\r to \\n
        - Collapse 3+ consecutive newlines to 2 (preserve paragraph breaks)
        - Strip trailing whitespace from each line

        Args:
            text: Text to normalize.

        Returns:
            Normalized text.
        """
        # Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # Collapse 3+ consecutive newlines to 2
        while "\n\n\n" in text:
            text = text.replace("\n\n\n", "\n\n")
        # Strip trailing whitespace per line
        lines = text.split("\n")
        lines = [line.rstrip() for line in lines]
        return "\n".join(lines)

    def _normalize_with_mapping(self, text: str) -> tuple[str, list[int]]:
        """Normalize whitespace and build index mapping from normalized to original positions.

        This allows finding a match in normalized text and mapping back to original
        character positions for accurate replacement.

        Args:
            text: Original text to normalize.

        Returns:
            Tuple of (normalized_text, mapping) where mapping[norm_idx] = original_idx.
        """
        result: list[str] = []
        mapping: list[int] = []  # mapping[norm_idx] = original_idx

        i = 0
        consecutive_newlines = 0

        while i < len(text):
            char = text[i]

            # Handle \r\n -> \n
            if char == "\r":
                if i + 1 < len(text) and text[i + 1] == "\n":
                    # \r\n -> \n, skip the \r
                    i += 1
                    continue
                else:
                    # Standalone \r -> \n
                    char = "\n"

            # Handle trailing spaces before newline
            if char == " " or char == "\t":
                # Look ahead for newline (skip trailing whitespace)
                j = i
                while j < len(text) and text[j] in " \t":
                    j += 1
                if j < len(text) and text[j] in "\n\r":
                    # Skip trailing whitespace before newline
                    i = j
                    continue

            # Handle multiple newlines (collapse 3+ to 2)
            if char == "\n":
                consecutive_newlines += 1
                if consecutive_newlines > 2:
                    # Skip extra newlines beyond 2
                    i += 1
                    continue
            else:
                consecutive_newlines = 0

            result.append(char)
            mapping.append(i)
            i += 1

        return "".join(result), mapping

    def _find_fuzzy_match(self, content: str, old_string: str) -> tuple[int, int, int] | None:
        """Find old_string in content using normalized whitespace matching.

        Args:
            content: Original file content.
            old_string: String to find (may have whitespace differences).

        Returns:
            Tuple of (start_pos, end_pos, match_count) in ORIGINAL content positions,
            or None if no match found. match_count is the number of matches found
            in normalized content (for uniqueness checking).
        """
        norm_content, content_mapping = self._normalize_with_mapping(content)
        norm_old = self._normalize_whitespace(old_string)

        if not norm_old:
            return None

        # Count matches in normalized content
        match_count = norm_content.count(norm_old)
        if match_count == 0:
            return None

        # Find first match position in normalized content
        norm_start = norm_content.find(norm_old)
        norm_end = norm_start + len(norm_old)

        # Map back to original positions
        if norm_start >= len(content_mapping) or norm_end > len(content_mapping):
            return None

        orig_start = content_mapping[norm_start]

        # For end position, we need the position AFTER the last matched char
        # The mapping gives us the start of the last normalized char
        # We need to find where that original char ends
        if norm_end == len(content_mapping):
            # Match extends to end of content
            orig_end = len(content)
        else:
            # End is the start of the next character after the match
            orig_end = content_mapping[norm_end]

        # However, we want to include any trailing whitespace that was normalized away
        # Extend orig_end to capture trailing whitespace before the next significant char
        while orig_end < len(content) and content[orig_end] in " \t":
            # Check if this whitespace is before a newline (trailing whitespace)
            peek = orig_end
            while peek < len(content) and content[peek] in " \t":
                peek += 1
            if peek < len(content) and content[peek] in "\n\r":
                orig_end = peek
                break
            else:
                break

        return (orig_start, orig_end, match_count)

    def _fuzzy_replace_all(self, content: str, old_string: str, new_string: str) -> str:
        """Replace all fuzzy matches of old_string with new_string.

        Iteratively finds and replaces matches using normalized whitespace matching,
        working from end to start to preserve positions.

        Args:
            content: Original file content.
            old_string: String to find (may have whitespace differences).
            new_string: Replacement string.

        Returns:
            Content with all matches replaced.
        """
        # Collect all match positions first
        matches: list[tuple[int, int]] = []
        remaining_content = content
        offset = 0

        while True:
            result = self._find_fuzzy_match(remaining_content, old_string)
            if result is None:
                break

            start, end, _ = result
            matches.append((start + offset, end + offset))

            # Move past this match
            offset += end
            remaining_content = content[offset:]

        # Replace from end to start to preserve positions
        result = content
        for start, end in reversed(matches):
            result = result[:start] + new_string + result[end:]

        return result

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

    def _format_snippet(self, content: str, edit_start_line: int, edit_end_line: int, context_lines: int = 2) -> str:
        """Format a snippet of file content with line numbers (cat -n style).

        Args:
            content: Full file content
            edit_start_line: 1-indexed line number where edit starts
            edit_end_line: 1-indexed line number where edit ends (inclusive)
            context_lines: Number of context lines before and after to include

        Returns:
            Formatted snippet with line numbers.
        """
        lines = content.splitlines()
        total_lines = len(lines)

        # Handle empty file
        if total_lines == 0:
            return "     1\t"

        # Ensure edit line numbers are within bounds
        edit_start_line = max(1, min(edit_start_line, total_lines))
        edit_end_line = max(edit_start_line, min(edit_end_line, total_lines))

        # Calculate snippet bounds
        start_line = max(1, edit_start_line - context_lines)
        end_line = min(total_lines, edit_end_line + context_lines)

        # Format lines with line numbers
        result_lines = []
        for i in range(start_line - 1, end_line):  # Convert to 0-indexed
            line_num = i + 1  # Convert back to 1-indexed for display
            line_content = lines[i]
            result_lines.append(f"{line_num:6}\t{line_content}")

        return "\n".join(result_lines)

    @named_tool(name="Edit")
    async def edit(self, file_path: str, old_string: str, new_string: str, replace_all: bool = False, fuzzy_match: bool = True) -> str:
        """Perform string replacement in a file with optional fuzzy whitespace matching.

        Args:
            file_path: Absolute path to the file to modify
            old_string: Text to find and replace (exact match preferred)
            new_string: Text to replace with (must differ from old_string)
            replace_all: Replace all occurrences instead of just first (default: False)
            fuzzy_match: If True, try whitespace-normalized matching when exact match
                fails. Normalizations include: line ending differences (\\r\\n vs \\n),
                trailing whitespace, and consecutive blank lines. (default: True)

        Returns:
            Success message with snippet, or error if string not found/not unique.
        """
        resolved_path = self._resolve_path(file_path)

        if not resolved_path.exists():
            return "<tool_use_error>File does not exist.</tool_use_error>"

        if not resolved_path.is_file():
            return f"Error: Path is not a file: {resolved_path}"

        if old_string == new_string:
            return "<tool_use_error>No changes to make: old_string and new_string are exactly the same.</tool_use_error>"

        try:
            content = resolved_path.read_text(encoding="utf-8")

            # Try exact match first
            count = content.count(old_string)
            used_fuzzy_match = False
            fuzzy_start: int | None = None
            fuzzy_end: int | None = None

            if count == 0 and fuzzy_match:
                # Exact match failed, try fuzzy whitespace matching
                fuzzy_result = self._find_fuzzy_match(content, old_string)
                if fuzzy_result is not None:
                    fuzzy_start, fuzzy_end, fuzzy_count = fuzzy_result
                    count = fuzzy_count
                    used_fuzzy_match = True

            if count == 0:
                return f"<tool_use_error>String to replace not found in file.\nString: {old_string}</tool_use_error>"

            if not replace_all and count > 1:
                match_type = "fuzzy (whitespace-normalized)" if used_fuzzy_match else "exact"
                return (
                    f"<tool_use_error>Found {count} {match_type} matches of the string to replace, but replace_all is false. "
                    f"To replace all occurrences, set replace_all to true. To replace only one occurrence, "
                    f"please provide more context to uniquely identify the instance.\nString: {old_string}</tool_use_error>"
                )

            # Perform replacement
            if used_fuzzy_match and fuzzy_start is not None and fuzzy_end is not None:
                # Fuzzy match: replace using original positions
                if replace_all:
                    # For replace_all with fuzzy match, we need to normalize and replace all
                    # This is more complex - we'll do iterative replacement
                    new_content = self._fuzzy_replace_all(content, old_string, new_string)
                else:
                    # Single replacement using mapped positions
                    new_content = content[:fuzzy_start] + new_string + content[fuzzy_end:]
                first_pos = fuzzy_start
            else:
                # Exact match: use standard string replacement
                if replace_all:
                    new_content = content.replace(old_string, new_string)
                else:
                    new_content = content.replace(old_string, new_string, 1)
                first_pos = content.find(old_string)

            # Calculate line numbers for the edit in original content
            char_count = 0
            edit_start_line = 1
            original_lines = content.splitlines(keepends=True)
            for i, line in enumerate(original_lines):
                if char_count <= first_pos < char_count + len(line):
                    edit_start_line = i + 1
                    break
                char_count += len(line)

            # Calculate end line (replacement string might span multiple lines)
            new_string_lines = new_string.splitlines()
            if new_string_lines:
                new_lines_count = len(new_string_lines)
            else:
                new_lines_count = 1
            edit_end_line = edit_start_line + max(0, new_lines_count - 1)

            # Write back
            resolved_path.write_text(new_content, encoding="utf-8")

            # Format success message with snippet
            snippet = self._format_snippet(new_content, edit_start_line, edit_end_line)

            if used_fuzzy_match:
                return (
                    f"The file {resolved_path} has been updated (using fuzzy whitespace matching). "
                    f"Note: The old_string had whitespace differences from the file content "
                    f"(e.g., line endings, trailing spaces, or blank lines). "
                    f"Here's the result of running `cat -n` on a snippet of the edited file:\n"
                    f"{snippet}"
                )
            else:
                return (
                    f"The file {resolved_path} has been updated. "
                    f"Here's the result of running `cat -n` on a snippet of the edited file:\n"
                    f"{snippet}"
                )

        except UnicodeDecodeError:
            return f"Error: Cannot read file as text (binary file?): {resolved_path}"
        except PermissionError:
            return f"Error: Permission denied: {resolved_path}"
        except Exception as e:
            return f"Error editing file: {e}"

    @named_tool(name="Write")
    async def write(self, file_path: str, content: str) -> str:
        """Create a new file with content. Does not overwrite existing files.

        Args:
            file_path: Absolute path to the file to write
            content: Content to write to the file

        Returns:
            Success message with file path, or error if file already exists.
        """
        resolved_path = self._resolve_path(file_path)

        # Check if file already exists
        if resolved_path.exists():
            return f"Error: File already exists: {resolved_path}. Cannot overwrite existing files. Use edit() for modifications."

        try:
            # Create parent directories if they don't exist
            resolved_path.parent.mkdir(parents=True, exist_ok=True)

            # Write content
            resolved_path.write_text(content, encoding="utf-8")

            return f"Successfully wrote {len(content)} characters to {resolved_path}"

        except PermissionError:
            return f"Error: Permission denied: {resolved_path}"
        except Exception as e:
            return f"Error writing file: {e}"
