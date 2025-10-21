"""
EditFileResource - Edit files with search-replace or full content replacement.

This resource handles:
- Search-and-replace editing (old_string/new_string)
- Full file content replacement
- Whitespace-insensitive matching fallback
- Fuzzy string matching ("did you mean")
- Multiple match detection and handling
- Diff generation
- File size validation
- Line range editing

Follows Cursor Agent Mode EDIT_FILE specification (ID: 7)
"""

import difflib
import os
import re
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dana.common.protocols.types import DictParams
from dana.common.protocols.war import tool_use
from dana.core.resource.base_resource import BaseResource


class EditFileResource(BaseResource):
    """
    Resource for editing files with search-replace or full replacement.

    Features:
    - Two editing modes: search-replace and full replacement
    - Whitespace-insensitive matching fallback
    - Fuzzy matching ("did you mean")
    - Multiple match detection and control
    - Diff generation for review
    - File size validation (max 3500 lines or 150000 chars)
    - Line range editing support

    Follows Cursor Agent Mode EDIT_FILE specification (ID: 7)
    """

    def __init__(
        self, resource_id: str | None = None, workspace_root: str | None = None, auto_save: bool = True, **kwargs
    ):
        """
        Initialize the EditFileResource.

        Args:
            resource_id: Unique identifier for this resource
            workspace_root: Root directory for relative paths (defaults to cwd)
            auto_save: Whether to automatically save changes (default: True)
            **kwargs: Additional arguments passed to BaseResource
        """
        super().__init__(resource_type="edit-file", resource_id=resource_id or "edit-file", **kwargs)
        self.workspace_root = Path(workspace_root) if workspace_root else Path.cwd()
        self.auto_save = auto_save
        self.max_lines = 3500
        self.max_chars = 150000

    @tool_use
    def edit(
        self,
        relative_workspace_path: str,
        language: str,
        blocking: bool,
        contents: str,
        line_ranges: list[dict] | None = None,
        should_edit_file_fail_for_large_files: bool = False,
        old_string: str | None = None,
        new_string: str | None = None,
        allow_multiple_matches: bool = False,
        use_whitespace_insensitive_fallback: bool = False,
        use_did_you_mean_fuzzy_match: bool = False,
        **kwargs,
    ) -> DictParams:
        """
        Edit a file using search-replace or full replacement.

        Args:
            relative_workspace_path: Path to file relative to workspace root (REQUIRED)
            language: Programming language of the file (REQUIRED)
            blocking: Whether to block on completion (REQUIRED)
            contents: New file contents for full replacement (REQUIRED)
            line_ranges: Specific line ranges to edit (OPTIONAL)
            should_edit_file_fail_for_large_files: Fail if file too large (OPTIONAL, default: False)
            old_string: String to search for in search-replace mode (OPTIONAL)
            new_string: Replacement string in search-replace mode (OPTIONAL)
            allow_multiple_matches: Allow multiple replacements (OPTIONAL, default: False)
            use_whitespace_insensitive_fallback: Ignore whitespace differences (OPTIONAL, default: False)
            use_did_you_mean_fuzzy_match: Enable fuzzy matching (OPTIONAL, default: False)
            **kwargs: Additional parameters

        Returns:
            {
                "diff": {"old_content": str, "new_content": str},
                "is_applied": bool,
                "apply_failed": bool,
                "linter_errors": list,
                "rejected": bool | None,
                "num_matches": int | None
            }
        """
        try:
            # Determine edit mode
            if old_string is not None and new_string is not None:
                mode = "search-replace"
            elif contents:
                mode = "full-replacement"
            else:
                return {
                    "diff": {"old_content": "", "new_content": ""},
                    "is_applied": False,
                    "apply_failed": True,
                    "linter_errors": [],
                    "rejected": None,
                    "num_matches": None,
                }

            # Resolve and validate file path
            file_path = self._resolve_path(relative_workspace_path)
            if not file_path:
                return {
                    "diff": {"old_content": "", "new_content": ""},
                    "is_applied": False,
                    "apply_failed": True,
                    "linter_errors": [],
                    "rejected": None,
                    "num_matches": None,
                }

            # Check if file exists
            if not file_path.exists():
                return {
                    "diff": {"old_content": "", "new_content": ""},
                    "is_applied": False,
                    "apply_failed": True,
                    "linter_errors": [],
                    "rejected": None,
                    "num_matches": None,
                }

            # Read current file contents
            try:
                with open(file_path, encoding="utf-8") as f:
                    original_content = f.read()
            except UnicodeDecodeError:
                with open(file_path, encoding="latin-1") as f:
                    original_content = f.read()

            # Check file size
            lines_count = len(original_content.split("\n"))
            chars_count = len(original_content)
            is_large_file = lines_count > self.max_lines or chars_count > self.max_chars

            if is_large_file and should_edit_file_fail_for_large_files and mode == "full-replacement":
                return {
                    "diff": {"old_content": "", "new_content": ""},
                    "is_applied": False,
                    "apply_failed": True,
                    "linter_errors": [],
                    "rejected": None,
                    "num_matches": None,
                }

            # Perform edit based on mode
            if mode == "search-replace":
                # Type check for search-replace mode (should not be None here)
                if old_string is None or new_string is None:
                    return {
                        "diff": {"old_content": original_content, "new_content": original_content},
                        "is_applied": False,
                        "apply_failed": True,
                        "linter_errors": [],
                        "rejected": None,
                        "num_matches": None,
                    }
                
                result = self._search_replace(
                    original_content=original_content,
                    old_string=old_string,
                    new_string=new_string,
                    allow_multiple_matches=allow_multiple_matches,
                    use_whitespace_insensitive_fallback=use_whitespace_insensitive_fallback,
                    use_did_you_mean_fuzzy_match=use_did_you_mean_fuzzy_match,
                )
                if not result["success"]:
                    return {
                        "diff": {"old_content": original_content, "new_content": original_content},
                        "is_applied": False,
                        "apply_failed": True,
                        "linter_errors": [],
                        "rejected": None,
                        "num_matches": None,
                    }
                new_content = result["new_content"]
                num_matches = result["num_matches"]
            else:
                # Full replacement mode
                if line_ranges:
                    # Apply to specific line ranges
                    new_content = self._apply_line_ranges(original_content, contents, line_ranges)
                else:
                    # Replace entire file
                    new_content = contents
                num_matches = None

            # Generate diff
            diff_result = self._generate_diff(original_content, new_content)

            # Apply changes if auto_save is enabled
            is_applied = False
            apply_failed = False
            if self.auto_save and blocking:
                try:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    is_applied = True
                except Exception:
                    apply_failed = True

            return {
                "diff": diff_result,
                "is_applied": is_applied,
                "apply_failed": apply_failed,
                "linter_errors": [],  # Empty for basic implementation
                "rejected": None,  # None for basic implementation
                "num_matches": num_matches,
            }

        except Exception:
            return {
                "diff": {"old_content": "", "new_content": ""},
                "is_applied": False,
                "apply_failed": True,
                "linter_errors": [],
                "rejected": None,
                "num_matches": None,
            }

    def _search_replace(
        self,
        original_content: str,
        old_string: str,
        new_string: str,
        allow_multiple_matches: bool,
        use_whitespace_insensitive_fallback: bool,
        use_did_you_mean_fuzzy_match: bool,
    ) -> dict:
        """Perform search-and-replace editing."""
        # Find matches
        if use_whitespace_insensitive_fallback:
            matches = self._find_whitespace_insensitive_matches(original_content, old_string)
        else:
            matches = self._find_exact_matches(original_content, old_string)

        # Check for fuzzy match if no exact matches found
        if len(matches) == 0 and use_did_you_mean_fuzzy_match:
            fuzzy_result = self._find_fuzzy_match(original_content, old_string)
            if fuzzy_result:
                matches = [fuzzy_result]

        # Validate number of matches
        if len(matches) == 0:
            return {"success": False, "error": f"String not found in file: '{old_string[:50]}...'"}

        if len(matches) > 1 and not allow_multiple_matches:
            return {
                "success": False,
                "error": f"Found {len(matches)} matches. Set allow_multiple_matches=True or make old_string more specific.",
            }

        # Perform replacements (from end to start to preserve positions)
        new_content = original_content
        for start, end in reversed(matches):
            new_content = new_content[:start] + new_string + new_content[end:]

        return {"success": True, "new_content": new_content, "num_matches": len(matches)}

    def _find_exact_matches(self, content: str, search_string: str) -> list:
        """Find exact string matches and return (start, end) positions."""
        matches = []
        start = 0
        while True:
            pos = content.find(search_string, start)
            if pos == -1:
                break
            matches.append((pos, pos + len(search_string)))
            start = pos + 1
        return matches

    def _find_whitespace_insensitive_matches(self, content: str, search_string: str) -> list:
        """Find matches ignoring whitespace differences."""
        # Normalize whitespace in search string
        normalized_search = re.sub(r"\s+", r"\\s+", re.escape(search_string))
        pattern = re.compile(normalized_search)

        matches = []
        for match in pattern.finditer(content):
            matches.append((match.start(), match.end()))
        return matches

    def _find_fuzzy_match(self, content: str, search_string: str, threshold: float = 0.8) -> tuple | None:
        """Find best fuzzy match using difflib."""
        # Split content into chunks of similar size to search string
        chunk_size = len(search_string)
        step_size = max(1, chunk_size // 4)  # Overlap chunks

        best_match = None
        best_ratio = 0

        for i in range(0, len(content) - chunk_size + 1, step_size):
            chunk = content[i : i + chunk_size]
            ratio = difflib.SequenceMatcher(None, search_string, chunk).ratio()

            if ratio > best_ratio and ratio >= threshold:
                best_ratio = ratio
                best_match = (i, i + chunk_size)

        return best_match

    def _apply_line_ranges(self, original_content: str, new_content: str, line_ranges: list[dict]) -> str:
        """Apply new content to specific line ranges."""
        lines = original_content.split("\n")
        new_lines = new_content.split("\n")

        # Apply each line range
        for line_range in line_ranges:
            start = line_range.get("start", 0)
            end = line_range.get("end", len(lines))
            lines[start:end] = new_lines

        return "\n".join(lines)

    def _generate_diff(self, old_content: str, new_content: str) -> dict:
        """Generate diff between old and new content."""
        return {"old_content": old_content, "new_content": new_content}

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
    Demo usage of EditFileResource.
    
    Run this script to see examples of how to use the EditFileResource.
    """
    import tempfile
    import shutil
    
    print("=" * 80)
    print("EditFileResource Usage Examples")
    print("=" * 80)
    print()
    
    # Create a temporary directory for demo
    temp_dir = tempfile.mkdtemp()
    print(f"Created temporary workspace: {temp_dir}")
    print()
    
    # Create a demo file
    demo_file = Path(temp_dir) / "demo.py"
    demo_content = """def hello(name):
    print(f"Hello {name}")
    return True

def goodbye(name):
    print(f"Goodbye {name}")
    return False
"""
    demo_file.write_text(demo_content)
    print(f"Created demo file: {demo_file}")
    print("Original content:")
    print(demo_content)
    print()
    
    # Initialize the resource
    resource = EditFileResource(workspace_root=temp_dir, auto_save=False)
    
    print("Example 1: Search-and-replace (simple)")
    print("-" * 80)
    result = resource.edit(
        relative_workspace_path="demo.py",
        language="python",
        blocking=True,
        contents="",  # Required but not used in search-replace mode
        old_string='print(f"Hello {name}")',
        new_string='print(f"Hello, {name}!")',
    )
    print(f"Applied: {result['is_applied']}")
    print(f"Failed: {result['apply_failed']}")
    print(f"Number of matches: {result.get('num_matches', 'N/A')}")
    print(f"Linter errors: {len(result['linter_errors'])}")
    print()
    
    print("Example 2: Full content replacement")
    print("-" * 80)
    new_content = """# Updated file
def greet(name: str) -> None:
    \"\"\"Greet someone.\"\"\"
    print(f"Hello, {name}!")
"""
    result = resource.edit(
        relative_workspace_path="demo.py",
        language="python",
        blocking=True,
        contents=new_content,
    )
    print(f"Applied: {result['is_applied']}")
    print(f"Failed: {result['apply_failed']}")
    print("New content:")
    print(new_content)
    print()
    
    print("Example 3: Search-replace with whitespace-insensitive fallback")
    print("-" * 80)
    # Reset demo file
    demo_file.write_text(demo_content)
    result = resource.edit(
        relative_workspace_path="demo.py",
        language="python",
        blocking=True,
        contents="",
        old_string="def hello(name):\n    print",  # May have different whitespace
        new_string="def hello(name):\n    # Say hello\n    print",
        use_whitespace_insensitive_fallback=True,
    )
    print(f"Applied: {result['is_applied']}")
    print(f"Failed: {result['apply_failed']}")
    print()
    
    print("Example 4: Multiple matches with allow_multiple_matches")
    print("-" * 80)
    demo_file.write_text(demo_content)
    result = resource.edit(
        relative_workspace_path="demo.py",
        language="python",
        blocking=True,
        contents="",
        old_string="return",
        new_string="# Modified\n    return",
        allow_multiple_matches=True,
    )
    print(f"Applied: {result['is_applied']}")
    print(f"Failed: {result['apply_failed']}")
    print(f"Number of matches: {result.get('num_matches', 'N/A')}")
    print()
    
    print("Example 5: Fuzzy matching with use_did_you_mean_fuzzy_match")
    print("-" * 80)
    demo_file.write_text(demo_content)
    result = resource.edit(
        relative_workspace_path="demo.py",
        language="python",
        blocking=True,
        contents="",
        old_string='def hello(name):',  # Exact match
        new_string='def hello(name: str):',
        use_did_you_mean_fuzzy_match=True,
    )
    print(f"Applied: {result['is_applied']}")
    print(f"Failed: {result['apply_failed']}")
    if result['is_applied']:
        print("Matched and replaced successfully with fuzzy matching")
    print()
    
    # Cleanup
    shutil.rmtree(temp_dir)
    print(f"Cleaned up temporary workspace")
    print()
    
    print("=" * 80)
    print("Usage in code:")
    print("=" * 80)
    print("""
# Import the resource
from edit_file_resource import EditFileResource

# Initialize
resource = EditFileResource(workspace_root="/path/to/workspace", auto_save=True)

# Search-and-replace mode (Cursor spec)
result = resource.edit(
    relative_workspace_path="path/to/file.py",
    language="python",
    blocking=True,
    contents="",  # Required but empty for search-replace
    old_string="old_text",
    new_string="new_text",
    allow_multiple_matches=False,
    use_whitespace_insensitive_fallback=False,
    use_did_you_mean_fuzzy_match=False
)

# Full replacement mode (Cursor spec)
result = resource.edit(
    relative_workspace_path="path/to/file.py",
    language="python",
    blocking=True,
    contents="Complete new file content"
)

# Check result (Cursor spec format)
if result['is_applied']:
    print(f"Applied successfully")
    print(f"Matches: {result.get('num_matches', 'N/A')}")
    print(f"Diff: {result['diff']}")
elif result['apply_failed']:
    print("Edit failed")
    """)
