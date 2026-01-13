"""
CreateFileResource - Create new empty files.

This resource handles:
- Creating new empty files at specified paths
- Automatic parent directory creation
- File existence checking
- Path validation and security

Follows Cursor Agent Mode CREATE_FILE specification (ID: 10)
Note: Creates ONLY empty files (no content parameter in Cursor spec)
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dana.common.protocols.types import DictParams
from dana.common.protocols.war import tool_use
from dana.core.resource.base_resource import BaseResource


class CreateFileResource(BaseResource):
    """
    Resource for creating new empty files in the workspace.

    Features:
    - Create empty files at specified paths
    - Automatic parent directory creation
    - File existence detection
    - Path validation to prevent directory traversal
    - Comprehensive error handling

    Follows Cursor Agent Mode CREATE_FILE specification (ID: 10)
    Note: Per Cursor spec, only creates empty files (no content parameter)
    """

    def __init__(self, resource_id: str | None = None, workspace_root: str | None = None, **kwargs):
        """
        Initialize the CreateFileResource.

        Args:
            resource_id: Unique identifier for this resource
            workspace_root: Root directory for relative paths (defaults to cwd)
            **kwargs: Additional arguments passed to BaseResource
        """
        super().__init__(resource_type="create-file", resource_id=resource_id or "create-file", **kwargs)
        self.workspace_root = Path(workspace_root) if workspace_root else Path.cwd()

    @tool_use
    def create(self, relative_workspace_path: str, **kwargs) -> DictParams:
        """
        Create a new empty file at the specified path.

        Args:
            relative_workspace_path: Path to file relative to workspace root (REQUIRED)
            **kwargs: Additional parameters (for framework compatibility)

        Returns:
            {
                "file_created_successfully": bool,  # True if created
                "file_already_exists": bool         # True if file existed
            }
        """
        try:
            # Validate and resolve file path
            file_path = self._resolve_path(relative_workspace_path)
            if not file_path:
                return {
                    "file_created_successfully": False,
                    "file_already_exists": False,
                }

            # Check if file already exists
            if file_path.exists():
                return {
                    "file_created_successfully": False,
                    "file_already_exists": True,
                }

            # Create parent directories if needed
            try:
                file_path.parent.mkdir(parents=True, exist_ok=True)
            except Exception:
                return {
                    "file_created_successfully": False,
                    "file_already_exists": False,
                }

            # Create empty file
            try:
                file_path.touch()  # Creates empty file with proper permissions
            except Exception:
                return {
                    "file_created_successfully": False,
                    "file_already_exists": False,
                }

            return {
                "file_created_successfully": True,
                "file_already_exists": False,
            }

        except Exception:
            return {
                "file_created_successfully": False,
                "file_already_exists": False,
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
    Demo usage of CreateFileResource.
    
    Run this script to see examples of how to use the CreateFileResource.
    Note: Per Cursor spec, this resource creates ONLY empty files.
    """
    import tempfile
    import shutil

    print("=" * 80)
    print("CreateFileResource Usage Examples")
    print("=" * 80)
    print("NOTE: Per Cursor Agent Mode spec, CREATE_FILE only creates EMPTY files")
    print("=" * 80)
    print()

    # Create a temporary directory for demo
    temp_dir = tempfile.mkdtemp()
    print(f"Created temporary workspace: {temp_dir}")
    print()

    # Initialize the resource
    resource = CreateFileResource(workspace_root=temp_dir)

    print("Example 1: Create a simple empty file")
    print("-" * 80)
    result = resource.create(relative_workspace_path="hello.txt")
    print(f"File created successfully: {result['file_created_successfully']}")
    print(f"File already exists: {result['file_already_exists']}")
    if result["file_created_successfully"]:
        created_file = Path(temp_dir) / "hello.txt"
        print(f"File exists: {created_file.exists()}")
        print(f"File size: {created_file.stat().st_size} bytes (empty)")
    print()

    print("Example 2: Create file with nested directories (auto-created)")
    print("-" * 80)
    result = resource.create(relative_workspace_path="src/components/Button.tsx")
    print(f"File created successfully: {result['file_created_successfully']}")
    print(f"File already exists: {result['file_already_exists']}")
    if result["file_created_successfully"]:
        created_file = Path(temp_dir) / "src/components/Button.tsx"
        print(f"File exists: {created_file.exists()}")
        print("Parent directories created: src/components/")
        print(f"File size: {created_file.stat().st_size} bytes (empty)")
    print()

    print("Example 3: Try to create existing file")
    print("-" * 80)
    result = resource.create(relative_workspace_path="hello.txt")
    print(f"File created successfully: {result['file_created_successfully']}")
    print(f"File already exists: {result['file_already_exists']}")
    print("Result: Cannot create - file already exists")
    print()

    print("Example 4: Create multiple empty files")
    print("-" * 80)
    files_to_create = ["config/settings.json", "config/database.conf", "logs/app.log", "logs/error.log"]
    for file_path in files_to_create:
        result = resource.create(relative_workspace_path=file_path)
        status = "✓" if result["file_created_successfully"] else "✗"
        print(f"{status} {file_path}")
    print()

    print("Example 5: Handle invalid path (security check)")
    print("-" * 80)
    result = resource.create(relative_workspace_path="../outside_workspace.txt")
    print(f"File created successfully: {result['file_created_successfully']}")
    print(f"File already exists: {result['file_already_exists']}")
    print("Result: Path outside workspace - rejected")
    print()

    print("Example 6: Create Python module structure")
    print("-" * 80)
    python_files = ["mypackage/__init__.py", "mypackage/core.py", "mypackage/utils.py", "tests/__init__.py", "tests/test_core.py"]
    for file_path in python_files:
        result = resource.create(relative_workspace_path=file_path)
        if result["file_created_successfully"]:
            print(f"Created: {file_path}")
    print()

    # List all created files
    print("Summary: All files created in temporary workspace")
    print("-" * 80)
    for root, dirs, files in os.walk(temp_dir):
        level = root.replace(temp_dir, "").count(os.sep)
        indent = " " * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        sub_indent = " " * 2 * (level + 1)
        for file in files:
            file_path = Path(root) / file
            size = file_path.stat().st_size
            print(f"{sub_indent}{file} ({size} bytes)")
    print()

    # Cleanup
    shutil.rmtree(temp_dir)
    print("Cleaned up temporary workspace")
    print()

    print("=" * 80)
    print("Usage in code (Cursor Agent Mode spec):")
    print("=" * 80)
    print("""
# Import the resource
from create_file_resource import CreateFileResource

# Initialize
resource = CreateFileResource(workspace_root="/path/to/workspace")

# Create empty file (ONLY parameter: relative_workspace_path)
result = resource.create(
    relative_workspace_path="new_file.txt"
)

# Check result (Cursor CREATE_FILE spec - ONLY 2 fields)
if result['file_created_successfully']:
    print("Empty file created successfully!")
elif result['file_already_exists']:
    print("File already exists")
else:
    print("Failed to create file")

# Note: Per Cursor spec, CREATE_FILE only creates EMPTY files.
# To add content, use EDIT_FILE resource after creation.
    """)
