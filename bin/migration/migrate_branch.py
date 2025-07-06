#!/usr/bin/env python3
"""
Branch Migration Tool for OpenDXA → Dana Migration

This script helps team members migrate their feature branches from old import paths
to new dana.* import paths while preserving git history and providing rollback capability.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], cwd: str = None) -> tuple[int, str, str]:
    """Run a shell command and return exit code, stdout, stderr."""
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            cwd=cwd
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def get_current_branch() -> str:
    """Get the current git branch name."""
    code, stdout, stderr = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if code == 0:
        return stdout.strip()
    else:
        raise Exception(f"Failed to get current branch: {stderr}")


def create_backup_branch(branch_name: str) -> str:
    """Create a backup branch before migration."""
    backup_name = f"backup-{branch_name}"
    
    # Check if backup already exists
    code, _, _ = run_command(["git", "rev-parse", "--verify", backup_name])
    if code == 0:
        print(f"⚠️  Backup branch '{backup_name}' already exists")
        return backup_name
    
    # Create backup
    code, stdout, stderr = run_command(["git", "checkout", "-b", backup_name])
    if code == 0:
        print(f"✅ Created backup branch: {backup_name}")
        
        # Switch back to original branch
        run_command(["git", "checkout", branch_name])
        return backup_name
    else:
        raise Exception(f"Failed to create backup branch: {stderr}")


def find_python_files(directory: Path) -> list[Path]:
    """Find all Python files in the given directory."""
    python_files = []
    for file_path in directory.rglob("*.py"):
        # Skip certain directories
        if any(skip in str(file_path) for skip in [".git", "__pycache__", ".pytest_cache", "node_modules"]):
            continue
        python_files.append(file_path)
    return python_files


def convert_imports_in_file(file_path: Path, dry_run: bool = False) -> int:
    """Convert imports in a single file. Returns number of changes made."""
    
    # Import mapping from old paths to new paths
    import_mappings = {
        # Core Dana Language
        "from dana.core.lang.parser": "from dana.core.lang.parser",
        "from dana.core.lang.interpreter": "from dana.core.lang.interpreter", 
        "from dana.core.lang.dana_sandbox": "from dana.core.lang.dana_sandbox",
        "from dana.core.lang": "from dana.core.lang",
        "import dana.core.lang": "import dana.core.lang",
        
        # Runtime and Module System
        "from dana.core.runtime.modules": "from dana.core.runtime.modules",
        "from dana.core.repl": "from dana.core.repl",
        "import dana.core.runtime.modules": "import dana.core.runtime.modules",
        "import dana.core.repl": "import dana.core.repl",
        
        # Standard Library Functions
        "from dana.core.lang.interpreter.functions": "from dana.core.stdlib",
        "import dana.core.lang.interpreter.functions": "import dana.core.stdlib",
        
        # Common Utilities
        "from dana.common": "from dana.common",
        "import dana.common": "import dana.common",
        
        # POET Framework
        "from dana.frameworks.poet": "from dana.frameworks.poet",
        "import dana.frameworks.poet": "import dana.frameworks.poet",
        
        # KNOWS Framework
        "from dana.frameworks.knows": "from dana.frameworks.knows",
        "import dana.frameworks.knows": "import dana.frameworks.knows",
        
        # Agent Framework
        "from dana.frameworks.agent": "from dana.frameworks.agent",
        "import dana.frameworks.agent": "import dana.frameworks.agent",
        
        # Integrations
        "from dana.integrations": "from dana.integrations",
        "import dana.integrations": "import dana.integrations",
    }
    
    try:
        with open(file_path, encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = 0
        
        # Apply import mappings
        for old_import, new_import in import_mappings.items():
            if old_import in content:
                content = content.replace(old_import, new_import)
                changes_made += content.count(new_import) - original_content.count(new_import)
        
        # Only write if changes were made and not in dry-run mode
        if changes_made > 0 and not dry_run:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        return changes_made
    
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return 0


def migrate_branch(branch_name: str, dry_run: bool = False) -> None:
    """Migrate a branch from old import paths to new ones."""
    
    print(f"{'🔍 DRY RUN: ' if dry_run else ''}Migrating branch: {branch_name}")
    print("=" * 60)
    
    # Check if we're on the right branch
    current_branch = get_current_branch()
    if current_branch != branch_name:
        print(f"❌ Currently on branch '{current_branch}', expected '{branch_name}'")
        print(f"Please run: git checkout {branch_name}")
        return
    
    # Create backup branch
    if not dry_run:
        backup_name = create_backup_branch(branch_name)
        print(f"💾 Backup created: {backup_name}")
    
    # Find all Python files
    repo_root = Path.cwd()
    python_files = find_python_files(repo_root)
    
    print(f"🔍 Found {len(python_files)} Python files to check")
    
    # Convert imports in each file
    total_changes = 0
    modified_files = []
    
    for file_path in python_files:
        changes = convert_imports_in_file(file_path, dry_run)
        if changes > 0:
            total_changes += changes
            modified_files.append(file_path)
            print(f"{'📝' if dry_run else '✏️ '} {file_path.relative_to(repo_root)}: {changes} changes")
    
    print("\n" + "=" * 60)
    print(f"{'🔍 Would modify' if dry_run else '✅ Modified'} {len(modified_files)} files")
    print(f"{'🔍 Would make' if dry_run else '✅ Made'} {total_changes} import changes")
    
    if not dry_run and total_changes > 0:
        # Stage the changes
        print("\n📦 Staging changes...")
        for file_path in modified_files:
            run_command(["git", "add", str(file_path)])
        
        # Create commit
        commit_msg = f"Migrate imports from opendxa.* to dana.* paths\n\n✨ Automated migration of {total_changes} import statements across {len(modified_files)} files"
        code, _, stderr = run_command(["git", "commit", "-m", commit_msg])
        
        if code == 0:
            print("✅ Migration committed successfully!")
        else:
            print(f"❌ Failed to commit changes: {stderr}")
    
    if dry_run:
        print("\n🔍 This was a dry run. To execute the migration, run:")
        print(f"   python scripts/migration/migrate_branch.py --branch {branch_name} --execute")
    else:
        print("\n🎉 Migration complete!")
        print(f"💡 To rollback if needed: git checkout {backup_name}")
        print("🧪 Next step: Run tests to verify everything works")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Migrate a branch from opendxa.* to dana.* imports")
    parser.add_argument("--branch", "-b", help="Branch name to migrate (defaults to current branch)")
    parser.add_argument("--dry-run", "-d", action="store_true", help="Show what would be changed without making changes")
    parser.add_argument("--execute", "-e", action="store_true", help="Execute the migration (opposite of dry-run)")
    
    args = parser.parse_args()
    
    # Determine dry run mode
    dry_run = args.dry_run or not args.execute
    
    # Get branch name
    if args.branch:
        branch_name = args.branch
    else:
        try:
            branch_name = get_current_branch()
        except Exception as e:
            print(f"❌ Error getting current branch: {e}")
            sys.exit(1)
    
    # Validate we're in a git repository
    if not Path(".git").exists():
        print("❌ This script must be run from the root of a git repository")
        sys.exit(1)
    
    try:
        migrate_branch(branch_name, dry_run)
    except KeyboardInterrupt:
        print("\n🛑 Migration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()