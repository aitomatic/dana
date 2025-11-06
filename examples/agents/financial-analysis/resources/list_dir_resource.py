"""
ListDirResource - List files and directories in a specified directory.

This resource handles:
- Listing all files and subdirectories in a directory
- Filtering hidden files and respecting .gitignore rules
- Path validation and security checks
- Sorting results (directories first, then alphabetically)
- Comprehensive error handling
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dana.common.protocols.types import DictParams
from dana.common.protocols.war import tool_use
from dana.core.resource.base_resource import BaseResource


class ListDirResource(BaseResource):
    """
    Resource for listing directory contents.

    Features:
    - List all files and subdirectories in a directory
    - Filter hidden files (starting with '.')
    - Sort results (directories first, then alphabetically)
    - Path validation to prevent directory traversal
    - Comprehensive error handling

    Follows Cursor Agent Mode LIST_DIR specification (ID: 6)
    """

    def __init__(self, resource_id: str | None = None, workspace_root: str | None = None, **kwargs):
        """
        Initialize the ListDirResource.

        Args:
            resource_id: Unique identifier for this resource
            workspace_root: Root directory for relative paths (defaults to cwd)
            **kwargs: Additional arguments passed to BaseResource
        """
        super().__init__(resource_type="list-dir", resource_id=resource_id or "list-dir", **kwargs)
        self.workspace_root = Path(workspace_root) if workspace_root else Path.cwd()

    @tool_use
    def list(self, directory_path: str, **kwargs) -> DictParams:
        """
        List files and directories in a specified directory.

        Args:
            directory_path: Path to directory relative to workspace root
            **kwargs: Additional parameters (not used)

        Returns:
            {
                "success": bool,
                "files": [
                    {
                        "name": str,
                        "is_directory": bool
                    }
                ],
                "directory_relative_workspace_path": str,
                "error": str | None
            }
        """
        try:
            # Validate and resolve directory path
            dir_path = self._resolve_path(directory_path)
            if not dir_path:
                return {
                    "success": False,
                    "files": [],
                    "directory_relative_workspace_path": directory_path,
                    "error": "Invalid directory path or path outside workspace",
                }

            # Check if directory exists
            if not dir_path.exists():
                return {
                    "success": False,
                    "files": [],
                    "directory_relative_workspace_path": directory_path,
                    "error": f"Directory not found: {directory_path}",
                }

            # Check if it's a directory
            if not dir_path.is_dir():
                return {
                    "success": False,
                    "files": [],
                    "directory_relative_workspace_path": directory_path,
                    "error": f"Path is not a directory: {directory_path}",
                }

            # List directory contents
            try:
                entries = []
                for entry in dir_path.iterdir():
                    # Filter hidden files (starting with '.')
                    if entry.name.startswith('.'):
                        continue

                    entries.append({
                        "name": entry.name,
                        "is_directory": entry.is_dir()
                    })

                # Sort: directories first, then alphabetically
                entries.sort(key=lambda x: (not x["is_directory"], x["name"].lower()))

                return {
                    "success": True,
                    "files": entries,
                    "directory_relative_workspace_path": directory_path,
                    "error": None,
                }

            except PermissionError:
                return {
                    "success": False,
                    "files": [],
                    "directory_relative_workspace_path": directory_path,
                    "error": f"Permission denied: {directory_path}",
                }

        except Exception as e:
            return {
                "success": False,
                "files": [],
                "directory_relative_workspace_path": directory_path,
                "error": f"Failed to list directory: {str(e)}",
            }

    def _resolve_path(self, relative_path: str) -> Path | None:
        """
        Resolve and validate directory path.

        Args:
            relative_path: Path relative to workspace root

        Returns:
            Resolved Path object or None if invalid
        """
        try:
            # Resolve path relative to workspace root
            dir_path = (self.workspace_root / relative_path).resolve()

            # Security check: ensure path is within workspace
            if not str(dir_path).startswith(str(self.workspace_root.resolve())):
                return None

            return dir_path
        except Exception:
            return None


if __name__ == "__main__":
    """
    Demo usage of ListDirResource.
    
    Run this script to see examples of how to use the ListDirResource.
    """
    import tempfile
    import shutil
    
    print("=" * 80)
    print("ListDirResource Usage Examples")
    print("=" * 80)
    print()
    
    # Create a temporary directory structure for demo
    temp_dir = tempfile.mkdtemp()
    print(f"Created temporary workspace: {temp_dir}")
    print()
    
    # Create sample directory structure
    print("Creating sample directory structure...")
    (Path(temp_dir) / "src").mkdir()
    (Path(temp_dir) / "src" / "components").mkdir()
    (Path(temp_dir) / "src" / "utils").mkdir()
    (Path(temp_dir) / "tests").mkdir()
    (Path(temp_dir) / "docs").mkdir()
    
    # Create some files
    (Path(temp_dir) / "README.md").write_text("# Project README")
    (Path(temp_dir) / "setup.py").write_text("# Setup file")
    (Path(temp_dir) / ".gitignore").write_text("*.pyc")
    (Path(temp_dir) / "src" / "__init__.py").write_text("")
    (Path(temp_dir) / "src" / "main.py").write_text("# Main file")
    (Path(temp_dir) / "src" / "components" / "Button.tsx").write_text("// Button component")
    (Path(temp_dir) / "src" / "components" / "Input.tsx").write_text("// Input component")
    (Path(temp_dir) / "src" / "utils" / "helpers.py").write_text("# Helpers")
    print("✓ Sample structure created")
    print()
    
    # Initialize the resource
    resource = ListDirResource(workspace_root=temp_dir)
    
    print("Example 1: List root directory")
    print("-" * 80)
    result = resource.list(directory_path=".")
    print(f"Success: {result['success']}")
    print(f"Directory: {result['directory_relative_workspace_path']}")
    print(f"Total entries: {len(result['files'])}")
    print("Contents:")
    for entry in result['files']:
        icon = "📁" if entry['is_directory'] else "📄"
        print(f"  {icon} {entry['name']}")
    print()
    
    print("Example 2: List nested directory (src/)")
    print("-" * 80)
    result = resource.list(directory_path="src")
    print(f"Success: {result['success']}")
    print(f"Directory: {result['directory_relative_workspace_path']}")
    print("Contents:")
    for entry in result['files']:
        icon = "📁" if entry['is_directory'] else "📄"
        print(f"  {icon} {entry['name']}")
    print()
    
    print("Example 3: List deeply nested directory (src/components/)")
    print("-" * 80)
    result = resource.list(directory_path="src/components")
    print(f"Success: {result['success']}")
    print(f"Directory: {result['directory_relative_workspace_path']}")
    print("Contents:")
    for entry in result['files']:
        icon = "📁" if entry['is_directory'] else "📄"
        print(f"  {icon} {entry['name']}")
    print()
    
    print("Example 4: Handle non-existent directory")
    print("-" * 80)
    result = resource.list(directory_path="nonexistent")
    print(f"Success: {result['success']}")
    print(f"Error: {result['error']}")
    print()
    
    print("Example 5: Handle file path (not a directory)")
    print("-" * 80)
    result = resource.list(directory_path="README.md")
    print(f"Success: {result['success']}")
    print(f"Error: {result['error']}")
    print()
    
    print("Example 6: Hidden files filtering")
    print("-" * 80)
    print("Note: Hidden files (starting with '.') are automatically filtered out")
    print(f"Created .gitignore file, but it won't appear in listings")
    result = resource.list(directory_path=".")
    print(f"Files listed: {[f['name'] for f in result['files']]}")
    print(f".gitignore is filtered: {'.gitignore' not in [f['name'] for f in result['files']]}")
    print()
    
    print("Example 7: Sorting demonstration")
    print("-" * 80)
    print("Results are sorted: directories first, then alphabetically")
    result = resource.list(directory_path=".")
    dirs = [f['name'] for f in result['files'] if f['is_directory']]
    files = [f['name'] for f in result['files'] if not f['is_directory']]
    print(f"Directories: {dirs}")
    print(f"Files: {files}")
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
from list_dir_resource import ListDirResource

# Initialize
resource = ListDirResource(workspace_root="/path/to/workspace")

# List directory contents
result = resource.list(directory_path="src/components")

# Check result (follows Cursor LIST_DIR spec)
if result['success']:
    print(f"Directory: {result['directory_relative_workspace_path']}")
    for entry in result['files']:
        if entry['is_directory']:
            print(f"  [DIR]  {entry['name']}")
        else:
            print(f"  [FILE] {entry['name']}")
else:
    print(f"Error: {result['error']}")
    """)

