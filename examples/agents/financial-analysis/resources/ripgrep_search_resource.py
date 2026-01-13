"""
RipgrepSearchResource - Fast text search across files using ripgrep or Python fallback.

This resource handles:
- Text search using ripgrep (rg) command when available
- Fallback to Python re module for systems without ripgrep
- Regex and literal text search
- Case sensitivity and word matching options
- File pattern filtering (include/exclude)
- Context lines (before/after matches)
"""

import os
import re
import subprocess
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dana.common.protocols.types import DictParams
from dana.common.protocols.war import tool_use
from dana.core.resource.base_resource import BaseResource


class RipgrepSearchResource(BaseResource):
    """
    Resource for searching text in files using ripgrep or Python fallback.

    Features:
    - Fast ripgrep search when available
    - Python regex fallback for compatibility
    - Regex and literal text patterns
    - Case sensitivity control
    - File pattern filtering
    - Context lines around matches
    - Line number and position tracking
    """

    def __init__(self, resource_id: str | None = None, workspace_root: str | None = None, **kwargs):
        """
        Initialize the RipgrepSearchResource.

        Args:
            resource_id: Unique identifier for this resource
            workspace_root: Root directory for searching (defaults to cwd)
            **kwargs: Additional arguments passed to BaseResource
        """
        super().__init__(resource_type="ripgrep-search", resource_id=resource_id or "ripgrep-search", **kwargs)
        self.workspace_root = Path(workspace_root) if workspace_root else Path.cwd()
        self.ripgrep_available = self._check_ripgrep_available()

    def _check_ripgrep_available(self) -> bool:
        """Check if ripgrep (rg) is available on the system."""
        try:
            result = subprocess.run(["rg", "--version"], capture_output=True, timeout=2)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    @tool_use
    def search(
        self,
        pattern: str,
        is_regex: bool = False,
        is_case_sensitive: bool = False,
        is_word_match: bool = False,
        file_pattern: str | None = None,
        exclude_pattern: str | None = None,
        max_results: int = 100,
        context_lines: int = 0,
        **kwargs,
    ) -> DictParams:
        """
        Search for text pattern in files.

        Args:
            pattern: Search pattern (literal text or regex)
            is_regex: Whether pattern is a regex (default: False)
            is_case_sensitive: Whether to match case (default: False)
            is_word_match: Whether to match whole words only (default: False)
            file_pattern: Glob pattern for files to include (e.g., "*.py")
            exclude_pattern: Glob pattern for files to exclude (e.g., "*.test.py")
            max_results: Maximum number of results to return (default: 100)
            context_lines: Number of context lines before/after match (default: 0)
            **kwargs: Additional parameters

        Returns:
            {
                "success": bool,
                "matches": [
                    {
                        "file_path": str,
                        "line_number": int,
                        "line_text": str,
                        "match_start": int,
                        "match_end": int,
                        "before_context": list[str],
                        "after_context": list[str]
                    }
                ],
                "total_matches": int,
                "search_method": str ("ripgrep" or "python"),
                "error": str (if failed)
            }
        """
        try:
            if self.ripgrep_available:
                return self._search_with_ripgrep(
                    pattern=pattern,
                    is_regex=is_regex,
                    is_case_sensitive=is_case_sensitive,
                    is_word_match=is_word_match,
                    file_pattern=file_pattern,
                    exclude_pattern=exclude_pattern,
                    max_results=max_results,
                    context_lines=context_lines,
                )
            else:
                return self._search_with_python(
                    pattern=pattern,
                    is_regex=is_regex,
                    is_case_sensitive=is_case_sensitive,
                    is_word_match=is_word_match,
                    file_pattern=file_pattern,
                    exclude_pattern=exclude_pattern,
                    max_results=max_results,
                    context_lines=context_lines,
                )

        except Exception as e:
            return {"success": False, "matches": [], "total_matches": 0, "error": f"Search failed: {str(e)}"}

    def _search_with_ripgrep(
        self,
        pattern: str,
        is_regex: bool,
        is_case_sensitive: bool,
        is_word_match: bool,
        file_pattern: str | None,
        exclude_pattern: str | None,
        max_results: int,
        context_lines: int,
    ) -> DictParams:
        """Search using ripgrep command."""
        try:
            # Build ripgrep command
            cmd = ["rg", "--line-number", "--column", "--no-heading"]

            # Add flags
            if not is_case_sensitive:
                cmd.append("--ignore-case")
            if is_word_match:
                cmd.append("--word-regexp")
            if not is_regex:
                cmd.append("--fixed-strings")
            if context_lines > 0:
                cmd.extend(["-A", str(context_lines), "-B", str(context_lines)])

            # Add file patterns
            if file_pattern:
                cmd.extend(["--glob", file_pattern])
            if exclude_pattern:
                cmd.extend(["--glob", f"!{exclude_pattern}"])

            # Add max count
            cmd.extend(["--max-count", str(max_results)])

            # Add pattern and search path
            cmd.append(pattern)
            cmd.append(str(self.workspace_root))

            # Run ripgrep
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            # Parse results
            matches = []
            if result.stdout:
                lines = result.stdout.strip().split("\n")
                for line in lines[:max_results]:
                    match = self._parse_ripgrep_line(line)
                    if match:
                        matches.append(match)

            return {
                "success": True,
                "matches": matches,
                "total_matches": len(matches),
                "search_method": "ripgrep",
                "error": None,
            }

        except subprocess.TimeoutExpired:
            return {"success": False, "matches": [], "total_matches": 0, "error": "Search timeout (>30s)"}
        except Exception:
            # Fallback to Python search
            return self._search_with_python(
                pattern, is_regex, is_case_sensitive, is_word_match, file_pattern, exclude_pattern, max_results, context_lines
            )

    def _parse_ripgrep_line(self, line: str) -> dict | None:
        """Parse a ripgrep output line."""
        try:
            # Format: filename:line:column:text
            parts = line.split(":", 3)
            if len(parts) >= 4:
                file_path = parts[0]
                line_number = int(parts[1])
                column = int(parts[2])
                line_text = parts[3]

                return {
                    "file_path": file_path,
                    "line_number": line_number,
                    "line_text": line_text,
                    "match_start": column - 1,  # Convert to 0-indexed
                    "match_end": column + len(line_text.strip()) - 1,
                    "before_context": [],
                    "after_context": [],
                }
        except (ValueError, IndexError):
            pass
        return None

    def _search_with_python(
        self,
        pattern: str,
        is_regex: bool,
        is_case_sensitive: bool,
        is_word_match: bool,
        file_pattern: str | None,
        exclude_pattern: str | None,
        max_results: int,
        context_lines: int,
    ) -> DictParams:
        """Search using Python re module (fallback)."""
        try:
            matches = []
            total_matches = 0

            # Compile regex pattern
            if is_word_match:
                regex_pattern = rf"\b{re.escape(pattern) if not is_regex else pattern}\b"
            elif not is_regex:
                regex_pattern = re.escape(pattern)
            else:
                regex_pattern = pattern

            flags = 0 if is_case_sensitive else re.IGNORECASE
            try:
                compiled_pattern = re.compile(regex_pattern, flags)
            except re.error as e:
                return {"success": False, "matches": [], "total_matches": 0, "error": f"Invalid regex pattern: {str(e)}"}

            # Walk through files
            for file_path in self._walk_files(file_pattern, exclude_pattern):
                if total_matches >= max_results:
                    break

                try:
                    with open(file_path, encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()

                    for line_num, line in enumerate(lines, start=1):
                        if total_matches >= max_results:
                            break

                        match = compiled_pattern.search(line)
                        if match:
                            # Get context lines
                            before_context = []
                            after_context = []
                            if context_lines > 0:
                                start_ctx = max(0, line_num - context_lines - 1)
                                end_ctx = min(len(lines), line_num + context_lines)
                                before_context = [lines[i].rstrip() for i in range(start_ctx, line_num - 1)]
                                after_context = [lines[i].rstrip() for i in range(line_num, end_ctx)]

                            matches.append(
                                {
                                    "file_path": str(file_path.relative_to(self.workspace_root)),
                                    "line_number": line_num,
                                    "line_text": line.rstrip(),
                                    "match_start": match.start(),
                                    "match_end": match.end(),
                                    "before_context": before_context,
                                    "after_context": after_context,
                                }
                            )
                            total_matches += 1

                except (PermissionError, OSError):
                    continue

            return {
                "success": True,
                "matches": matches,
                "total_matches": total_matches,
                "search_method": "python",
                "error": None,
            }

        except Exception as e:
            return {"success": False, "matches": [], "total_matches": 0, "error": f"Python search failed: {str(e)}"}

    def _walk_files(self, file_pattern: str | None, exclude_pattern: str | None):
        """Walk through files matching patterns."""

        if file_pattern:
            if os.path.isfile(file_pattern):
                yield Path(file_pattern).absolute()
                return

        # Convert glob patterns to regex
        file_regex = self._glob_to_regex(file_pattern) if file_pattern else None
        exclude_regex = self._glob_to_regex(exclude_pattern) if exclude_pattern else None

        for root, dirs, files in os.walk(self.workspace_root):
            # Skip hidden directories and common ignore patterns
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["node_modules", "__pycache__", "venv"]]

            for file in files:
                if file.startswith("."):
                    continue

                file_path = Path(root) / file
                rel_path = str(file_path.relative_to(self.workspace_root))

                # Check patterns
                if file_regex and not file_regex.match(file):
                    continue
                if exclude_regex and exclude_regex.match(file):
                    continue

                yield file_path

    def _glob_to_regex(self, pattern: str) -> re.Pattern:
        """Convert glob pattern to regex."""
        # Simple glob to regex conversion
        regex_pattern = pattern.replace(".", r"\.").replace("*", ".*").replace("?", ".")
        return re.compile(regex_pattern)


if __name__ == "__main__":
    """
    Demo usage of RipgrepSearchResource.
    
    Run this script to see examples of how to use the RipgrepSearchResource.
    """

    print("=" * 80)
    print("RipgrepSearchResource Usage Examples")
    print("=" * 80)
    print()

    # Initialize the resource
    resource = RipgrepSearchResource(workspace_root="examples/agents/teaching/data")

    print(f"Ripgrep available: {resource.ripgrep_available}")
    print(f"Search method: {'ripgrep (fast)' if resource.ripgrep_available else 'python (fallback)'}")
    print()

    print("Example 1: Simple text search (case-insensitive)")
    print("-" * 80)
    result = resource.search(
        pattern="analyze",
        is_regex=False,
        is_case_sensitive=False,
        max_results=5,
    )
    print(f"Success: {result['success']}")
    print(f"Total matches: {result['total_matches']}")
    print(f"Search method: {result['search_method']}")
    if result["matches"]:
        print("First match:")
        match = result["matches"][0]
        print(f"  File: {match['file_path']}")
        print(f"  Line {match['line_number']}: {match['line_text']}")
    print()

    print("Example 2: Regex search")
    print("-" * 80)
    result = resource.search(
        pattern=r"def\s+\w+\(",  # Match function definitions
        is_regex=True,
        is_case_sensitive=True,
        max_results=10,
    )
    print(f"Success: {result['success']}")
    print(f"Total matches: {result['total_matches']}")
    print("Function definitions found:")
    for i, match in enumerate(result["matches"][:5], 1):
        print(f"  {i}. {match['file_path']}:{match['line_number']} - {match['line_text'].strip()}")
    print()

    print("Example 3: Search with file pattern filter")
    print("-" * 80)
    result = resource.search(
        pattern="import",
        is_regex=False,
        file_pattern="*.py",  # Only search in Python files
        max_results=5,
    )
    print(f"Success: {result['success']}")
    print(f"Total matches in .py files: {result['total_matches']}")
    print()

    print("Example 4: Word match search")
    print("-" * 80)
    result = resource.search(
        pattern="read",  # Will only match whole word "read", not "thread" or "reading"
        is_regex=False,
        is_word_match=True,
        max_results=5,
    )
    print(f"Success: {result['success']}")
    print(f"Total matches (whole word only): {result['total_matches']}")
    print()

    print("Example 5: Search with context lines")
    print("-" * 80)
    result = resource.search(
        pattern="@tool_use",
        is_regex=False,
        context_lines=2,  # Show 2 lines before and after match
        max_results=1,
    )
    if result["success"] and result["matches"]:
        match = result["matches"][0]
        print(f"Match in {match['file_path']} at line {match['line_number']}:")
        print("Before context:")
        for line in match["before_context"]:
            print(f"  {line}")
        print(f"Match: {match['line_text']}")
        print("After context:")
        for line in match["after_context"]:
            print(f"  {line}")
    print()

    print("=" * 80)
    print("Usage in code:")
    print("=" * 80)
    print("""
# Import the resource
from ripgrep_search_resource import RipgrepSearchResource

# Initialize
resource = RipgrepSearchResource(workspace_root="/path/to/workspace")

# Simple text search
result = resource.search(
    pattern="search_text",
    is_regex=False,
    is_case_sensitive=False,
    max_results=100
)

# Regex search with file filtering
result = resource.search(
    pattern=r"class\\s+\\w+Resource",
    is_regex=True,
    file_pattern="*.py",
    exclude_pattern="*test*.py",
    max_results=50
)

# Process results
if result['success']:
    for match in result['matches']:
        print(f"{match['file_path']}:{match['line_number']} - {match['line_text']}")
else:
    print(f"Error: {result['error']}")
    """)
